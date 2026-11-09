## Alumnos
- Bordón Lucas
- Bordón Matías
- Juan Andrés López

## proyecto pdf-extractect
Extraer texto de un PDF proporcionado por el usuario. Hacer un resumen de dicho texto utilizando modelo IA.

## Instalación y ejecución

### 1. Variables de entorno

El proyecto usa **un único archivo `.env` en la raíz del repositorio**. Crealo a partir de la plantilla y completá los valores reales:

```bash
cp .env.example .env
```

Lo consumen los tres stacks vía `env_file: ../../.env`: la app lee `MONGO_USER`/`MONGO_PASS` en runtime y mongodb lee `MONGO_INITDB_ROOT_USERNAME`/`MONGO_INITDB_ROOT_PASSWORD` (deben coincidir con las anteriores).

### 2. Red compartida (una sola vez)

Los tres servicios viven en archivos compose separados (`servicios/app/`, `servicios/mongodb/`, `servicios/traefik/`) y se comunican por una **red externa pre-existente**. Creala **una única vez** antes de levantar cualquier stack:

```bash
docker network create pdf-extractext-network
```

⚠️ **Prerrequisito estricto**: si la red no existe, ningún stack levanta (`network declared as external, but could not be found`).

### 3. Levantar los servicios (desde la raíz, con `-f`)

```bash
# Reverse proxy: publica los puertos 80, 443 y 8080 (dashboard en :8080)
docker compose -f servicios/traefik/docker-compose.yml up -d

# Base de datos MongoDB
docker compose -f servicios/mongodb/docker-compose.yml up -d

# Monolito FastAPI (la primera ejecución compila la imagen)
docker compose -f servicios/app/docker-compose.yml up -d
```

El orden no es estricto: la conexión de la app a Mongo es diferida por request, así que no se cae si Mongo todavía no está levantado. Cada stack también puede operarse de forma independiente desde su propia carpeta (`cd servicios/app && docker compose up -d`).

### 4. Verificación

```bash
docker ps
curl -k https://universidad.localhost/api/v1/health
```

### Detener los servicios

```bash
docker compose -f servicios/app/docker-compose.yml down
docker compose -f servicios/mongodb/docker-compose.yml down
docker compose -f servicios/traefik/docker-compose.yml down
```

Los datos de MongoDB persisten en el volumen `pdf-extractext_mongodb_data` entre bajadas y levantadas (`down` no borra volúmenes).

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
