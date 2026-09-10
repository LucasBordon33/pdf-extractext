from fastapi import HTTPException, UploadFile, status
from services.pdf_service import PDFService
from services.pdf_validator import PDFValidator
from config.constants import PDF_NOT_FOUND, PDF_PROCESS_ERROR
from config.exceptions import (
    PDFNotFoundException,
    PDFRejectedException,
    PDFNotValidException,
)


class PDFController:
    def __init__(self, pdf_service=None, pdf_repository = None, pdf_validator=None):
        self.pdf_service = pdf_service or PDFService(pdf_repository)
        self.pdf_validator = pdf_validator or PDFValidator()

    async def upload_pdf(self, file: UploadFile) -> dict:
        try:
            await self._validate_file(file)
            result = await self.pdf_service.upload_pdf(file)
            return result
        except PDFNotValidException as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except PDFRejectedException as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except PDFNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{PDF_PROCESS_ERROR}: {str(e)}",
            )

    def get_all_pdfs(self) -> dict:
        try:
            pdfs = self.pdf_service.repository.get_pdfs()
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
        try:
            await self._validate_file(file)
            result = await self.pdf_service.update_pdf(pdf_id, file)
            return result
        except PDFNotValidException as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except PDFRejectedException as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except PDFNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{PDF_PROCESS_ERROR}: {str(e)}",
            )

    def delete_existing_pdf(self, pdf_id: str) -> dict:
        try:
            deleted = self.pdf_service.repository.delete_pdf(pdf_id)
            return deleted
        except PDFNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=PDF_NOT_FOUND
            )

    async def _validate_file(self, file: UploadFile) -> None:
        await self.pdf_validator.validate_is_pdf(file)
