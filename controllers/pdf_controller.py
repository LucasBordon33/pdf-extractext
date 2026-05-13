from fastapi import HTTPException, UploadFile
from services.pdf_service import PDFService
from repositories.pdf_repository import PDFRepository
from models.pdf import PDF




class PDFController():
    def __init__(self):
        self.pdf_service = PDFService()
        self.pdf_repository = PDFRepository()

    async def upload_pdf(self, file: UploadFile):
     if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")
     try:
        ## en este bloque iría el CHECKSUM, <- IMPORTANTE
        result = await self.pdf_service.process_pdf(file)
        pdf = PDF(name=result["filename"],text=result["text"])
        pdf_id = self.pdf_repository.create_pdf(pdf)
        return {
            "id": pdf_id,
            "filename": result["filename"]
        }
     except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar PDF: {str(e)}")


    def get_all_pdfs(self):
     try:
        return self.pdf_repository.get_pdfs()
     except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener los PDFs")

    def update_existing_pdf(self,pdf_id: str, pdf: PDF):
     existing = self.pdf_repository.get_pdf_by_id(pdf_id)
     if not existing:
        raise HTTPException(status_code=404, detail="PDF no encontrado")
     return self.pdf_repository.update_pdf(pdf_id, pdf)

    def delete_existing_pdf(self,pdf_id: str):
     return self.pdf_repository.delete_pdf(pdf_id)
