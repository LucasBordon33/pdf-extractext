from fastapi import HTTPException
from models.pdf import PDF
import models.pdf as pdf_model 

def get_all_pdfs():
    try:
        pdfs = pdf_model.get_pdfs()
        return pdfs
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al obtener los PDFs")

def create_new_pdf(pdf: PDF):
    if not pdf.name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")
    
    pdf_id = pdf_model.create_pdf(pdf)
    return {"id": pdf_id, "msg": "Creado exitosamente"}

def update_existing_pdf(pdf_id: str, pdf: PDF):
    existing = pdf_model.get_pdf_by_id(pdf_id)
    if not existing:
        raise HTTPException(status_code=404, detail="PDF no encontrado")
    
    return pdf_model.update_pdf(pdf_id, pdf)

def delete_existing_pdf(pdf_id: str):
    return pdf_model.delete_pdf(pdf_id)