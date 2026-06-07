from fastapi import APIRouter, status, UploadFile, File
from controllers.pdf_controller import PDFController
from models.pdf import PDF

class PDFRouter:
    def __init__(self):
        self.router = APIRouter(prefix="/api/v1", tags=["pdfs"])
        self._add_routes()
        self.pdf_controller = PDFController()

    def _add_routes(self):
        @self.router.get("/pdfs")
        def read():
            return self.pdf_controller.get_all_pdfs()

        @self.router.put("/pdfs/{pdf_id}")
        async def update(pdf_id: str, file: UploadFile = File(...)):
         return await self.pdf_controller.update_existing_pdf(pdf_id, file)
        
        @self.router.delete("/pdfs/{pdf_id}", status_code=status.HTTP_204_NO_CONTENT)
        def delete(pdf_id: str):
            return self.pdf_controller.delete_existing_pdf(pdf_id)

        @self.router.post("/upload", status_code=status.HTTP_201_CREATED)
        async def upload_pdf(file: UploadFile = File(...)):
            return await self.pdf_controller.upload_pdf(file)

        @self.router.get("/health")
        def health_check():
            return {"status": "healthy", "service": "pdf-extractext"}
