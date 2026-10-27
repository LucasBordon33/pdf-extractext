# Análisis de cumplimiento de TDD — pdf-extractext

**Fecha:** 2026-08-29
**Alcance:** Repositorio `pdf-extractext` (rama `master`).
**Método:** Revisión del código fuente, de los 4 archivos de test y del historial de `git` (orden temporal de commits de tests vs. implementación). Verificación ejecutando la suite de tests localmente.

---

## 1. Veredicto

**NO cumple con TDD.**

- No hay evidencia en el historial de que los tests se hayan escrito **antes** de la implementación (no existe ningún ciclo red → green).
- Los tests y la implementación se commitean **juntos en el mismo commit** (patrón *test-after*), por lo que nunca se observó un test fallando por el comportamiento faltante.
- La suite actual está **completamente roja**, pero no por un ciclo TDD en curso: está roja porque un refactor posterior renombró métodos y cambió firmas sin actualizar los tests.
- Hay anti-patrones claros: tests acoplados a la implementación (métodos privados, colaboradores internos), dependencia de una base de datos real (MongoDB) sin aislamiento ni mocks, y escritura en "rebanadas horizontales" en lugar de rebanadas verticales.

---

## 2. Metodología

1. Lectura del código fuente: `main.py`, `routers/pdf_router.py`, `controllers/pdf_controller.py`, `services/pdf_service.py`, `services/pdf_validator.py`, `repositories/pdf_repository.py`, `models/pdf.py`, `config/settings.py`.
2. Lectura de los tests: `tests/test_router.py`, `tests/test_controller.py`, `tests/test_extract_text.py`, `tests/test_repository.py`.
3. Análisis del historial git para determinar el **orden temporal** entre tests y código (requisito del ciclo red → green).
4. Ejecución de la suite de tests para verificar el estado real.

---

## 3. Evidencia en el historial de git (orden red → green)

El requisito central de TDD es que el test falle (rojo) **antes** de escribir la implementación mínima que lo hace pasar (verde). En este repositorio, tests y código de producción siempre aparecen **en el mismo commit**:

| Commit | Fecha | Qué agrega | Orden |
|---|---|---|---|
| `3ada6de` "Agregado el sistema de conversion de PDF a String" | 2026-04-13 | `tests/test_extract_text.py` + PDFs de datos **+** implementación de `PDFService` | Test + implementación juntos |
| `cdcd9e2` "Mejorada lógica de pdf_service.py, mejorada logica de las TDD de la extracción de texto" | 2026-05-11 | `tests/test_extract_text.py` **+** `services/pdf_service.py` | Test + implementación juntos |
| `3137df1` "TDD de CRUD añadido" | 2026-05-11 | `tests/test_crud.py` **+** controller, router y service del CRUD | Test + implementación juntos |

**Conclusión:** No existe ningún commit que contenga solo un test fallando (estado rojo) previo a la implementación. El ciclo red → green → refactor **nunca se ejecutó**; el término "TDD" en los mensajes de commit etiqueta lo que en realidad es desarrollo *test-after* (tests escritos después o en paralelo al código).

---

## 4. Estado actual de la suite (verificación ejecutando los tests)

La suite se ejecuta con `unittest` (no hay config de pytest ni CI). **Todos los tests fallan o cuelgan**, y las causas son refactors que no actualizaron los tests:

| Suite | Resultado | Causa raíz |
|---|---|---|
| `tests/test_extract_text.py` | 3 errores | El test llama a `service.extract_text_from_pdf_stream(...)` pero el método fue renombrado a **privado** `_extract_text_from_pdf_stream` en `services/pdf_service.py:32` (commit `1a96000`). `AttributeError`. |
| `tests/test_controller.py` | 3 errores | El test instancia `PDFController(PDFService(), PDFRepository())` pero el `__init__` ahora no recibe argumentos (la inyección de dependencias se eliminó en el refactor, `pdf_controller.py:15`). `TypeError`. Además, `test_upload_pdf` abre `tests/resources/test.pdf`, **archivo inexistente** (solo existe `tests/data/`). |
| `tests/test_repository.py` | cuelga / depende de Mongo | Sin `.env` lanza `ValueError`; con un `.env` dummy se cuelga intentando conectar a `mongodb:27017`. No hay mock ni base aislada. |
| `tests/test_router.py` | cuelga / depende de Mongo | Idem: `main.py` importa `settings.py` → `MongoClient`. No hay test client con dependencias reemplazadas. |

**Implicación:** El equipo no corre la suite (o no la mantiene), porque el refactor de "mejora de principios" (`1a96000`, 2026-07-17) rompió los tests y estos no se corrigieron en 6 semanas de commits posteriores. En TDD, la suite debe estar siempre en verde al finalizar cada ciclo; aquí está rota por desactualización, no por un ciclo en curso.

---

## 5. Análisis contra los criterios de la disciplina

### 5.1 Seams (dónde se testea)

- **No hay seams pre-acordados ni documentados.** No existe `CONTEXT.md` ni ADRs que definan la interfaz pública a testear.
- Los tests se dispersan por **cuatro capas a la vez** (router, controller, service, repository) sin que ninguna sea una frontera consistente.
- `test_controller.py` instancia colaboradores internos directamente (`PDFController(PDFService(), PDFRepository())`) en lugar de testear a través de una interfaz pública (el router sería el seam natural). Esto además está roto porque la inyección se eliminó.
- `test_extract_text.py` originalmente testeaba el **método privado** `_extract_text` (versión de `3ada6de`), una prueba acoplada al detalle interno.

### 5.2 Anti-patrones presentes

- **Acoplado a la implementación** — Tests sobre métodos privados (`_extract_text`), instanciación directa de colaboradores, y dependencia de una base de datos real en lugar de un doble de prueba. El test se rompe por refactors sin cambio de comportamiento (exactamente lo que ocurrió en `1a96000`).
- **Rebanada horizontal** — El CRUD completo + sus 4-5 tests se commitearon de una vez (`3137df1`); la extracción de texto + tests idem (`3ada6de`). No se trabajó en rebanadas verticales (un test → una implementación → repetir). El propio `test_crud.py` original usaba nombres numerados (`test_1_create_pdf`, `test_2_...`), reflejo de escritura en lote.
- **Sin aislamiento / no deterministas** — Los tests de repository y router dependen de estado real de MongoDB y de datos creados por el propio test (create → read → update → delete encadenados). Falla por causas externas al código (DB caída, datos residuales, timeouts de red).
- **Valores esperados débiles o auto-referenciales** — En `test_repository.py` se valida con `assertIsNotNone` / `assertIsInstance(list)` sobre resultados de la propia base, sin una fuente de verdad independiente (literal conocido del spec).

### 5.3 Reglas del ciclo

- **Rojo antes de verde:** No se cumple (ver sección 3).
- **Una rebanada a la vez:** No se cumple; los commits agrupan features completas + tests.
- **El refactor no es parte del ciclo:** La disciplina TDD exige que tras un refactor la suite siga en verde. Aquí el refactor de `1a96000` dejó la suite rota y nunca se reparó, es decir, **se rompió el invariante de suite en verde**.

---

## 6. Hallazgos puntuales por archivo

| Archivo | Hallazgo |
|---|---|
| `tests/test_extract_text.py:13,20,27` | Llama a método público inexistente; el real es privado. Test no actualizado tras refactor. |
| `tests/test_controller.py:11` | `PDFController(PDFService(), PDFRepository())` — firma obsoleta; rompe en `TypeError`. |
| `tests/test_controller.py:14` | Abre `tests/resources/test.pdf`; ese directorio no existe (solo `tests/data/`). |
| `services/pdf_service.py:32` | `_extract_text_from_pdf_stream` privado: el seam correcto sería el público `extract_text_from_pdf_stream` (o renombrar el test). |
| `repositories/pdf_repository.py:15-22` | Levanta conexión real a Mongo en `__init__`; imposible de testear sin infraestructura externa. |
| `config/settings.py:12-16` | Lanza `ValueError` sin `.env`; impide que cualquier test importe `main` de forma aislada. |

---

## 7. Recomendaciones para alcanzar cumplimiento

1. **Definir los seams** y documentarlos (crear `CONTEXT.md`). Sugerencia: seam de servicio (`extract_text_from_pdf_stream`, `calculate_checksum`) y seam de router/HTTP con dependencias inyectadas o mockeadas.
2. **Aislar la base de datos**: inyectar una conexión mock/fake en `PDFRepository` (ya acepta `db` en `__init__`, buena base) y mockearla en tests de controller/router. Nunca tocar Mongo real en tests.
3. **Restaurar la inyección de dependencias** en `PDFController` (que acepte `service` y `repository` por parámetro) para que sea testeable sin refactorizar la firma de test.
4. **Rehacer los tests bajo el ciclo real**: escribir primero el test que falla, verlo rojo, implementar lo mínimo, verlo verde, refactorizar manteniendo verde. Commits separados de "test rojo" y "implementación".
5. **Automatizar**: agregar runner de pytest, `pytest-cov`, y un job de CI que ejecute la suite en cada PR; la suite debe estar en verde para fusionar.
6. **Corregir el estado actual**: actualizar `test_extract_text.py` al nombre del método público, arreglar `test_controller.py` a la firma y al fixture correcto (`tests/data/simple.pdf`).

---

## 8. Resumen ejecutivo

| Criterio | ¿Se cumple? |
|---|---|
| Test escrito antes que el código (rojo) | ❌ No (siempre juntos en el mismo commit) |
| Una rebanada vertical por ciclo | ❌ No (bulk de tests + feature) |
| Suite en verde tras refactors | ❌ No (suite rota desde `1a96000`) |
| Tests en seams acordados | ❌ No (4 capas, sin acuerdo documentado) |
| Tests aislados / sin infraestructura externa | ❌ No (depende de MongoDB real) |
| Tests libres de anti-patrones (privados, tautológicos) | ❌ No (métodos privados, colaboradores directos) |
| **Cumplimiento global de TDD** | **❌ No cumple** |

Los tests representan un intento de cobertura *a posteriori* ("test-after"), con buenas intenciones (casos de PDF válido/vacío/inválido, casos HTTP), pero la mecánica, el orden y el aislamiento requeridos por TDD no están presentes, y la suite se encuentra actualmente en rojo por desactualización.
