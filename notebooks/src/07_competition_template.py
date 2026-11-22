# %% [markdown]
# # Module 7–8: Competition Template
#
# **เวลา:** 14:45 – 16:00 น.
#
# ## เป้าหมาย
#
# - รวมโค้ดทั้งหมดเป็น notebook เดียวที่กด Run All แล้ววิ่งจบภารกิจเอง
# - ชดเชยความเร็วเมื่อแรงดันแบตเตอรี่ตก รถจะได้วิ่งเหมือนตอนจูน
# - บันทึกผลทุกรอบ แล้วจูนบนสนามจริงก่อนแข่ง
#
# ## วันแข่ง
#
# - แข่งทีละคัน คนละ 2 รอบ ใช้ Net Time รอบที่ดีที่สุด รอบละไม่เกิน **90 วินาที**
# - กรรมการวางป้ายใหม่ก่อนทุกรอบ ห้ามแก้โค้ด ระหว่าง Run 1 กับ Run 2 จูนพารามิเตอร์ได้ 5 นาที
# - `Net Time = เวลาวิ่งจริง + Penalty − Bonus` (ดู `docs/competition-rules.md`)
#
# notebook นี้ไม่มีโค้ดใหม่มากนัก ส่วนใหญ่ดึงมาจาก Module 2–6 และค่าที่บันทึกไว้ใน `my_params.json`

# %% [setup]

# %%
import csv
import time

from jetbot_nstru import fsm
from jetbot_nstru.fsm import Command, MissionConfig, MissionState, Observation, step
from jetbot_nstru.line import LineConfig, detect_line
from jetbot_nstru.params import load_params, save_params
from jetbot_nstru.pid import PID, MotorTrim, battery_scale, mix_motors, speed_for_error
from jetbot_nstru.signs import SignConfig, SignVoter, detect_sign

# %% [markdown]
# ## 1. พารามิเตอร์ทั้งหมดรวมไว้ที่เดียว
#
# ค่าเริ่มต้นมาจาก `my_params.json` ที่บันทึกใน Module 2–4 ถ้าจะจูนหน้าสนาม แก้ที่ `PARAMS` นี้ที่เดียว
# แล้ว Run All ใหม่ ช่วงพัก 5 นาทีจะได้ไม่ต้องไล่หาค่าในหลาย cell

# %%
saved = load_params()
PARAMS = {
    "left_gain": saved.get("left_gain", 1.0),
    "right_gain": saved.get("right_gain", 1.0),
    "roi_top": saved.get("roi_top", 0.55),
    "black_v_max": saved.get("black_v_max", 90),
    "kp": saved.get("kp", 0.6),
    "kd": saved.get("kd", 0.05),
    "max_speed": saved.get("max_speed", 0.45),
    "min_speed": saved.get("min_speed", 0.25),
    "reference_voltage": saved.get("reference_voltage", 12.0),  # แรงดันตอนจูน (บันทึกในข้อ 5)
    "time_limit": 90.0,
    "stream": False,  # เปิดเฉพาะตอนซ้อม: ส่งภาพทำให้ loop ช้าลงเล็กน้อย
}
MISSION = MissionConfig(
    cross_time=saved.get("cross_time", 0.35),
    turn_speed=saved.get("turn_speed", 0.35),
    cooldown=saved.get("cooldown", 1.0),
)
for name, value in sorted(PARAMS.items()):
    print("{:18s} {}".format(name, value))
print(MISSION)

# %% [markdown]
# ## 2. ชดเชยแบตเตอรี่
#
# แบต 3S เต็มที่ 12.6 V และตกลงเรื่อย ๆ ระหว่างวัน มอเตอร์หมุนเร็วตามแรงดัน
# ถ้าจูน `Kp` ไว้ตอนแบต 12.4 V แล้วแข่งตอน 11.2 V รถจะช้าลงราว 10% และเข้าโค้งไม่เหมือนเดิม
#
# **TODO:** เขียน `compensate(speed, voltage)` คืน `speed` คูณ `battery_scale(voltage, PARAMS["reference_voltage"])`
# ถ้า `voltage` เป็น `None` (อ่านแบตไม่ได้) ให้คืน `speed` เดิม

# %%
def compensate(speed, voltage):
    # BEGIN SOLUTION: ถ้า voltage is None คืน speed; ไม่อย่างนั้นคืน speed * battery_scale(voltage, PARAMS["reference_voltage"])
    if voltage is None:
        return speed
    return speed * battery_scale(voltage, PARAMS["reference_voltage"])
    # END SOLUTION


PARAMS_BACKUP = dict(PARAMS)
PARAMS["reference_voltage"] = 12.0
assert compensate(0.4, None) == 0.4
assert abs(compensate(0.4, 12.0) - 0.4) < 1e-9
assert compensate(0.4, 10.8) > 0.4  # แบตอ่อน สั่งแรงขึ้น
assert abs(compensate(0.4, 6.0) - 0.4 * 1.25) < 1e-9  # จำกัดไม่ให้เกิน 1.25 เท่า
PARAMS = PARAMS_BACKUP

# %%
!sudo systemctl stop jetbotmini_stats

from jetbot_nstru.hardware import CsiCamera, Oled, beep, open_robot, read_battery_voltage

robot = open_robot()
oled = Oled()
camera = CsiCamera(width=320, height=240, lock_exposure=True)


def battery_now():
    try:
        return read_battery_voltage()
    except Exception as error:  # อ่านแบตไม่ได้ไม่ควรทำให้แข่งไม่ได้
        print("อ่านแรงดันแบตไม่ได้ ({}) วิ่งโดยไม่ชดเชย".format(error))
        return None


print("แบตตอนนี้:", battery_now(), "V")

# %% [markdown]
# ## 3. ภารกิจเต็ม
#
# `observe` และ `apply` เหมือนเฉลย Module 6 ต่างกันแค่ความเร็วทุกค่าผ่าน `compensate` ก่อน
# `run_race()` คืนรายการเหตุการณ์ (เวลา, state, ข้อความบน OLED) ไว้ตรวจผลหลังวิ่ง

# %%
trim = MotorTrim(PARAMS["left_gain"], PARAMS["right_gain"])
line_cfg = LineConfig(roi_top=PARAMS["roi_top"], black_v_max=PARAMS["black_v_max"])
sign_cfg = SignConfig()
voter = SignVoter(window=7, min_votes=4)


def observe(frame):
    line_result = detect_line(frame, line_cfg)
    sign = detect_sign(frame, sign_cfg)
    confirmed = voter.update(sign.label if sign else None)
    green_bottom = None
    if line_result.green_box is not None:
        _, y, _, h = line_result.green_box
        green_bottom = (y + h) / float(frame.shape[0])
    observation = Observation(line_result.found, line_result.error, line_result.width_ratio, green_bottom, confirmed)
    return observation, line_result, sign


def apply(command, steer, speed):
    if command.kind == "follow":
        robot.set_motors(*mix_motors(speed, steer, trim))
    elif command.kind == "drive":
        robot.set_motors(command.left * trim.left_gain, command.right * trim.right_gain)
    else:
        robot.stop()
    if command.display is not None:
        oled.show(command.display)
    if command.beep:
        beep(robot)


def run_race(server=None):
    voltage = battery_now()
    max_speed = compensate(PARAMS["max_speed"], voltage)
    min_speed = compensate(PARAMS["min_speed"], voltage)
    cfg = MISSION._replace(cross_speed=compensate(MISSION.cross_speed, voltage),
                           turn_speed=compensate(MISSION.turn_speed, voltage))
    pid = PID(kp=PARAMS["kp"], kd=PARAMS["kd"])
    voter.reset()
    state = MissionState()
    steer = 0.0
    events = []
    frames = 0
    oled.show("GO")
    start = last = time.monotonic()
    try:
        while state.mode != fsm.DONE and time.monotonic() - start < PARAMS["time_limit"]:
            frame = camera.read()
            now = time.monotonic()
            dt, last = max(now - last, 1e-3), now

            observation, line_result, sign = observe(frame)
            previous_mode = state.mode
            state, command = step(state, observation, now, cfg)
            if state.mode not in (fsm.FOLLOW, fsm.PARK_APPROACH):
                pid.reset()
            elif line_result.found:
                steer = pid.update(line_result.error, dt)
            apply(command, steer, speed_for_error(observation.error, max_speed, min_speed))

            if state.mode != previous_mode or command.display is not None:
                events.append((round(now - start, 2), state.mode, command.display))
            frames += 1
            if server is not None:
                from jetbot_nstru.viz import VizState, draw_overlay
                server.push(draw_overlay(frame, VizState(fsm_state=state.mode, line_roi=line_result.roi_box,
                                                         cx=line_result.cx, cy=line_result.cy, sign=sign)))
    finally:
        robot.stop()
    elapsed = time.monotonic() - start
    print("{} ใน {:.2f} วินาที, {:.1f} FPS, แบต {} V".format(
        "จบภารกิจ" if state.mode == fsm.DONE else "DNF/หมดเวลา", elapsed, frames / max(elapsed, 1e-3), voltage))
    return elapsed, state.mode == fsm.DONE, voltage, events


# %% [markdown]
# ## 4. ตรวจผลหลังวิ่ง
#
# **TODO:** เขียน `estimate_bonus(events)` นับโบนัสที่รถน่าจะได้จาก log:
#
# - ข้อความบน OLED ที่เป็นชื่อป้าย (`LEFT`, `RIGHT`, `STRAIGHT`, `STOP`, `PARKING`) ป้ายละ 2 วินาที
# - เข้า state `STOP_WAIT` ครั้งละ 2 วินาที
# - ข้อความ `PARKED` 3 วินาที
#
# ตัวเลขนี้ไว้เทียบกับที่กรรมการให้: ถ้าต่างกันมาก แปลว่ารถอ่านป้ายผิดหรือ OLED ไม่ได้แสดงผล

# %%
SIGN_NAMES = ("LEFT", "RIGHT", "STRAIGHT", "STOP", "PARKING")


def estimate_bonus(events):
    # BEGIN SOLUTION: วนทุก (t, mode, display) แล้วบวกคะแนนตามเงื่อนไข 3 ข้อ (ระวัง STOP_WAIT นับตอนเปลี่ยน state เท่านั้น)
    bonus = 0.0
    previous_mode = None
    for _, mode, display in events:
        if display in SIGN_NAMES:
            bonus += 2
        if display == "PARKED":
            bonus += 3
        if mode == fsm.STOP_WAIT and previous_mode != fsm.STOP_WAIT:
            bonus += 2
        previous_mode = mode
    return bonus
    # END SOLUTION


sample = [(1.2, "FOLLOW", "STOP"), (2.0, "STOP_WAIT", None), (5.2, "CROSS", None),
          (8.0, "FOLLOW", "PARKING"), (9.5, "PARK_APPROACH", None), (11.0, "DONE", "PARKED")]
assert estimate_bonus(sample) == 2 + 2 + 2 + 3
assert estimate_bonus([]) == 0

# %% [markdown]
# ## 5. ซ้อมบนสนามจริง
#
# วางรถที่ START แล้วรัน cell นี้ ทุกรอบจะถูกต่อท้ายใน `race_log.csv` (ไม่ขึ้น git) พร้อมค่าที่ใช้
# ตอนซ้อมเปิด `PARAMS["stream"] = True` เพื่อดูภาพที่ `http://<IP>:8080` ได้

# %%
LOG_PATH = os.path.join(root, "race_log.csv")


def practice_run():
    server = None
    if PARAMS["stream"]:
        from jetbot_nstru.viz import MjpegServer
        server = MjpegServer(port=8080, max_fps=10).start()
    try:
        elapsed, finished, voltage, events = run_race(server)
    finally:
        if server is not None:
            server.stop()
    bonus = estimate_bonus(events)
    for event in events:
        print(event)
    print("โบนัสโดยประมาณ {:.0f} วินาที, Net Time โดยประมาณ {:.2f} (ยังไม่รวม penalty)".format(bonus, elapsed - bonus))
    new_file = not os.path.exists(LOG_PATH)
    with open(LOG_PATH, "a", newline="") as handle:
        writer = csv.writer(handle)
        if new_file:
            writer.writerow(["time", "elapsed", "finished", "voltage", "bonus", "kp", "kd", "max_speed"])
        writer.writerow([time.strftime("%H:%M:%S"), round(elapsed, 2), finished, voltage, bonus,
                         PARAMS["kp"], PARAMS["kd"], PARAMS["max_speed"]])


practice_run()

# %% [markdown]
# ถ้ารอบนี้วิ่งดี บันทึกค่าและแรงดันแบตตอนนี้เป็น `reference_voltage` รอบแข่งจะชดเชยจากจุดนี้

# %%
print(save_params(kp=PARAMS["kp"], kd=PARAMS["kd"], max_speed=PARAMS["max_speed"], min_speed=PARAMS["min_speed"],
                  cross_time=MISSION.cross_time, turn_speed=MISSION.turn_speed, cooldown=MISSION.cooldown,
                  reference_voltage=battery_now() or PARAMS["reference_voltage"]))

# %% [markdown]
# ## 6. รอบแข่ง
#
# 1. ชาร์จแบตหรือเปลี่ยนก้อนก่อนเข้าคิว แบตต่ำกว่า 11.1 V รถจะเริ่มอ่อนแรงเกินชดเชย
# 2. `PARAMS["stream"] = False` แล้ว Run All ก่อนถึงคิวตัวเอง (กล้องเปิดใช้เวลาราว 2 วินาที)
# 3. วางรถที่ START เมื่อกรรมการให้สัญญาณ รัน cell ด้านล่าง
# 4. ถ้ารถหลุดเส้น กด ■ หยิบรถกลับมาวาง แล้วรัน cell ใหม่ (เวลาของกรรมการเดินต่อ)

# %%
practice_run()

# %%
camera.release()
robot.stop()
oled.show("BYE")

# %% [markdown]
# ## Checklist ก่อนแข่ง
#
# - [ ] `my_params.json` มีค่า trim, ROI, PID และ `reference_voltage` ครบ
# - [ ] Run All จากบนลงล่างได้โดยไม่มี error และไม่มี `NotImplementedError`
# - [ ] OLED แสดงชื่อป้ายทุกป้าย และมีเสียง beep
# - [ ] หยุดที่ STOP ครบ 3 วินาที ล้อนิ่งสนิท
# - [ ] จุดตัดเขียวที่ไม่มีป้าย รถวิ่งตรงไป
# - [ ] เข้าจอด PARKING แล้วหยุดเอง ก่อน 90 วินาที
# - [ ] ซ้อมครบอย่างน้อย 3 รอบติดกันโดยไม่หลุดเส้น
# - [ ] ปิด stream และเปิด Jupyter บนเครื่องตัวเองไว้พร้อม ไม่ต้องหาลิงก์ตอนถึงคิว
