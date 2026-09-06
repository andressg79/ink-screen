# 📝 Template de Prompt para Creación de Pixel Art (32x32)

Este documento contiene un template optimizado para solicitar a modelos de lenguaje locales (como DeepSeek-R1, Mistral, Llama, o tu configuración "nano banana") que generen retratos pixel art en el formato de texto plano exacto requerido por el proyecto `ink-screen`.

---

## 📋 Especificaciones Técnicas del Asset

*   **Dimensiones:** Exactamente 32 líneas por 32 caracteres de ancho.
*   **Composición:** Plano Medio Corto (cabeza y hombros), personaje centrado, simulando estar hablando (boca entreabierta).
*   **Paleta de 4 Tonos (Escala de Grises):**
    *   `.` : Blanco (Fondo, luces altas y piel iluminada).
    *   `-` : Gris Claro (Transiciones de piel, brillo en cabello o ropas).
    *   `+` : Gris Oscuro (Sombras profundas, interior de capuchas, volumen de cabello).
    *   `#` : Negro (Bordes, contorno de ojos, boca, líneas definitorias de hombros).

---

## 💬 Template de Prompt para Cargar al LLM

Copia y pega el siguiente texto en tu cliente de IA (reemplazando `[PERSONAJE]` con el personaje deseado, por ejemplo, *Mago Oscuro*, *Pícaro*, *Tabernero*):

```text
Actúa como un artista experto de pixel art retro de los años 80 y un generador de caracteres ASCII. 
Quiero que diseñes un retrato pixel art de un [PERSONAJE] en Plano Medio Corto (cabeza, cuello y hombros) y simulando estar hablando (boca ligeramente abierta) para un juego RPG de consola clásico.

Deberás generar una rejilla exacta de 32x32 caracteres utilizando estrictamente esta paleta de 4 tonos:
- '.' representa el Blanco (para el fondo e iluminación principal).
- '-' representa el Gris Claro (para tonos medios y sombreados suaves).
- '+' representa el Gris Oscuro (para sombras de volumen y profundidad).
- '#' representa el Negro (para los contornos exteriores, ojos, cejas, y líneas clave del rostro y ropas).

Instrucciones de formato críticas:
1. Tu salida debe ser únicamente la rejilla de 32x32 caracteres dentro de un bloque de código markdown simple. No agregues explicaciones, introducciones, ni comentarios adicionales.
2. Cada una de las 32 líneas debe tener exactamente 32 caracteres de longitud (ni más, ni menos). No uses espacios a menos que sean caracteres válidos de fondo, pero se prefiere usar '.' para el fondo blanco.
3. Asegúrate de centrar el retrato en la rejilla. Deja los bordes laterales y el área superior como fondo '.' para enmarcarlo correctamente.
4. El personaje debe ser fácilmente reconocible por sus características físicas (ej. orejas puntiagudas para elfo, barba tupida para enano, sombrero para mago, etc.) gracias al contraste entre los 4 tonos.
```

---

## 💡 Consejos de Uso para Modelos Locales

1.  **Validación de Longitud:** Algunos modelos de lenguaje pequeños pueden fallar ocasionalmente en contar exactamente 32 caracteres por línea. Si la imagen se ve deformada al cargarla en `assets/`, abre el archivo en VS Code y verifica que todas las líneas midan exactamente 32 caracteres.
2.  **Ajustes Manuales:** Los LLM son excelentes para dar la estructura inicial (sombras generales y contorno). Puedes usar un editor de texto plano para pulir detalles de un solo píxel (como añadir un colmillo o mover el brillo de un ojo).
3.  **Integración Directa:** Una vez generado, guarda el bloque de texto crudo en `assets/[nombre_personaje].txt`. El sistema lo cargará automáticamente en la próxima petición HTTP sin necesidad de reiniciar la API.
