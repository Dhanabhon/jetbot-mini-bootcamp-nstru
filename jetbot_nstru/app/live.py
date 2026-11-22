"""The /live page: a read-only screen for a projector, laid out like the mission demo clip.

Camera picture, a copy of what the code sent to the OLED, the Net Time estimate and what the FSM is doing,
updated four times a second. It only GETs /live/state, which never counts as the control page's heartbeat:
the robot still stops when the control page closes, however many /live screens are open.

Python 3.6 compatible.
"""
import html
import json
import socket

LIVE_PAGE = """<!doctype html><html lang="th"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TITLE · Live</title>
<style>
  :root { --bg:#ecf1ea; --card:#fbfcf9; --edge:#d9e2d6; --ink:#16261d; --muted:#5d6e63; --accent:#1f7a4d;
          --accent-soft:#dcebe0; --warn:#b54434; --oled:#0d1618; --oled-ink:#9be6f2; --oled-dim:#55787f;
          --font:"Sarabun","Noto Sans Thai","IBM Plex Sans Thai","Leelawadee UI","Thonburi",system-ui,sans-serif;
          --mono:"JetBrains Mono","SFMono-Regular",Menlo,Consolas,monospace; }
  * { box-sizing:border-box; }
  body { margin:0; min-height:100vh; background:var(--bg); color:var(--ink); font:16px/1.45 var(--font); }
  .wrap { max-width:1500px; margin:0 auto; padding:clamp(16px,2.4vw,36px); display:grid;
          gap:clamp(12px,1.5vw,22px); grid-template-columns:minmax(0,1.45fr) minmax(300px,1fr);
          grid-template-areas:"head head" "cam oled" "cam net" "bar bar"; }
  @media (min-width:901px) {  /* a projector shows everything on one screen: the camera shrinks to fit */
    .wrap { height:100vh; grid-template-rows:auto auto minmax(0,1fr) auto; }
    .cam { grid-template-rows:auto minmax(0,1fr); }
    .cam img { height:100%; aspect-ratio:auto; }
    .oled, .net { overflow:auto; } }
  @media (min-width:901px) and (max-height:959px) { ol.events { display:none; } }  /* 1080p shows them */
  @media (min-width:901px) and (max-height:780px) {  /* 720p projectors */
    .wrap { gap:10px; padding:12px 20px; } h1 { font-size:24px; margin:4px 0 0; } .card { padding:12px; gap:8px; }
    .bezel { padding:8px 14px; } .bezel strong { font-size:28px; margin:2px 0; }
    .rows dt, .rows dd { padding:4px 10px; } .rows .total { padding:6px 10px; margin-top:4px; } }
  @media (max-width:900px) { .wrap { grid-template-columns:minmax(0,1fr); grid-template-areas:"head" "cam" "oled" "net" "bar"; } }
  header { grid-area:head; }
  .pill { display:inline-flex; align-items:center; gap:8px; padding:4px 12px; border-radius:999px;
          background:var(--accent-soft); color:var(--accent); font-size:13px; font-weight:700; letter-spacing:.08em; }
  .pill i { width:8px; height:8px; border-radius:50%; background:var(--accent); animation:pulse 1.6s ease-in-out infinite; }
  body.offline .pill { background:#f4dcd6; color:var(--warn); } body.offline .pill i { background:var(--warn); animation:none; }
  @keyframes pulse { 50% { opacity:.25; } }
  @media (prefers-reduced-motion:reduce) { .pill i { animation:none; } }
  h1 { margin:8px 0 2px; font-size:clamp(26px,2.8vw,42px); line-height:1.15; letter-spacing:-.01em; }
  .sub { margin:0; color:var(--muted); }
  .card { background:var(--card); border:1px solid var(--edge); border-radius:16px; padding:clamp(14px,1.4vw,22px);
          display:grid; gap:12px; align-content:start; min-width:0; }
  .card h2 { margin:0; font-size:15px; display:flex; justify-content:space-between; gap:12px; align-items:baseline; }
  .card h2 small { color:var(--muted); font-weight:400; font-size:12px; text-align:right; }
  .cam { grid-area:cam; }
  .cam img { width:100%; aspect-ratio:4/3; object-fit:contain; border-radius:10px; background:#cfd7cc; display:block; }
  .oled { grid-area:oled; }
  .bezel { background:var(--oled); border-radius:14px; padding:14px 18px; font-family:var(--mono); color:var(--oled-ink);
           box-shadow:inset 0 0 0 3px #22333a, 0 8px 18px -10px rgba(13,22,24,.6); }
  .bezel .tag, .bezel .clock { color:var(--oled-dim); font-size:12px; letter-spacing:.06em; }
  .bezel strong { display:block; margin:6px 0; font-size:clamp(28px,3vw,46px); font-weight:700; line-height:1.1;
                  overflow-wrap:anywhere; text-shadow:0 0 12px rgba(155,230,242,.35); }
  ol.events { margin:0; padding:0; list-style:none; font:12px/1.6 var(--mono); color:var(--muted); }
  ol.events li:last-child { color:var(--ink); font-weight:700; }
  .net { grid-area:net; }
  .rows { display:grid; grid-template-columns:1fr auto; margin:0; font-variant-numeric:tabular-nums; }
  .rows dt, .rows dd { margin:0; padding:6px 10px; border-bottom:1px solid var(--edge); transition:background-color .3s; }
  .rows dd { text-align:right; font-weight:600; }
  .rows .pen { color:var(--muted); font-size:14px; }
  .rows .hit { background:var(--accent-soft); }
  .rows .total { border:0; margin-top:6px; padding:10px; background:var(--accent-soft); font-size:clamp(18px,1.6vw,24px); font-weight:700; }
  .rows dt.total { border-radius:10px 0 0 10px; } .rows dd.total { border-radius:0 10px 10px 0; color:var(--accent); }
  .bar { grid-area:bar; display:flex; flex-wrap:wrap; gap:12px 20px; align-items:center; justify-content:space-between; }
  #status { margin:0; font-size:clamp(18px,1.7vw,26px); font-weight:700; }
  body.offline #status { color:var(--warn); }
  .chips { display:flex; flex-wrap:wrap; gap:8px; }
  .chips span { border:1px solid var(--edge); border-radius:999px; padding:5px 12px; font-size:13px; background:#fff;
                font-variant-numeric:tabular-nums; }
  .chips .off { color:var(--warn); border-color:#e7b9af; }
</style>
<div class="wrap">
  <header>
    <span class="pill"><i></i>LIVE</span>
    <h1>TITLE</h1>
    <p class="sub">JetBot Mini · ROBOT · <span id="tab"></span></p>
  </header>
  <section class="card cam" aria-labelledby="cam_h">
    <h2 id="cam_h">มุมกล้องของหุ่นยนต์ <small>IMX219 · ภาพจริง · สิ่งที่โค้ดเห็น</small></h2>
    <img id="cam" src="/stream" alt="ภาพสดจากกล้องหุ่นยนต์ พร้อมกรอบเส้นและป้ายที่โค้ดตรวจเจอ">
  </section>
  <section class="card oled" aria-labelledby="oled_h">
    <h2 id="oled_h">จอ OLED บนหุ่นยนต์</h2>
    <div class="bezel" role="img" aria-live="polite" aria-label="ข้อความบนจอ OLED">
      <div class="tag">JETBOT MINI</div><strong id="oled">—</strong><div class="clock" id="oled_t">t = 0.0 s</div>
    </div>
    <ol class="events" id="events" aria-label="เหตุการณ์ล่าสุดของ FSM"></ol>
  </section>
  <section class="card net" aria-labelledby="net_h">
    <h2 id="net_h">Net Time = เวลาวิ่ง + Penalty − Bonus <small>ประมาณจากสิ่งที่โค้ดทำ<br>กรรมการเป็นผู้ตัดสิน</small></h2>
    <dl class="rows">
      <dt>เวลาวิ่ง</dt><dd id="r_time">0.0 วิ</dd>
      <dt id="l_signs">อ่านป้ายถูก + แสดงบน OLED</dt><dd id="r_signs">0</dd>
      <dt id="l_stop">หยุดที่ STOP ครบ 3 วิ</dt><dd id="r_stop">0</dd>
      <dt id="l_park">จอดสนิทที่ PARKING</dt><dd id="r_park">0</dd>
      <dt class="pen">Penalty: เลี้ยวผิด +10 · หลุดเส้น +5 · ชนเสา +3</dt><dd class="pen">กรรมการนับ</dd>
      <dt class="total">Net Time</dt><dd class="total" id="r_net">0.0 วิ</dd>
    </dl>
  </section>
  <section class="card bar" aria-label="สถานะ">
    <p id="status" aria-live="polite">กำลังเชื่อมต่อหุ่นยนต์…</p>
    <div class="chips"><span id="c_mode">—</span><span id="c_conn">—</span><span id="c_batt">แบต —</span><span>≤ 90 วิ / รอบ</span></div>
  </section>
</div>
<script>
const $ = id => document.getElementById(id);
const SIGN = {LEFT: "เลี้ยวซ้าย", RIGHT: "เลี้ยวขวา", STRAIGHT: "ตรงไป", STOP: "หยุด", PARKING: "จอด"};
const STEP = {
  CROSS: "ถึงสี่เหลี่ยมเขียว → วิ่งข้ามจุดตัด", TURN_LEFT: "เลี้ยวซ้ายที่จุดตัด", TURN_RIGHT: "เลี้ยวขวาที่จุดตัด",
  STOP_WAIT: "หยุดนิ่ง 3 วินาทีที่ป้าย STOP", PARK_APPROACH: "เข้าจอดที่ PARKING", DONE: "จอดแล้ว จบภารกิจ",
};
let base = 0, baseAt = 0, shown = 0, running = false, bonus = 0, offline = false;
let last = {signs: 0, stops: 0, parked: false};

function describe(m) {
  if (!m) return "โปรแกรมนี้ไม่มีแท็บภารกิจ เปิด jetbot_app.py หรือ 07_race_runner.py";
  if (!m.running) return m.message || "รอ Start ที่แท็บ 6–7 ภารกิจ";
  if (m.mode === "FOLLOW")
    return m.pending ? "อ่านป้าย" + (SIGN[m.pending] || m.pending) + "ล่วงหน้า → รอสี่เหลี่ยมเขียวแล้วทำตามป้าย"
                     : "เดินตามเส้นดำ มองหาป้ายข้างหน้า";
  return STEP[m.mode] || m.mode;
}
function seconds(t) { return t.toFixed(1) + " วิ"; }
function flash(id, on) { $(id).classList.toggle("hit", on); $(id.replace("l_", "r_")).classList.toggle("hit", on); }

function render(s) {
  $("tab").textContent = "แท็บที่เปิด: " + s.active;
  $("oled").textContent = s.oled || "—";
  $("c_batt").textContent = s.battery == null ? "แบต —" : "แบต " + s.battery.toFixed(2) + " V";
  $("c_conn").textContent = s.connected ? "หน้าควบคุมเปิดอยู่" : "หน้าควบคุมปิด รถไม่วิ่ง";
  $("c_conn").className = s.connected ? "" : "off";
  const m = s.mission;
  $("status").textContent = describe(m);
  if (!m) { $("c_mode").textContent = "ไม่มีภารกิจ"; return; }
  $("c_mode").textContent = (m.watch_only ? "ดูอย่างเดียว (มอเตอร์ไม่หมุน)" : "วิ่งจริง") + " · " + m.mode;
  if (m.running && !running) shown = 0;  // a new run
  running = m.running;
  base = m.running || !m.result ? m.elapsed : m.result.elapsed;
  baseAt = performance.now();
  const b = m.bonus;
  bonus = 2 * b.signs + 2 * b.stops + (b.parked ? 3 : 0);
  $("r_signs").textContent = b.signs ? "−2 × " + b.signs : "0";
  $("r_stop").textContent = b.stops ? "−" + 2 * b.stops : "0";
  $("r_park").textContent = b.parked ? "−3" : "0";
  flash("l_signs", b.signs > last.signs); flash("l_stop", b.stops > last.stops); flash("l_park", b.parked && !last.parked);
  last = b;
  $("events").replaceChildren(...m.events.slice(-5).map(e => {
    const li = document.createElement("li"); li.textContent = e; return li;
  }));
}

function tick() {  // the timer runs smoothly between polls
  const t = running ? Math.max(shown, base + (performance.now() - baseAt) / 1000) : base;
  shown = t;
  $("r_time").textContent = seconds(t);
  $("r_net").textContent = seconds(t - bonus);
  $("oled_t").textContent = "t = " + t.toFixed(1) + " s";
  requestAnimationFrame(tick);
}

async function poll() {
  try {
    const res = await fetch("/live/state", {cache: "no-store"});
    if (!res.ok) throw new Error(res.status);
    render(await res.json());
    if (offline) { offline = false; $("cam").src = "/stream?t=" + Date.now(); }  // reopen: the old stream ended
  } catch (e) {
    offline = true;
    running = false;
    $("status").textContent = "ขาดการเชื่อมต่อกับหุ่นยนต์ ตรวจ Wi-Fi หรือรันโปรแกรมใหม่";
  }
  document.body.classList.toggle("offline", offline);
  setTimeout(poll, 250);
}
poll();
requestAnimationFrame(tick);
</script>
</html>
"""


def build_live_page(title, robot_name):
    """The /live page as bytes, with the program title and robot name filled in."""
    return LIVE_PAGE.replace("TITLE", html.escape(title)).replace("ROBOT", html.escape(robot_name)).encode("utf-8")


def live_routes(app, title, robot_name=None):
    """on_get hook for MjpegServer: /live is the page, /live/state the read-only JSON it polls."""
    page = build_live_page(title, robot_name or socket.gethostname())

    def on_get(path):
        if path == "/live":
            return "text/html; charset=utf-8", page
        if path == "/live/state":
            return "application/json", json.dumps(app.live()).encode("utf-8")
        return None

    return on_get
