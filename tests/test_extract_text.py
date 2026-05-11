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
        #Verifica que el PDF esté bien generado
     contenido_basura = b"Este es un texto plano, no un PDF"
    
     with self.assertRaises(ValueError) as context:
        self.service._extract_text_from_pdf_stream(contenido_basura)
    
     self.assertIn("No se pudo leer el archivo como PDF", str(context.exception))

if __name__ == "__main__":
    unittest.main()
