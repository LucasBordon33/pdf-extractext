# CONTEXT.md — Seams y reglas de testeo

> Documento derivado de la sección 7 ("Recomendaciones para alcanzar cumplimiento") de
> [`analisis-tdd.md`](./analisis-tdd.md). Define **dónde** se testea el proyecto
> (seams/fronteras), **cómo** aislar cada capa y **bajo qué reglas** se desarrolla con TDD.

## 1. Seams (fronteras de testeo)

El proyecto se prueba en **tres seams acordados**. Ningún test cruza hacia
infraestructura externa: la base de datos MongoDB real **nunca** se toca en tests.

| Seam | Qué se prueba | Qué se aísla | Herramienta de aislamiento |
|---|---|---|---|
| **Servicio** (`services/pdf_service.py`) | Lógica de negocio pura: `extract_text_from_pdf_stream`, `calculate_checksum`, detección de duplicados (`is_duplicate`) | Repositorio y lector de PDF | `MagicMock` para el repositorio; `patch` sobre `PdfReader` |
| **Router HTTP + Controller** (`routers/pdf_router.py`, `controllers/pdf_controller.py`) | Contrato HTTP (status codes, payloads) y orquestación del controller | Servicio y validador (async), conexión a Mongo | `AsyncMock` / `FakeRepository` + inyección de dependencias |
| **Repositorio** (`repositories/pdf_repository.py`) | Consultas, serialización, `ObjectId`, excepciones de dominio (`PDFNotFoundException`) | Servidor MongoDB | **`mongomock`** (MongoDB en memoria) |

## 2. Cómo probar Router HTTP y Controllers

- `PDFController` recibe sus colaboradores por **inyección en el constructor**
  (`PDFController(pdf_service=..., pdf_validator=...)`). En tests **siempre** se
  inyectan dobles; nunca se deja que el controller construya sus dependencias reales.
- Toda colaboración **asíncrona** se mockea con **`AsyncMock`**
  (`unittest.mock.AsyncMock`): `service.upload_pdf`, `service.update_pdf` y
  `validator.validate_is_pdf` se llaman con `await`; un `MagicMock` común rompe con
  `TypeError: 'MagicMock' object can't be awaited`.
- Para el **router** se inyecta un `FakeRepository` en memoria a través de la cadena
  real `PDFService → PDFController`, y se parchea únicamente la instanciación de
  `PDFController` en el router (`patch("routers.pdf_router.PDFController", ...)`).
  Se prueba con `fastapi.testclient.TestClient`, sin levantar servidor ni Mongo.
- Referencia: `tests/test_controller.py` y `tests/test_router.py`.

## 3. Cómo probar el Repositorio (aislando la base de datos)

- `PDFRepository` **requiere** la conexión inyectada en su constructor:
  `PDFRepository(db)`. En producción el punto de composición la obtiene de
  `config.settings.get_db()` (conexión diferida; importar el módulo no crea clientes
  ni exige variables de entorno).
- En tests se inyecta **`mongomock`**: `PDFRepository(db=mongomock.MongoClient()["test_db"])`.
  Esto permite probar consultas, serialización e `ObjectId` reales (paquete `bson`)
  sin un servidor MongoDB corriendo.
- Prohibido en tests: levantar un `MongoClient` real, depender de `.env`, o parchear
  `ObjectId`/colecciones a mano — `mongomock` ya cubre ese comportamiento.
- Referencia: `tests/test_repository.py`.

## 4. Regla de ciclo TDD (rojo → verde → refactor) en rebanadas verticales

Todo desarrollo futuro sigue el ciclo **por rebanada vertical** (una porción
completa y mínima de funcionalidad que atraviesa las capas necesarias — router,
controller, servicio, repositorio — no capas horizontales separadas):

1. **Rojo**: escribir primero *un* test de la rebanada con **pytest** (funciones
   sueltas, `assert` nativo, fixtures con `@pytest.fixture`; async con
   `pytest-asyncio` en modo `auto`). Ejecutarlo y **verlo fallar** por el motivo
   correcto. Commit del test rojo por separado.
2. **Verde**: implementar lo **mínimo** para que ese test pase. Ejecutar y verlo
   verde. Commit de la implementación.
3. **Refactor**: mejorar el diseño sin cambiar comportamiento, manteniendo la suite
   en verde (`pytest` completo tras cada cambio). Commit del refactor.

Reglas derivadas:

- **Una rebanada vertical por ciclo**; prohibido commitear "bulk" de tests junto con
  la feature entera (test-after).
- Los tests viven **solo en los seams** de este documento y se mantienen aislados
  (sin Mongo real, sin llamadas a métodos privados, sin tests tautológicos).
- La suite debe estar **en verde para fusionar**: el job de CI
  (`.github/workflows/ci.yml`) ejecuta `uv sync --locked` + `uv run pytest` en cada
  push a `master`.

## 5. Comandos de referencia

```bash
# Instalar dependencias (dev incluye pytest, pytest-asyncio, mongomock)
uv sync

# Ejecutar toda la suite
uv run pytest
```
