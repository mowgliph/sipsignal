# ⚡ SIPSIGNAL: CICLO DE TRABAJO ESTÁNDAR

Sigue exactamente este ciclo para completar la tarea:

1. **🧠 Brainstorm**: Usa la skill `superpowers:brainstorming`. Diseña la implementación detallada, explora alternativas y obtén aprobación del usuario.
2. **📋 GitHub Issue**: Crea un issue descriptivo con `gh issue create`. Usa etiquetas (feat/bug/chore) y milestones si corresponde.
3. **🌿 Nueva Rama**: Crea una rama temporal desde `develop` (ej: `feat/XXX-nombre-corto`).
4. **⚙️ Implementación**: Realiza los cambios necesarios en la nueva rama siguiendo las guías de estilo del proyecto.
5. **✅ Verificación y Tests**: Ejecuta los tests usando el entorno virtual (`source venv/bin/activate && pytest`). Resuelve errores nuevos y preexistentes.
6. **🧹 Linting**: Ejecuta `ruff check . --fix` y `ruff format .` antes de realizar el commit.
7. **🔀 Integración (Merge)**: Cambia a `develop` y haz merge de la rama temporal (`git merge --no-ff feature/XXX-nombre`).
8. **🚀 Commit y Push**: Realiza el commit con un mensaje convencional (ej: `feat: descripción (#XXX)`) y push a `origin develop`.
9. **🗑️ Cierre**: Cierra el issue en GitHub con `gh issue close XXX` y elimina la rama temporal localmente.

**EL OBJETIVO ES IMPLEMENTAR EL SIGUIENTE PROMPT:**
[INSERTA AQUÍ LA TAREA ESPECÍFICA]
