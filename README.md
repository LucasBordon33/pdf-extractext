## Alumnos
- Bordón Lucas
- Bordón Matías
- Juan Andrés López

## proyecto pdf-extractect
Extraer texto de un PDF proporcionado por el usuario. Hacer un resumen de dicho texto utilizando modelo IA.

## Método de uso
-Iniciar el contenedor Docker, instalando las dependencias necesarias
-Una vez inicializado, realizar peticiones al servidor levantado. Desde una terminal de Linux, se hace utilizando el comando curl.
-Las rutas aceptadas son GET, PUT, POST y DELETE. Ejemplo: curl -k -X GET "https://universidad.localhost/api/v1/pdfs" -H "accept: application/json" 

## API

Todos los endpoints viven bajo el prefijo `/api/v1` (ver `interfaces/routers/pdf_router.py`):

| Método | Ruta | Descripción | Códigos de respuesta |
|---|---|---|---|
| POST | `/upload` | Sube un PDF: valida formato, verifica duplicados por checksum, extrae el texto y lo registra. | 201, 400, 409, 500 |
| GET | `/pdfs` | Lista todos los PDFs registrados. | 200, 500 |
| GET | `/pdfs/{pdf_id}` | Obtiene un PDF por su identificador. | 200, 404, 500 |
| PUT | `/pdfs/{pdf_id}` | Reemplaza un PDF existente por uno nuevo (mismas reglas que el alta). | 200, 400, 404, 409, 500 |
| DELETE | `/pdfs/{pdf_id}` | Elimina un PDF por su identificador. | 204, 404, 500 |
| GET | `/health` | Health check del servicio. | 200 |

Ejemplo:

```bash
curl -k -X GET "https://universidad.localhost/api/v1/pdfs/{pdf_id}" -H "accept: application/json"
```

## Arquitectura

El proyecto sigue **Clean Architecture**: las dependencias apuntan siempre hacia adentro y el framework nunca atraviesa el núcleo.

| Capa | Carpeta | Responsabilidad |
|---|---|---|
| Dominio | `domain/` | Entidad `PDF` (con sus invariantes), value object `PDFFile` y excepciones de negocio. |
| Aplicación | `application/` | Puertos (interfaces `ReaderPort`, `WriterPort`, `ValidatorPort`, `TextExtractorPort`) y casos de uso con las reglas de negocio. |
| Infraestructura | `infrastructure/` | Adaptadores: repositorio Mongo, validador de formato y extractor de texto con pypdf. |
| Interfaces | `interfaces/` | Router HTTP, controller (traduce errores de dominio a HTTP) y composition root (`interfaces/dependencies.py`). |

La conexión a MongoDB es diferida (`config/settings.get_db()`): importar la app no abre conexiones. Configurá las variables de entorno copiando `.env.example` como `.env`.

## Tests

```bash
uv sync        # instala dependencias, incluidas las de desarrollo (pytest, pytest-cov, mongomock)
uv run pytest  # corre toda la suite con cobertura
```

La suite está aislada: no requiere MongoDB real ni variables de entorno (usa repositorio en memoria, mocks y `mongomock`). El CI (`.github/workflows/ci.yml`) la ejecuta en cada push a `master` y en cada pull request.

## tecnologias

* Python
* UV 
* Modelo IA
* Base de datos no relacional MongoDB

## metodologias

* TDD
* Proyecto dirigido en GitHub
* Los 6 primeros principios de los 12-factor APP 

## principios de programacion

* KISS
* DRY
* YAGNI
* SOLID
