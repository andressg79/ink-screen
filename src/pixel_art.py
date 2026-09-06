import os
import logging
from PIL import Image

logger = logging.getLogger(__name__)

# Base directories resolution
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# Cache to store loaded sprites
# Format: { "elfo": ["...", ...], "caballero": ["...", ...] }
SPRITES = {}

def load_sprites():
    """
    Scans the assets directory and loads all .txt sprite matrices into the memory cache.
    """
    global SPRITES
    SPRITES.clear()
    
    if not os.path.isdir(ASSETS_DIR):
        logger.warning(f"Directorio de assets no encontrado en: {ASSETS_DIR}")
        return

    for filename in os.listdir(ASSETS_DIR):
        if filename.endswith(".txt"):
            name = os.path.splitext(filename)[0].lower().strip()
            filepath = os.path.join(ASSETS_DIR, filename)
            try:
                with open(filepath, "r") as f:
                    lines = [line.rstrip("\r\n") for line in f.readlines()]
                    # Ensure sprite has exactly 32 lines and 32 characters per line
                    if len(lines) >= 32:
                        lines = [line[:32].ljust(32) for line in lines[:32]]
                        SPRITES[name] = lines
                        logger.info(f"Cargado sprite: '{name}' de {filepath}")
                    else:
                        logger.warning(f"El archivo {filepath} no tiene suficientes líneas (mínimo 32). Ignorado.")
            except Exception as e:
                logger.error(f"Error al cargar sprite '{name}' desde {filepath}: {e}")

# Initial load on import
load_sprites()

# Ordered 2x2 dithering patterns for 4 levels of grayscale:
# 0 (White): all 255
# 1 (Light Gray): 1 black pixel out of 4 (upper left)
# 2 (Dark Gray): 2 black pixels out of 4 (diagonal checkerboard)
# 3 (Black): all 0
PATTERNS = {
    '.': [
        [255, 255],
        [255, 255]
    ],
    '-': [
        [0, 255],
        [255, 255]
    ],
    '+': [
        [0, 255],
        [255, 0]
    ],
    '#': [
        [0, 0],
        [0, 0]
    ],
    ' ': [  # spaces are transparent/white
        [255, 255],
        [255, 255]
    ]
}

def get_pixel_art_image(avatar_name: str) -> Image.Image:
    """
    Generates a 64x64 monochrome PIL Image representing the character.
    Uses 2x2 ordered dithering pattern to render 4 shades of gray.
    Accepts the avatar name (str). Defaults to "paisano" if not found.
    """
    if not isinstance(avatar_name, str):
        logger.warning(f"El parámetro avatar_name debe ser str. Se recibió {type(avatar_name)}. Fallback a 'paisano'.")
        avatar_name = "paisano"

    name_clean = avatar_name.lower().strip()
    
    # Check if loaded, otherwise reload once (in case of new files added during runtime)
    if name_clean not in SPRITES:
        load_sprites()

    # Fallback to paisano
    if name_clean not in SPRITES:
        logger.warning(f"Avatar '{name_clean}' no encontrado en los assets cargados. Usando fallback 'paisano'.")
        name_clean = "paisano"

    # Secondary fallback to blank image if even paisano fails
    if name_clean not in SPRITES:
        logger.error("No se pudo cargar ni el fallback 'paisano'. Generando imagen en blanco.")
        return Image.new("1", (64, 64), 255)

    sprite_data = SPRITES[name_clean]

    # Create 64x64 image
    img = Image.new("1", (64, 64), 255)
    pixels = img.load()

    for y, line in enumerate(sprite_data):
        for x, char in enumerate(line):
            if y < 32 and x < 32:
                # Retrieve the 2x2 dither pattern
                pat = PATTERNS.get(char, PATTERNS['.'])
                # Map one 32x32 sprite pixel to a 2x2 block in the 64x64 output canvas
                pixels[2*x,     2*y]     = pat[0][0]
                pixels[2*x + 1, 2*y]     = pat[0][1]
                pixels[2*x,     2*y + 1] = pat[1][0]
                pixels[2*x + 1, 2*y + 1] = pat[1][1]

    return img
