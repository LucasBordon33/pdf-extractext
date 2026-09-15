import unittest
from unittest.mock import MagicMock, patch
from services.pdf_service import PDFService


class TestPDFService(unittest.TestCase):
    def setUp(self):
        self.mock_repo = MagicMock()
        self.service = PDFService(repository=self.mock_repo)

    @patch("services.pdf_service.PdfReader")
    def test_pdf_simple(self, mock_pdf_reader):
        mock_reader_instance = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Hola mundo"
        mock_reader_instance.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader_instance

        pdf_content = b"%PDF-1.4 fake pdf content"
        texto = self.service._extract_text_from_pdf_stream(pdf_content)
        self.assertIn("Hola mundo", texto)

    @patch("services.pdf_service.PdfReader")
    def test_pdf_vacio(self, mock_pdf_reader):
        mock_reader_instance = MagicMock()
        mock_reader_instance.pages = []
        mock_pdf_reader.return_value = mock_reader_instance

        pdf_content = b"%PDF-1.4 fake pdf content"
        texto = self.service._extract_text_from_pdf_stream(pdf_content)
        self.assertEqual(texto, "")

    @patch("services.pdf_service.PdfReader")
    def test_pdf_invalido(self, mock_pdf_reader):
        mock_pdf_reader.side_effect = Exception("Invalid PDF")

        contenido_basura = b"Este es un texto plano, no un PDF"
        with self.assertRaises(ValueError) as context:
            self.service._extract_text_from_pdf_stream(contenido_basura)
        self.assertIn("No se pudo leer el archivo como PDF", str(context.exception))

    def test_is_duplicate(self):
        self.mock_repo.find_by_checksum.return_value = {"checksum": "abc123"}
        self.assertTrue(self.service.is_duplicate("abc123"))
        self.mock_repo.find_by_checksum.return_value = None
        self.assertFalse(self.service.is_duplicate("xyz"))


if __name__ == "__main__":
    unittest.main()
