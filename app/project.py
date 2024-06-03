from app.cache import Cache
from app.models.models import ProjectModel
from app.vectordb.tools import FindEmbeddingsPath


class Project:

    def __init__(self, model: ProjectModel):
        self.vector = None
        self.model = model
        
        if self.model.cache:
            self.cache = Cache(self)
        else:
            self.cache = None
            
        if self.model.type == "rag":
            FindEmbeddingsPath(self.model.name)
            

    def delete(self):
        if self.vector:
            self.vector.delete()
        if self.cache:
            self.cache.delete()
        
