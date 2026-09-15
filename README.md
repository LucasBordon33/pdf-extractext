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
