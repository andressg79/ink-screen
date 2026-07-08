#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Script de validación de hardware para la pantalla E-Ink.
# Puede ejecutarse de forma independiente en la Orange Pi.

import os
import sys
import time
import logging

# Ensure project root is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("test_screen")

def main():
    logger.info("==========================================")
    logger.info(" Iniciando Diagnóstico de Pantalla E-Ink  ")
    logger.info("==========================================")

    try:
        from src.driver.epd2in9_v2 import EPD
        from PIL import Image, ImageDraw, ImageFont
        logger.info("Módulos importados correctamente.")
    except ImportError as e:
        logger.error(f"Error al importar módulos requeridos: {e}")
        logger.info("Asegúrese de activar el entorno virtual y tener Pillow instalado.")
        sys.exit(1)

    epd = EPD()
    
    # Check if mock mode is active
    from src.driver import epdconfig
    is_mock = getattr(epdconfig, "MOCK_MODE", False) or getattr(epdconfig, "mock_mode", False) or (hasattr(epdconfig, "implementation") and getattr(epdconfig.implementation, "mock_mode", False))
    if is_mock:
        logger.info("--- EJECUTANDO EN MODO MOCK (macOS / Local) ---")
    else:
        logger.info("--- EJECUTANDO EN DISPOSITIVO FÍSICO (Orange Pi) ---")

    logger.info("1. Inicializando pantalla (Full Refresh)...")
    if epd.init() != 0:
        logger.error("Error al inicializar la pantalla.")
        sys.exit(1)
    
    logger.info("2. Limpiando pantalla...")
    epd.Clear()

    # Create canvas for 296x128 landscape mode
    logger.info("3. Generando patrón de prueba (Líneas y Textos)...")
    # Width and height are defined in the driver class but horizontal canvas is 296x128
    width, height = epd.height, epd.width  # 296, 128
    
    img = Image.new("1", (width, height), 255)
    draw = ImageDraw.Draw(img)
    
    # Try to load a font, fallback to default
    font_path = None
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/Library/Fonts/Arial.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf"]:
        if os.path.exists(p):
            font_path = p
            break
            
    if font_path:
        font_title = ImageFont.truetype(font_path, 16)
        font_text = ImageFont.truetype(font_path, 12)
    else:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()

    # Draw border rectangle
    draw.rectangle([(0, 0), (width - 1, height - 1)], fill=None, outline=0, width=2)
    
    # Draw diagonals to test pixel accuracy
    draw.line([(0, 0), (width - 1, height - 1)], fill=0, width=1)
    draw.line([(0, height - 1), (width - 1, 0)], fill=0, width=1)
    
    # Draw a solid white circle in the middle to clear a text area
    circle_r = 45
    center_x, center_y = width // 2, height // 2
    draw.ellipse(
        [(center_x - circle_r, center_y - circle_r), (center_x + circle_r, center_y + circle_r)],
        fill=255, outline=0, width=2
    )

    # Draw text in the circle
    draw.text((center_x - 35, center_y - 15), "Orange Pi", font=font_title, fill=0)
    draw.text((center_x - 30, center_y + 5), "RV2 Test", font=font_text, fill=0)
    
    # Print labels near corners
    draw.text((8, 8), "Top-Left (0,0)", font=font_text, fill=0)
    draw.text((width - 95, 8), "Top-Right", font=font_text, fill=0)
    draw.text((8, height - 20), "Bottom-Left", font=font_text, fill=0)
    draw.text((width - 95, height - 20), "Bottom-Right", font=font_text, fill=0)

    logger.info("4. Enviando lienzo de calibración a la pantalla...")
    epd.display(epd.getbuffer(img))
    
    logger.info("Pantalla actualizada. Esperando 5 segundos...")
    time.sleep(5)

    # -----------------------------------------------------------------
    # Test Partial Refresh
    # -----------------------------------------------------------------
    logger.info("5. Iniciando test de actualización parcial (Conteo)...")
    # Quick reset for fast mode
    epd.init_Fast()
    
    for i in range(5, -1, -1):
        logger.info(f"  Cuenta regresiva: {i}...")
        # Create fresh canvas
        num_img = Image.new("1", (width, height), 255)
        num_draw = ImageDraw.Draw(num_img)
        
        # Border
        num_draw.rectangle([(0, 0), (width - 1, height - 1)], fill=None, outline=0, width=2)
        
        # Header info
        num_draw.text((20, 20), "PRUEBA DE REFRESCO PARCIAL", font=font_title, fill=0)
        
        # Big number in the center
        if font_path:
            font_big = ImageFont.truetype(font_path, 48)
            num_draw.text((center_x - 15, center_y - 20), str(i), font=font_big, fill=0)
        else:
            num_draw.text((center_x - 5, center_y - 10), f"[{i}]", font=font_title, fill=0)
            
        num_draw.text((20, height - 30), "Actualizando sin parpadeo completo...", font=font_text, fill=0)
        
        # Write to display in partial mode
        epd.display_Partial(epd.getbuffer(num_img))
        time.sleep(1)

    logger.info("6. Limpiando pantalla y durmiendo el módulo...")
    epd.init()
    epd.Clear()
    epd.sleep()
    
    logger.info("==========================================")
    logger.info(" Diagnóstico Finalizado Exitosamente!    ")
    logger.info("==========================================")

if __name__ == "__main__":
    main()
