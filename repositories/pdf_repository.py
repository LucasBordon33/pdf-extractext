from bson import ObjectId
from config.settings import db
from models.pdf import PDF


class PDFRepository():

    def __init__(self):
        pass

    def _serialize_pdf(self,doc):
     doc["id"] = str(doc.pop("_id"))
     return doc


    def get_pdfs(self):
     return [self._serialize_pdf(doc) for doc in db["pdfs"].find()]


    def create_pdf(self,pdf: PDF):
     result = db["pdfs"].insert_one(pdf.model_dump(exclude={"id"}))
     return str(result.inserted_id)


    def get_pdf_by_id(self,pdf_id: str):
     doc = db["pdfs"].find_one({"_id": ObjectId(pdf_id)})
     if doc:
        return self._serialize_pdf(doc)
     return None


    def update_pdf(self,pdf_id: str, pdf: PDF):
     db["pdfs"].update_one(
        {"_id": ObjectId(pdf_id)}, {"$set": pdf.model_dump(exclude={"id"})}
     )
     return {"msg": "PDF actualizado"}


    def delete_pdf(self,pdf_id: str):
     db["pdfs"].delete_one({"_id": ObjectId(pdf_id)})
     return {"msg": "PDF borrado"}

