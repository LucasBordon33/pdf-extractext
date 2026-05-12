from fastapi import APIRouter, status
from controllers import pdf_controller
from models.pdf import PDF

router = APIRouter(prefix="/api/v1", tags=["crud"])


@router.post("/pdfs", status_code=status.HTTP_201_CREATED)
def create(pdf: PDF):
    return pdf_controller.create_new_pdf(pdf)


@router.get("/pdfs")
def read():
    return pdf_controller.get_all_pdfs()


@router.put("/pdfs/{pdf_id}")
def update(pdf_id: str, pdf: PDF):
    return pdf_controller.update_existing_pdf(pdf_id, pdf)


@router.delete("/pdfs/{pdf_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(pdf_id: str):
    pdf_controller.delete_existing_pdf(pdf_id)
