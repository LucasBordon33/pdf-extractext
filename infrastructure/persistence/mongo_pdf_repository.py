"""
INFRAESTRUCTURA — Adaptador de persistencia MongoDB.

Implementa el puerto `PDFRepositoryPort`. SOLO acceso a datos:
- No existe lógica de duplicados (la regla vive en la capa de aplicación);
  aquí solo hay la consulta `find_by_checksum`.
- Detalles de Mongo (ObjectId, colección "pdfs") quedan confinados aquí.

Para migrar a SQL: crear un `SQLPDFRepository(PDFRepositoryPort)` y
registrarlo en `interfaces/dependencies.py`. Nada más cambia.
"""
from bson import ObjectId
from bson.errors import InvalidId

from application.ports import PDFRepositoryPort
from domain.entities import PDF


class MongoPDFRepository(PDFRepositoryPort):
    def __init__(self, db) -> None:
        if db is None:
            raise RuntimeError("Database connection not available")
        self._collection = db["pdfs"]

    @staticmethod
    def _serialize(doc: dict) -> dict:
        doc["id"] = str(doc.pop("_id"))
        return doc

    # --- Consultas (sin reglas de negocio) ------------------------------
    def find_by_checksum(self, checksum: str) -> dict | None:
        doc = self._collection.find_one({"checksum": checksum})
        return self._serialize(doc) if doc else None

    def find_all(self) -> list[dict]:
        return [self._serialize(doc) for doc in self._collection.find()]

    def find_by_id(self, pdf_id: str) -> dict | None:
        try:
            doc = self._collection.find_one({"_id": ObjectId(pdf_id)})
        except InvalidId:
            return None
        return self._serialize(doc) if doc else None

    # --- Persistencia ----------------------------------------------------
    def save(self, pdf: PDF) -> str:
        # La entidad de dominio no tiene `id`: Mongo genera `_id` y se
        # expone como "id" solo al serializar (read-model), nunca en dominio.
        result = self._collection.insert_one(pdf.model_dump())
        return str(result.inserted_id)

    def update(self, pdf_id: str, pdf: PDF) -> dict | None:
        result = self._collection.update_one(
            {"_id": ObjectId(pdf_id)},
            {"$set": pdf.model_dump()},
        )
        if result.matched_count == 0:
            return None
        return self._serialize(self._collection.find_one({"_id": ObjectId(pdf_id)}))

    def delete(self, pdf_id: str) -> bool:
        return self._collection.delete_one({"_id": ObjectId(pdf_id)}).deleted_count > 0
