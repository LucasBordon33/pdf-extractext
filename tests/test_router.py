import importlib
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from controllers.pdf_controller import PDFController
from services.pdf_service import PDFService
from config.exceptions import PDFNotFoundException


class FakeRepository:
    """Repositorio en memoria que aísla los tests del router de MongoDB."""

    def __init__(self):
        self._pdfs = [
            {"id": "1", "name": "test.pdf", "checksum": "abc", "text": "hola"}
        ]

    def get_pdfs(self):
        return [dict(pdf) for pdf in self._pdfs]

    def find_by_checksum(self, checksum):
        for pdf in self._pdfs:
            if pdf["checksum"] == checksum:
                return dict(pdf)
        return None

    def delete_pdf(self, pdf_id):
        for pdf in self._pdfs:
            if pdf["id"] == pdf_id:
                self._pdfs.remove(pdf)
                return {
                    "status": "success",
                    "id": pdf_id,
                    "message": "PDF eliminado correctamente",
                }
        raise PDFNotFoundException(f"PDF con id {pdf_id} no encontrado")


@pytest.fixture()
def fake_repository():
    return FakeRepository()


@pytest.fixture()
def client(fake_repository):
    controller = PDFController(
        pdf_service=PDFService(repository=fake_repository)
    )

    # El router instancia PDFController() internamente; se inyecta el
    # controller cableado con el FakeRepository en su lugar. Se recarga
    # `main` para reconstruir la app con el controller de este test,
    # dentro del patch (así nunca se toca Mongo real, ni siquiera al
    # restaurar el módulo).
    with patch("routers.pdf_router.PDFController", return_value=controller):
        import main

        importlib.reload(main)
        yield TestClient(main.app)
        importlib.reload(main)


def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_get_pdfs(client):
    response = client.get("/api/v1/pdfs")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)
    assert response.json()["count"] == 1
    assert response.json()["data"][0]["filename"] == "test.pdf"


def test_delete_pdf(client, fake_repository):
    response = client.delete("/api/v1/pdfs/1")
    assert response.status_code == 204
    with pytest.raises(PDFNotFoundException):
        fake_repository.delete_pdf("1")
