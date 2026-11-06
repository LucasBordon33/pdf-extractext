# CONTEXT.md — Seams y reglas de testeo

> Documento derivado de la sección 7 ("Recomendaciones para alcanzar cumplimiento") de
> [`analisis-tdd.md`](./analisis-tdd.md) y actualizado tras la migración completa al
> stack de Clean Architecture (`domain/`, `application/`, `infrastructure/`,
> `interfaces/`). Define **dónde** se testea el proyecto (seams/fronteras),
> **cómo** aislar cada capa y **bajo qué reglas** se desarrolla con TDD.

## 0. Mapa de la arquitectura (referencia para los seams)

| Capa | Código | Rol |
|---|---|---|
| Dominio | `domain/entities.py`, `domain/pdf_file.py`, `domain/exceptions.py` | Entidad `PDF`, value object `PDFFile`, excepciones de negocio |
| Aplicación | `application/ports.py`, `application/use_cases.py` | Puertos (interfaces ABC) y casos de uso con las reglas de negocio |
| Infraestructura | `infrastructure/persistence/`, `infrastructure/pdf/` | Adaptadores: repositorio Mongo, validador de formato, extractor pypdf |
| Interfaces | `interfaces/routers/`, `interfaces/controllers/`, `interfaces/dependencies.py` | Router HTTP, controller (traducción de errores) y composition root |
| Config | `config/settings.py` | Conexión diferida a Mongo (`get_db()`), sin wiring al importar |

Las dependencias apuntan siempre hacia adentro:
`interfaces → application → domain`; `infrastructure` implementa los puertos
definidos por la aplicación. La persistencia aplica el **Principio de
Segregación de Interfaces (ISP)**: el antiguo `PDFRepositoryPort` se dividió
en dos contratos separados — `ReaderPort` (solo consultas) y `WriterPort`
(solo mutaciones) — que cada adaptador concreto implementa ambos; cada caso
de uso depende únicamente del rol que usa.

## 1. Seams (fronteras de testeo)

El proyecto se prueba en **tres seams acordados**. Ningún test cruza hacia
infraestructura externa: la base de datos MongoDB real **nunca** se toca en tests
y ningún test depende de variables de entorno ni de `.env`.

| Seam | Qué se prueba | Qué se aísla | Herramienta de aislamiento |
|---|---|---|---|
| **HTTP (integración)** (`main.app`, `interfaces/routers/pdf_router.py`, `interfaces/controllers/pdf_controller.py`) | Contrato HTTP (status codes, payloads), mapeo `UploadFile` → `PDFFile`, traducción de excepciones de dominio a `HTTPException` (400/404/409/500) | Composition root real y MongoDB | `app.dependency_overrides[get_pdf_controller]` con casos de uso reales + repositorio en memoria que implementa los puertos segregados `ReaderPort` y `WriterPort` |
| **Casos de uso / dominio** (`application/use_cases.py`, `domain/`) | Reglas de negocio puras: duplicados por checksum (`_ensure_not_duplicate`), cálculo de checksum (`_calculate_checksum`), existencia previa en update/delete, propiedades derivadas de `PDFFile` | Puertos de persistencia, validación y extracción | Dobles de prueba contra los puertos (`ReaderPort`/`WriterPort` según el rol del caso de uso, `ValidatorPort`, `TextExtractorPort`): fakes en memoria o `MagicMock(spec=...)` |
| **Adaptador de persistencia** (`infrastructure/persistence/mongo_pdf_repository.py`) | Implementación del puerto sobre Mongo: consultas, serialización `_id` → `id`, tolerancia a `ObjectId` inválidos | Servidor MongoDB | **`mongomock`** (MongoDB en memoria) |

## 2. Cómo probar el seam HTTP (router + controller)

- El composition root vive en `interfaces/dependencies.py`: `get_pdf_controller()`
  compone el bundle `PDFUseCases` con sus adaptadores **por request**, vía
  `Depends(get_pdf_controller)`. Importar `main` **no** construye nada ni exige
  variables de entorno (la conexión a Mongo es diferida, `config.settings.get_db()`).
- En tests se sobrescribe la dependencia con el mecanismo nativo de FastAPI:

  ```python
  main.app.dependency_overrides[get_pdf_controller] = lambda: PDFController(use_cases)
  ```

  inyectando un bundle `PDFUseCases` real construido sobre un
  `InMemoryPDFRepository(ReaderPort, WriterPort)`. Así se ejercita la cadena completa
  (router → controller → casos de uso → dominio) sustituyendo solo la persistencia.
- Se prueba con `fastapi.testclient.TestClient`, sin levantar servidor ni Mongo.
- Si se testea el controller en forma unitaria, el `UploadFile` se simula con
  `AsyncMock` para `read()` (el mapeo `_to_domain_file` lo aguarda); un `MagicMock`
  común rompe con `TypeError: object can't be used in 'await' expression`.
- Referencia: `tests/test_router.py`.

## 3. Cómo probar el adaptador de persistencia (aislando la base de datos)

- `MongoPDFRepository(db)` **requiere** la conexión inyectada en su constructor; en
  producción la obtiene de `config.settings.get_db()` (conexión diferida; importar
  el módulo no crea clientes ni exige variables de entorno).
- En tests se inyecta **`mongomock`**:
  `MongoPDFRepository(mongomock.MongoClient()["test_db"])`. Esto permite probar
  consultas, serialización y `ObjectId` reales (paquete `bson`) sin un servidor
  MongoDB corriendo.
- Prohibido en tests: levantar un `MongoClient` real, depender de `.env`, o parchear
  `ObjectId`/colecciones a mano — `mongomock` ya cubre ese comportamiento.
- Estado actual: la suite unitaria del adaptador está pendiente de escribir; hoy el
  adaptador queda cubierto de forma indirecta por el seam HTTP (con el repositorio
  en memoria sustituyéndolo).

## 4. Regla de ciclo TDD (rojo → verde → refactor) en rebanadas verticales

Todo desarrollo futuro sigue el ciclo **por rebanada vertical** (una porción completa
y mínima de funcionalidad que atraviesa las capas necesarias — router, controller,
casos de uso, puertos/adaptadores — no capas horizontales separadas):

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
  (sin Mongo real, sin `.env`, sin llamadas a métodos privados, sin tests
  tautológicos).
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
