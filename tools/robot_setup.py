#!/usr/bin/env python3
"""Set up one JetBot Mini for the bootcamp, one step at a time, following the instructor.

Run on the robot as user jetson, with HDMI, keyboard and mouse attached:

    cd ~/jetbot-mini-bootcamp-nstru && python3 tools/robot_setup.py

    --check-only   staff pre-check: system and hardware tests only, changes nothing
    --step N       run one step again (every step is safe to repeat)
    --dry-run      print the commands instead of running them (works on a laptop)

Written for the robot's Python 3.6: standard library only, no dataclasses, no capture_output.
"""
import argparse
import getpass
import os
import re
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

CONFIG_DIR = os.path.expanduser("~/.jetbot-nstru")
ROBOT_FILE = os.path.join(CONFIG_DIR, "robot.conf")  # the robot number, written by step 2
HOTSPOT_FILE = os.path.join(CONFIG_DIR, "hotspot.conf")  # password pattern; staff copy it from the flash drive
LOG_FILE = os.path.expanduser("~/robot_setup.log")

YAHBOOM_SERVICES = ("jetbotmini_start", "jetbotmini_stats")  # phone APP + IP display that crashes without wlan0
STATUS_SERVICE = "nstru_status"
TIMEZONE = "Asia/Bangkok"
HOTSPOT_IP = "10.42.0.1"  # NetworkManager's address for a shared (hotspot) connection
MIN_FREE_GB = 2.0
LOW_BATTERY_V = 11.1
KEY1_PIN = 8  # BCM numbering, Key1_pin in Yahboom's yahboom-jetbotmini.py
KEY_WAIT_S = 10
DRY_RUN_NUMBER = 7


# ---------- pure helpers (unit-tested on a laptop) ----------

def parse_robot_number(text: str) -> int:
    """Robot number from the sticker, 1-99. Raises ValueError with a message the learner can act on."""
    text = text.strip()
    if not text.isdigit() or not 1 <= int(text) <= 99:
        raise ValueError("ใส่ตัวเลข 1-99 ตามสติ๊กเกอร์บนตัวรถ")
    return int(text)


def hostname_for(number: int) -> str:
    return "jetbot-%02d" % number


def ssid_for(number: int) -> str:
    return "JETBOT-%02d" % number


def password_for(pattern: str, number: int) -> str:
    """Hotspot password from the staff's pattern: `{num}` in the pattern becomes the two-digit number."""
    password = pattern.strip().format(num="%02d" % number)
    if not 8 <= len(password) <= 63:
        raise ValueError("WPA2 password must be 8-63 characters, got %d" % len(password))
    return password


def hosts_with_hostname(hosts: str, name: str) -> str:
    """/etc/hosts with 127.0.1.1 pointing at `name`, so sudo stops warning `unable to resolve host`."""
    line = "127.0.1.1\t%s" % name
    if re.search(r"^127\.0\.1\.1\s", hosts, flags=re.M):
        return re.sub(r"^127\.0\.1\.1\s.*$", line, hosts, flags=re.M)
    return hosts.rstrip("\n") + "\n" + line + "\n"


def iw_interface_modes(iw_list: str) -> set:
    """Modes under `Supported interface modes:` in `iw list`, e.g. {'managed', 'AP', 'monitor'}."""
    block = re.search(r"Supported interface modes:\n((?:\s+\* .+\n)+)", iw_list)
    return set(re.findall(r"\* (\S+)", block.group(1))) if block else set()


AP_BLOCKING_FLAGS = ("disabled", "no IR", "radar", "passive", "no IBSS")  # old iw says "passive scanning"


def iw_ap_channels(iw_list: str) -> set:
    """Channel numbers in `iw list` where the dongle may start an AP itself (not DFS, not listen-only)."""
    return {int(m.group(1)) for m in re.finditer(r"\* \d+(?:\.\d+)? MHz \[(\d+)\](.*)", iw_list)
            if not any(flag in m.group(2) for flag in AP_BLOCKING_FLAGS)}


def iw_ssid(iw_dev_info: str) -> str:
    """SSID that wlan0 is on or broadcasting, from `iw dev wlan0 info`, or ''."""
    match = re.search(r"^\s*ssid (.+)$", iw_dev_info, flags=re.M)
    return match.group(1).strip() if match else ""


def parse_ipv4(ip_addr_output: str) -> str:
    """First IPv4 address in `ip -4 -o addr show <dev>` output, or '' when there is none."""
    match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", ip_addr_output)
    return match.group(1) if match else ""


def jupyter_dropin() -> str:
    """systemd drop-in that opens Jupyter in the repo. Delete the file to get Yahboom's folder back."""
    return "[Service]\nWorkingDirectory=%s\n" % REPO


def status_unit(user: str) -> str:
    return (
        "[Unit]\nDescription=NSTRU bootcamp boot beep and OLED status\nAfter=network.target\n\n"
        "[Service]\nType=simple\nUser={user}\nWorkingDirectory={repo}\n"
        "ExecStart=/usr/bin/python3 tools/status_display.py\nRestart=always\nRestartSec=5\n\n"
        "[Install]\nWantedBy=multi-user.target\n"
    ).format(user=user, repo=REPO)


CHANNELS_5GHZ = (36, 40, 44, 48, 149, 153, 157, 161)  # non-DFS 20 MHz channels, allowed in Thailand
CHANNELS_24GHZ = (1, 6, 11)  # the only 2.4 GHz channels that do not overlap


def pick_channel(number: int, ap_channels: set) -> int:
    """Wi-Fi channel for robot `number`: 5 GHz when the dongle allows an AP there, else 1/6/11.

    Consecutive numbers get different channels, so robots on neighbouring desks interfere least.
    """
    channels = [c for c in CHANNELS_5GHZ if c in ap_channels] or \
        [c for c in CHANNELS_24GHZ if c in ap_channels] or list(CHANNELS_24GHZ)
    return channels[(number - 1) % len(channels)]


# ---------- talking to the system ----------

def read_text(path: str) -> str:
    try:
        with open(path) as f:
            return f.read()
    except (IOError, OSError):
        return ""


def saved_robot_number() -> int:
    try:
        return parse_robot_number(read_text(ROBOT_FILE))
    except ValueError:
        return 0


class Shell(object):
    """Runs commands for the steps, or only prints the ones that change the robot with --dry-run."""

    def __init__(self, dry_run: bool):
        self.dry_run = dry_run
        self.log = open(LOG_FILE, "a")

    def say(self, text: str = "") -> None:
        print(text)
        self.log.write(text + "\n")
        self.log.flush()

    def read(self, cmd: list) -> str:
        """Output of a read-only command (also on failure); '' if it is missing. sudo reads are skipped in dry-run."""
        if self.dry_run and cmd[0] == "sudo":
            return ""
        try:
            return subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
        except subprocess.CalledProcessError as exc:
            return exc.output or ""
        except OSError:
            return ""

    def run(self, cmd: list, stdin: str = None) -> bool:
        """Run a command that changes the robot. Returns True on success."""
        self.say("  $ " + " ".join(cmd))
        if self.dry_run:
            return True
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE if stdin is not None else None,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        out, _ = proc.communicate(stdin)
        if out.strip() and cmd[:2] != ["sudo", "tee"]:  # tee echoes the whole file back
            self.say("    " + out.strip().replace("\n", "\n    "))
        if proc.returncode != 0:
            self.say("  ✗ คำสั่งนี้ไม่สำเร็จ (exit %d)" % proc.returncode)
        return proc.returncode == 0

    def write_root_file(self, path: str, text: str) -> bool:
        return self.run(["sudo", "mkdir", "-p", os.path.dirname(path)]) and \
            self.run(["sudo", "tee", path], stdin=text)

    def ask(self, question: str) -> str:
        answer = "" if self.dry_run else input(question)
        self.log.write("%s%s\n" % (question, answer))
        return answer.strip()

    def confirm(self, question: str) -> bool:
        return self.dry_run or self.ask(question + " [y/n] ").lower().startswith("y")

    def service_state(self, name: str) -> tuple:
        """(is-enabled, is-active) of a unit; is-enabled is 'not-found' when the unit does not exist."""
        enabled = self.read(["systemctl", "is-enabled", name]).strip()
        active = self.read(["systemctl", "is-active", name]).strip()
        return (enabled if re.match(r"^[a-z-]+$", enabled) else "not-found"), active

    def reload_and(self, *actions) -> bool:
        ok = self.run(["sudo", "systemctl", "daemon-reload"])
        for action in actions:
            ok = ok and self.run(["sudo", "systemctl"] + list(action))
        return ok


# ---------- steps: each returns True (pass), False (fail) or None (skipped) ----------

def step_system(sh: Shell) -> bool:
    mem = re.search(r"MemTotal:\s+(\d+)", read_text("/proc/meminfo"))
    disk = os.statvfs("/")
    free_gb = disk.f_bavail * disk.f_frsize / 1e9
    has_wlan0 = os.path.exists("/sys/class/net/wlan0")
    iw_list = sh.read(["iw", "list"])
    modes = iw_interface_modes(iw_list)
    ap_5ghz = sorted(c for c in iw_ap_channels(iw_list) if c in CHANNELS_5GHZ)
    try:
        from jetbot_nstru.hardware import read_battery_voltage
        battery = read_battery_voltage()
    except Exception as exc:  # no smbus on a laptop, or the MCU did not answer
        sh.say("  (อ่านแบตไม่ได้: %s)" % exc)
        battery = 0.0
    sh.say("  Board    : %s" % (read_text("/proc/device-tree/model").strip("\x00\n") or "?"))
    sh.say("  RAM      : %.1f GB" % (int(mem.group(1)) / 1024.0 ** 2 if mem else 0))
    sh.say("  L4T      : %s" % (read_text("/etc/nv_tegra_release").split(",")[0].strip("# \n") or "?"))
    sh.say("  Python   : %d.%d" % sys.version_info[:2])
    sh.say("  Disk free: %.1f GB" % free_gb)
    sh.say("  wlan0    : %s (AP mode: %s)" % ("yes" if has_wlan0 else "NO", "yes" if "AP" in modes else "no"))
    sh.say("  5 GHz AP : %s" % (", ".join(map(str, ap_5ghz)) or "no (2.4 GHz only)"))
    sh.say("  Thai font: %s" % ("yes" if sh.read(["fc-list", ":lang=th"]).strip() else "no"))
    sh.say("  Battery  : %.2f V" % battery)

    problems = []
    if not has_wlan0:
        problems.append("ไม่เจอ USB Wi-Fi dongle (wlan0) เสียบ dongle แล้วรันขั้นนี้ใหม่")
    elif "AP" not in modes:
        problems.append("dongle ตัวนี้เปิด hotspot (AP mode) ไม่ได้ แจ้งทีมงาน")
    if free_gb < MIN_FREE_GB:
        problems.append("พื้นที่ดิสก์เหลือน้อยกว่า %.0f GB" % MIN_FREE_GB)
    if battery and battery < LOW_BATTERY_V:
        sh.say("  ! แบตต่ำกว่า %.1f V ชาร์จก่อนทดสอบมอเตอร์" % LOW_BATTERY_V)
    for problem in problems:
        sh.say("  ✗ " + problem)
    return not problems


def step_hostname(sh: Shell) -> bool:
    number = saved_robot_number()
    if number and not sh.confirm("  หุ่นยนต์หมายเลข %02d ใช่ไหม" % number):
        number = 0
    while not number:
        if sh.dry_run:
            number = DRY_RUN_NUMBER
            break
        try:
            number = parse_robot_number(sh.ask("  หมายเลขหุ่นยนต์ (ดูสติ๊กเกอร์): "))
        except ValueError as exc:
            sh.say("  " + str(exc))
    name = hostname_for(number)
    hosts = read_text("/etc/hosts")
    if not sh.dry_run:
        if not os.path.isdir(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
        with open(ROBOT_FILE, "w") as f:
            f.write("%d\n" % number)
    if sh.read(["hostname"]).strip() == name and hosts_with_hostname(hosts, name) == hosts:
        sh.say("  ✓ ชื่อเครื่องเป็น %s อยู่แล้ว" % name)
        return True
    return sh.run(["sudo", "hostnamectl", "set-hostname", name]) and \
        sh.write_root_file("/etc/hosts", hosts_with_hostname(hosts, name))


def step_time(sh: Shell) -> bool:
    ok = True
    if os.path.realpath("/etc/localtime").endswith(TIMEZONE):
        sh.say("  ✓ เขตเวลาเป็น %s อยู่แล้ว" % TIMEZONE)
    else:
        ok = sh.run(["sudo", "timedatectl", "set-timezone", TIMEZONE])
    sh.say("  เวลาในเครื่องตอนนี้: " + sh.read(["date", "+%Y-%m-%d %H:%M"]).strip())
    if sh.confirm("  ตรงกับเวลาที่ผู้สอนบอกไหม"):
        return ok
    while True:
        text = sh.ask("  พิมพ์วันเวลาที่ถูก (YYYY-MM-DD HH:MM): ")
        try:
            time.strptime(text, "%Y-%m-%d %H:%M")
            break
        except ValueError:
            sh.say("  รูปแบบไม่ถูก ตัวอย่าง 2026-11-23 09:05")
    return sh.run(["sudo", "date", "-s", text]) and ok


def step_yahboom_services(sh: Shell) -> bool:
    ok = True
    for name in YAHBOOM_SERVICES:
        enabled, active = sh.service_state(name)
        if enabled in ("disabled", "not-found") and active != "active":
            sh.say("  ✓ %s ปิดอยู่แล้ว" % name)
            continue
        ok = sh.run(["sudo", "systemctl", "disable", "--now", name]) and ok
    return ok


def step_hotspot(sh: Shell) -> None:
    sh.say("  ยังไม่เปิดใช้ขั้นนี้: รอผล nmcli และ iw list จากหุ่นจริง จึงยังไม่แก้อะไร")
    return None


def step_power_mode(sh: Shell) -> bool:
    if "MAXN" in sh.read(["sudo", "nvpmodel", "-q"]):
        sh.say("  ✓ ใช้ MAXN อยู่แล้ว")
        return True
    return sh.run(["sudo", "nvpmodel", "-m0"])


def jupyter_service(sh: Shell) -> str:
    units = sh.read(["systemctl", "list-unit-files", "--type=service", "--no-legend"])
    names = re.findall(r"^(\S*jupyter\S*)\.service\s+enabled", units, flags=re.M | re.I)
    return names[0] if names else ""


def step_jupyter(sh: Shell) -> bool:
    name = jupyter_service(sh) or ("jetbotmini_jupyter" if sh.dry_run else "")
    if not name:
        sh.say("  ✗ ไม่พบ service ของ Jupyter ที่เปิดตอน boot แจ้งทีมงาน")
        return False
    for config in ("jupyter_notebook_config.py", "jupyter_lab_config.py"):
        text = read_text(os.path.expanduser("~/.jupyter/" + config))
        if re.search(r"^\s*c\.\w+\.(notebook_dir|root_dir)\s*=", text, flags=re.M):
            sh.say("  ✗ ~/.jupyter/%s กำหนด folder ไว้เอง ค่าของขั้นนี้จะไม่มีผล แจ้งทีมงาน" % config)
            return False
    path = "/etc/systemd/system/%s.service.d/nstru.conf" % name
    if read_text(path) == jupyter_dropin():
        sh.say("  ✓ %s เปิดที่ %s อยู่แล้ว" % (name, REPO))
        return True
    return sh.write_root_file(path, jupyter_dropin()) and sh.reload_and(("restart", name))


def step_status_service(sh: Shell) -> bool:
    path = "/etc/systemd/system/%s.service" % STATUS_SERVICE
    unit = status_unit(getpass.getuser())
    enabled, active = sh.service_state(STATUS_SERVICE)
    if read_text(path) == unit and enabled == "enabled" and active == "active":
        sh.say("  ✓ %s ทำงานอยู่แล้ว" % STATUS_SERVICE)
        return True
    return sh.write_root_file(path, unit) and \
        sh.reload_and(("enable", STATUS_SERVICE), ("restart", STATUS_SERVICE))


def check(sh: Shell, label: str, test) -> bool:
    try:
        ok = test(sh)
    except Exception as exc:  # report every hardware fault, then carry on with the next test
        sh.say("  ✗ %s: %s" % (label, exc))
        return False
    sh.say("  %s %s" % ("✓" if ok else "✗", label))
    return ok


def camera_ok(sh: Shell) -> bool:
    import cv2
    from jetbot_nstru.hardware import CsiCamera

    with CsiCamera(lock_exposure=False) as camera:
        for _ in range(10):  # let auto exposure settle
            frame = camera.read()
    path = os.path.expanduser("~/setup_camera.jpg")
    cv2.imwrite(path, frame)
    sh.say("    บันทึกภาพไว้ที่ %s เปิดดูได้" % path)
    return frame.mean() > 10  # an all-black frame means the lens cap or the ribbon cable


def buzzer_ok(sh: Shell) -> bool:
    from jetbot_nstru.hardware import set_buzzer

    set_buzzer(True)
    time.sleep(0.3)
    set_buzzer(False)
    return sh.confirm("    ได้ยินเสียง Buzzer ไหม")


def wheels_ok(sh: Shell) -> bool:
    from jetbot_nstru.hardware import open_robot

    robot = open_robot()
    ok = True
    try:
        sh.ask("    ยกล้อให้ลอยจากพื้น แล้วกด Enter")
        for side, speeds in (("ซ้าย", (0.4, 0.0)), ("ขวา", (0.0, 0.4))):
            robot.set_motors(*speeds)
            time.sleep(1.0)
            robot.stop()
            ok = sh.confirm("    ล้อ%sหมุนไปข้างหน้า และล้ออีกข้างหยุดนิ่ง ใช่ไหม" % side) and ok
    finally:
        robot.stop()
    return ok


def oled_ok(sh: Shell) -> bool:
    from jetbot_nstru.hardware import Oled

    Oled().show("TEST OK")
    return sh.confirm("    จอ OLED ขึ้นคำว่า TEST OK ไหม")


def key_ok(sh: Shell) -> bool:
    import RPi.GPIO as GPIO  # Jetson.GPIO installs under this name, as Yahboom's app uses it

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(KEY1_PIN, GPIO.IN)
    try:
        idle = GPIO.input(KEY1_PIN)
        sh.say("    กดปุ่ม KEY1 บนบอร์ดภายใน %d วินาที" % KEY_WAIT_S)
        deadline = time.monotonic() + KEY_WAIT_S
        while time.monotonic() < deadline:
            if GPIO.input(KEY1_PIN) != idle:
                return True
            time.sleep(0.02)
        return False
    finally:
        GPIO.cleanup(KEY1_PIN)


def step_hardware(sh: Shell) -> bool:
    if sh.dry_run:
        sh.say("  (ข้ามใน dry-run: ต้องใช้หุ่นจริง)")
        return None
    # Yahboom's APP holds the motors and camera, and the status services own the OLED.
    holders = [n for n in YAHBOOM_SERVICES + (STATUS_SERVICE,) if sh.service_state(n)[1] == "active"]
    for name in holders:
        sh.run(["sudo", "systemctl", "stop", name])
    try:
        results = [check(sh, "กล้อง", camera_ok), check(sh, "Buzzer", buzzer_ok),
                   check(sh, "ล้อซ้ายและขวา", wheels_ok), check(sh, "จอ OLED", oled_ok),
                   check(sh, "ปุ่ม KEY1", key_ok)]
    finally:
        for name in holders:
            sh.run(["sudo", "systemctl", "start", name])
    return all(results)


# (number, title, what the learner should know, function, read-only)
STEPS = (
    (1, "ตรวจระบบ", "ดูรุ่นบอร์ด หน่วยความจำ พื้นที่ดิสก์ แบตเตอรี่ และ Wi-Fi dongle", step_system, True),
    (2, "ตั้งชื่อหุ่นยนต์", "ชื่อเครื่องในเครือข่าย ใช้หมายเลขจากสติ๊กเกอร์ เช่น jetbot-07", step_hostname, False),
    (3, "ตั้งเวลา", "นาฬิกาของระบบใช้ตั้งชื่อไฟล์และบันทึก log", step_time, False),
    (4, "ปิดโปรแกรมของ Yahboom", "โปรแกรม APP มือถือแย่งมอเตอร์และกล้องกับโค้ดของเรา", step_yahboom_services, False),
    (5, "Hotspot ของหุ่นยนต์", "notebook จะต่อ Wi-Fi ของหุ่นยนต์ตัวเองโดยตรง", step_hotspot, False),
    (6, "Power mode", "MAXN ใช้ CPU ครบ 4 core งาน vision จึงเร็วขึ้น", step_power_mode, False),
    (7, "Jupyter Lab", "ให้ Jupyter เปิดที่ folder ของ bootcamp", step_jupyter, False),
    (8, "จอ OLED และเสียงตอน boot", "แสดงชื่อ Wi-Fi รหัส และแบต และส่งเสียง 3 ครั้งเมื่อ boot เสร็จ",
     step_status_service, False),
    (9, "ทดสอบฮาร์ดแวร์", "ตรวจของจริงทีละชิ้นก่อนเริ่มเขียนโค้ด", step_hardware, True),
)
MARK = {True: "✓ ผ่าน", False: "✗ ไม่ผ่าน", None: "- ข้าม"}


def summary(sh: Shell, results: list, offer_shutdown: bool) -> int:
    sh.say("\n=== ขั้น 10: สรุป ===")
    for number, title, ok in results:
        sh.say("  %2d  %s  %s" % (number, MARK[ok], title))
    number = saved_robot_number()
    if number:
        sh.say("\n  Wi-Fi  : %s\n  Jupyter: http://%s:8888" % (ssid_for(number), HOTSPOT_IP))
    sh.say("  log    : " + LOG_FILE)
    if any(ok is False for _, _, ok in results):
        sh.say("\n  มีขั้นที่ไม่ผ่าน แจ้งทีมงานพร้อมเปิดไฟล์ log ให้ดู")
        return 1
    if offer_shutdown and sh.confirm("\n  ปิดเครื่องเพื่อถอดจอเลยไหม"):
        sh.run(["sudo", "shutdown", "-h", "now"])
    return 0


def main(argv: list = None) -> int:
    parser = argparse.ArgumentParser(description="Set up a JetBot Mini for the NSTRU bootcamp.")
    parser.add_argument("--check-only", action="store_true", help="run only the read-only checks")
    parser.add_argument("--step", type=int, choices=[s[0] for s in STEPS], help="run one step")
    parser.add_argument("--dry-run", action="store_true", help="print changes instead of making them")
    args = parser.parse_args(argv)
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        print("รันเป็น user jetson ไม่ต้องใส่ sudo โปรแกรมจะขอรหัสผ่านเอง")
        return 2

    sh = Shell(args.dry_run)
    if not args.dry_run and not sh.run(["sudo", "-v"]):
        return 2
    chosen = [s for s in STEPS if (args.step in (None, s[0])) and (s[4] or not args.check_only)]
    results = []
    for number, title, why, step, _ in chosen:
        sh.say("\n=== ขั้น %d: %s ===\n  %s" % (number, title, why))
        if sh.ask("  กด Enter เพื่อเริ่ม (พิมพ์ s เพื่อข้าม) ").lower() == "s":
            results.append((number, title, None))
            continue
        try:
            ok = step(sh)
        except Exception as exc:  # one broken step must not hide the rest of the summary
            sh.say("  ✗ error: %s" % exc)
            ok = False
        results.append((number, title, ok))
    return summary(sh, results, offer_shutdown=not (args.step or args.check_only))


if __name__ == "__main__":
    sys.exit(main())
