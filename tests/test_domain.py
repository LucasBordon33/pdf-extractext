"""
Tests unitarios del seam de DOMINIO (ver CONTEXT.md §1, seam 2).

Objetos puros (sin dobles ni infraestructura): el invariante de la
entidad `PDF` (checksum obligatorio) y las propiedades derivadas e
inmutabilidad del value object `PDFFile`.
"""
import dataclasses

import pytest
from pydantic import ValidationError

from domain.entities import PDF
from domain.pdf_file import PDFFile


# --- Entidad PDF: invariante de checksum requerido ----------------------

def test_pdf_valido_se_construye():
    pdf = PDF(name="doc.pdf", text="contenido", checksum="abc123")
    assert pdf.name == "doc.pdf"
    assert pdf.text == "contenido"
    assert pdf.checksum == "abc123"


def test_pdf_sin_checksum_viola_el_invariante():
    with pytest.raises(ValidationError):
        PDF(name="doc.pdf", text="contenido")


@pytest.mark.parametrize("checksum", ["", "   "])
def test_pdf_con_checksum_vacio_o_espacios_viola_el_invariante(checksum):
    with pytest.raises(ValidationError):
        PDF(name="doc.pdf", text="contenido", checksum=checksum)


# --- Value object PDFFile ------------------------------------------------

def test_pdffile_propiedades_derivadas():
    content = b"%PDF-1.4 contenido"
    pdf_file = PDFFile.from_upload("doc.pdf", content)

    assert pdf_file.size == len(content)
    assert pdf_file.has_pdf_extension is True
    assert pdf_file.has_pdf_magic_bytes is True


def test_pdffile_extension_y_firma_invalidas():
    pdf_file = PDFFile.from_upload("doc.txt", b"texto plano")

    assert pdf_file.has_pdf_extension is False
    assert pdf_file.has_pdf_magic_bytes is False


def test_pdffile_es_inmutable():
    pdf_file = PDFFile.from_upload("doc.pdf", b"%PDF-1.4")

    with pytest.raises(dataclasses.FrozenInstanceError):
        pdf_file.filename = "otro.pdf"


def test_pdffile_filename_ausente_se_normaliza_a_vacio():
    pdf_file = PDFFile.from_upload(None, b"%PDF-1.4")

    assert pdf_file.filename == ""
    assert pdf_file.has_pdf_extension is False
