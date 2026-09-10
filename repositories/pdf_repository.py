from bson import ObjectId
from bson.errors import InvalidId
from models.pdf import PDF


class PDFRepository:
    def __init__(self, db=None):
        if db is None:
            from config.settings import db as _db

            db = _db

        if db is None:
            raise RuntimeError("Database connection not available")
        self.db = db
        self.collection = self.db["pdfs"]

    def find_by_checksum(self, checksum: str) -> dict | None:
        return self.collection.find_one({"checksum": checksum})

    def get_pdfs(self) -> list[dict]:
        return [self._serialize_pdf(doc) for doc in self.collection.find()]

    def create_pdf(self, pdf: PDF) -> str:
        result = self.collection.insert_one(pdf.model_dump(exclude={"id"}))
        return str(result.inserted_id)

    def get_pdf_by_id(self, pdf_id: str) -> dict | None:
        try:
            doc = self.collection.find_one({"_id": ObjectId(pdf_id)})
            return self._serialize_pdf(doc) if doc else None
        except InvalidId:
            return None

    def update_pdf(self, pdf_id: str, pdf: PDF) -> dict | None:
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(pdf_id)}, {"$set": pdf.model_dump(exclude={"id"})}
            )
            if result.matched_count == 0:
                return None

            updated_doc = self.collection.find_one({"_id": ObjectId(pdf_id)})
            return self._serialize_pdf(updated_doc) if updated_doc else None
        except InvalidId:
            return None

    def delete_pdf(self, pdf_id: str) -> dict | None:
        try:
            result = self.collection.delete_one({"_id": ObjectId(pdf_id)})
            if result.deleted_count == 0:
                return None
            return {
                "status": "success",
                "id": pdf_id,
                "message": "PDF eliminado correctamente",
            }
        except InvalidId:
            return None

    @staticmethod
    def _serialize_pdf(doc: dict) -> dict:
        doc["id"] = str(doc.pop("_id"))
        return doc
