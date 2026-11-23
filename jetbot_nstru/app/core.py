"""Browser app for the JetBot: one camera loop, one web page, one panel (tab) per bootcamp module.

The loop reads a frame, hands it to the panel on screen, sends the panel's picture to the page and its
(left, right) motor command to the robot. Only that loop touches the motors, and it stops them when the page
stops pinging, when another tab is chosen, when Space is pressed and when the program ends.

Add your own panel: subclass Panel, give it a name, title, controls (HTML) and script (JS that sets
panels.<name>), then add it to PANEL_TYPES in jetbot_nstru/app/__init__.py.

Python 3.6 compatible (JetPack 4 on Jetson Nano).
"""
import argparse
import signal
import sys
import threading
import time
from collections import OrderedDict

from ..line import LineConfig
from ..params import PARAMS_PATH, load_params, save_params
from ..pid import MotorTrim
from ..viz import MjpegServer
from .live import live_routes

HEARTBEAT_TIMEOUT = 1.5  # s without a request from the page before the motors stop
BATTERY_EVERY = 2.0  # s between battery reads; I2C is slow and the value changes slowly
PID_DEFAULTS = {"kp": 0.6, "kd": 0.05, "max_speed": 0.45, "min_speed": 0.25}  # same as the Module 4 notebook
CAMERA_HINT = ("กล้องอาจถูก notebook อื่นใช้อยู่: ใน Jupyter Lab เลือก Kernel > Shut Down All Kernels "
               "แล้วสั่ง sudo systemctl restart nvargus-daemon ก่อนรันใหม่")


class Context:
    """Hardware and the settings panels share, so a value tuned on one tab is used by the next without saving."""

    def __init__(self, params, robot=None, oled=None, save=save_params, battery=None, beep=None,
                 clock=time.monotonic):
        self.params = dict(params)
        self.robot = robot
        self.oled = oled
        self.save = save
        self.clock = clock
        self.trim = MotorTrim(params.get("left_gain", 1.0), params.get("right_gain", 1.0))
        self.line = LineConfig()._replace(**{k: params[k] for k in ("roi_top", "black_v_max") if k in params})
        self.pid = dict(PID_DEFAULTS, **{k: params[k] for k in PID_DEFAULTS if k in params})
        self.battery_error = ""
        self.oled_text = ""  # last text sent to the OLED, shown on the /live page even without a screen
        self._read_battery = battery
        self._beep = beep
        self._battery = (None, float("-inf"))
        self._lock = threading.Lock()

    def battery(self, now=None):
        """Battery volts, read at most every BATTERY_EVERY s. None when it can't be read."""
        now = self.clock() if now is None else now
        with self._lock:
            volts, read_at = self._battery
            if self._read_battery is None or now - read_at < BATTERY_EVERY:
                return volts
            try:
                volts, self.battery_error = round(self._read_battery(), 2), ""
            except Exception as exc:  # a missing battery reading must never stop the robot app
                volts, self.battery_error = None, str(exc)
            self._battery = (volts, now)
            return volts

    def show(self, text, big=True):
        """Write to the OLED if there is one. The status service may overwrite it, see run()'s hint."""
        self.oled_text = text
        if self.oled is None:
            return
        try:
            self.oled.show(text, big=big)
        except (OSError, IOError) as exc:
            print("เขียนจอ OLED ไม่ได้: {}".format(exc))

    def beep(self):
        return bool(self._beep and self._beep())


class TimedDrive:
    """Fixed wheel speeds until a deadline. The camera loop asks for the motors every frame."""

    def __init__(self):
        self.motors = None
        self.until = float("-inf")

    def start(self, motors, seconds, now):
        self.motors, self.until = motors, now + seconds

    def stop(self):
        self.until = float("-inf")

    def running(self, now):
        return now < self.until

    def command(self, now):
        return self.motors if now < self.until else None


class Panel:
    """One tab of the app. The server thread calls handle() and state(); the camera loop calls step()."""

    name = ""
    title = ""
    controls = ""  # HTML inside the panel's <section>; prefix ids with the panel name
    script = ""  # JS run once on load: set panels.<name> = {show(state) {...}}; act("start") posts to this panel

    def __init__(self, ctx):
        self.ctx = ctx
        self._lock = threading.Lock()

    def state(self):
        """What the page shows. Polled about 3 times a second."""
        return {}

    def handle(self, action, data):
        """A button or slider on the page, e.g. action "/set". Return the new state, None for unknown (404),
        or raise ValueError/TypeError for bad input (400)."""
        return None

    def step(self, frame, now, fps):
        """One camera frame: return (picture for the page, (left, right) motors or None to stop)."""
        return frame, None

    def halt(self, message):
        """Stop whatever drives the motors and say why. Called from either thread; must be cheap."""

    def page_optional(self):
        """True while the panel may drive with no control page open (only a run started from a button on the
        robot, which the same button stops). Everything else stops when the page goes quiet."""
        return False


class App:
    """Routes the page's requests to panels and runs the active panel each frame, with the safety stops."""

    def __init__(self, panels, ctx=None, clock=time.monotonic):
        if not panels:
            raise ValueError("need at least one panel")
        self.panels = OrderedDict((panel.name, panel) for panel in panels)
        self.active = panels[0].name
        self.ctx = ctx
        self._clock = clock
        self._last_seen = clock()
        self._lock = threading.Lock()

    def handle(self, path, data):
        """on_post hook for MjpegServer: /ping, /select, /halt, or /<panel>/<action>."""
        with self._lock:
            self._last_seen = self._clock()
            active = self.active
        if path == "/ping":
            return self._reply(active)
        if path == "/select":
            name = data.get("panel")
            if name not in self.panels:
                raise ValueError("panel must be one of {}".format(list(self.panels)))
            with self._lock:
                if name != self.active:
                    self.panels[self.active].halt("หยุดเพราะเปลี่ยนหน้า")
                self.active = name
            return self._reply(name)
        if path == "/halt":
            for panel in self.panels.values():
                panel.halt("หยุดแล้ว")
            return self._reply(active)
        parts = path.split("/")
        if len(parts) != 3 or parts[1] not in self.panels:
            return None
        if parts[1] != active:  # a panel off screen must never start driving
            raise ValueError("เลือกหน้า {} ก่อน".format(parts[1]))
        return self.panels[parts[1]].handle("/" + parts[2], data)

    def step(self, frame, now, fps):
        """One loop turn: (picture, motors). Motors are None once the page has gone quiet."""
        with self._lock:
            panel = self.panels[self.active]
            quiet = now - self._last_seen > HEARTBEAT_TIMEOUT
        quiet = quiet and not panel.page_optional()
        if quiet:
            panel.halt("หยุดเพราะหน้าเว็บขาดการเชื่อมต่อ")
        picture, motors = panel.step(frame, now, fps)
        return picture, None if quiet else motors

    def live(self):
        """Read-only snapshot for the /live page. Never counts as the control page's heartbeat, so a projector
        left open cannot keep the robot driving after the control page is gone."""
        with self._lock:
            active = self.active
            connected = self._clock() - self._last_seen <= HEARTBEAT_TIMEOUT
        mission = self.panels.get("mission")
        ctx = self.ctx
        return {"active": self.panels[active].title, "connected": connected,
                "battery": ctx.battery() if ctx is not None else None, "oled": ctx.oled_text if ctx is not None else "",
                "mission": mission.state() if mission is not None else None}

    def _reply(self, name):
        battery = self.ctx.battery() if self.ctx is not None else None
        return {"active": name, "state": self.panels[name].state(), "battery": battery}


def drive(robot, motors, moving):
    """Send this frame's motor command. Returns whether the robot is now moving."""
    if motors is not None:
        robot.set_motors(*motors)
        return True
    if moving:
        robot.stop()
    return False


PAGE_HEAD = """<!doctype html><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TITLE</title>
<style>
  :root { --bg:#111; --panel:#1c1d1f; --line:#2c2e31; --text:#e8eff1; --muted:#9aa4a8; --accent:#ef9f27;
          --ok:#97c459; --bad:#e24b4a; --blue:#378add; }
  body { margin:0; background:var(--bg); color:var(--text); font:15px/1.4 system-ui, sans-serif; }
  header { max-width:960px; margin:0 auto; padding:12px 16px 0; display:flex; flex-wrap:wrap; gap:8px 16px; align-items:center; }
  header h1 { font-size:17px; margin:0; flex:1 1 auto; }
  #batt { color:var(--muted); font-variant-numeric:tabular-nums; }
  a.live { color:var(--muted); font-size:13px; } a.live:hover, a.live:focus-visible { color:var(--text); }
  nav { width:100%; display:flex; gap:4px; overflow-x:auto; border-bottom:1px solid var(--line); }
  nav button { background:none; color:var(--muted); border-radius:6px 6px 0 0; padding:8px 12px; white-space:nowrap; }
  nav button[aria-selected=true] { color:var(--text); background:var(--panel); box-shadow:inset 0 -2px var(--accent); }
  main { max-width:960px; margin:0 auto; padding:16px; display:grid; gap:16px; grid-template-columns:minmax(0,3fr) minmax(240px,2fr); }
  @media (max-width:700px) { main { grid-template-columns:1fr; } }
  img { width:100%; height:auto; image-rendering:pixelated; border-radius:6px; background:#000; }
  .side { display:grid; gap:12px; align-content:start; }
  section { background:var(--panel); border-radius:6px; padding:16px; display:grid; gap:14px; align-content:start; }
  section[hidden] { display:none; }
  h2 { font-size:15px; margin:0; } h3 { font-size:14px; margin:0; color:var(--muted); font-weight:600; }
  label { display:grid; gap:4px; color:var(--muted); }
  label b { color:var(--text); font-variant-numeric:tabular-nums; }
  label.row { display:flex; gap:8px; align-items:center; }
  input[type=range] { width:100%; accent-color:var(--accent); }
  input[type=number], input[type=text] { font:inherit; padding:8px; border-radius:6px; border:1px solid var(--line);
                                         background:var(--bg); color:var(--text); min-width:0; }
  .row2 { display:grid; grid-template-columns:1fr 1fr; gap:8px; }
  button { font:inherit; padding:10px; border:0; border-radius:6px; font-weight:600; cursor:pointer; color:#111; background:var(--muted); }
  button:focus-visible, input:focus-visible { outline:2px solid var(--text); outline-offset:2px; }
  button:active { transform:translateY(1px); } button:disabled { opacity:.4; cursor:default; }
  .go { background:var(--ok); } .halt { background:var(--bad); color:#fff; } .save { background:var(--accent); }
  .blue { background:var(--blue); color:#fff; }
  .big { font-size:28px; font-weight:700; font-variant-numeric:tabular-nums; margin:0; }
  .hint { margin:0; color:var(--muted); font-size:13px; } .hint b { color:var(--text); }
  table { border-collapse:collapse; font-variant-numeric:tabular-nums; font-size:13px; }
  td { padding:2px 8px 2px 0; color:var(--muted); } td b { color:var(--text); }
  #msg { min-height:2.8em; margin:0; color:var(--muted); }
  #msg.ok { color:var(--ok); } #msg.bad { color:var(--bad); }
</style>
"""

PAGE_SCRIPT = """
const panels = {};
let active = "FIRST", lastMessage = "", offline = false;
const $ = id => document.getElementById(id);
function say(text, cls) { const m = $("msg"); m.textContent = text; m.className = cls || ""; }
async function post(path, body) {
  const res = await fetch(path, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body || {})});
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || res.status);
  return data;
}
function show(s) {
  const p = panels[active];
  if (p && p.show) p.show(s);
  if (s.message === undefined) return;
  if (s.message && s.message !== lastMessage)
    say(s.message, s.level || (s.saved === true ? "ok" : s.saved === false ? "bad" : ""));
  lastMessage = s.message;
}
function act(action, body) {
  return post("/" + active + "/" + action, body).then(s => { show(s); return s; })
    .catch(e => say("ส่งไม่สำเร็จ: " + e.message, "bad"));
}
function range(name, key) {  // wire <input id="name_key"> and its value label <b id="name_key_v">
  const el = $(name + "_" + key);
  el.addEventListener("input", () => { $(name + "_" + key + "_v").textContent = el.value; act("set", {[key]: Number(el.value)}); });
}
function setRange(name, key, value) {
  const el = $(name + "_" + key);
  if (document.activeElement !== el) el.value = value;
  $(name + "_" + key + "_v").textContent = value;
}
function activate(r) {
  if (r.active !== active) { lastMessage = ""; say(""); }
  active = r.active;
  for (const s of document.querySelectorAll("section[data-panel]")) s.hidden = s.dataset.panel !== active;
  for (const t of document.querySelectorAll("nav button")) t.setAttribute("aria-selected", t.dataset.panel === active);
  $("batt").textContent = r.battery == null ? "" : "แบต " + r.battery.toFixed(2) + " V";
  show(r.state);
}
for (const t of document.querySelectorAll("nav button"))
  t.addEventListener("click", () => post("/select", {panel: t.dataset.panel}).then(activate).catch(e => say(e.message, "bad")));
document.addEventListener("keydown", e => {  // Space stops the robot from any tab
  if (e.code === "Space" && e.target.tagName !== "INPUT") { e.preventDefault(); post("/halt").then(activate); }
});
document.addEventListener("keyup", e => { if (e.code === "Space") e.preventDefault(); });  // no button click on Space
window.addEventListener("pagehide", () =>  // keepalive lets the request finish after the tab closes
  fetch("/halt", {method: "POST", keepalive: true, headers: {"Content-Type": "application/json"}, body: "{}"}));
function ping() {
  post("/ping").then(r => { if (offline) { offline = false; say(""); } activate(r); })
    .catch(() => { offline = true; say("ขาดการเชื่อมต่อกับหุ่นยนต์ รอสักครู่ หรือรันโปรแกรมใหม่", "bad"); });
}
setInterval(ping, 300);
"""


def build_page(title, panels):
    """The whole web page: tabs (only when there is more than one panel), camera picture and each panel's controls."""
    tabs = ""
    if len(panels) > 1:
        tabs = '<nav role="tablist" aria-label="หน้า">{}</nav>'.format("".join(
            '<button role="tab" data-panel="{0}" aria-selected="{1}">{2}</button>'.format(
                p.name, "true" if i == 0 else "false", p.title) for i, p in enumerate(panels)))
    sections = "".join('<section data-panel="{}"{}>{}</section>'.format(p.name, "" if i == 0 else " hidden", p.controls)
                       for i, p in enumerate(panels))
    body = ('<header><h1>{title}</h1><a class="live" href="/live" target="_blank" rel="noopener">จอแสดงผล ↗</a>'
            '<span id="batt"></span>{tabs}</header>'
            '<main><img src="/stream" alt="ภาพจากกล้องของหุ่นยนต์ พร้อมสิ่งที่โค้ดเห็น">'
            '<div class="side">{sections}<p id="msg" aria-live="polite"></p></div></main>').format(
        title=title, tabs=tabs, sections=sections)
    script = PAGE_SCRIPT.replace('"FIRST"', '"{}"'.format(panels[0].name))
    script += "".join("{{\n{}\n}}\n".format(p.script) for p in panels) + "ping();\n"
    return (PAGE_HEAD.replace("TITLE", title) + body + "<script>" + script + "</script>\n").encode("utf-8")


def _exit_on_signal(signum, frame):
    raise SystemExit(0)  # unwinds through run's finally, so robot.stop() runs


def _open_oled():
    from ..hardware import Oled
    try:
        return Oled()
    except Exception as exc:  # no OLED library or no screen: the app still runs
        print("ไม่ใช้จอ OLED ({})".format(exc))
        return None


def run(panel_types, title, argv=None, options=None):
    """Open the hardware, serve the page and run the camera loop until Ctrl+C."""
    # Closing the Jupyter Terminal tab sends SIGHUP; without this the motors keep their last command.
    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, _exit_on_signal)
    parser = argparse.ArgumentParser(description=title)
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args(argv)

    from ..hardware import CsiCamera, beep, open_robot, read_battery_voltage  # here so tests run without a robot

    try:
        robot = open_robot()
    except Exception as exc:
        sys.exit("เปิดมอเตอร์ไม่ได้: {}".format(exc))
    ctx = Context(load_params(), robot=robot, oled=_open_oled(), battery=read_battery_voltage, beep=beep)
    options = options or {}
    panels = [cls(ctx, **options.get(cls.name, {})) for cls in panel_types]
    app = App(panels, ctx)
    try:
        server = MjpegServer(port=args.port, page=build_page(title, panels), on_post=app.handle,
                             on_get=live_routes(app, title))
    except OSError as exc:
        sys.exit("เปิด port {} ไม่ได้ ({}) ปิด kernel ของ notebook ทุกตัว หรือใช้ --port 8081".format(args.port, exc))
    try:
        camera = CsiCamera(width=320, height=240, lock_exposure=True)
    except RuntimeError as exc:
        server.stop()
        sys.exit("{}\n{}".format(exc, CAMERA_HINT))

    print("เปิด http://10.42.0.1:{} ใน Chrome  (กด Ctrl+C เพื่อจบโปรแกรม)".format(server.port))
    print("จอแสดงผลสำหรับโปรเจกเตอร์ (ดูอย่างเดียว): http://10.42.0.1:{}/live".format(server.port))
    print("ค่าที่โหลดจาก {}: {}".format(PARAMS_PATH, ctx.params or "(ยังไม่มี ใช้ค่าเริ่มต้น)"))
    if ctx.oled is not None:
        print("ถ้าจอ OLED ถูกเขียนทับ สั่ง sudo systemctl stop nstru_status jetbotmini_stats ก่อน")
    moving, fps, last = False, None, time.monotonic()
    with server, camera:
        try:
            while True:
                frame = camera.read()
                now = time.monotonic()
                instant = 1.0 / max(now - last, 1e-3)
                fps = instant if fps is None else 0.9 * fps + 0.1 * instant  # smoothed so the HUD is readable
                last = now
                picture, motors = app.step(frame, now, fps)
                moving = drive(robot, motors, moving)
                server.push(picture)
        except KeyboardInterrupt:
            print("\nจบโปรแกรม ค่าที่บันทึกล่าสุดอยู่ใน {}".format(PARAMS_PATH))
        except RuntimeError as exc:  # camera gives no frame while another process holds it
            sys.exit("{}\n{}".format(exc, CAMERA_HINT))
        finally:
            robot.stop()
