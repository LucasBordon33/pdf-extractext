from fastapi import HTTPException, UploadFile, status
from services.pdf_service import PDFService
from services.pdf_validator import PDFValidator
from repositories.pdf_repository import PDFRepository
from models.pdf import PDF

"""
Controlador de PDF que llama a todos los servicios necesarios según los requests que llegan 

"""



class PDFController:
    def __init__(self):
        self.pdf_service = PDFService()
        self.pdf_repository = PDFRepository()
        self.pdf_validator = PDFValidator()

    async def upload_pdf(self, file: UploadFile) -> dict:        
        await self._validate_file(file)
        
        try:
            pdf_data = await self._process_and_map_pdf(file)
            
            if self.pdf_repository.is_duplicate(pdf_data.checksum):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El PDF ya se encuentra repetido en la base de datos."
                )

            pdf_id = self.pdf_repository.create_pdf(pdf_data)
            return self._build_response("PDF subido correctamente", pdf_id, pdf_data)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Error al procesar PDF: {str(e)}"
            )

    def get_all_pdfs(self) -> dict:
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Error al obtener los PDFs"
            )

    async def update_existing_pdf(self, pdf_id: str, file: UploadFile) -> dict:
        self._ensure_pdf_exists(pdf_id)
        await self._validate_file(file)

        try:
            pdf_data = await self._process_and_map_pdf(file)
            updated = self.pdf_repository.update_pdf(pdf_id, pdf_data)

            if not updated:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF no encontrado")

            if updated.get("status") == "error":
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=updated.get("message"))

            return {
                "status": "success",
                "id": updated["id"],
                "filename": updated["name"],
                "checksum": updated["checksum"],
                "message": "PDF actualizado correctamente"
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Error al procesar PDF: {str(e)}"
            )

    def delete_existing_pdf(self, pdf_id: str) -> dict:
        self._ensure_pdf_exists(pdf_id)
        deleted = self.pdf_repository.delete_pdf(pdf_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF no encontrado")
        return deleted

    # Métodos privados auxiliares 

    async def _validate_file(self, file: UploadFile) -> None:
        error_msg = await self.pdf_validator._validate_is_pdf(file)
        if error_msg:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    def _ensure_pdf_exists(self, pdf_id: str) -> None:
        if not self.pdf_repository.get_pdf_by_id(pdf_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF no encontrado")

    async def _process_and_map_pdf(self, file: UploadFile) -> PDF:
        result = await self.pdf_service.process_pdf(file)
        return PDF(
            name=result["filename"],
            text=result["text"],
            checksum=result["checksum"]
        )

    def _build_response(self, message: str, pdf_id: str, pdf: PDF) -> dict:
        return {
            "status": "success",
            "id": pdf_id,
            "filename": pdf.name,
            "checksum": pdf.checksum,
            "message": message
        }

