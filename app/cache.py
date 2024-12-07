import math
import shutil
import chromadb
import uuid

from app.vectordb.tools import find_embeddings_path

class Cache:
  
    def __init__(self, project):
        self.project = project
        self.client = chromadb.PersistentClient(path=find_embeddings_path(self.project.model.name + "_cache"))
        self.collection = self.client.get_or_create_collection(name=self.project.model.name + "_cache")
        
    def verify(self, question):
        results = self.collection.query(
            query_texts=[question],
            n_results=1,
            include=["metadatas", "documents", "distances"],
        )
        
        if len(results["ids"][0]) == 0:
            return None
        else:
            distance = math.exp(-results["distances"][0][0])
            if distance > self.project.model.cache_threshold:
                metadata = results["metadatas"][0][0]
                answer = metadata["answer"]
                return answer
            else:
                return None
        

    def add(self, question, answer):
        self.collection.add(
            documents=[question],
            metadatas=[{"question": question, "answer": answer}],
            ids=[str(uuid.uuid4())],
        )
        
        return True
      
    def delete(self):
        try:
            embeddingsPath = find_embeddings_path(self.project.model.name + "_cache")
            shutil.rmtree(embeddingsPath, ignore_errors=True)
        except BaseException:
            pass