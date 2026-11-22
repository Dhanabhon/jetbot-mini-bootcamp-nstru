"""Everything that touches the real JetBot Mini: motors, CSI camera, OLED, battery, buzzer.

Kept apart from the vision and control code so those run and test on a laptop.

VERIFY ON ROBOT marks values that come from the Yahboom / NVIDIA JetBot images but have not
been checked on a bootcamp robot yet. Module 1 has a cell that prints Yahboom's own code so the
instructor can confirm or fix them before the bootcamp.
"""
import logging
import threading

import cv2

log = logging.getLogger(__name__)

# VERIFY ON ROBOT: Yahboom's expansion board MCU, read by its battery display.
BATTERY_I2C_BUS = 1
BATTERY_I2C_ADDRESS = 0x1B
BATTERY_REGISTER = 0x00
BATTERY_SCALE = 13.3 / 1023.0  # raw 10-bit reading to volts
FULL_BATTERY_VOLTAGE = 12.6  # 3S Li-ion, from the syllabus


def open_robot():
    """Motor driver with set_motors(left, right) and stop(), values in -1..1."""
    try:
        from jetbotmini import Robot  # Yahboom JetBot Mini image (VERIFY ON ROBOT)
    except ImportError:
        from jetbot import Robot  # NVIDIA JetBot image
    return Robot()


def gstreamer_pipeline(width: int = 320, height: int = 240, fps: int = 30, flip: int = 0,
                       lock_exposure: bool = True) -> str:
    """CSI camera pipeline that always hands OpenCV the newest frame (drop=true, 1 buffer).

    Capture at the sensor's native 1280x720 and let the GPU scale down, which keeps the full 77 degree view.
    """
    lock = " aelock=true awblock=true" if lock_exposure else ""  # VERIFY ON ROBOT: needs L4T 32.4+
    return (
        "nvarguscamerasrc{lock} ! "
        "video/x-raw(memory:NVMM), width=1280, height=720, framerate={fps}/1 ! "
        "nvvidconv flip-method={flip} ! video/x-raw, width={w}, height={h}, format=BGRx ! "
        "videoconvert ! video/x-raw, format=BGR ! appsink drop=true max-buffers=1"
    ).format(lock=lock, fps=fps, flip=flip, w=width, h=height)


class CsiCamera:
    """IMX219 through GStreamer. Use as a context manager so the camera is always released."""

    def __init__(self, width: int = 320, height: int = 240, fps: int = 30, flip: int = 0,
                 lock_exposure: bool = True):
        self.width = width
        self.height = height
        self._cap = cv2.VideoCapture(gstreamer_pipeline(width, height, fps, flip, lock_exposure), cv2.CAP_GSTREAMER)
        if not self._cap.isOpened() and lock_exposure:
            log.warning("camera refused aelock/awblock, opening with auto exposure")
            self._cap = cv2.VideoCapture(gstreamer_pipeline(width, height, fps, flip, False), cv2.CAP_GSTREAMER)
        if not self._cap.isOpened():
            raise RuntimeError(
                "Cannot open the CSI camera. Another notebook may still hold it: shut down that "
                "kernel, or run `sudo systemctl restart nvargus-daemon`, then try again."
            )

    def read(self):
        ok, frame = self._cap.read()
        if not ok:
            raise RuntimeError("Camera returned no frame. Check the ribbon cable and restart the kernel.")
        return frame

    def release(self) -> None:
        self._cap.release()

    def __enter__(self) -> "CsiCamera":
        return self

    def __exit__(self, *exc) -> None:
        self.release()


class Oled:
    """128x32 SSD1306 on I2C bus 1, as used by the JetBot stats screen.

    Run `sudo systemctl stop jetbotmini_stats` first, or the stats service overwrites the screen.
    """

    def __init__(self, i2c_bus: int = 1, height: int = 32):
        import Adafruit_SSD1306
        from PIL import Image, ImageDraw, ImageFont

        model = Adafruit_SSD1306.SSD1306_128_32 if height == 32 else Adafruit_SSD1306.SSD1306_128_64
        self._display = model(rst=None, i2c_bus=i2c_bus, gpio=1)  # gpio=1 skips the reset pin
        self._display.begin()
        self._image = Image.new("1", (self._display.width, self._display.height))
        self._draw = ImageDraw.Draw(self._image)
        self._small = ImageFont.load_default()
        try:
            self._big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        except IOError:
            self._big = self._small
        self.clear()

    def clear(self) -> None:
        self._draw.rectangle((0, 0, self._display.width, self._display.height), fill=0)
        self._display.image(self._image)
        self._display.display()

    def show(self, text: str, big: bool = True) -> None:
        """Show one big word (a sign name) or up to 4 small lines separated by newlines."""
        self._draw.rectangle((0, 0, self._display.width, self._display.height), fill=0)
        if big:
            self._draw.text((0, 4), text, font=self._big, fill=255)
        else:
            for row, line in enumerate(text.split("\n")[:4]):
                self._draw.text((0, row * 8), line, font=self._small, fill=255)
        self._display.image(self._image)
        self._display.display()


def read_battery_voltage() -> float:
    """Battery voltage in volts. VERIFY ON ROBOT: register and scale come from Yahboom's battery display."""
    import smbus

    bus = smbus.SMBus(BATTERY_I2C_BUS)
    try:
        high, low = bus.read_i2c_block_data(BATTERY_I2C_ADDRESS, BATTERY_REGISTER, 2)
    finally:
        bus.close()
    return ((high << 8) + low) * BATTERY_SCALE


_buzzer_warned = []  # non-empty once the missing-buzzer warning has been logged


def beep(robot, duration: float = 0.1) -> bool:
    """Sound the buzzer without blocking the control loop. Returns False if the robot has none.

    VERIFY ON ROBOT: the Yahboom driver's buzzer attribute. Until confirmed, a missing buzzer is
    logged once instead of crashing the mission loop.
    """
    buzzer = getattr(robot, "buzzer", None)
    if buzzer is None:
        if not _buzzer_warned:
            log.warning("robot has no .buzzer; see Module 1 section 5 to find Yahboom's buzzer call")
            _buzzer_warned.append(True)
        return False
    buzzer.value = 1
    threading.Timer(duration, setattr, (buzzer, "value", 0)).start()
    return True
