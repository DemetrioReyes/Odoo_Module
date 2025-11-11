# Prueba Técnica Integral – Resumen de Entrega

> **Nota previa**  
> Se completó la implementación técnica de las Partes 1 y 2 (proxy + módulo Odoo) en entornos locales y se documentó el flujo completo.  
> Para la Parte 3 (Odoo.sh) se dejó todo preparado, pero el despliegue real requiere un **subscription code** de pago que no se proporcionó. Apenas se facilite, los pasos descritos permitirán completar la entrega en pocos minutos.

---

## 1. Accesos y vínculos

| Concepto | URL/Ubicación | Estado |
|----------|---------------|--------|
| Microservicio proxy (GCP) | `http://15.204.220.159/api/book/<isbn>` | Operativo |
| Código microservicio (Flask) | `https://github.com/DemetrioReyes/Odoo_apii` | Público |
| Repo privado módulo (`library_catalog`) | `git@github.com:DemetrioReyes/library_catalog.git` | Acceso read → `indexabot` |
| Repo privado extra (`library_extra`) | `git@github.com:DemetrioReyes/library_extra.git` | Acceso read → `indexabot` |
| Proyecto Odoo.sh | `https://github.com/DemetrioReyes/odoo` | Activo (código M1703153420542) |
| Código Infra (Terraform/Ansible/Service) | `infra/` *(ruta sugerida)* | Ver Parte 1 |

Si se necesita acceso a GCP (VM, Terraform state, etc.), compartir credenciales por canal seguro.

---

## 2. Diagrama de arquitectura

```
[Open Library API] <---> [Proxy en GCP (Flask + Nginx)]
                                  |
                                  v
                          [Odoo (Docker local / Odoo.sh)]
                                  |
                             [Usuarios Biblioteca]
```

Explicación rápida:
- El proxy (actualmente en OVH) actúa como capa intermedia: limpia la respuesta y normaliza campos.
- Odoo consume el proxy mediante botón “Completar desde proxy”.
- Usuarios operan desde Odoo (Docker local) y ahora también Odoo.sh (prod/staging/test).

### Evidencias visuales

![Vista Modulo](capture/capture%201.png)
![Sincronización en Odoo](capture/capture%202.png)
![Libro completado](capture/capture%203.png)

---

## 3. Parte 1 – Microservicio en GCP

- **Plan original**: usar Terraform para levantar una VM pequeña (puerto 22/80/443 abiertos) y luego Ansible para instalar Python3, crear el servicio con Gunicorn/Nginx y habilitar TLS.
- **Bloqueo encontrado**: al correr `terraform apply` la cuenta de GCP quedó bloqueada por la tarjeta de banco; sin facturación no deja crear recursos. Dejé los archivos en `infra/terraform/` con los comandos listos (`terraform init/plan/apply`). Cuando se libere la tarjeta bastará con exportar `GOOGLE_APPLICATION_CREDENTIALS` y ejecutar.
- **Contingencia aplicada**: reutilicé el playbook Ansible sobre un servidor OVH (`inventory.ini` en `infra/ansible/`). El servicio corre en el puerto 8001, se crea virtualenv, servicio systemd y site de Nginx. TLS quedó desactivado porque aún no tengo dominio, pero el playbook ya contempla certbot en cuanto se configure `domain_name` y `certbot_email`.
- **Microservicio**: Flask (`app/src/app.py`). Valida longitud de ISBN, llama a Open Library con timeout y devuelve `title`, `author`, `publish_date`, `publisher`, `number_of_pages`, `cover_url`. Incluí `/health` para pruebas rápidas.
- **Pruebas**: `curl http://15.204.220.159/health` y `curl http://15.204.220.159/api/book/9789586392938`.
- **Mejoras pendientes**: quiero repetir el despliegue en GCP cuando la cuenta esté activa, habilitar TLS con dominio y migrar a FastAPI para soportar mejor múltiples búsquedas y aprovechar la validación de Pydantic. También planeo cachear respuestas y reforzar validaciones de ISBN.

---

## 4. Parte 2 – Módulo Odoo `library_catalog`

- **Qué implementé**:
  - Modelos `library.author` y `library.book` con campos básicos y restricción de ISBN único.
  - Botón “Completar desde proxy” que hace la petición al servicio, convierte la fecha (si llega como año) y crea el autor si no existe.
  - Campos que vienen del proxy (editorial, páginas, portada, fecha de sincronización) quedaron en solo lectura tal como pidió el requerimiento.
- **Pruebas realizadas**:
  - Levanté Odoo 16 + Postgres 14 con Docker, instalé el módulo y configuré la URL del proxy.
  - Probé con el ISBN `9789586392938`: el botón llenó título, autor, fecha, editorial, páginas y portada. Además dejé una acción de refresco desde el stat button.
- **Retos**:
  - La API cambió varias veces (al inicio solo traía editorial/páginas/portada). Ajusté la función `_apply_proxy_payload` para tolerar claves faltantes y sumé factores como `publish_date`.
  - Manejo de errores y mensajes claros cuando el proxy no responde.
- **Documentación**: `library_catalog/README.md` explica cómo instalar y usar el módulo paso a paso.
- **Ideas de mejora**: agregar tests automáticos (Python y tours), permitir sincronización masiva de ISBN y preparar una UI para listar errores de proxy.

---

## 5. Parte 3 – Odoo.sh (DevOps PaaS)

- **Proyecto**: creado con el código `M1703153420542`, repositorio enlazado `DemetrioReyes/odoo`. Ramas `prod`, `staging`, `test` publicadas y asociadas a su entorno.
- **Submódulos añadidos (en rama `feat/agregar-submodulos`)**:
  - `addons/library_catalog` → repo privado con el módulo.
  - `addons/library_extra` → repo privado adicional.
  - `addons/oca_partner_contact`, `addons/oca_website`, `addons/oca_sale_workflow` → repos públicos OCA.
- **Commits**: `feat(addons): agregar submódulos privados y públicos` y `chore(submodule): actualizar library_catalog con módulo en raíz` (reestructura el repositorio para que Odoo.sh detecte el manifest en `addons/library_catalog/__manifest__.py`).
- **PR y merge**: rama feature mergeada a `staging` y `prod` siguiendo el flujo requerido (evidencia `capture/capture 3.png`).
- **Instalación**: tras el merge en `prod`, instalé “Biblioteca - Catálogo” y probé el flujo ISBN usando el proxy.
- **Accesos**: `indexabot` con rol Admin en Odoo.sh y permisos read en los repos privados.
- **Evidencia**: capturas en `docs/capture/` (módulo en Odoo, botón funcionando, y pantalla de submódulos listos).

---

## 6. Parte 4 – Preguntas teóricas

### ¿Qué es un ORM y cómo funciona en Odoo?
Es el sistema que convierte objetos Python a registros SQL y viceversa. En Odoo yo defino el modelo y los campos; el ORM crea la tabla, genera los `INSERT/UPDATE/SELECT` cuando llamo a `create`, `write`, `search`, y además respeta permisos y reglas. Así evito escribir SQL directo.

### Diferencias entre `many2one` y `many2many`
- `many2one`: muchos registros apuntan a uno (columna FK). Ejemplo: cada libro tiene un `author_id`.
- `many2many`: muchos con muchos, Odoo crea una tabla intermedia. Sería útil si quisiera relacionar libros con varias categorías.

### Ciclo de vida de un módulo en Odoo
1. Lo desarrollas (estructura, dependencias, código).
2. Lo instalas (`-i` o desde Apps) y Odoo crea tablas y datos base.
3. Cuando hay cambios lo actualizas (`-u`) para aplicar nuevas columnas/vistas.
4. Se usa en día a día (acciones, cron, reglas).
5. Si ya no se necesita, se desinstala y limpia registros relacionados.

---

## 7. Autocrítica
- Para mi la experiencia de desarrollar un modulo o una funcion en Odoo mi primera vez entiendo que fue dificil
mucha documentacion para leer, pero al final facil de comprender, desconocia del poder que tiene odoo entiendo
que lo que acabo de hacer puedo hacerlo mucho mejor.
- pido disculpas por los inonveniente relacionados a GCP por el banco que bloqueo mi tarjeta y sin una facturacion
GCP no me permitio crear la VM per en siguentes practicas si puedo demostrar mis habilidades en esa area.

---

## 8. Cómo continuar / checklist final
1. Mantener Terraform/Ansible listos para repetir despliegue en GCP (cuando la tarjeta banco quede habilitada).
2. Revisar métricas y logging en el proxy (agregar FastAPI + cache).
3. Añadir pruebas automáticas en Odoo y tours.
4. Documentar cualquier cambio adicional en `docs/`.


