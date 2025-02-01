import json
import logging
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from app import tools
from app.chat import Chat
from app.database import DBWrapper
from app.guard import Guard
from app.models.models import ChatModel, QuestionModel, User
from app.project import Project
from app.projects.base import ProjectBase


class Inference(ProjectBase):

    def chat(self, project: Project, chat_model: ChatModel, user: User, db: DBWrapper):

        chat: Chat = Chat(chat_model, self.brain.chat_store)
        output = {
            "question": chat_model.question,
            "type": "inference",
            "sources": [],
            "guard": False,
            "tokens": {
                "input": 0,
                "output": 0
            },
            "project": project.model.name,
            "id": chat.chat_id
        }

        if project.model.guard:
            guard = Guard(project.model.guard, self.brain, db)
            if guard.verify(chat_model.question):
                output["answer"] = project.model.censorship or self.brain.defaultCensorship
                output["guard"] = True
                self.brain.post_processing_counting(output)
                yield output

        model = self.brain.get_llm(project.model.llm, db)

        sysTemplate = project.model.system or self.brain.defaultSystem

        if sysTemplate:
            model.llm.system_prompt = sysTemplate

            if not chat.memory.get_all():
                chat.memory.chat_store.add_message(chat.memory.chat_store_key,
                                                   ChatMessage(role=MessageRole.SYSTEM, content=sysTemplate))

        chat.memory.chat_store.add_message(chat.memory.chat_store_key,
                                           ChatMessage(role=MessageRole.USER, content=chat_model.question))
        messages = chat.memory.get_all()

        try:
            if chat_model.stream:
                resp_gen = model.llm.stream_chat(messages)
                response = ""
                for text in resp_gen:
                    response += text.delta
                    yield "data: " + json.dumps({"text": text.delta}) + "\n\n"
                output["answer"] = response
                chat.memory.chat_store.add_message(chat.memory.chat_store_key,
                                                   ChatMessage(role=MessageRole.ASSISTANT, content=response))
                
                self.brain.post_processing_reasoning(output)
                self.brain.post_processing_counting(output)
                
                yield "data: " + json.dumps(output) + "\n"
                yield "event: close\n\n"
            else:
                resp = model.llm.chat(messages)
                if resp.message and resp.message.content:
                    output["answer"] = resp.message.content.strip()
                else:
                    output["answer"] = ""
                
                chat.memory.chat_store.add_message(chat.memory.chat_store_key, ChatMessage(role=MessageRole.ASSISTANT,
                                                                                           content=resp.message.content.strip()))

                self.brain.post_processing_reasoning(output)
                self.brain.post_processing_counting(output)

                yield output
        except Exception as e:
            logging.exception(e)
            if chat_model.stream:
                yield "data: Inference failed\n"
                yield "event: error\n\n"
            raise e

    def question(self, project: Project, question_model: QuestionModel, user: User, db: DBWrapper):
        output = {
            "question": question_model.question,
            "type": "inference",
            "sources": [],
            "guard": False,
            "tokens": {
                "input": 0,
                "output": 0
            },
            "project": project.model.name
        }

        if project.model.guard:
            guard = Guard(project.model.guard, self.brain, db)
            if guard.verify(question_model.question):
                output["answer"] = project.model.censorship or self.brain.defaultCensorship
                output["guard"] = True
                self.brain.post_processing_counting(output)
                yield output

        model = self.brain.get_llm(project.model.llm, db)

        sysTemplate = question_model.system or project.model.system or self.brain.defaultSystem

        messages = []

        if sysTemplate:
            model.llm.system_prompt = sysTemplate
            messages.append(ChatMessage(
                role=MessageRole.SYSTEM, content=sysTemplate
            ))

        messages.append(ChatMessage(role=MessageRole.USER,
                        content=question_model.question))

        try:
            if question_model.stream:
                resp_gen = model.llm.stream_chat(messages)
                response = ""
                for text in resp_gen:
                    response += text.delta
                    yield "data: " + json.dumps({"text": text.delta}) + "\n\n"
                output["answer"] = response
                
                self.brain.post_processing_reasoning(output)
                self.brain.post_processing_counting(output)
                
                yield "data: " + json.dumps(output) + "\n"
                yield "event: close\n\n"
            else:
                resp = model.llm.chat(messages)
                output["answer"] = resp.message.content.strip()
                
                self.brain.post_processing_reasoning(output)
                self.brain.post_processing_counting(output)
                
                yield output
        except Exception as e:
            logging.exception(e)
            if question_model.stream:
                yield "data: Inference failed\n"
                yield "event: error\n\n"
            raise e
