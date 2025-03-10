import base64
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
import requests

from restai.models.models import ImageModel

def generate(imageModel: ImageModel):
    model = DallEAPIWrapper()
    model.model_name = "dall-e-3"
    image_url = model.run(imageModel.prompt)

    response = requests.get(image_url)
    response.raise_for_status()
    image_data = response.content
    return base64.b64encode(image_data).decode('utf-8')
