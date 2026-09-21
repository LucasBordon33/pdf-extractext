import unittest
import mongomock
from bson import ObjectId

from repositories.pdf_repository import PDFRepository
from models.pdf import PDF
from config.exceptions import PDFNotFoundException


class TestPDFRepository(unittest.TestCase):
    def setUp(self):
        # Base de datos MongoDB falsificada en memoria: sin infraestructura externa
        self.client = mongomock.MongoClient()
        self.db = self.client["test_db"]
        self.repo = PDFRepository(db=self.db)

    def _create_pdf(self, name="test.pdf", text="contenido", checksum="abc") -> str:
        return self.repo.create_pdf(PDF(name=name, text=text, checksum=checksum))

    def test_find_by_checksum(self):
        self._create_pdf()
        result = self.repo.find_by_checksum("abc")
        self.assertIsNotNone(result)
        self.assertEqual(result["checksum"], "abc")

    def test_find_by_checksum_not_found(self):
        result = self.repo.find_by_checksum("nonexistent")
        self.assertIsNone(result)

    def test_create_pdf(self):
        pdf_id = self._create_pdf()
        self.assertIsNotNone(pdf_id)
        stored = self.repo.get_pdf_by_id(pdf_id)
        self.assertEqual(stored["name"], "test.pdf")

    def test_get_pdfs(self):
        self._create_pdf()
        pdfs = self.repo.get_pdfs()
        self.assertIsInstance(pdfs, list)
        self.assertEqual(len(pdfs), 1)
        self.assertEqual(pdfs[0]["name"], "test.pdf")

    def test_get_pdf_by_id(self):
        pdf_id = self._create_pdf()
        result = self.repo.get_pdf_by_id(pdf_id)
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], pdf_id)
        self.assertEqual(result["name"], "test.pdf")

    def test_get_pdf_by_id_not_found(self):
        with self.assertRaises(PDFNotFoundException):
            self.repo.get_pdf_by_id(str(ObjectId()))

    def test_get_pdf_by_id_invalid_id(self):
        with self.assertRaises(PDFNotFoundException):
            self.repo.get_pdf_by_id("id-invalido")

    def test_update_pdf(self):
        pdf_id = self._create_pdf()
        updated = self.repo.update_pdf(pdf_id, PDF(name="nuevo.pdf", text="nuevo"))
        self.assertEqual(updated["name"], "nuevo.pdf")

    def test_update_pdf_not_found(self):
        pdf = PDF(name="test.pdf", text="contenido")
        with self.assertRaises(PDFNotFoundException):
            self.repo.update_pdf(str(ObjectId()), pdf)

    def test_update_pdf_invalid_id(self):
        pdf = PDF(name="test.pdf", text="contenido")
        with self.assertRaises(PDFNotFoundException):
            self.repo.update_pdf("id-invalido", pdf)

    def test_delete_pdf(self):
        pdf_id = self._create_pdf()
        result = self.repo.delete_pdf(pdf_id)
        self.assertTrue(result)
        self.assertEqual(result["id"], pdf_id)
        with self.assertRaises(PDFNotFoundException):
            self.repo.get_pdf_by_id(pdf_id)

    def test_delete_pdf_not_found(self):
        with self.assertRaises(PDFNotFoundException):
            self.repo.delete_pdf(str(ObjectId()))

    def test_delete_pdf_invalid_id(self):
        with self.assertRaises(PDFNotFoundException):
            self.repo.delete_pdf("id-invalido")

    def test_is_duplicate_removed(self):
        with self.assertRaises(AttributeError):
            self.repo.is_duplicate("abc")


if __name__ == "__main__":
    unittest.main()
