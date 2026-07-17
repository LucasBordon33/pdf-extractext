import os


"""

Servicio que ayuda a la validación de archivos PDF

"""


class PDFValidator():
    def __init__(self):
        self.valid_size = int(os.getenv("MX_FILE_SIZE","10"))*1024*1024
        
    async def _validate_is_pdf(self, file):
     if not file.filename.lower().endswith(".pdf"):
        return "Solo se permiten archivos PDF"

     file_header = await file.read(5)
     await file.seek(0)

     if not file_header.startswith(b"%PDF-"):
        return "El archivo no es un PDF válido"

     file.file.seek(0, 2)   # mover al final
     size = file.file.tell()  # síncrono, sin await
     file.file.seek(0)      # volver al inicio

     if size > self.valid_size:
        return "El archivo excede el tamaño permitido"

     return ""
 