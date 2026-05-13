import unittest
from fastapi import UploadFile
from controllers.pdf_controller import PDFController
from services.pdf_service import PDFService
from models.pdf import PDF
from repositories.pdf_repository import PDFRepository

class TestPDFController(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.controller = PDFController(PDFService(), PDFRepository())

    async def test_upload_pdf(self):
        with open("tests/resources/test.pdf", "rb") as f:
            fake_file = UploadFile(filename="test.pdf", file=f)
            result = await self.controller.upload_pdf(fake_file)
            self.assertIn("id", result)
            self.assertEqual(result["filename"], "test.pdf")

    def test_get_all_pdfs(self):
        result = self.controller.get_all_pdfs()
        self.assertIsInstance(result, list)

    def test_update_existing_pdf_not_found(self):
        with self.assertRaises(Exception):
            self.controller.update_existing_pdf("fake_id", PDF(name="x", text="y"))

if __name__ == "__main__":
    unittest.main()
