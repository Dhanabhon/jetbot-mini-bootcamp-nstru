"""The robot setup program's parsing and naming rules, plus a full --dry-run on the laptop."""
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import robot_setup as setup  # noqa: E402
import status_display  # noqa: E402

IW_LIST = """Wiphy phy0
\tBand 1:
\t\tFrequencies:
\t\t\t* 2412 MHz [1] (20.0 dBm)
\t\t\t* 2484 MHz [14] (disabled)
\tBand 2:
\t\tFrequencies:
\t\t\t* 5180 MHz [36] (20.0 dBm)
\t\t\t* 5260 MHz [52] (20.0 dBm) (radar detection)
\t\t\t* 5745 MHz [149] (20.0 dBm)
\t\t\t* 5765 MHz [153] (20.0 dBm) (no IR)
\t\t\t* 5785 MHz [157] (passive scanning, no IBSS)
\tSupported interface modes:
\t\t * IBSS
\t\t * managed
\t\t * AP
\t\t * monitor
\tsoftware interface modes (can always be added):
"""


@pytest.mark.parametrize("text, number", [("7", 7), (" 07\n", 7), ("99", 99)])
def test_robot_number_accepts_sticker_numbers(text, number):
    assert setup.parse_robot_number(text) == number


@pytest.mark.parametrize("text", ["", "0", "100", "seven", "-3"])
def test_robot_number_rejects_anything_else(text):
    with pytest.raises(ValueError):
        setup.parse_robot_number(text)


def test_names_use_two_digit_numbers():
    assert setup.hostname_for(7) == "jetbot-07"
    assert setup.ssid_for(12) == "JETBOT-12"


def test_password_fills_the_number_into_the_pattern():
    assert setup.password_for("robotpass{num}\n", 7) == "robotpass07"


def test_password_shorter_than_wpa2_minimum_is_rejected():
    with pytest.raises(ValueError):
        setup.password_for("ab{num}", 7)


def test_hosts_line_is_replaced_not_duplicated():
    hosts = "127.0.0.1\tlocalhost\n127.0.1.1\tjetson-desktop\n"
    assert setup.hosts_with_hostname(hosts, "jetbot-07") == "127.0.0.1\tlocalhost\n127.0.1.1\tjetbot-07\n"


def test_hosts_line_is_added_when_missing():
    assert setup.hosts_with_hostname("127.0.0.1\tlocalhost\n", "jetbot-07").endswith("127.0.1.1\tjetbot-07\n")


def test_iw_list_modes():
    assert setup.iw_interface_modes(IW_LIST) == {"IBSS", "managed", "AP", "monitor"}
    assert setup.iw_interface_modes("") == set()


def test_ap_channels_skip_disabled_dfs_and_listen_only():
    assert setup.iw_ap_channels(IW_LIST) == {1, 36, 149}


def test_channels_rotate_over_5ghz_when_the_dongle_allows_it():
    allowed = set(setup.CHANNELS_5GHZ) | {1, 6, 11}
    picked = [setup.pick_channel(n, allowed) for n in range(1, 11)]
    assert picked[:3] == [36, 40, 44]
    assert picked[8] == 36  # robot 9 wraps around after 8 channels
    assert all(a != b for a, b in zip(picked, picked[1:]))


def test_channels_fall_back_to_1_6_11():
    assert [setup.pick_channel(n, {1, 6, 11, 52}) for n in range(1, 5)] == [1, 6, 11, 1]
    assert setup.pick_channel(2, set()) == 6  # iw output unreadable: still a non-overlapping channel


def test_channels_use_only_the_5ghz_ones_that_are_allowed():
    assert [setup.pick_channel(n, {36, 149, 1}) for n in range(1, 4)] == [36, 149, 36]


def test_iw_ssid_and_ipv4_parsing():
    info = "Interface wlan0\n\tifindex 4\n\tssid JETBOT-07\n\ttype AP\n"
    assert setup.iw_ssid(info) == "JETBOT-07"
    assert setup.iw_ssid("Interface wlan0\n\ttype managed\n") == ""
    out = "4: wlan0    inet 10.42.0.1/24 brd 10.42.0.255 scope global wlan0\n"
    assert setup.parse_ipv4(out) == "10.42.0.1"
    assert setup.parse_ipv4("") == ""


def test_oled_lines_say_what_is_missing():
    assert status_display.status_lines("JETBOT-07", "pw", "10.42.0.1", True, 11.84) == [
        "JETBOT-07", "PW pw", "10.42.0.1:8888", "BAT 11.8V"]
    assert status_display.status_lines("", "", "", False, 0.0)[0] == "NO WIFI DONGLE"
    assert status_display.status_lines("", "", "", True, 0.0) == ["NO HOTSPOT", "PW -", "NO IP", "BAT ?"]


def test_oled_rows_fit_the_128_pixel_screen():
    rows = status_display.status_lines("JETBOT-07", "x" * 16, "192.168.100.200", True, 12.6)
    assert all(len(row) <= 21 for row in rows)  # default PIL font is 6 px wide


def test_dry_run_runs_every_step_without_sudo(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(setup, "LOG_FILE", str(tmp_path / "setup.log"))
    monkeypatch.setattr(setup, "ROBOT_FILE", str(tmp_path / "robot.conf"))
    real_check_output = subprocess.check_output

    def no_sudo(cmd, **kwargs):
        assert cmd[0] != "sudo", "dry-run must not run sudo"
        return real_check_output(cmd, **kwargs)

    monkeypatch.setattr(subprocess, "check_output", no_sudo)

    setup.main(["--dry-run"])

    out = capsys.readouterr().out
    for number in range(1, 11):
        assert "ขั้น %d:" % number in out
    assert "$ sudo hostnamectl set-hostname jetbot-07" in out
    assert "nstru_status" in out
    assert not os.path.exists(setup.ROBOT_FILE)
