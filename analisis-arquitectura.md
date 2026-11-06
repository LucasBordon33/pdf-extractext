# Análisis de Arquitectura de Capas — pdf-extractext

**Fecha:** 2026-08-29
**Alcance:** Repositorio `pdf-extractext` (rama `master`).
**Objetivo:** Determinar qué estilo de arquitectura se está usando (N-capas, Hexagonal, Onion o Clean), evaluar el cumplimiento de cada uno y proponer una evolución.
**Método:** Lectura del código fuente, verificación de dependencias (imports, instanciación) y puntos calientes del historial de `git`.

---

## 1. Veredicto

**La arquitectura actual es un monolito N-capas clásico (4 capas técnicas horizontales).**

No es Hexagonal, no es Onion y no es Clean. El proyecto tiene la **forma física** que recuerda a esos estilos (carpetas `controllers/`, `services/`, `repositories/`), pero le faltan los elementos estructurales que los definen: **interfaces/puertos, núcleo de dominio con reglas de negocio, inversión de dependencias y casos de uso explícitos**.

| Arquitectura | ¿Es? | ¿Por qué? |
|---|---|---|
| **N-capas** | ✅ **Sí** | 4 capas horizontales con flujo descendente concreto (web → app → servicio → persistencia). |
| **Hexagonal** | ❌ No | Sin puertos ni adaptadores; el "núcleo" está acoplado al framework y a Mongo. |
| **Onion** | ❌ No | El núcleo de dominio no existe (entidades anémicas, sin reglas); las capas externas instancian internas concretas. |
| **Clean** | ❌ No | No hay entidades / casos de uso / adaptadores separados; framework (FastAPI) filtrado al servicio. |

**Conclusión ejecutiva:** es una base razonable y simple de N-capas, pero la **ausencia de inversión de dependencias** y la **dispersión de reglas de negocio** (duplicados, checksum, validación) impiden evolucionar hacia Hexagonal/Onion/Clean sin antes crear un núcleo de dominio y puertos.

---

## 2. Arquitectura actual (mapa)

### 2.1 Capas y ubicación

| # | Capa | Rol | Código |
|---|---|---|---|
| 1 | **Presentación / HTTP** | Contratos HTTP, endpoints | `main.py`, `routers/pdf_router.py` |
| 2 | **Aplicación / Orquestación** | Casos de uso, respuesta HTTP | `controllers/pdf_controller.py` |
| 3 | **Servicios (lógica técnica)** | Extracción de texto, checksum, validación | `services/pdf_service.py`, `services/pdf_validator.py` |
| 4 | **Persistencia / Infraestructura** | Mongo, serialización | `repositories/pdf_repository.py`, `config/settings.py` |
| — | **Modelos (DTO compartido)** | Transporte de datos | `models/pdf.py` |

### 2.2 Grafo de dependencias (concreto, top-down)

```
main.py
  └─ routers/pdf_router.py          (instancia PDFController)
       └─ controllers/pdf_controller.py   (instancia PDFService, PDFRepository, PDFValidator)
            ├─ services/pdf_service.py     (instancia PDFRepository — no la usa)
            ├─ services/pdf_validator.py
            └─ repositories/pdf_repository.py  (usa config.settings.db)
                  └─ config/settings.py    (MongoClient se crea AL IMPORTAR)
                        └─ MongoDB (Atlas / docker)
models/pdf.py  ← compartida por todas las capas
```

### 2.3 Puntos calientes del historial (dónde está el acoplamiento)

Los archivos que más cambian juntos son exactamente las capas: `pdf_controller.py` (12 cambios), `pdf_service.py` (11), `pdf_repository.py` (11), `main.py` (10), `pdf_router.py` (7). El stack de capas es el "punto caliente" del sistema: cada cambio de lógica obliga a tocar la cadena completa de forma encadenada.

---

## 3. Análisis contra N-capas

### Lo que se cumple
- **Separación horizontal clásica** de 4 capas con nombres convencionales y flujo descendente: router → controller → service → repository.
- **Los modelos (DTO)** son objetos de transporte pydantic, como manda la tradición N-capas.
- Comprensible de un vistazo: la regla de dependencia "arriba → abajo" se respeta en la dirección de los imports.

### Lo que falla en su propia lógica
1. **Regla de negocio en la capa de infraestructura.** `is_duplicate` (`repositories/pdf_repository.py:25-26`) es una regla de negocio ("un PDF no puede repetirse por checksum") viviendo en la capa de persistencia. En N-capas, la lógica de negocio pertenece a la capa de servicios.
2. **La regla se duplica en dos capas**: `controllers/pdf_controller.py:26` también evalúa `is_duplicate`, y `repositories/pdf_repository.py:43` la vuelve a evaluar dentro de `update_pdf`. La regla está fragmentada.
3. **Capas que instancian capas concretas** (acoplamiento por construcción): `PDFRouter` crea `PDFController` (`pdf_router.py:17`), `PDFController` crea `PDFService`/`PDFRepository`/`PDFValidator` (`pdf_controller.py:15-18`), `PDFService` crea `PDFRepository` (`pdf_service.py:18`). No hay interfaces entre capas → cualquier cambio de infraestructura (p. ej. migrar a SQL) reventaría toda la cadena.
4. **Servicio anémico / técnico**: `PDFService` no contiene reglas de negocio, solo operaciones técnicas de `pypdf` (leer stream, extraer texto, sha256). El "dominio" real (qué es un PDF válido, qué no puede duplicarse) está fuera del servicio.

---

## 4. Análisis contra Hexagonal (Ports & Adapters)

### Requisitos del patrón
- El **dominio/núcleo** es agnóstico al mundo exterior.
- Los **puertos** (interfaces) definen cómo el núcleo se comunica: puertos de entrada (casos de uso) y de salida (persistencia).
- Los **adaptadores** implementan los puertos para un framework/tecnología concreta.

### Evaluación

| Requisito | Estado | Evidencia |
|---|---|---|
| Puertos (interfaces) | ❌ **No existen** | Sin `Protocol`, `ABC` ni interfaces en todo el código (verificado por grep). |
| Núcleo aislado del framework | ❌ **Acoplado** | `PDFService.process_pdf(self, file)` (`pdf_service.py:20-27`) recibe un objeto **`UploadFile` de FastAPI** y llama `await file.read()` / `file.filename`. El framework de entrada llega hasta la capa de servicio. |
| Puertos de salida (persistencia) | ❌ No | El controller y el service dependen de la clase concreta `PDFRepository`. |
| Adaptador de entrada desacoplado | ⚠️ Parcial | Los `routers/` y `controllers/` usan `UploadFile` y `HTTPException` (framework) — eso es aceptable para un adaptador —, pero el problema es que ese tipo **atraviesa hacia el núcleo**. |
| Adaptador de salida intercambiable | ❌ No | `config/settings.py:20-21` crea `MongoClient(uri)` y `db` **al importar el módulo**; el repository lo usa directo. No hay puerto que permita intercambiar Mongo por otra cosa. |

**Veredicto Hexagonal:** la separación física de carpetas es engañosa. Para ser hexagonal falta lo esencial: un puerto de entrada (`extract_pdf(source: bytes) -> PdfText`), un puerto de salida (`PdfStore` como `Protocol`) y adaptadores que los implementen. Hoy el "hexágono" está desarmado: el centro habla con el framework y con Mongo directamente.

---

## 5. Análisis contra Onion

### Requisitos del patrón
- **Núcleo de dominio** en el centro (entidades + reglas), sin dependencias.
- Anillos concéntricos: domain → application services → adapters/infrastructure.
- **La regla de dependencia**: todo apunta **hacia adentro**; las capas externas dependen de **interfaces** definidas por las internas, no de implementaciones.

### Evaluación

| Requisito | Estado | Evidencia |
|---|---|---|
| Núcleo de dominio con entidades ricas | ❌ No | `models/pdf.py:10-14` es una entidad **anémica** (DTO puro: `id`, `name`, `text`, `checksum`, sin métodos). Las reglas del dominio no viven en el núcleo. |
| Reglas de negocio en el dominio | ❌ No | La regla de duplicados vive en `repositories/pdf_repository.py` (infraestructura) y en `controllers/pdf_controller.py` (aplicación), no en el centro. |
| Dependencias hacia adentro (por interfaces) | ❌ No | Las capas externas **instancian** implementaciones concretas internas: `PDFService` crea su propio `PDFRepository` (`pdf_service.py:18`); `PDFController` crea sus dependencias (`pdf_controller.py:15-18`). Es exactamente la violación que Onion prohíbe. |
| Anillos visibles | ⚠️ Solo en carpetas | La nomenclatura `controllers/services/repositories` sugiere anillos, pero no hay interfaces que los unan. |

**Veredicto Onion:** la cebolla está "vacía por dentro". Los anillos existen como carpetas, pero el centro (dominio) no tiene contenido y los anillos externos dependen de implementaciones, no de interfaces hacia adentro. En una cebolla real, `PDFService` debería depender de un `PdfStore` (interfaz) y recibir el store por inyección.

---

## 6. Análisis contra Clean

### Requisitos del patrón
- 4 capas: **Entities → Use Cases → Interface Adapters → Frameworks & Drivers**.
- **La regla de dependencia**: siempre apuntando hacia adentro (hacia Entities/Use Cases).
- El framework es lo más externo y jamás debe filtrarse al interior.

### Evaluación

| Capa Clean | ¿Existe? | Evidencia |
|---|---|---|
| **Entities** | ⚠️ Pobre | `models/pdf.py` sería la entidad, pero es un DTO de transporte sin comportamiento de dominio. Además expone `id` (detalle de infraestructura Mongo/ObjectId) en la entidad. |
| **Use Cases** | ❌ No | No hay capa de casos de uso. `PDFController` mezcla **orquestación del caso de uso** (subir/actualizar/eliminar PDF) con **formato de respuesta HTTP** y traducción de errores a `HTTPException`. |
| **Interface Adapters** | ❌ No | No hay adaptadores que conviertan datos del framework al formato de los casos de uso (p. ej. `UploadFile → bytes`). Esa conversión se hace dentro del servicio. |
| **Frameworks & Drivers** | ⚠️ Incompleto | `main.py` y `routers/` son los "drivers", pero `MongoClient` se crea en `config/settings.py` en tiempo de import (acoplamiento al driver en el momento de cargar la app). |

**Violación crítica de la regla de dependencia:** el tipo del framework **fluye hacia adentro** hasta la capa de casos de uso/servicios: `UploadFile` (FastAPI) entra en `PDFService.process_pdf` (`pdf_service.py:20`). Y las excepciones del framework (`HTTPException`) salen del controller (adaptador), que es aceptable, pero se filtran desde la capa de aplicación.

**Veredicto Clean:** falta el andamiaje de Clean. La dirección de las dependencias es la correcta en los imports (web → servicio → persistencia) pero **sin inversión**: no hay abstracciones a las que las capas interiores apunten. Clean exige que el servicio dependa de un puerto de persistencia, no de la implementación concreta.

---

## 7. Matriz comparativa

| Criterio | Actual (N-capas) | Hexagonal | Onion | Clean |
|---|---|---|---|---|
| Separación física en capas | ✅ 4 capas | ✅ anillos | ✅ anillos | ✅ 4 capas |
| Núcleo/dominio aislado del framework | ❌ (`UploadFile` en servicio) | ❌ | ❌ | ❌ |
| Inversión de dependencias (interfaces) | ❌ | ❌ | ❌ | ❌ |
| Reglas de negocio en el lugar correcto | ❌ (en repository) | ❌ | ❌ | ❌ |
| Puertos / adaptadores | ❌ | ❌ | ❌ | ❌ |
| Casos de uso explícitos | ❌ (mezclados en controller) | ❌ | ❌ | ❌ |
| Testabilidad por sustitución (mock de Mongo) | ❌ | ❌ | ❌ | ❌ |
| **Cumplimiento del estilo** | **✅ Sí** | **❌ No** | **❌ No** | **❌ No** |

> Las tres arquitecturas "objetivo" fallan en los mismos tres puntos: **aislamiento del dominio**, **inversión de dependencias** y **ubicación de las reglas de negocio**. La buena noticia: los defectos son los mismos, así que una sola evolución arregla las tres.

---

## 8. Brechas concretas (evidencia file:line)

| # | Brecha | Evidencia | Arquitectura afectada |
|---|---|---|---|
| 1 | El servicio recibe un tipo del framework (`UploadFile`). | `services/pdf_service.py:20-27` (`await file.read()`, `file.filename`) | Hexagonal, Clean |
| 2 | Sin interfaces/puertos (ni `Protocol` ni `ABC`). | Todo el código (grep sin resultados) | Hexagonal, Onion, Clean |
| 3 | Capas externas instancian internas concretas. | `pdf_router.py:17`, `pdf_controller.py:15-18`, `pdf_service.py:18` | Onion, Clean, Hexagonal |
| 4 | Regla de negocio `is_duplicate` en infraestructura y duplicada. | `repositories/pdf_repository.py:25-26,43` y `controllers/pdf_controller.py:26` | N-capas (SRP), Onion |
| 5 | Mongo se conecta al importar el módulo (sin wiring diferido). | `config/settings.py:12-21` | Hexagonal, Clean |
| 6 | Sin casos de uso: controller = orquestación + formato HTTP. | `controllers/pdf_controller.py:20-129` | Clean |
| 7 | Entidad anémica con detalle de infraestructura (`id`). | `models/pdf.py:10-14` | Onion, Clean |
| 8 | Chequeo duplicado de 404 en update. | `pdf_controller.py:68` y `:75-76` | N-capas |

---

## 9. Recomendación de evolución

La evolución natural es **N-capas → Clean (con elementos Hexagonal/Onion)**, en pasos incrementales que no requieren reescribir nada:

1. **Desacoplar el servicio del framework** (mayor impacto). Cambiar `process_pdf(self, file: UploadFile)` a `process_pdf(self, filename: str, content: bytes)`. La conversión `UploadFile → bytes` queda en el adaptador HTTP (controller/router). Esto aísla el núcleo (brecha #1).
2. **Definir un puerto de persistencia.** Crear un `Protocol PdfStore` (o interfaz) con `create/get/update/delete/is_duplicate`; `PDFRepository` lo implementa. `PDFController` y `PDFService` dependen del `Protocol`, recibido por **inyección de constructor** (brechas #2, #3).
3. **Mover la regla de negocio al dominio.** `is_duplicate` pasa a la capa de servicios (y, a futuro, a la entidad `PDF`). El repositorio vuelve a ser solo persistencia (brecha #4).
4. **Composition root explícito.** Que `main.py` (o un `wiring.py`) construya las dependencias reales una sola vez; `config/settings.py` deja de conectar Mongo al importar (brecha #5). Esto, de paso, **arregla los tests** (hoy cuelgan esperando Mongo real).
5. **Extraer casos de uso (Clean).** Dividir `PDFController` en casos de uso (`UploadPdf`, `ListPdfs`, `UpdatePdf`, `DeletePdf`) + un *presenter* que formatee respuestas HTTP (brecha #6).
6. **Endurecer la entidad.** Hacer que `PDF` valide su propio invariante (checksum requerido para persistir) y quitar `id`/`_id` de la entidad de dominio (brecha #7).

Con los pasos 1-2, el código pasa de N-capas a algo ya cercano a **Hexagonal**; con 4-6, a **Clean**; el **Onion** se cumple de forma implícita cuando el dominio queda en el centro y todas las dependencias apuntan hacia adentro por interfaces.

---

## 10. Resumen

- **Es N-capas** (4 capas técnicas horizontales), correctamente estructurada para un sistema simple, pero con acoplamiento concreto entre capas.
- **No es Hexagonal, Onion ni Clean**: faltan puertos/interfaces, núcleo de dominio con reglas, inversión de dependencias y casos de uso.
- Las tres arquitecturas objetivo fallan por los **mismos** tres defectos, lo que hace la evolución barata: desacoplar del framework, introducir un `Protocol` de persistencia con inyección, y mover las reglas al dominio.
- **La deuda técnica que más duele hoy** es la testabilidad: los tests no pueden sustituir Mongo ni el servicio por dobles porque todo se instancia de forma concreta; resolver la inversión de dependencias (pasos 1-2) desbloquea tanto la arquitectura como los tests rotos.
