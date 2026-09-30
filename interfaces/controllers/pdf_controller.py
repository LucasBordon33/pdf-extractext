"""
INTERFACES — Adaptador HTTP (controller).

Responsabilidades ÚNICAS (todo lo del framework vive solo aquí):
1. Mapear `UploadFile` (FastAPI) -> `PDFFile` (dominio) ANTES de invocar
   los casos de uso. La capa de aplicación nunca ve tipos del framework.
2. Traducir excepciones de dominio a `HTTPException`
   (InvalidPDFError->400, DuplicatePDFError->409, PDFNotFoundError->404).
3. Formatear las respuestas HTTP.

No contiene reglas de negocio ni instancia dependencias: recibe el bundle
de casos de uso por inyección (ver `interfaces/dependencies.py`).
"""
from fastapi import HTTPException, UploadFile

from application.use_cases import PDFUseCases
from domain.exceptions import DuplicatePDFError, InvalidPDFError, PDFNotFoundError
from domain.pdf_file import PDFFile


class PDFController:
    def __init__(self, use_cases: PDFUseCases) -> None:
        self._use_cases = use_cases

    # ------------------------------------------------------------------
    # Mapeo framework -> dominio (adaptador)
    # ------------------------------------------------------------------
    @staticmethod
    async def _to_domain_file(file: UploadFile) -> PDFFile:
        """Convierte el UploadFile de FastAPI en el value object de dominio."""
        return PDFFile.from_upload(filename=file.filename, content=await file.read())

    # ------------------------------------------------------------------
    # Endpoints
    # ------------------------------------------------------------------
    async def upload_pdf(self, file: UploadFile):
        pdf_file = await self._to_domain_file(file)
        try:
            result = self._use_cases.register.execute(pdf_file)
        except InvalidPDFError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except DuplicatePDFError as e:
            raise HTTPException(status_code=409, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al procesar PDF: {e}")
        return {
            "status": "success",
            "id": result["id"],
            "filename": result["filename"],
            "checksum": result["checksum"],
            "message": "PDF subido correctamente",
        }

    def get_all_pdfs(self):
        try:
            pdfs = self._use_cases.list_all.execute()
        except Exception:
            raise HTTPException(status_code=500, detail="Error al obtener los PDFs")
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

    async def update_existing_pdf(self, pdf_id: str, file: UploadFile):
        pdf_file = await self._to_domain_file(file)
        try:
            updated = self._use_cases.update.execute(pdf_id, pdf_file)
        except PDFNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except InvalidPDFError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except DuplicatePDFError as e:
            raise HTTPException(status_code=409, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al procesar PDF: {e}")
        return {
            "status": "success",
            "id": updated["id"],
            "filename": updated["name"],
            "checksum": updated["checksum"],
            "message": "PDF actualizado correctamente",
        }

    def delete_existing_pdf(self, pdf_id: str):
        try:
            self._use_cases.delete.execute(pdf_id)
        except PDFNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        return {"status": "success", "id": pdf_id, "message": "PDF eliminado correctamente"}
