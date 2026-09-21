from bson import ObjectId
from bson.errors import InvalidId
from models.pdf import PDF
from config.exceptions import PDFNotFoundException


class PDFRepository:
    def __init__(self, db):
        if db is None:
            raise ValueError(
                "PDFRepository requiere una conexión de base de datos inyectada (db)"
            )
        self.db = db
        self.collection = self.db["pdfs"]

    def find_by_checksum(self, checksum: str) -> dict | None:
        return self.collection.find_one({"checksum": checksum})

    def get_pdfs(self) -> list[dict]:
        return [self._serialize_pdf(doc) for doc in self.collection.find()]

    def create_pdf(self, pdf: PDF) -> str:
        result = self.collection.insert_one(pdf.model_dump(exclude={"id"}))
        return str(result.inserted_id)

    def get_pdf_by_id(self, pdf_id: str) -> dict:
        try:
            doc = self.collection.find_one({"_id": ObjectId(pdf_id)})
            if not doc:
                raise PDFNotFoundException(f"PDF con id {pdf_id} no encontrado")
            return self._serialize_pdf(doc)
        except InvalidId:
            raise PDFNotFoundException(f"PDF con id {pdf_id} no encontrado")

    def update_pdf(self, pdf_id: str, pdf: PDF) -> dict:
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(pdf_id)}, {"$set": pdf.model_dump(exclude={"id"})}
            )
            if result.matched_count == 0:
                raise PDFNotFoundException(f"PDF con id {pdf_id} no encontrado")

            updated_doc = self.collection.find_one({"_id": ObjectId(pdf_id)})
            return self._serialize_pdf(updated_doc) if updated_doc else None
        except InvalidId:
            raise PDFNotFoundException(f"PDF con id {pdf_id} no encontrado")

    def delete_pdf(self, pdf_id: str) -> dict:
        try:
            result = self.collection.delete_one({"_id": ObjectId(pdf_id)})
            if result.deleted_count == 0:
                raise PDFNotFoundException(f"PDF con id {pdf_id} no encontrado")
            return {
                "status": "success",
                "id": pdf_id,
                "message": "PDF eliminado correctamente",
            }
        except InvalidId:
            raise PDFNotFoundException(f"PDF con id {pdf_id} no encontrado")

    @staticmethod
    def _serialize_pdf(doc: dict) -> dict:
        doc["id"] = str(doc.pop("_id"))
        return doc
