import os
import sys
import time
import logging

logger = logging.getLogger(__name__)

# Check if we should run in MOCK mode
MOCK_MODE = os.environ.get("INK_SCREEN_MOCK", "0") == "1"

# Pins mapping for Orange Pi RV2 (Physical -> GPIO)
# DC (Pin 22) -> GPIO 49
# RST (Pin 11) -> GPIO 71
# BUSY (Pin 13) -> GPIO 72
# CS (Pin 24) -> handled automatically by SPI (/dev/spidev3.0)
RST_PIN = 71
DC_PIN = 49
BUSY_PIN = 72
CS_PIN = 76  # Dummy, CS is managed by spidev driver hardware

class OrangePiRV2:
    def __init__(self):
        self.mock_mode = False
        try:
            import spidev
            self.SPI = spidev.SpiDev()
        except ImportError:
            logger.warning("spidev not found. Running in MOCK mode.")
            self.mock_mode = True
            self.SPI = None

        if not self.mock_mode:
            logger.info("Initializing hardware interfaces for Orange Pi RV2...")
            self._gpio_export(RST_PIN)
            self._gpio_export(DC_PIN)
            self._gpio_export(BUSY_PIN)

            self._gpio_set_direction(RST_PIN, "out")
            self._gpio_set_direction(DC_PIN, "out")
            self._gpio_set_direction(BUSY_PIN, "in")

    def _gpio_export(self, pin):
        if os.path.exists(f"/sys/class/gpio/gpio{pin}"):
            return  # Already exported
        try:
            with open("/sys/class/gpio/export", "w") as f:
                f.write(str(pin))
            # Give udev rules a moment to update permissions
            time.sleep(0.1)
        except OSError as e:
            logger.error(f"Error exporting GPIO {pin}: {e}")

    def _gpio_unexport(self, pin):
        if not os.path.exists(f"/sys/class/gpio/gpio{pin}"):
            return
        try:
            with open("/sys/class/gpio/unexport", "w") as f:
                f.write(str(pin))
        except OSError as e:
            logger.error(f"Error unexporting GPIO {pin}: {e}")

    def _gpio_set_direction(self, pin, direction):
        try:
            with open(f"/sys/class/gpio/gpio{pin}/direction", "w") as f:
                f.write(direction)
        except OSError as e:
            logger.error(f"Error setting direction for GPIO {pin}: {e}")

    def digital_write(self, pin, value):
        if self.mock_mode:
            return
        try:
            with open(f"/sys/class/gpio/gpio{pin}/value", "w") as f:
                f.write("1" if value else "0")
        except OSError as e:
            logger.error(f"Error writing to GPIO {pin}: {e}")

    def digital_read(self, pin):
        if self.mock_mode:
            return 0
        try:
            with open(f"/sys/class/gpio/gpio{pin}/value", "r") as f:
                return int(f.read().strip())
        except OSError as e:
            logger.error(f"Error reading from GPIO {pin}: {e}")
            return 0

    def delay_ms(self, delaytime):
        time.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        if self.mock_mode:
            return
        self.SPI.writebytes(data)

    def spi_writebyte2(self, data):
        if self.mock_mode:
            return
        # spidev writebytes2 is faster for large buffers
        self.SPI.writebytes2(data)

    def module_init(self):
        if self.mock_mode:
            logger.info("EPD Mock Module Init")
            return 0

        # Open SPI bus 3, device 0 (/dev/spidev3.0)
        try:
            self.SPI.open(3, 0)
            self.SPI.max_speed_hz = 4000000
            self.SPI.mode = 0b00
            logger.info("SPI3.0 interface opened successfully.")
            return 0
        except Exception as e:
            logger.error(f"Failed to open SPI device: {e}")
            return -1

    def module_exit(self):
        if self.mock_mode:
            logger.info("EPD Mock Module Exit")
            return

        logger.info("Closing SPI and clean GPIO...")
        if self.SPI:
            self.SPI.close()

        self.digital_write(RST_PIN, 0)
        self.digital_write(DC_PIN, 0)
        
        # We don't unexport to avoid permission errors on successive runs,
        # but the pins are set to safe low states.

class MockEPDConfig:
    def __init__(self):
        self.mock_mode = True
        logger.info("Initializing Mock EPD Config...")

    def digital_write(self, pin, value):
        pass

    def digital_read(self, pin):
        return 0

    def delay_ms(self, delaytime):
        time.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        pass

    def spi_writebyte2(self, data):
        pass

    def module_init(self):
        logger.info("Mock EPD Module Init")
        return 0

    def module_exit(self):
        logger.info("Mock EPD Module Exit")

# Select implementation based on environment
if MOCK_MODE:
    implementation = MockEPDConfig()
else:
    implementation = OrangePiRV2()

# Map all public methods to the module namespace to maintain Waveshare compatibility
for func in [x for x in dir(implementation) if not x.startswith('_')]:
    setattr(sys.modules[__name__], func, getattr(implementation, func))

# Expose pin definitions at module level
RST_PIN = RST_PIN
DC_PIN = DC_PIN
BUSY_PIN = BUSY_PIN
CS_PIN = CS_PIN
