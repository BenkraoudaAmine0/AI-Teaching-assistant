import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME", "ai_teaching_assistant")

client = MongoClient(MONGO_URL)

db = client[DB_NAME]

# User collection
users_collection = db["users"]
# Chunk collection
chunk_collection = db["text"]
# chat history collection
chat_history_collection = db["chat_history"]
