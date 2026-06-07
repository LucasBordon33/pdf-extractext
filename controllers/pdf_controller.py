from fastapi import HTTPException, UploadFile
from services.pdf_service import PDFService
from services.pdf_validator import PDFValidator
from repositories.pdf_repository import PDFRepository
from models.pdf import PDF


class PDFController:
    def __init__(self):
        self.pdf_service = PDFService()
        self.pdf_repository = PDFRepository()
        self.pdf_validator = PDFValidator()

    async def upload_pdf(self, file: UploadFile):        
        response = await self.pdf_validator._validate_is_pdf(file)
        if response != "":
            raise HTTPException(status_code=400, detail=response)
        try:
           result = await self.pdf_service.process_pdf(file)
           pdf = PDF(
            name=result["filename"],
            text=result["text"],
            checksum=result["checksum"]
         )

        # Verifica duplicado antes de guardar
           if self.pdf_repository.is_duplicate(pdf.checksum):
            return {
                "status": "error",
                "message": "El PDF ya se encuentra repetido en la base de datos."
            }

        # Crea el PDF y lo guarda
           pdf_id = self.pdf_repository.create_pdf(pdf)
           return {
            "status": "success",
            "id": pdf_id,
            "filename": result["filename"],
            "checksum": result["checksum"],
            "message": "PDF subido correctamente"
         }
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error al procesar PDF: {str(e)}"
            )

    # Muestra todos los PDFs
    def get_all_pdfs(self):
     try:
        pdfs = self.pdf_repository.get_pdfs()
        formatted = [
            {
                "id": pdf["id"],
                "filename": pdf["name"],
                "checksum": pdf.get("checksum"),
                "text_preview": pdf.get("text", "")
            }
            for pdf in pdfs
        ]
        return {
            "status": "success",
            "count": len(formatted),
            "data": formatted,
            "message": "Lista de PDFs obtenida correctamente"
        }
     except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener los PDFs")


    # Actualiza un PDF concreto
    async def update_existing_pdf(self, pdf_id: str, file: UploadFile):
     existing = self.pdf_repository.get_pdf_by_id(pdf_id)
     if existing is None:
        raise HTTPException(status_code=404, detail="PDF no encontrado")

     response = await self.pdf_validator._validate_is_pdf(file)
     if response != "":
        raise HTTPException(status_code=400, detail=response)

     try:
        result = await self.pdf_service.process_pdf(file)
        pdf = PDF(
            name=result["filename"],
            text=result["text"],
            checksum=result["checksum"]
        )
        updated = self.pdf_repository.update_pdf(pdf_id, pdf)

        if updated is None:
            raise HTTPException(status_code=404, detail="PDF no encontrado")

        if updated.get("status") == "error":
            return updated

        return {
            "status": "success",
            "id": updated["id"],
            "filename": updated["name"],
            "checksum": updated["checksum"],
            "message": "PDF actualizado correctamente"
        }
     except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al procesar PDF: {str(e)}"
        )


    def delete_existing_pdf(self, pdf_id: str):
     existing = self.pdf_repository.get_pdf_by_id(pdf_id)
     if existing is None:
        raise HTTPException(status_code=404, detail="PDF no encontrado")
     deleted = self.pdf_repository.delete_pdf(pdf_id)
     if deleted is None:
         raise HTTPException(status_code=404, detail="PDF no encontrado")
     return deleted

