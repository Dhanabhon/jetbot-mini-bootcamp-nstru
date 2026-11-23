"""Race day app: tune in the browser, then press KEY1 on the robot to start the run and its timer, KEY1 again to stop.

Run on the robot, in a Jupyter Lab Terminal (shut down all notebook kernels first, they hold the camera and motors):

    cd ~/jetbot-mini-bootcamp-nstru
    python3 jetbot_race.py

Open http://10.42.0.1:8080 in Chrome to tune: tabs for trim, line, PID and signs; each tab's Save writes
my_params.json, the same file the notebooks use. Back on the "แข่ง (KEY1)" tab, put the robot at START and press
KEY1. A KEY1 run keeps going if the laptop loses Wi-Fi; KEY1, Space, closing the page, 90 s or a lost line stop it.
http://10.42.0.1:8080/live shows the camera, OLED and timer for a projector.
Every run is appended to race_log.csv. Ctrl+C in the Terminal ends the program.

The code is in jetbot_nstru/app/race.py. Python 3.6 compatible.
"""
from jetbot_nstru.app.core import run
from jetbot_nstru.app.race import RACE_PANELS

if __name__ == "__main__":
    run(RACE_PANELS, "JetBot วันแข่ง (KEY1)")
