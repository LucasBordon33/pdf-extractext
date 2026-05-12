from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

user = os.getenv("MONGO_USER")
password = os.getenv("MONGO_PASS")

if not user or not password:
    raise ValueError(
        "Faltan las variables de entorno MONGO_USER y/o MONGO_PASS. "
        "Creá un archivo .env en la raíz del proyecto basado en .env.example"
    )

uri = f"mongodb+srv://{user}:{password}@pdf-extractext.crqbr3j.mongodb.net/?appName=PDF-Extractext"

client = MongoClient(uri)
db = client["PDF-Extractext"]
