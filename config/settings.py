from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

user = os.getenv("MONGO_USER")
password = os.getenv("MONGO_PASS")

uri = f"mongodb+srv://{user}:{password}@pdf-extractext.crqbr3j.mongodb.net/?appName=PDF-Extractext"

client = MongoClient(uri)
db = client["PDF-Extractext"]
