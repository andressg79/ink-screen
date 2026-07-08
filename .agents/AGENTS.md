# Reglas del Espacio de Trabajo (Workspace Rules)

Este archivo define las políticas obligatorias de desarrollo y flujo de trabajo para todos los agentes de IA (incluyendo Antigravity/Gemini) que operen en este repositorio.

## Reglas de Git y Flujo de Trabajo

> [!IMPORTANT]
> **A partir de la inicialización y el primer push del repositorio, se prohíbe terminantemente realizar cambios directamente en la rama `main`.**

### 1. Desarrollo basado en ramas (Branch-based Development)
- Cualquier modificación, adición de código, pruebas o documentación debe ser realizada en una rama de desarrollo dedicada.
- Las ramas deben tener nombres descriptivos según el propósito de los cambios:
  - `feature/nombre-de-la-caracteristica` para nuevas funcionalidades.
  - `bugfix/nombre-del-error` para corrección de fallos.
  - `docs/nombre-de-la-documentacion` para cambios en documentación.
  - `refactor/nombre-de-la-refactorizacion` para mejoras de código sin cambio de comportamiento.

### 2. Ciclo de Vida de los Cambios
1. **Crear rama**: Antes de realizar cualquier cambio, crear la rama correspondiente localmente:
   ```bash
   git checkout -b <nombre-de-la-rama>
   ```
2. **Realizar y verificar cambios**: Editar archivos, correr pruebas locales y validar la calidad del código.
3. **Commit y Push**: Crear commits ordenados y subir la rama a GitHub:
   ```bash
   git push origin <nombre-de-la-rama>
   ```
4. **Abrir Pull Request (PR)**: Crear el Pull Request usando el CLI de GitHub:
   ```bash
   gh pr create --title "Título corto descriptivo" --body "Descripción detallada de los cambios y plan de verificación"
   ```

### 3. Aprobación y Merges obligatorios
- **Aprobación de Andres Sabini**: Todo PR debe ser revisado y aprobado explícitamente por el usuario (`Andres Sabini` / `andressg79`) antes de integrarse.
- **Prohibición de auto-merge**: Ningún agente de IA puede mergear un PR a la rama `main` por su cuenta.
- **Cierre de Tareas**: Una tarea no se considerará completada o finalizada hasta que el PR correspondiente haya sido aprobado y mergeado por el usuario, y la rama `main` local haya sido actualizada.
