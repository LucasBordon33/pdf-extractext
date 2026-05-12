from bson import ObjectId
from config.settings import db
from models.pdf import PDF


def _serialize_pdf(doc):
    doc["id"] = str(doc.pop("_id"))
    return doc


def get_pdfs():
    return [_serialize_pdf(doc) for doc in db["pdfs"].find()]


def create_pdf(pdf: PDF):
    result = db["pdfs"].insert_one(pdf.model_dump(exclude={"id"}))
    return str(result.inserted_id)


def get_pdf_by_id(pdf_id: str):
    doc = db["pdfs"].find_one({"_id": ObjectId(pdf_id)})
    if doc:
        return _serialize_pdf(doc)
    return None


def update_pdf(pdf_id: str, pdf: PDF):
    db["pdfs"].update_one(
        {"_id": ObjectId(pdf_id)}, {"$set": pdf.model_dump(exclude={"id"})}
    )
    return {"msg": "PDF actualizado"}


def delete_pdf(pdf_id: str):
    db["pdfs"].delete_one({"_id": ObjectId(pdf_id)})
    return {"msg": "PDF borrado"}

