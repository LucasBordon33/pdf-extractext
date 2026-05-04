from config.settings import db
from models.pdf import Pdf

def get_pdfs():
    return list(db["pdfs"].find())

def create_pdf(pdf: Pdf):
    result = db["pdfs"].insert_one(pdf.dict())
    return str(result.inserted_id)

def get_pdf_by_id(pdf_id: str):
    return db["pdfs"].find_one({"_id": pdf_id})

def update_pdf(pdf_id: str, pdf: Pdf):
    db["pdfs"].update_one({"_id": pdf_id}, {"$set": pdf.dict()})
    return {"msg": "PDF actualizado"}

def delete_pdf(pdf_id: str):
    db["pdfs"].delete_one({"_id": pdf_id})
    return {"msg": "PDF borrado"}
