"""JetBot NSTRU: everything from the bootcamp in one program, ready to use after the course.

Run on the robot (shut down all notebook kernels first, they hold the camera and motors):

    cd ~/jetbot-mini-bootcamp-nstru
    python3 jetbot_app.py            # --port 8081 if 8080 is taken

then open http://10.42.0.1:8080 in Chrome. Each tab is one module:

    1 ตรวจเครื่อง   battery, camera, buzzer, OLED, a short drive
    2 Trim         drive straight, enter the drift, the app works out left_gain / right_gain
    3 เส้นดำ        roi_top and black_v_max with the line and green masks
    4 PID          follow the line and change Kp, Kd and speeds while it drives
    5 ป้าย          live sign reading with extent / balance, and photo capture for training
    5 ป้าย CNN      photos, one-button ResNet18 training on the robot's GPU, live reading with a confidence slider
    6–7 ภารกิจ      the whole mission, watch-only mode, battery compensation, race_log.csv

http://10.42.0.1:8080/live is a read-only screen for a projector: live camera, OLED copy, Net Time estimate.

A value changed on one tab is used by the others right away; each tab's Save writes it to my_params.json,
which the notebooks read too. Space stops the robot from any tab, and the motors also stop when the page
closes or the laptop leaves the robot's Wi-Fi.

Build on it: write a Panel subclass and give it a tab, for example

    from jetbot_nstru.app import PANEL_TYPES, Panel

    class SpinPanel(Panel):
        name, title = "spin", "หมุนตัว"
        controls = '<h2>หมุนตัว</h2><button class="go" id="spin_go">หมุน 1 วินาที</button>'
        script = 'panels.spin = {}; $("spin_go").addEventListener("click", () => act("go"));'

        def __init__(self, ctx):
            super().__init__(ctx)
            self.until = 0.0

        def handle(self, action, data):
            if action != "/go":
                return None
            self.until = self.ctx.clock() + 1.0
            return {"message": "หมุนแล้ว"}

        def halt(self, message):
            self.until = 0.0

        def step(self, frame, now, fps):
            return frame, (0.3, -0.3) if now < self.until else None   # (picture, motors or None)

    PANEL_TYPES[SpinPanel.name] = SpinPanel   # before run_app()

The rest of the API is in jetbot_nstru/app/core.py; the module tabs in jetbot_nstru/app/*.py are worked examples.
Python 3.6 compatible.
"""
from jetbot_nstru.app import run_app

if __name__ == "__main__":
    run_app()
