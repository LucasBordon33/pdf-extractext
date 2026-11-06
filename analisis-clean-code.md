# Análisis de Clean Code — pdf-extractext

**Fecha:** 2026-08-29
**Alcance:** Repositorio `pdf-extractext` (rama `master`).
**Método:** Revisión manual del código fuente y búsqueda de duplicaciones/código muerto con grep. Evaluación contra los principios **DRY, KISS, YAGNI y SOLID** (con apoyo del skill *clean-code*).

---

## 1. Veredicto global

| Principio | Estado | Nivel |
|---|---|---|
| DRY | ⚠️ Incumplido | Moderado (2 duplicaciones funcionales + strings repetidos) |
| KISS | ⚠️ Parcialmente cumplido | Bien en general, con 2-3 complejidades innecesarias |
| YAGNI | ❌ Incumplido | Código muerto y especulativo concreto |
| SOLID | ⚠️ Parcialmente cumplido | S y D con violaciones claras; L no aplica; O e I moderadas |

**Veredicto:** El código es corto, legible y de bajo acoplamiento a nivel de texto, pero **no cumple a cabalidad** con los principios. Las violaciones más importantes son: duplicación de la lógica de checksum, regla de negocio de duplicados repartida en dos capas, código muerto (dependency no usada, método estático sin llamar, imports sin usar), y violación de **DIP** (dependencias concretas, sin inyección ni abstracciones).

---

## 2. DRY — Don't Repeat Yourself

### 2.1 Duplicación funcional (la más grave)

**Cálculo de checksum implementado dos veces:**

| Lugar | Código |
|---|---|
| `services/pdf_service.py:29-30` | `def calculate_checksum(self, data): return hashlib.sha256(data).hexdigest()` |
| `repositories/pdf_repository.py:72-73` | `@staticmethod def generate_checksum(data): return hashlib.sha256(data).hexdigest()` |

La copia de la capa de repositorio **nunca se llama desde ningún lado** (verificado con grep: solo aparece su definición). Es duplicación **y** código muerto a la vez. Debería existir una única fuente (p. ej., en el servicio, o un módulo de utilidad).

### 2.2 Regla de negocio de duplicados en dos capas

La validación "¿este checksum ya existe?" está implementada y ejecutada en **dos lugares**:

- `controllers/pdf_controller.py:26` — `if self.pdf_repository.is_duplicate(pdf_data.checksum): raise ...`
- `repositories/pdf_repository.py:43` — `if self.is_duplicate(pdf.checksum): return {"status": "error", ...}` (dentro de `update_pdf`)

La misma regla, con el mismo mensaje, vive en dos capas. Si cambia la regla (p. ej., permitir duplicados), hay que tocar dos archivos.

### 2.3 Strings literales repetidos

- `"El PDF ya se encuentra repetido en la base de datos."` → `pdf_controller.py:29` y `pdf_repository.py:46`.
- `"PDF no encontrado"` → `pdf_controller.py:76, 100, 112` (tres veces, una por método).
- Patrón `raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="...")` repetido en `pdf_controller.py:38-41` y `:91-94`, y el patrón 404 en `:76, :100, :112`.

### 2.4 Detección de "no encontrado" duplicada en update

En `update_existing_pdf` el 404 se maneja **dos veces**: primero `_ensure_pdf_exists` (`pdf_controller.py:110-112`) y luego `if not updated: raise 404` (`pdf_controller.py:75-76`). Redundante; una sola comprobación basta.

---

## 3. KISS — Keep It Simple

### Puntos fuertes
- Clases y métodos **cortos**, con nombres declarativos (`is_duplicate`, `calculate_checksum`, `get_pdf_by_id`).
- La cadena upload → validar → procesar → persistir está bien separada en helpers (`_validate_file`, `_process_and_map_pdf`, `_build_response`).

### Complejidades innecesarias

1. **Llamada a método privado de otra clase** — `pdf_controller.py:106` invoca `self.pdf_validator._validate_is_pdf(file)`. Usar un método "privado" desde otra clase rompe el encapsulamiento; debería llamarse `validate_is_pdf` (público).
2. **Mezcla async/sync dentro del validador** — `pdf_validator.py:19-27` combina `await file.read(5)` con manipulación síncrona de `file.file.seek/tell` para obtener el tamaño. Funcional pero confuso; es más simple (y testeable) pasar el tamaño ya resuelto o validar en una sola estrategia.
3. **Manejo de errores por código de retorno** — `repositories/pdf_repository.py:43-47` devuelve un dict `{"status": "error", ...}` en lugar de lanzar una excepción, lo que obliga al controller a hacer un caso especial (`pdf_controller.py:78-79`). El Clean Code (cap. 7) recomienda **excepciones en lugar de códigos de retorno**: la lógica queda más limpia y no hay dos "idiomas" de error.
4. **Retorno `None`** — `get_pdf_by_id`, `update_pdf` y `delete_pdf` devuelven `None` ante fallos (`pdf_repository.py:36-40, 54-60, 66-69`), forzando a cada llamador a chequear nulos. La alternativa limpia: lanzar excepción de dominio y dejar que el controller la traduzca a HTTP.

---

## 4. YAGNI — You Aren't Gonna Need It

Código especulativo o muerto confirmado:

1. **`services/pdf_service.py:18`** — `self.repository = PDFRepository()`: la instancia se crea pero **nunca se usa** en ningún método del servicio (grep: solo aparece la asignación). El servicio debería depender solo del parsing/extractor.
2. **`repositories/pdf_repository.py:72-73`** — método estático `generate_checksum`: **nunca llamado** (el checksum lo calcula `PDFService.calculate_checksum`).
3. **`main.py:15-17`** — bloque de `uvicorn` comentado: código muerto que debería eliminarse.
4. **Imports sin usar** — `services/pdf_service.py:5` (`from models.pdf import PDF`) y `routers/pdf_router.py:3` (`from models.pdf import PDF`).
5. **Fixture de test inexistente** — `tests/test_controller.py:14` abre `tests/resources/test.pdf`, pero solo existe `tests/data/`; el test está roto y el fixture no fue generado.

---

## 5. SOLID

### S — Single Responsibility Principle

- **Violación principal: `PDFRepository`.** Mezcla responsabilidades de *persistencia* (CRUD, serialización) con *regla de negocio* (`is_duplicate`, `pdf_repository.py:25-26`). Además, la misma regla de negocio también se evalúa en el controller, así que la lógica de dominio está dispersa en dos capas.
- **`PDFController`** orquesta operaciones, valida, mapea DTOs y construye respuestas HTTP (`_build_response`). Es aceptable como capa de aplicación, pero la construcción de respuestas duplica formato entre `upload_pdf` y `update_existing_pdf` (debería ser una sola función de mapeo de respuesta).
- **`PDFValidator`** y **`PDFService`**: responsabilidades únicas y coherentes (validación / extracción de texto). Cumplen.

### O — Open/Closed Principle

- **`PDFValidator._validate_is_pdf`** (`pdf_validator.py:15`): agregar una nueva regla de validación obliga a **modificar** el método. No está abierto a extensión (se necesitaría una lista de validadores o estrategias).
- **`PDFRepository`**: es el punto más "abierto" del sistema porque acepta `db` por constructor (`pdf_repository.py:15-16`), lo que permite inyectar un mock. Bien por ese lado, pero la regla de negocio embebida lo cierra a variaciones de la misma.

### L — Liskov Substitution Principle

- **No aplica**: no existe jerarquía de herencia ni polimorfismo de subtipos en el proyecto. Sin violaciones.
- Nota: `update_pdf` devuelve **tres formas distintas** (dict de éxito, dict de error, `None`) — es un "código de retorno polimórfico", olor a código relacionado con el manejo de errores más que con LSP.

### I — Interface Segregation Principle

- No hay interfaces ni protocolos en el proyecto. **`PDFRepository` expone una interfaz "gorda"**: CRUD + `is_duplicate` + `generate_checksum` (sin uso) + helpers. Los clientes (`PDFController`, `PDFService`) se ven obligados a conocer métodos que no necesitan.
- La segregación se resolvería con interfaces específicas por rol (p. ej., `PdfReader` / `PdfWriter`), o al menos eliminando los métodos muertos.

### D — Dependency Inversion Principle

**Es la violación más seria del proyecto:**

- `PDFController.__init__` (`pdf_controller.py:15-18`) **instancia directamente** a sus dependencias concretas: `PDFService()`, `PDFRepository()`, `PDFValidator()`. Los módulos de alto nivel dependen de módulos de bajo nivel concretos, no de abstracciones.
- `PDFService.__init__` (`pdf_service.py:17-18`) también instancia `PDFRepository()` — incluso sin usarlo.
- `PDFRouter.__init__` (`pdf_router.py:14-17`) instancia `PDFController()` concreto.
- La única inyección por constructor es la de `PDFRepository(db=None)`, y quedó aislada: `PDFController` **no** acepta dependencias inyectadas. Esto no solo viola DIP, sino que es la causa directa de que `tests/test_controller.py` esté roto (instancia `PDFController(PDFService(), PDFRepository())` y la firma ya no lo permite).

**Efecto práctico:** imposible testear/mockear capas por separado; el sistema está atado a implementaciones concretas y a infraestructura real (MongoDB).

---

## 6. Resumen por archivo

| Archivo | DRY | KISS | YAGNI | SOLID |
|---|---|---|---|---|
| `controllers/pdf_controller.py` | Strings/patrones HTTP repetidos; doble 404 en update | Bien; llama a método privado del validador | — | DIP ❌; O moderada; S aceptable |
| `services/pdf_service.py` | Checksum duplicado con repositorio | Bien | Código muerto: `self.repository`; import sin usar | DIP ❌ (instancia repo concreto) |
| `services/pdf_validator.py` | — | Mezcla async/sync; método "privado" usado externamente | — | O ❌ (agregar regla = modificar) |
| `repositories/pdf_repository.py` | Checksum duplicado; regla de duplicado duplicada | Errores por código de retorno y `None` | `generate_checksum` muerto | S ❌ (regla de negocio en repositorio); I ❌ (interfaz gorda) |
| `routers/pdf_router.py` | — | Bien | Import sin usar | DIP ❌ (instancia controller concreto) |
| `main.py` | — | Bien | Bloque uvicorn comentado | DIP ❌ (composición toda concreta) |

---

## 7. Recomendaciones (ordenadas por impacto)

1. **Inyección de dependencias (DIP)**: `PDFController.__init__(self, pdf_service=None, pdf_repository=None, pdf_validator=None)` y `PDFService.__init__(self, repository=None)`. De paso **arregla los tests rotos** y permite mockear MongoDB.
2. **Una sola fuente de checksum**: eliminar `PDFRepository.generate_checksum` y dejar solo `PDFService.calculate_checksum` (DRY + YAGNI).
3. **Mover la regla de negocio de duplicados al servicio**: que `is_duplicate` viva en una sola capa (servicio) y el repositorio quede solo como persistencia (SRP). Unificar mensajes en constantes.
4. **Excepciones en vez de códigos de retorno/`None`** en el repositorio (lanzar excepción de dominio, traducir a HTTP en el controller) — KISS y cap. 7 de Clean Code.
5. **Eliminar código muerto**: `self.repository` en `PDFService`, bloque comentado de `main.py`, imports sin usar (`pdf_service.py:5`, `pdf_router.py:3`), y el fixture inexistente del test (YAGNI).
6. **Hacer público `validate_is_pdf`** y quitar la manipulación mezclada de streams del validador (KISS, encapsulamiento).
7. **Eliminar la doble comprobación de 404 en `update_existing_pdf`** (DRY).
8. **Opción futura**: definir `Protocol`s/interfaces (`PDFRepository`, validador) para segregar y completar la inversión de dependencias (I + D).

---

## 8. Checklist del skill clean-code

- [ ] ¿La función es menor a 20 líneas? — **Sí** en general (todas las funciones cumplen).
- [ ] ¿Hace exactamente una cosa? — **Parcial**: `update_existing_pdf` y `_validate_is_pdf` agrupan varias reglas.
- [ ] ¿Los nombres son buscables y revelan intención? — **Sí** (salvo `_validate_is_pdf` llamado con prefijo privado y `update_existing_pdf` vs `update_pdf`).
- [ ] ¿Evité comentarios haciendo el código más claro? — **Sí**; los comentarios restantes son docstrings de módulo (aceptables).
- [ ] ¿Paso demasiados argumentos? — **No** (0-1 argumentos en todas las funciones).
- [ ] ¿Hay un test fallando para este cambio? — **N/A** para análisis; cabe notar que la suite actual está rota.
- [ ] ¿Evité errores por códigos de retorno/`None`? — **No** (repositorio devuelve `None` y dicts de error).
