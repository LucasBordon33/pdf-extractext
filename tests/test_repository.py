import unittest
from unittest.mock import MagicMock
from repositories.pdf_repository import PDFRepository
from models.pdf import PDF


class MockCollection:
    """Simple in-memory mock for MongoDB collection."""
    def __init__(self):
        self._data = {}
        self._counter = 0

    def _make_id(self):
        from bson import ObjectId
        self._counter += 1
        # Generate 24-char hex string
        return ObjectId(f"0000000000000000000000{self._counter:02x}")

    def insert_one(self, document):
        _id = self._make_id()
        self._data[str(_id)] = {**document, "_id": _id}

        class Result:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id
        return Result(_id)

    def find(self):
        return self._data.values()

    def find_one(self, filter):
        if "_id" in filter:
            return self._data.get(str(filter["_id"]))
        return None

    def update_one(self, filter, update):
        doc_id = str(filter.get("_id"))
        if doc_id in self._data:
            # only handle $set updates for now
            set_data = update.get("$set", {})
            self._data[doc_id].update(set_data)
        return MagicMock(modified_count=1)

    def delete_one(self, filter):
        doc_id = str(filter.get("_id"))
        if doc_id in self._data:
            del self._data[doc_id]
        return MagicMock(deleted_count=1)


class MockDB:
    def __init__(self):
        self.pdfs = MockCollection()

    def __getitem__(self, name):
        if name == "pdfs":
            return self.pdfs
        raise KeyError(name)


class TestPDFRepository(unittest.TestCase):

    def setUp(self):
        mock_db = MockDB()
        self.repo = PDFRepository(db=mock_db)

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
        self.assertEqual(result, {"msg": "PDF borrado"})

    def test_generate_checksum(self):
        checksum = self.repo.generate_checksum(b"test data")
        self.assertIsInstance(checksum, str)
        self.assertEqual(len(checksum), 64)

    def test_generate_checksum_from_text(self):
        checksum = self.repo.generate_checksum_from_text("test data")
        self.assertIsInstance(checksum, str)
        self.assertEqual(len(checksum), 64)

    def test_verify_checksum(self):
        pdf = PDF(name="test.pdf", text="contenido", checksum="abc123")
        pdf_id = self.repo.create_pdf(pdf)
        # Should return False because actual checksum does not match
        result = self.repo.verify_checksum(pdf_id, b"other data")
        # Since pdf was saved with checksum="abc123", verification against other data fails
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
