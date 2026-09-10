import unittest
from unittest.mock import MagicMock, patch
from repositories.pdf_repository import PDFRepository
from bson import ObjectId
from models.pdf import PDF


class TestPDFRepository(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_collection = MagicMock()
        self.mock_db.__getitem__ = MagicMock(return_value=self.mock_collection)
        self.repo = PDFRepository(db=self.mock_db)
    
    def test_find_by_checksum(self):
        self.mock_collection.find_one.return_value = {"checksum": "abc"}
        result = self.repo.find_by_checksum("abc")
        self.assertIsNotNone(result)
        self.assertEqual(result["checksum"], "abc")
        self.mock_collection.find_one.assert_called_once_with({"checksum": "abc"})
    
    def test_find_by_checksum_not_found(self):
        self.mock_collection.find_one.return_value = None
        result = self.repo.find_by_checksum("nonexistent")
        self.assertIsNone(result)
    
    def test_create_pdf(self):
        mock_result = MagicMock()
        mock_result.inserted_id = "fake_object_id_123"
        self.mock_collection.insert_one.return_value = mock_result

        pdf = PDF(name="test.pdf", text="contenido")
        pdf_id = self.repo.create_pdf(pdf)
        self.assertIsNotNone(pdf_id)
        self.mock_collection.insert_one.assert_called_once()
    
    def test_get_pdfs(self):
        mock_doc = {
            "_id": "fake_id",
            "name": "test.pdf",
            "text": "contenido",
            "checksum": "abc",
        }
        self.mock_collection.find.return_value = [mock_doc]

        pdfs = self.repo.get_pdfs()
        self.assertIsInstance(pdfs, list)
        self.assertEqual(len(pdfs), 1)
        self.assertEqual(pdfs[0]["name"], "test.pdf")
    @patch("repositories.pdf_repository.ObjectId", side_effect=lambda x: x)    
    def test_get_pdf_by_id(self, mock_oid):
        mock_doc = {
            "_id": "fake_id",
            "name": "test.pdf",
            "text": "contenido",
            "checksum": "abc",
        }
        self.mock_collection.find_one.return_value = mock_doc

        pdf = PDF(name="test.pdf", text="contenido")
        pdf_id = self.repo.create_pdf(pdf)
        result = self.repo.get_pdf_by_id(pdf_id)
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "test.pdf")

    @patch("repositories.pdf_repository.ObjectId", side_effect=lambda x: x)
    def test_update_pdf(self, mock_oid):
        self.mock_collection.find_one.return_value = {
            "_id": "fake_id",
            "name": "test.pdf",
            "text": "contenido",
            "checksum": "abc",
        }
        mock_result = MagicMock()
        mock_result.matched_count = 1
        self.mock_collection.update_one.return_value = mock_result

        updated_doc = {
            "_id": "fake_id",
            "name": "nuevo.pdf",
            "text": "nuevo",
            "checksum": "def",
        }
        self.mock_collection.find_one.return_value = updated_doc

        pdf = PDF(name="test.pdf", text="contenido")
        updated = self.repo.update_pdf("fake_id", PDF(name="nuevo.pdf", text="nuevo"))
        self.assertEqual(updated["name"], "nuevo.pdf")

    @patch("repositories.pdf_repository.ObjectId", side_effect=lambda x: x)
    def test_delete_pdf(self, mock_oid):
        mock_result = MagicMock()
        mock_result.deleted_count = 1
        self.mock_collection.delete_one.return_value = mock_result

        pdf = PDF(name="test.pdf", text="contenido")
        pdf_id = self.repo.create_pdf(pdf)
        result = self.repo.delete_pdf(pdf_id)
        self.assertTrue(result)


    def test_is_duplicate_removed(self):
        with self.assertRaises(AttributeError):
            self.repo.is_duplicate("abc")


if __name__ == "__main__":
    unittest.main()
