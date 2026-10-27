"""
Tests unitarios del seam de INFRAESTRUCTURA (ver CONTEXT.md §1, seam 3).

1. Reglas del validador de formato: estrategias atómicas inyectables
   (patrón Estrategia / OCP) y comportamiento del compositor por defecto.
2. Adaptador de persistencia `MongoPDFRepository` sobre **mongomock**
   (MongoDB en memoria): nunca se toca un servidor real.
3. Composition root: el grafo completo de `interfaces/dependencies.py`
   se construye y ejecuta de punta a punta sustituyendo únicamente el
   driver (cliente de Mongo) por el de mongomock, sin variables de
   entorno ni conexión de red.
"""
import hashlib
from pathlib import Path
from unittest.mock import MagicMock

import mongomock
import pytest
from bson import ObjectId

import config.settings as settings
from domain.entities import PDF
from domain.exceptions import InvalidPDFError
from domain.pdf_file import PDFFile
from infrastructure.pdf.pdf_validator import (
    FileFormatPDFValidator,
    HasPDFExtension,
    HasPDFMagicBytes,
    MaxFileSize,
    PDFValidationRule,
)
from infrastructure.persistence.mongo_pdf_repository import MongoPDFRepository
from interfaces.dependencies import get_pdf_controller

SIMPLE_PDF = (Path(__file__).parent / "data" / "simple.pdf").read_bytes()


# ----------------------------------------------------------------------
# Reglas del validador de formato (estrategias atómicas, OCP)
# ----------------------------------------------------------------------
def test_regla_extension_acepta_pdf():
    HasPDFExtension().check(PDFFile.from_upload("doc.pdf", b"cualquier contenido"))


def test_regla_extension_rechaza_otro_formato():
    with pytest.raises(InvalidPDFError, match="Solo se permiten archivos PDF"):
        HasPDFExtension().check(PDFFile.from_upload("doc.txt", b"contenido"))


def test_regla_firma_acepta_contenido_pdf():
    HasPDFMagicBytes().check(PDFFile.from_upload("doc.pdf", b"%PDF-1.4 contenido"))


def test_regla_firma_rechaza_contenido_sin_firma():
    with pytest.raises(InvalidPDFError, match="no es un PDF válido"):
        HasPDFMagicBytes().check(PDFFile.from_upload("doc.pdf", b"texto plano"))


def test_regla_tamano_acepta_contenido_pequeno():
    MaxFileSize(max_size_mb=1).check(PDFFile.from_upload("doc.pdf", b"%PDF-1.4 corto"))


def test_regla_tamano_rechaza_contenido_grande():
    content = b"%PDF-1.4 " + b"x" * (1024 * 1024)  # supera 1 MB
    with pytest.raises(InvalidPDFError, match="tamaño"):
        MaxFileSize(max_size_mb=1).check(PDFFile.from_upload("doc.pdf", content))


def test_validador_por_defecto_acepta_pdf_valido():
    FileFormatPDFValidator().validate(PDFFile.from_upload("doc.pdf", b"%PDF-1.4 ok"))


def test_validador_por_defecto_respeta_el_orden_de_las_reglas():
    # El archivo falla la extensión Y la firma: gana la primera regla.
    with pytest.raises(InvalidPDFError, match="Solo se permiten archivos PDF"):
        FileFormatPDFValidator().validate(PDFFile.from_upload("doc.txt", b"texto"))


def test_validador_admite_reglas_inyectables_sin_cambiar_validate():
    # OCP: una regla nueva se respeta sin modificar el método del compositor.
    class ReglaDePrueba(PDFValidationRule):
        def check(self, pdf_file: PDFFile) -> None:
            raise InvalidPDFError("regla propia inyectada")

    with pytest.raises(InvalidPDFError, match="regla propia inyectada"):
        FileFormatPDFValidator(rules=[ReglaDePrueba()]).validate(
            PDFFile.from_upload("doc.pdf", b"%PDF-1.4")
        )


# ----------------------------------------------------------------------
# MongoPDFRepository sobre mongomock (sin servidor MongoDB)
# ----------------------------------------------------------------------
@pytest.fixture()
def repo():
    return MongoPDFRepository(mongomock.MongoClient()["test_db"])


def _pdf(name: str = "doc.pdf", checksum: str = "abc123") -> PDF:
    return PDF(name=name, text="contenido", checksum=checksum)


def test_repositorio_exige_conexion_inyectada():
    with pytest.raises(RuntimeError, match="Database connection"):
        MongoPDFRepository(None)


def test_save_devuelve_id_y_persiste_el_documento(repo):
    pdf_id = repo.save(_pdf())
    assert isinstance(pdf_id, str) and pdf_id
    stored = repo.find_by_id(pdf_id)
    assert stored["id"] == pdf_id
    assert stored["name"] == "doc.pdf"
    assert stored["checksum"] == "abc123"
    assert "_id" not in stored  # el detalle de Mongo no escapa del adaptador


def test_find_by_checksum_localiza_y_descarta(repo):
    repo.save(_pdf(checksum="abc"))
    assert repo.find_by_checksum("abc")["checksum"] == "abc"
    assert repo.find_by_checksum("xyz") is None


def test_find_all_devuelve_read_models_sin_id_de_mongo(repo):
    repo.save(_pdf(name="a.pdf", checksum="1"))
    repo.save(_pdf(name="b.pdf", checksum="2"))
    docs = repo.find_all()
    assert len(docs) == 2
    assert all("id" in doc and "_id" not in doc for doc in docs)


def test_find_by_id_inexistente_devuelve_none(repo):
    assert repo.find_by_id(str(ObjectId())) is None


def test_find_by_id_malformado_devuelve_none(repo):
    assert repo.find_by_id("no-es-un-objectid") is None


def test_update_existente_refleja_los_cambios(repo):
    pdf_id = repo.save(_pdf(checksum="viejo"))
    updated = repo.update(pdf_id, _pdf(name="nuevo.pdf", checksum="nuevo"))
    assert updated["name"] == "nuevo.pdf"
    assert updated["checksum"] == "nuevo"
    assert repo.find_by_id(pdf_id)["checksum"] == "nuevo"


def test_update_inexistente_devuelve_none(repo):
    assert repo.update(str(ObjectId()), _pdf()) is None


def test_update_id_malformado_devuelve_none(repo):
    # Contrato coherente con find_by_id: id inválido ≡ no encontrado.
    assert repo.update("no-es-un-objectid", _pdf()) is None


def test_delete_existente_elimina_el_documento(repo):
    pdf_id = repo.save(_pdf())
    assert repo.delete(pdf_id) is True
    assert repo.find_by_id(pdf_id) is None


def test_delete_inexistente_devuelve_false(repo):
    assert repo.delete(str(ObjectId())) is False


def test_delete_id_malformado_devuelve_false(repo):
    # Contrato coherente con find_by_id: id inválido ≡ no encontrado.
    assert repo.delete("no-es-un-objectid") is False


# ----------------------------------------------------------------------
# Composition root (grafo completo, sin tocar MongoDB real)
# ----------------------------------------------------------------------
async def test_composition_root_registra_un_pdf_de_punta_a_punta(monkeypatch):
    """Se sustituye SOLO el driver (cliente de Mongo) por el de mongomock
    y se ejecuta el flujo real completo: controller -> casos de uso ->
    validador -> extractor pypdf -> MongoPDFRepository. Sin variables de
    entorno y sin conexión de red."""
    monkeypatch.setattr(settings, "_client", mongomock.MongoClient())
    controller = get_pdf_controller()

    file = MagicMock()
    file.filename = "simple.pdf"

    async def read() -> bytes:
        return SIMPLE_PDF

    file.read = read

    result = await controller.upload_pdf(file)

    assert result["status"] == "success"
    assert result["filename"] == "simple.pdf"
    assert result["checksum"] == hashlib.sha256(SIMPLE_PDF).hexdigest()
    assert result["id"]
