"""The JetBot browser app: every bootcamp module as a tab on one page. See core.py for how it works.

    from jetbot_nstru.app import run_app
    run_app()                          # every tab
    run_app(["pid"], "จูน PID")        # one tab
"""
from collections import OrderedDict

from .check import CheckPanel
from .cnn import CnnPanel
from .core import App, Context, Panel, TimedDrive, build_page, run
from .line import LinePanel
from .mission import MissionPanel
from .pid import PidPanel
from .signs import SignPanel
from .trim import TrimPanel

# Tab order on the page. Add your own Panel subclass here to give it a tab.
PANEL_TYPES = OrderedDict((cls.name, cls) for cls in (
    CheckPanel, TrimPanel, LinePanel, PidPanel, SignPanel, CnnPanel, MissionPanel))


def run_app(names=None, title="JetBot NSTRU", argv=None, options=None):
    """Run the app with the named tabs (all of them by default). options: {"mission": {"watch_only": True}}."""
    names = list(PANEL_TYPES) if names is None else names
    unknown = [name for name in names if name not in PANEL_TYPES]
    if unknown:
        raise ValueError("unknown panels {}; choose from {}".format(unknown, list(PANEL_TYPES)))
    run([PANEL_TYPES[name] for name in names], title, argv=argv, options=options)


__all__ = ["App", "Context", "Panel", "TimedDrive", "PANEL_TYPES", "build_page", "run_app"]
