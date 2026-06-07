import hashlib
from bson import ObjectId
from models.pdf import PDF
from bson.errors import InvalidId

class PDFRepository:
    def __init__(self, db=None):
        if db is None:
            from config.settings import db as _db
            db = _db
        self.db = db

    def _serialize_pdf(self, doc):
        doc["id"] = str(doc.pop("_id"))
        return doc

    @staticmethod
    def generate_checksum(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def is_duplicate(self, checksum: str) -> bool:
        if self.db is None:
            raise RuntimeError("Database connection not available")
        return self.db["pdfs"].find_one({"checksum": checksum}) is not None


    def get_pdfs(self):
        if self.db is None:
            return []
        return [self._serialize_pdf(doc) for doc in self.db["pdfs"].find()]

    def create_pdf(self, pdf: PDF):
        if self.db is None:
            raise RuntimeError("Database connection not available")
        
        result = self.db["pdfs"].insert_one(pdf.model_dump(exclude={"id"}))
        return str(result.inserted_id)
        
        

    def get_pdf_by_id(self, pdf_id: str):
     if self.db is None:
        return None
     try:
        doc = self.db["pdfs"].find_one({"_id": ObjectId(pdf_id)})
     except InvalidId:
        return None
     if doc:
        return self._serialize_pdf(doc)
     return None

    def update_pdf(self, pdf_id: str, pdf: PDF) -> dict | None:
     if self.db is None:
        raise RuntimeError("Database connection not available")

     if self.is_duplicate(pdf.checksum):
        return {
            "status": "error",
            "message": "El PDF ya se encuentra repetido en la base de datos."
        }

     result = self.db["pdfs"].update_one(
        {"_id": ObjectId(pdf_id)},
        {"$set": pdf.model_dump(exclude={"id"})}
     )

     if result.matched_count == 0:
        return None  

     updated_doc = self.db["pdfs"].find_one({"_id": ObjectId(pdf_id)})
     return self._serialize_pdf(updated_doc)


    def delete_pdf(self, pdf_id: str) -> dict | None:
     if self.db is None:
        raise RuntimeError("Database connection not available")

     result = self.db["pdfs"].delete_one({"_id": ObjectId(pdf_id)})
     if result.deleted_count == 0:
        return None 
     return {"status": "success", "id": pdf_id, "message": "PDF eliminado correctamente"}
