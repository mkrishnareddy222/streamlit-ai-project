from dotenv import load_dotenv 
import os

from dotenv import load_dotenv 

load_dotenv() 

GROQ_API_KEY = os.getenv("GROQ_API_KEY") 
MODEL_NAME = os.getenv("MODEL_NAME") 
ENVIRONMENT = os.getenv("ENVIRONMENT")
BACKEND_STREAM_URL = os.getenv("BACKEND_STREAM_URL")

