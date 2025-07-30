import os

from dotenv import load_dotenv

load_dotenv(override=True)

LLM_API_KEY = os.getenv('LLM_API_KEY')
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')

MILVUS_URI = 'http://150.158.55.76:19530'

COLLECTION_NAME = 't_collection01'
