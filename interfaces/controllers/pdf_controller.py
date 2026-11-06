from fastapi import HTTPException, UploadFile

from application.use_cases import PDFUseCases
from domain.exceptions import DuplicatePDFError, InvalidPDFError, PDFNotFoundError
from domain.pdf_file import PDFFile

# Traducción centralizada: error de dominio -> código HTTP. Agregar un
# nuevo error de dominio = sumar una fila a esta tabla; ningún endpoint
# cambia (DRY).
_DOMAIN_ERROR_STATUS: tuple[tuple[type[Exception], int], ...] = (
    (InvalidPDFError, 400),
    (DuplicatePDFError, 409),
    (PDFNotFoundError, 404),
)


def _as_http_error(exc: Exception, action: str) -> HTTPException:
    """Traduce cualquier excepción al contrato HTTP de la API: los errores
    de dominio a su código de estado y el resto a 500 con contexto."""
    for error_type, status_code in _DOMAIN_ERROR_STATUS:
        if isinstance(exc, error_type):
            return HTTPException(status_code=status_code, detail=str(exc))
    return HTTPException(status_code=500, detail=f"Error al {action}: {exc}")


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
        except Exception as e:
            raise _as_http_error(e, "procesar PDF") from e
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
        except Exception as e:
            raise _as_http_error(e, "obtener los PDFs") from e
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
        except Exception as e:
            raise _as_http_error(e, "procesar PDF") from e
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
        except Exception as e:
            raise _as_http_error(e, "eliminar el PDF") from e
        return {"status": "success", "id": pdf_id, "message": "PDF eliminado correctamente"}
