import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "chat_app_db")

client = MongoClient(MONGO_URI)
db = client[MONGO_DATABASE]


def close_mongo_client() -> None:
	"""Close the shared client during application shutdown."""
	client.close()
