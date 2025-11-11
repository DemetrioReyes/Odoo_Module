# Biblioteca - Catálogo

## ¿Qué hace este módulo?
- Permite registrar autores con nombre, nacionalidad y biografía.
- Permite crear libros con ISBN y autor.
- Tiene un botón **Completar desde proxy** que trae datos del servicio interno (editorial, páginas, portada, fecha).
- Los datos del proxy quedan en modo solo lectura para que nadie los cambie a mano.

## Requisitos
- Odoo 16.0.
- Módulo `base` (ya viene en Odoo).
- Librería `requests` (incluida en Odoo oficial).
- Acceso al proxy interno: `http://15.204.220.159/api/book`.

## Instalación local (ejemplo rápido con Docker)
1. Instalar Docker Desktop.
2. Crear carpeta `~/odoo_dev` con este `docker-compose.yml`:
   ```yaml
   version: "3.9"
   services:
     web:
       image: odoo:16.0
       depends_on:
         - db
       ports:
         - "8069:8069"
       environment:
         - HOST=db
         - USER=odoo
         - PASSWORD=odoo
       volumes:
         - ./addons:/mnt/extra-addons
     db:
       image: postgres:14
       environment:
         - POSTGRES_DB=postgres
         - POSTGRES_USER=odoo
         - POSTGRES_PASSWORD=odoo
   ```
3. Copiar este módulo dentro de `~/odoo_dev/addons/library_catalog`.
4. Iniciar servicios: `cd ~/odoo_dev && docker compose up`.
5. Entrar a `http://localhost:8069`, crear una base nueva.
6. Activar modo desarrollador (`Ctrl+K` → "debug").
7. Apps → actualizar lista → instalar **Biblioteca - Catálogo**.

## Configuración del proxy
1. Ir a `Ajustes → Catálogo de libros`.
2. Poner la URL base `http://15.204.220.159/api/book`.
3. Si hay token, escribirlo (queda cifrado).
4. Guardar.

## Cómo usarlo
1. Menú `Biblioteca → Libros`.
2. Crear un libro, escribir el ISBN y guardar.
3. Pulsar el botón **Completar desde proxy**.
4. Revisar que editorial, páginas, portada y fecha se llenaron solos.
5. Menú `Biblioteca → Autores` para ver o editar autores.

## Errores comunes
- **Sin ISBN**: el botón está oculto hasta que se guarde un ISBN.
- **Proxy caído**: muestra mensaje "No se pudo conectar". Revisar URL/token.
- **Datos incompletos**: si el proxy no envía título o autor, el módulo los deja en blanco para que los completes manualmente.

