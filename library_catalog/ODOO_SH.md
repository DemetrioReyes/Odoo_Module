# Guía simple para subir el módulo a Odoo.sh

## 1. Repositorios
- Crear un repo privado con este módulo (`library_catalog`).
- Crear otro repo privado vacío o con otro módulo (ej. `library_extra`).
- Dar acceso de lectura a `indexabot` en ambos repos (Settings → Collaborators).

## 2. Proyecto en Odoo.sh
- Crear proyecto nuevo.
- Verificar que existan las ramas `prod`, `staging`, `test`.

## 3. Preparar la rama feature
```bash
git clone git@ssh.git.odoo.sh:TU_ORG/TU_PROYECTO.git
cd TU_PROYECTO
git checkout staging
git checkout -b feat/add-submodules
```

## 4. Añadir submódulos
```bash
git submodule add git@github.com:tu_usuario/library_catalog.git addons/library_catalog
git submodule add git@github.com:tu_usuario/library_extra.git addons/library_extra
git submodule add https://github.com/OCA/partner-contact.git addons/oca_partner_contact
git submodule add https://github.com/OCA/website.git addons/oca_website
git submodule add https://github.com/OCA/sale-workflow.git addons/oca_sale_workflow
```

> Cambia los nombres por tus repos reales si eliges otros.

## 5. Commit y push (Conventional Commits)
```bash
git add .gitmodules addons/
git commit -m "feat(addons): add private and public submodules"
git push origin feat/add-submodules
```

## 6. Pull Request
- En la web de Odoo.sh, crear PR de `feat/add-submodules` hacia `staging`.
- Revisar archivos (especialmente `.gitmodules` y las carpetas).
- Aprobar y hacer merge (para la prueba lo puedes aprobar tú mismo).

## 7. Pasar a producción
- Desde Odoo.sh, promover el commit merged de `staging` a `prod`.
- Esperar a que el build termine.
- Entrar a `prod`, ir a Apps, instalar `Biblioteca - Catálogo`.

## 8. Permisos finales
- En Odoo.sh → Settings → Members → invitar `indexabot` como **Admin**.
- Confirmar que `indexabot` ya tiene acceso de lectura a los dos repos privados.

Con esto cumples la Parte 3: módulos cargados vía submódulos, ramas configuradas y despliegue activo en producción.

