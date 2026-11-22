#!/usr/bin/env python3
"""Boot beep and OLED status for the bootcamp, run by the nstru_status service (robot_setup.py step 8).

Replaces Yahboom's jetbotmini_stats, which crash-loops when the Wi-Fi dongle is unplugged, and
jetbotmini_start, whose three beeps told the learner the robot had finished booting.
"""
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import robot_setup as setup  # noqa: E402  (also puts the repo on sys.path)

REFRESH_S = 2
BOOT_MARKER = "/dev/shm/nstru_booted"  # tmpfs: gone after a reboot, so a service restart stays quiet


def status_lines(ssid: str, password: str, ip: str, has_dongle: bool, battery: float) -> list:
    """The four 8-pixel rows of the 128x32 OLED."""
    battery_line = "BAT %.1fV" % battery if battery else "BAT ?"
    if not has_dongle:
        return ["NO WIFI DONGLE", "plug it in and", "reboot", battery_line]
    return [
        ssid or "NO HOTSPOT",
        "PW " + password if password else "PW -",
        ("%s:8888" % ip) if ip else "NO IP",
        battery_line,
    ]


def command_output(cmd: list) -> str:
    try:
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL, universal_newlines=True)
    except (OSError, subprocess.CalledProcessError):
        return ""


def current_password(ssid: str) -> str:
    """Show the password only for our own hotspot, worked out from the staff's pattern file."""
    number = setup.saved_robot_number()
    pattern = setup.read_text(setup.HOTSPOT_FILE)
    if not (number and pattern and ssid == setup.ssid_for(number)):
        return ""
    try:
        return setup.password_for(pattern, number)
    except ValueError:
        return ""


def boot_beeps() -> None:
    from jetbot_nstru.hardware import set_buzzer

    if os.path.exists(BOOT_MARKER):
        return
    for _ in range(3):
        set_buzzer(True)
        time.sleep(0.1)
        set_buzzer(False)
        time.sleep(0.2)
    open(BOOT_MARKER, "w").close()


def battery_volts() -> float:
    from jetbot_nstru.hardware import read_battery_voltage

    try:
        return read_battery_voltage()
    except (ImportError, OSError):
        return 0.0


def main() -> None:
    from jetbot_nstru.hardware import Oled

    try:
        boot_beeps()
    except (ImportError, OSError) as exc:
        print("buzzer: %s" % exc, flush=True)
    oled = Oled()
    while True:
        ssid = setup.iw_ssid(command_output(["iw", "dev", "wlan0", "info"]))
        lines = status_lines(
            ssid,
            current_password(ssid),
            setup.parse_ipv4(command_output(["ip", "-4", "-o", "addr", "show", "wlan0"])),
            os.path.exists("/sys/class/net/wlan0"),
            battery_volts(),
        )
        oled.show("\n".join(lines), big=False)
        time.sleep(REFRESH_S)


if __name__ == "__main__":
    main()
