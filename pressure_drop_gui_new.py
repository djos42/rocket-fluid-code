# -*- coding: utf-8 -*-
"""The following was written by Claude based on a code I gave it"""

"""
Pressure budget GUI - wrapper around the feed-line pressure drop script.
Your original script is untouched: compute() below repeats the same
rocketprops / CoolProp calls in the same order, with the inputs coming
from the window instead of being hard-coded.

pip install PySide6 rocketprops CoolProp
Run from a terminal (python pressure_drop_gui.py) or from Spyder.
"""
import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFrame, QGraphicsDropShadowEffect, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget)

from CoolProp.CoolProp import PropsSI
from rocketprops.line_supt import calc_line_vel_dp
from rocketprops.rocket_prop import get_prop
from rocketprops.valve_supt import cv_valve_dp

# ---------------------------------------------------------------- settings
K_BEND = 0.75                  # loss coefficient per bend (same as your script)
SHOW_FLASH_CHECK = True        # extra row: downstream pressure vs vapor pressure
FLUIDS = {                     # label: (rocketprops name, CoolProp name)
    "nitrous oxide": ("N2O", "N2O"),
    "ethanol": ("ethanol", "Ethanol"),
}
IN_PER_M, LBM_PER_KG, PSI_PER_BAR, FT_PER_M = 39.37007874, 2.20462262, 14.5037738, 3.28083990

# (key, label, default, unit)
GROUPS = [
    ("line", [
        ("od", "outer diameter", "0.5", "in"),
        ("wall", "wall thickness", "0.035", "in"),
        ("length", "length", "5", "m"),
        ("rough", "roughness", "1.4", "µm"),
        ("bends", "bends", "6", "x"),
    ]),
    ("flow state", [
        ("mdot", "mass flow", "2.13", "kg/s"),
        ("p", "tank pressure", "100", "bar"),
        ("t", "temperature", "15", "°C"),
    ]),
    ("valves", [
        ("cv_main", "main valve Cv", "5", ""),
        ("cv_check", "check valve Cv", "2", ""),
    ]),
]

CYAN, VIOLET, MAGENTA, PINK, AMBER, RED = (
    "#19f3ff", "#9b5cff", "#ff2bd6", "#ff8bd9", "#ffb000", "#ff3860")
SEG_COLORS = [CYAN, VIOLET, MAGENTA, PINK]
SEG_NAMES = ["line", "dynamic", "main valve", "check valve"]


# ------------------------------------------------------------- calculation
def compute(fluid, od, wall, length_m, mdot, p_bar, t_c, rough_um, bends,
            cv_main, cv_check):
    rp_name, cp_name = FLUIDS[fluid]
    lin = length_m * IN_PER_M
    wpps = mdot * LBM_PER_KG
    ppsi = p_bar * PSI_PER_BAR
    ppa = p_bar * 1e5
    tk = t_c + 273.15
    tr = tk * 1.8
    roughin = rough_um / 25400.0
    kbend = K_BEND * bends
    ind = od - 2 * wall
    if ind <= 0:
        raise ValueError("wall thickness leaves no bore")

    pObj = get_prop(rp_name)

    vel, dp = calc_line_vel_dp(pObj, TdegR=tr, Ppsia=ppsi, wdotPPS=wpps,
                               IDinches=ind, roughness=roughin,
                               Kfactors=kbend, len_inches=lin)
    fv = vel / FT_PER_M                      # m/s
    dpbarl = dp / PSI_PER_BAR                # line loss, bar

    rho = PropsSI('D', 'T', tk, 'P', ppa, cp_name)
    dplbar = 0.5 * rho * fv ** 2 / 1e5       # dynamic pressure, bar

    dpmv = cv_valve_dp(pObj, Cv=cv_main, wdotPPS=wpps, TdegR=tr, Ppsia=ppsi)
    dpcv = cv_valve_dp(pObj, Cv=cv_check, wdotPPS=wpps, TdegR=tr,
                       Ppsia=(ppsi - dpmv))
    dpbarmv, dpbarcv = dpmv / PSI_PER_BAR, dpcv / PSI_PER_BAR

    total = dplbar + dpbarmv + dpbarcv + dpbarl
    psat = PropsSI('P', 'T', tk, 'Q', 0, cp_name) / 1e5 if SHOW_FLASH_CHECK else None
    return dict(vel=fv, line=dpbarl, dyn=dplbar, main=dpbarmv, check=dpbarcv,
                total=total, psat=psat, p=p_bar, id=ind)


# ------------------------------------------------------------------ widgets
class BudgetBar(QWidget):
    """Tank pressure as a bar; each loss eats into it from the left."""
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(96)
        self.d = None

    def set_data(self, d):
        self.d = d
        self.update()

    def paintEvent(self, _):
        q = QPainter(self)
        W, top, h = self.width() - 2, 14, 28
        q.setPen(QPen(QColor("#2b1d52"), 1))
        q.setBrush(QColor("#0d0719"))
        q.drawRect(1, top, W, h)
        if self.d:
            d, x = self.d, 1.0
            for val, col in zip((d["line"], d["dyn"], d["main"], d["check"]), SEG_COLORS):
                w = min(max(val, 0) / d["p"] * W, 1 + W - x)
                q.fillRect(int(x), top + 1, int(w), h - 1, QColor(col))
                x += w
            if d["psat"] is not None:
                tx = int(1 + max(0.0, (d["p"] - d["psat"]) / d["p"]) * W)
                q.setPen(QPen(QColor(AMBER), 2))
                q.drawLine(tx, top - 8, tx, top + h + 8)
                q.setPen(QColor(AMBER))
                label = "flash limit"
                lw = q.fontMetrics().horizontalAdvance(label)
                q.drawText(min(max(tx - lw // 2, 0), self.width() - lw), top + h + 22, label)
        lx = 2
        for name, col in zip(SEG_NAMES, SEG_COLORS):
            q.fillRect(lx, top + h + 38, 9, 9, QColor(col))
            q.setPen(QColor("#7f6fb8"))
            q.drawText(lx + 14, top + h + 47, name)
            lx += 14 + q.fontMetrics().horizontalAdvance(name) + 18


class Scanlines(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def paintEvent(self, _):
        q = QPainter(self)
        q.setPen(QPen(QColor(0, 0, 0, 34), 1))
        for y in range(0, self.height(), 3):
            q.drawLine(0, y, self.width(), y)


def glow(widget, color, blur=22):
    fx = QGraphicsDropShadowEffect(widget)
    fx.setBlurRadius(blur)
    fx.setOffset(0, 0)
    fx.setColor(QColor(color))
    widget.setGraphicsEffect(fx)


QSS = f"""
QWidget {{ background:#0a0614; color:#d9f7ff; font-family:"Consolas","DejaVu Sans Mono",monospace; font-size:13px; }}
QLabel {{ background:transparent; }}
QFrame#panel {{ background:#110a22; border:1px solid #2b1d52; }}
QLabel#group {{ color:{CYAN}; font-size:12px; }}
QLabel#dim {{ color:#7f6fb8; }}
QLabel#title {{ color:{CYAN}; font-family:"OCR A Extended","Consolas",monospace; font-size:24px; }}
QLabel#big {{ color:{MAGENTA}; font-family:"OCR A Extended","Consolas",monospace; font-size:44px; }}
QLineEdit {{ background:#0d0719; border:1px solid #2b1d52; border-bottom:2px solid {CYAN};
             padding:4px 6px; color:#fff; selection-background-color:{MAGENTA}; }}
QLineEdit:focus {{ border-bottom:2px solid {MAGENTA}; }}
QLineEdit[bad="true"] {{ border-bottom:2px solid {RED}; }}
QComboBox {{ background:#0d0719; border:1px solid {CYAN}; padding:5px 8px; color:{CYAN}; }}
QComboBox::drop-down {{ border:none; width:22px; }}
QComboBox QAbstractItemView {{ background:#0d0719; color:{CYAN}; border:1px solid {CYAN};
             selection-background-color:{MAGENTA}; selection-color:#0a0614; outline:0; }}
QPushButton {{ background:transparent; border:1px solid #2b1d52; color:#7f6fb8; padding:6px 14px; }}
QPushButton:hover {{ border:1px solid {MAGENTA}; color:{MAGENTA}; }}
"""


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("pressure budget")
        self.resize(1020, 700)
        self.edits, self.out = {}, {}
        self.timer = QTimer(self, singleShot=True, interval=120)
        self.timer.timeout.connect(self.recalc)

        root = QHBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(20)

        # ---- left: inputs
        left = QVBoxLayout()
        left.setSpacing(12)
        title = QLabel("pressure budget_")
        title.setObjectName("title")
        glow(title, CYAN, 18)
        sub = QLabel("feed line  //  rocketprops + coolprop")
        sub.setObjectName("dim")
        left.addWidget(title)
        left.addWidget(sub)

        cap_fluid = QLabel("> propellant (click to change)")
        cap_fluid.setObjectName("dim")
        left.addWidget(cap_fluid)
        self.fluid = QComboBox()
        self.fluid.addItems(FLUIDS.keys())
        self.fluid.currentIndexChanged.connect(self.timer.start)
        left.addWidget(self.fluid)

        for gname, fields in GROUPS:
            panel = QFrame(objectName="panel")
            grid = QGridLayout(panel)
            grid.setContentsMargins(14, 10, 14, 12)
            grid.setVerticalSpacing(8)
            head = QLabel(gname)
            head.setObjectName("group")
            grid.addWidget(head, 0, 0, 1, 3)
            for i, (key, label, default, unit) in enumerate(fields, start=1):
                e = QLineEdit(default)
                e.setAlignment(Qt.AlignRight)
                e.textChanged.connect(self.timer.start)
                self.edits[key] = e
                lab = QLabel("> " + label)
                u = QLabel(unit)
                u.setObjectName("dim")
                grid.addWidget(lab, i, 0)
                grid.addWidget(e, i, 1)
                grid.addWidget(u, i, 2)
            grid.setColumnMinimumWidth(0, 150)
            grid.setColumnMinimumWidth(1, 110)
            grid.setColumnMinimumWidth(2, 34)
            left.addWidget(panel)
        left.addStretch()
        reset = QPushButton("reset defaults")
        reset.clicked.connect(self.reset)
        left.addWidget(reset, alignment=Qt.AlignLeft)
        root.addLayout(left, 0)

        # ---- right: readout
        right = QFrame(objectName="panel")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(22, 16, 22, 16)
        rl.setSpacing(6)
        cap = QLabel("total pressure loss")
        cap.setObjectName("dim")
        self.big = QLabel("--")
        self.big.setObjectName("big")
        glow(self.big, MAGENTA, 26)
        rl.addWidget(cap)
        rl.addWidget(self.big)
        self.status = QLabel("")
        self.status.setWordWrap(True)
        rl.addWidget(self.status)
        rl.addSpacing(8)

        rows = QGridLayout()
        rows.setVerticalSpacing(7)
        spec = [("vel", "line velocity", "m/s"), ("line", "line (friction + bends)", "bar"),
                ("dyn", "dynamic pressure", "bar"), ("main", "main valve", "bar"),
                ("check", "check valve", "bar")]
        for i, (k, name, unit) in enumerate(spec):
            v = QLabel("--")
            v.setAlignment(Qt.AlignRight)
            self.out[k] = v
            rows.addWidget(QLabel(name), i, 0)
            rows.addWidget(v, i, 1)
            ul = QLabel(unit)
            ul.setObjectName("dim")
            rows.addWidget(ul, i, 2)
        rows.setColumnStretch(0, 1)
        rl.addLayout(rows)
        rl.addSpacing(10)
        self.bar = BudgetBar()
        rl.addWidget(self.bar)
        rl.addStretch()
        root.addWidget(right, 1)

        self.scan = Scanlines(self)
        self.scan.raise_()
        self.recalc()

    def resizeEvent(self, e):
        self.scan.setGeometry(self.rect())
        self.scan.raise_()

    def reset(self):
        for _, fields in GROUPS:
            for key, _, default, _ in fields:
                self.edits[key].setText(default)
        self.fluid.setCurrentIndex(0)

    def _num(self, key):
        e = self.edits[key]
        try:
            val = float(e.text().replace(",", "."))
            bad = False
        except ValueError:
            val, bad = None, True
        e.setProperty("bad", bad)
        e.style().unpolish(e)
        e.style().polish(e)
        return val

    def recalc(self):
        vals = {k: self._num(k) for k in self.edits}
        if any(v is None for v in vals.values()):
            return self.fail("check the highlighted inputs")
        try:
            r = compute(self.fluid.currentText(), vals["od"], vals["wall"], vals["length"],
                        vals["mdot"], vals["p"], vals["t"], vals["rough"], vals["bends"],
                        vals["cv_main"], vals["cv_check"])
        except Exception as ex:                     # show the problem, keep the window alive
            return self.fail(str(ex))
        self.big.setText(f"{r['total']:.2f} bar")
        for k in ("vel", "line", "dyn", "main", "check"):
            self.out[k].setText(f"{r[k]:.3f}" if k != "vel" else f"{r[k]:.2f}")
        self.bar.set_data(r)
        down = r["p"] - r["total"]
        if r["psat"] is None:
            msg, col = f"bore {r['id']:.3f} in", "#7f6fb8"
        elif down < r["psat"]:
            msg, col = (f"downstream {down:.1f} bar  <  vapor {r['psat']:.1f} bar : liquid would flash", RED)
        else:
            msg, col = (f"downstream {down:.1f} bar  >  vapor {r['psat']:.1f} bar", "#7f6fb8")
        self.status.setStyleSheet(f"color:{col};")
        self.status.setText(msg)

    def fail(self, msg):
        self.big.setText("--")
        for v in self.out.values():
            v.setText("--")
        self.bar.set_data(None)
        self.status.setStyleSheet(f"color:{AMBER};")
        self.status.setText(msg)


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(QSS)
    w = Window()
    w.show()
    app.exec()
    return w


if __name__ == "__main__":
    main()
