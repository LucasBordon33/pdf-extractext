import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from services.pdf_service import PDFService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["pdf"])

pdf_service = PDFService()

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")

    try:
        result = await pdf_service.process_pdf(file)
        logger.info("PDF procesado exitosamente: %s", file.filename)
        return {"message": "PDF procesado exitosamente", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Error al procesar PDF: %s", file.filename)
        raise HTTPException(status_code=500, detail=f"Error interno al procesar el PDF")


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "pdf-extractext"}
