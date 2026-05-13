from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

user = os.getenv("MONGO_USER")
password = os.getenv("MONGO_PASS")
host = os.getenv("MONGO_HOST", "localhost")
port = os.getenv("MONGO_PORT", "27017")

if not user or not password:
    raise ValueError(
        "Faltan las variables de entorno MONGO_USER y/o MONGO_PASS. "
        "Creá un archivo .env en la raíz del proyecto basado en .env.example"
    )

uri = f"mongodb://{user}:{password}@{host}:{port}/"

client = MongoClient(uri)
db = client["PDF-Extractext"]
