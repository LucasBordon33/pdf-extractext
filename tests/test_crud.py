import unittest
from fastapi.testclient import TestClient
from main import app  # Tu punto de entrada de FastAPI

class TestPDFCrud(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_1_create_pdf(self):
        """TDD: Probar creación exitosa (Status 201)"""
        payload = {"name": "Guía de Ingeniería", "text": "Contenido de sucesiones..."}
        response = self.client.post("/pdfs", json=payload)
        
        self.assertEqual(response.status_code, 201)
        self.assertIn("id", response.json())
        self.assertEqual(response.json()["msg"], "Creado exitosamente")

    def test_2_get_all_pdfs(self):
        """TDD: Probar lectura de lista (Status 200)"""
        response = self.client.get("/pdfs")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_3_update_pdf_not_found(self):
        """TDD: Probar error 404 al actualizar ID inexistente"""
        payload = {"name": "Editado", "text": "Nuevo texto"}
        response = self.client.put("/pdfs/999999999999999999999999", json=payload)
        self.assertEqual(response.status_code, 404)

    def test_4_delete_pdf_success(self):
        """TDD: Probar borrado exitoso (Status 204)"""
        new_pdf = self.client.post("/pdfs", json={"name": "Temp", "text": "Temp"}).json()
        pdf_id = new_pdf["id"]
        
        response = self.client.delete(f"/pdfs/{pdf_id}")
        self.assertEqual(response.status_code, 204)

if __name__ == "__main__":
    unittest.main()