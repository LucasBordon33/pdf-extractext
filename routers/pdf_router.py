from fastapi import APIRouter
from controllers import pdf_controller
from models.pdf import PDF

router = APIRouter()

## crear pdf_controller y luego crear las funciones que van en router :V

@router.post("/pdfs")
def create(pdf: PDF):
    pass

@router.get("/pdfs")
def read():
    pass

@router.put("/pdfs/{user_id}")
def update(pdf_id: str, pdf: PDF):
    pass

@router.delete("/pdfs/{pdf_id}")
def delete(pdf_id: str):
    pass