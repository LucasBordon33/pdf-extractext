import unittest
from services.pdf_service import PDFService

class TestPDFService(unittest.TestCase):

    def setUp(self):
        self.service = PDFService()

    def test_pdf_simple(self):
        # PDF de prueba con texto "Hola mundo"
        with open("tests/data/simple.pdf", "rb") as f:
            contenido = f.read()
        texto = self.service._extract_text(contenido)
        self.assertIn("Hola mundo", texto)

    def test_pdf_vacio(self):
        ## lee el pdf preparado y se asegura que lo leyó bien comparandolo 
        with open("tests/data/vacio.pdf", "rb") as f:
            contenido = f.read()
        texto = self.service._extract_text(contenido)
        self.assertEqual(texto, "")

    def test_pdf_invalido(self):
        ## se fija si cuando no es un PDF no explota
        with self.assertRaises(Exception):
            self.service._extract_text(b"contenido que no es un PDF")

if __name__ == "__main__":
    unittest.main()
