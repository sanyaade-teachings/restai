import os
from fastapi import HTTPException
from modules.loaders import LOADERS


def IndexDocuments(brain, project, documents):
    texts = brain.text_splitter.split_documents(documents)
    texts_final = [doc.page_content for doc in texts]
    metadatas = [doc.metadata for doc in texts]

    for metadata in metadatas:
      for key, value in list(metadata.items()):
        if value is None:
            del metadata[key]
    
    project.db.add_texts(texts=texts_final, metadatas=metadatas)
    return texts_final


def FindFileLoader(filepath, ext):
    if ext in LOADERS:
      loader_class, loader_args = LOADERS[ext]
      return loader_class(filepath, **loader_args)
    else:
        raise Exception("Invalid file type.")
      
      
def FindEmbeddingsPath(projectName): 
    embeddings_path = os.environ["EMBEDDINGS_PATH"]
    project_dirs = [d for d in os.listdir(embeddings_path) if os.path.isdir(os.path.join(embeddings_path, d))]

    for dir in project_dirs:
        if dir.startswith(projectName + "_"):
            return os.path.join(embeddings_path, dir)

    raise Exception("Project not found.")