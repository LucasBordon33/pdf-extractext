import mongomock
import pytest
from bson import ObjectId

from repositories.pdf_repository import PDFRepository
from models.pdf import PDF
from config.exceptions import PDFNotFoundException


@pytest.fixture()
def repo():
    # Base de datos MongoDB falsificada en memoria: sin infraestructura externa
    db = mongomock.MongoClient()["test_db"]
    return PDFRepository(db=db)


def _create_pdf(repo, name="test.pdf", text="contenido", checksum="abc") -> str:
    return repo.create_pdf(PDF(name=name, text=text, checksum=checksum))


def test_find_by_checksum(repo):
    _create_pdf(repo)
    result = repo.find_by_checksum("abc")
    assert result is not None
    assert result["checksum"] == "abc"


def test_find_by_checksum_not_found(repo):
    assert repo.find_by_checksum("nonexistent") is None


def test_create_pdf(repo):
    pdf_id = _create_pdf(repo)
    assert pdf_id is not None
    stored = repo.get_pdf_by_id(pdf_id)
    assert stored["name"] == "test.pdf"


def test_get_pdfs(repo):
    _create_pdf(repo)
    pdfs = repo.get_pdfs()
    assert isinstance(pdfs, list)
    assert len(pdfs) == 1
    assert pdfs[0]["name"] == "test.pdf"


def test_get_pdf_by_id(repo):
    pdf_id = _create_pdf(repo)
    result = repo.get_pdf_by_id(pdf_id)
    assert result is not None
    assert result["id"] == pdf_id
    assert result["name"] == "test.pdf"


def test_get_pdf_by_id_not_found(repo):
    with pytest.raises(PDFNotFoundException):
        repo.get_pdf_by_id(str(ObjectId()))


def test_get_pdf_by_id_invalid_id(repo):
    with pytest.raises(PDFNotFoundException):
        repo.get_pdf_by_id("id-invalido")


def test_update_pdf(repo):
    pdf_id = _create_pdf(repo)
    updated = repo.update_pdf(pdf_id, PDF(name="nuevo.pdf", text="nuevo"))
    assert updated["name"] == "nuevo.pdf"


def test_update_pdf_not_found(repo):
    pdf = PDF(name="test.pdf", text="contenido")
    with pytest.raises(PDFNotFoundException):
        repo.update_pdf(str(ObjectId()), pdf)


def test_update_pdf_invalid_id(repo):
    pdf = PDF(name="test.pdf", text="contenido")
    with pytest.raises(PDFNotFoundException):
        repo.update_pdf("id-invalido", pdf)


def test_delete_pdf(repo):
    pdf_id = _create_pdf(repo)
    result = repo.delete_pdf(pdf_id)
    assert result
    assert result["id"] == pdf_id
    with pytest.raises(PDFNotFoundException):
        repo.get_pdf_by_id(pdf_id)


def test_delete_pdf_not_found(repo):
    with pytest.raises(PDFNotFoundException):
        repo.delete_pdf(str(ObjectId()))


def test_delete_pdf_invalid_id(repo):
    with pytest.raises(PDFNotFoundException):
        repo.delete_pdf("id-invalido")


def test_is_duplicate_removed(repo):
    with pytest.raises(AttributeError):
        repo.is_duplicate("abc")
