"""
INTERFACES — Router FastAPI.

El router NO instancia el controller: lo recibe inyectado con
`Depends(get_pdf_controller)` (el composition root vive en
`interfaces/dependencies.py`). Esto desacopla al router del grafo de
construcción y permite sustituir dependencias en tests con
`app.dependency_overrides`.
"""
from fastapi import APIRouter, Depends, File, UploadFile, status

from interfaces.controllers.pdf_controller import PDFController
from interfaces.dependencies import get_pdf_controller

router = APIRouter(prefix="/api/v1", tags=["pdfs"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_pdf(
    file: UploadFile = File(...),
    controller: PDFController = Depends(get_pdf_controller),
):
    return await controller.upload_pdf(file)


@router.get("/pdfs")
def read(controller: PDFController = Depends(get_pdf_controller)):
    return controller.get_all_pdfs()


@router.put("/pdfs/{pdf_id}")
async def update(
    pdf_id: str,
    file: UploadFile = File(...),
    controller: PDFController = Depends(get_pdf_controller),
):
    return await controller.update_existing_pdf(pdf_id, file)


@router.delete("/pdfs/{pdf_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(pdf_id: str, controller: PDFController = Depends(get_pdf_controller)):
    return controller.delete_existing_pdf(pdf_id)


@router.get("/health")
def health_check():
    return {"status": "healthy", "service": "pdf-extractext"}
