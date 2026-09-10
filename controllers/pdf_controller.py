from fastapi import HTTPException, UploadFile, status
from services.pdf_service import PDFService
from services.pdf_validator import PDFValidator
from models.pdf import PDF
from config.constants import PDF_NOT_FOUND, PDF_PROCESS_ERROR


class PDFController:
    def __init__(self, pdf_service=None, pdf_validator=None):
        self.pdf_service = pdf_service or PDFService()
        self.pdf_validator = pdf_validator or PDFValidator()

    async def upload_pdf(self, file: UploadFile) -> dict:
        await self._validate_file(file)
        try:
            result = await self.pdf_service.upload_pdf(file)
            return result
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{PDF_PROCESS_ERROR}: {str(e)}",
            )

    def get_all_pdfs(self) -> dict:
        try:
            pdfs = self.pdf_service.pdf_repository.get_pdfs()
            formatted = [
                {
                    "id": pdf["id"],
                    "filename": pdf["name"],
                    "checksum": pdf.get("checksum"),
                    "text_preview": pdf.get("text", ""),
                }
                for pdf in pdfs
            ]
            return {
                "status": "success",
                "count": len(formatted),
                "data": formatted,
                "message": "Lista de PDFs obtenida correctamente",
            }
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener los PDFs",
            )

    async def update_existing_pdf(self, pdf_id: str, file: UploadFile) -> dict:
        self._ensure_pdf_exists(pdf_id)
        await self._validate_file(file)
        try:
            result = await self.pdf_service.update_pdf(pdf_id, file)
            return result
        except ValueError as e:
            if str(e) == PDF_NOT_FOUND:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=PDF_NOT_FOUND
                )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{PDF_PROCESS_ERROR}: {str(e)}",
            )

    def delete_existing_pdf(self, pdf_id: str) -> dict:
        self._ensure_pdf_exists(pdf_id)
        deleted = self.pdf_service.pdf_repository.delete_pdf(pdf_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=PDF_NOT_FOUND
            )
        return deleted

    async def _validate_file(self, file: UploadFile) -> None:
        error_msg = await self.pdf_validator._validate_is_pdf(file)
        if error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg
            )

    def _ensure_pdf_exists(self, pdf_id: str) -> None:
        if not self.pdf_service.pdf_repository.get_pdf_by_id(pdf_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=PDF_NOT_FOUND
            )
