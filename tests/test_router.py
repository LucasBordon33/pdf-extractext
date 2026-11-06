from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import main
from application.ports import ReaderPort, WriterPort
from application.use_cases import (
    DeletePDFUseCase,
    ListPDFsUseCase,
    PDFUseCases,
    RegisterPDFUseCase,
    UpdatePDFUseCase,
)
from domain.entities import PDF
from infrastructure.pdf.pypdf_text_extractor import PypdfTextExtractor
from infrastructure.pdf.pdf_validator import FileFormatPDFValidator
from interfaces.controllers.pdf_controller import PDFController
from interfaces.dependencies import get_pdf_controller

DATA_DIR = Path(__file__).parent / "data"


class InMemoryPDFRepository(ReaderPort, WriterPort):
    """Repositorio en memoria: implementa los puertos de persistencia
    segregados del stack nuevo, aislado por completo de MongoDB."""

    def __init__(self, seed: list[dict] | None = None) -> None:
        self._pdfs = {pdf["id"]: dict(pdf) for pdf in (seed or [])}

    def find_by_checksum(self, checksum: str) -> dict | None:
        return next(
            (dict(p) for p in self._pdfs.values() if p["checksum"] == checksum),
            None,
        )

    def find_all(self) -> list[dict]:
        return [dict(p) for p in self._pdfs.values()]

    def find_by_id(self, pdf_id: str) -> dict | None:
        pdf = self._pdfs.get(pdf_id)
        return dict(pdf) if pdf else None

    def save(self, pdf: PDF) -> str:
        pdf_id = f"pdf-{len(self._pdfs) + 1}"
        self._pdfs[pdf_id] = {"id": pdf_id, **pdf.model_dump()}
        return pdf_id

    def update(self, pdf_id: str, pdf: PDF) -> dict | None:
        if pdf_id not in self._pdfs:
            return None
        self._pdfs[pdf_id] = {"id": pdf_id, **pdf.model_dump()}
        return dict(self._pdfs[pdf_id])

    def delete(self, pdf_id: str) -> bool:
        return self._pdfs.pop(pdf_id, None) is not None


def _build_controller(repository: InMemoryPDFRepository) -> PDFController:
    """Compone el grafo real de casos de uso con el repositorio falso."""
    validator = FileFormatPDFValidator()
    extractor = PypdfTextExtractor()
    use_cases = PDFUseCases(
        register=RegisterPDFUseCase(repository, repository, validator, extractor),
        update=UpdatePDFUseCase(repository, repository, validator, extractor),
        list_all=ListPDFsUseCase(repository),
        delete=DeletePDFUseCase(repository),
    )
    return PDFController(use_cases)


@pytest.fixture()
def fake_repository() -> InMemoryPDFRepository:
    return InMemoryPDFRepository(
        seed=[{"id": "1", "name": "test.pdf", "checksum": "abc", "text": "hola"}]
    )


@pytest.fixture()
def client(fake_repository):
    main.app.dependency_overrides[get_pdf_controller] = lambda: _build_controller(
        fake_repository
    )
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


def _read_pdf(name: str) -> bytes:
    return (DATA_DIR / name).read_bytes()


def _upload_bytes() -> bytes:
    """Contenido distinto al del seed: mismo PDF válido con un sufijo
    agregado tras el %%EOF (pypdf lo tolera, como ya hace tests/spike_tests.js),
    lo que cambia el checksum sin romper la extracción."""
    return _read_pdf("simple.pdf") + b"update-test-suffix"


def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_get_pdfs(client):
    response = client.get("/api/v1/pdfs")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["data"][0]["filename"] == "test.pdf"
    assert body["data"][0]["text_preview"] == "hola"


def test_upload_pdf(client):
    response = client.post(
        "/api/v1/upload",
        files={"file": ("simple.pdf", _read_pdf("simple.pdf"), "application/pdf")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "success"
    assert body["filename"] == "simple.pdf"
    assert body["id"]
    assert body["checksum"]


def test_upload_duplicate_pdf(client):
    upload = {"file": ("simple.pdf", _read_pdf("simple.pdf"), "application/pdf")}
    assert client.post("/api/v1/upload", files=upload).status_code == 201
    duplicate = client.post("/api/v1/upload", files=upload)
    assert duplicate.status_code == 409


def test_upload_invalid_pdf(client):
    response = client.post(
        "/api/v1/upload",
        files={"file": ("fake.pdf", b"esto no es un pdf", "application/pdf")},
    )
    assert response.status_code == 400


def test_update_pdf(client):
    response = client.put(
        "/api/v1/pdfs/1",
        files={"file": ("simple.pdf", _upload_bytes(), "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "1"
    assert body["filename"] == "simple.pdf"
    assert body["checksum"] != "abc"


def test_update_pdf_not_found(client):
    response = client.put(
        "/api/v1/pdfs/no-existe",
        files={"file": ("simple.pdf", _upload_bytes(), "application/pdf")},
    )
    assert response.status_code == 404


def test_delete_pdf(client, fake_repository):
    response = client.delete("/api/v1/pdfs/1")
    assert response.status_code == 204
    assert fake_repository.find_by_id("1") is None
    # La segunda eliminación ya no encuentra el PDF: 404
    assert client.delete("/api/v1/pdfs/1").status_code == 404


def test_error_inesperado_al_listar_da_500():
    """Un fallo no previsto (p. ej. caída de la base de datos) se traduce
    a 500 con contexto a través del manejador de errores centralizado
    del controller (`_as_http_error`)."""
    class RepositorioQueFalla(InMemoryPDFRepository):
        def find_all(self) -> list[dict]:
            raise RuntimeError("boom de prueba")

    main.app.dependency_overrides[get_pdf_controller] = lambda: _build_controller(
        RepositorioQueFalla(
            seed=[{"id": "1", "name": "test.pdf", "checksum": "abc", "text": "hola"}]
        )
    )
    try:
        response = TestClient(main.app).get("/api/v1/pdfs")
        assert response.status_code == 500
        assert "boom de prueba" in response.json()["detail"]
    finally:
        main.app.dependency_overrides.clear()
