from fastapi import APIRouter, UploadFile, File, HTTPException
from services.pdf_service import PDFService

# Agrega un prefijo para que todas las rutas del archivo empiecen con "/api/v1"
router = APIRouter(prefix="/api/v1", tags=["pdf"])

# Intancia a la clase en el otro archivo pdf_service
pdf_service = PDFService()

# Acepta unicamente los archivos en formato PDF en la ruta "/upload" y entrega el PDF válido a pdf_service
@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")

    result = await pdf_service.process_pdf(file)
    return {"message": "PDF procesado exitosamente", "data": result}

# Estándar en la industria que sirve para que otros sistemas o servidores pregunten periódicamente: "¿Estás encendido y funcionando bien?"
@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "pdf-extractext"}
