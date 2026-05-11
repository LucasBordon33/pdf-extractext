from fastapi import APIRouter
from controllers import pdf_controller # Importamos el controlador que creamos
from models.pdf import PDF

router = APIRouter()

@router.post("/pdfs")
def create(pdf: PDF):
    return pdf_controller.create_new_pdf(pdf)

@router.get("/pdfs")
def read():
    return pdf_controller.get_all_pdfs()

@router.put("/pdfs/{pdf_id}")
def update(pdf_id: str, pdf: PDF):
    return pdf_controller.update_existing_pdf(pdf_id, pdf)

@router.delete("/pdfs/{pdf_id}")
def delete(pdf_id: str):
    return pdf_controller.delete_existing_pdf(pdf_id)