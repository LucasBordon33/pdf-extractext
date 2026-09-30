from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_NAME = "PDF-Extractext"

_client: MongoClient | None = None


def _build_uri() -> str:
    user = os.getenv("MONGO_USER")
    password = os.getenv("MONGO_PASS")
    host = os.getenv("MONGO_HOST", "mongodb")
    port = os.getenv("MONGO_PORT", "27017")

    if not user or not password:
        raise ValueError(
            "Faltan las variables de entorno MONGO_USER y/o MONGO_PASS. "
            "Creá un archivo .env en la raíz del proyecto basado en .env.example"
        )

    return f"mongodb://{user}:{password}@{host}:{port}/"


def get_client() -> MongoClient:
    """Devuelve el cliente de MongoDB, creándolo de forma diferida (lazy)."""
    global _client
    if _client is None:
        _client = MongoClient(_build_uri())
    return _client


def get_db():
    """Devuelve la base de datos de la aplicación (conexión diferida)."""
    return get_client()[DATABASE_NAME]
