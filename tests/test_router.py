import unittest
from fastapi.testclient import TestClient
from main import app

class TestPDFRouter(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

    def test_create_pdf(self):
        response = self.client.post("/api/v1/pdfs", json={"name": "test.pdf", "text": "contenido"})
        self.assertEqual(response.status_code, 201)
        self.assertIn("id", response.json())

    def test_get_pdfs(self):
        response = self.client.get("/api/v1/pdfs")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

if __name__ == "__main__":
    unittest.main()
