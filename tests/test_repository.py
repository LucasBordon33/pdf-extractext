import unittest
from repositories.pdf_repository import PDFRepository
from models.pdf import PDF

class TestPDFRepository(unittest.TestCase):

    def setUp(self):
        self.repo = PDFRepository()

    def test_create_pdf(self):
        pdf = PDF(name="test.pdf", text="contenido")
        pdf_id = self.repo.create_pdf(pdf)
        self.assertIsNotNone(pdf_id)

    def test_get_pdfs(self):
        pdfs = self.repo.get_pdfs()
        self.assertIsInstance(pdfs, list)

    def test_get_pdf_by_id(self):
        pdf = PDF(name="test.pdf", text="contenido")
        pdf_id = self.repo.create_pdf(pdf)
        result = self.repo.get_pdf_by_id(pdf_id)
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "test.pdf")

    def test_update_pdf(self):
        pdf = PDF(name="test.pdf", text="contenido")
        pdf_id = self.repo.create_pdf(pdf)
        updated = self.repo.update_pdf(pdf_id, PDF(name="nuevo.pdf", text="nuevo"))
        self.assertEqual(updated["name"], "nuevo.pdf")

    def test_delete_pdf(self):
        pdf = PDF(name="test.pdf", text="contenido")
        pdf_id = self.repo.create_pdf(pdf)
        result = self.repo.delete_pdf(pdf_id)
        self.assertTrue(result)

if __name__ == "__main__":
    unittest.main()
