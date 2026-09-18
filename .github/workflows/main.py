import json
import os
from datetime import datetime, date

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.slider import Slider
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kalori_data.json")

BG_COLOR = (0.07, 0.07, 0.09, 1)
CARD_COLOR = (0.15, 0.15, 0.18, 1)
INPUT_COLOR = (0.20, 0.20, 0.24, 1)
ACCENT = (0.30, 0.65, 1.0, 1)
GREEN = (0.30, 0.78, 0.38, 1)
RED = (0.92, 0.32, 0.32, 1)
TEXT_COLOR = (0.92, 0.92, 0.94, 1)
MUTED = (0.62, 0.62, 0.66, 1)


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                d.setdefault("entries", {})
                return d
        except Exception:
            pass
    return {"daily_goal": None, "start_weight": None, "entries": {}}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def bg_rect(widget, color):
    with widget.canvas.before:
        Color(*color)
        widget._bg_rect = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(
        pos=lambda w, v: setattr(w._bg_rect, "pos", v),
        size=lambda w, v: setattr(w._bg_rect, "size", v),
    )


def flat_button(text, bg=CARD_COLOR, fg=TEXT_COLOR, **kwargs):
    return Button(
        text=text,
        background_normal="",
        background_down="",
        background_color=bg,
        color=fg,
        **kwargs,
    )


class SetupScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical", padding=dp(24), spacing=dp(14))
        bg_rect(root, BG_COLOR)

        root.add_widget(Label(
            text="Kalori Takip - Kurulum", font_size="22sp", bold=True,
            color=TEXT_COLOR, size_hint=(1, None), height=dp(46)
        ))

        root.add_widget(Label(
            text="Günlük kalori hedefiniz", color=MUTED,
            size_hint=(1, None), height=dp(22)
        ))

        self.goal_label = Label(
            text="2000 kcal", font_size="30sp", bold=True, color=ACCENT,
            size_hint=(1, None), height=dp(46)
        )
        root.add_widget(self.goal_label)

        self.goal_slider = Slider(min=1000, max=4500, step=50, value=2000,
                                   size_hint=(1, None), height=dp(36))
        self.goal_slider.bind(value=self.on_goal_change)
        root.add_widget(self.goal_slider)

        quick_row = BoxLayout(size_hint=(1, None), height=dp(42), spacing=dp(6))
        for val in (1600, 1800, 2000, 2200, 2500, 3000):
            b = flat_button(str(val), bg=CARD_COLOR)
            b.bind(on_release=lambda inst, v=val: self.set_goal(v))
            quick_row.add_widget(b)
        root.add_widget(quick_row)

        root.add_widget(Label(
            text="Başlangıç kilonuz (kg)", color=MUTED,
            size_hint=(1, None), height=dp(22)
        ))
        self.weight_input = TextInput(
            text="", multiline=False, input_filter="float", font_size="18sp",
            size_hint=(1, None), height=dp(46), background_color=INPUT_COLOR,
            foreground_color=TEXT_COLOR, cursor_color=TEXT_COLOR,
            padding=[dp(12), dp(11), 0, 0],
        )
        root.add_widget(self.weight_input)

        root.add_widget(BoxLayout())

        self.save_btn = flat_button("Kaydet ve Başla", bg=ACCENT, fg=(1, 1, 1, 1),
                                     size_hint=(1, None), height=dp(52), font_size="18sp",
                                     bold=True)
        self.save_btn.bind(on_release=self.save_and_start)
        root.add_widget(self.save_btn)

        self.add_widget(root)

    def on_pre_enter(self):
        d = App.get_running_app().data
        if d.get("daily_goal"):
            self.goal_slider.value = d["daily_goal"]
            self.goal_label.text = f"{d['daily_goal']} kcal"
        if d.get("start_weight"):
            self.weight_input.text = str(d["start_weight"])

    def on_goal_change(self, instance, value):
        self.goal_label.text = f"{int(value)} kcal"

    def set_goal(self, val):
        self.goal_slider.value = val

    def save_and_start(self, *args):
        app = App.get_running_app()
        try:
            w = float(self.weight_input.text.replace(",", "."))
        except ValueError:
            w = app.data.get("start_weight") or 0
        app.data["daily_goal"] = int(self.goal_slider.value)
        app.data["start_weight"] = w
        save_data(app.data)
        app.sm.current = "main"


class DayRow(BoxLayout):
    def __init__(self, date_str, app, **kwargs):
        super().__init__(
            orientation="horizontal", size_hint=(1, None), height=dp(56),
            spacing=dp(8), padding=[dp(10), dp(4), dp(10), dp(4)], **kwargs
        )
        bg_rect(self, CARD_COLOR)
        self.date_str = date_str
        self.app = app

        try:
            d = datetime.strptime(date_str, "%Y-%m-%d")
            disp = d.strftime("%d.%m.%Y")
        except ValueError:
            disp = date_str

        self.add_widget(Label(text=disp, color=TEXT_COLOR, size_hint=(0.30, 1),
                               font_size="15sp"))

        existing = app.data["entries"].get(date_str)
        self.input = TextInput(
            text="" if existing is None else str(existing),
            hint_text="kcal", multiline=False, input_filter="int", font_size="16sp",
            size_hint=(0.30, 1), background_color=INPUT_COLOR,
            foreground_color=TEXT_COLOR, cursor_color=TEXT_COLOR,
            padding=[dp(10), dp(10), 0, 0],
        )
        self.input.bind(text=self.on_text_change)
        self.add_widget(self.input)

        self.diff_label = Label(text="", size_hint=(0.40, 1), font_size="15sp", bold=True)
        self.add_widget(self.diff_label)

        self.update_diff()

    def on_text_change(self, instance, value):
        if value.strip() == "":
            self.app.data["entries"][self.date_str] = None
        else:
            try:
                self.app.data["entries"][self.date_str] = int(value)
            except ValueError:
                pass
        save_data(self.app.data)
        self.update_diff()

    def update_diff(self):
        goal = self.app.data.get("daily_goal") or 0
        val = self.app.data["entries"].get(self.date_str)
        if val is None:
            self.diff_label.text = "-"
            self.diff_label.color = MUTED
            return
        diff = val - goal
        if diff > 0:
            self.diff_label.text = f"+{diff} fazla"
            self.diff_label.color = RED
        elif diff < 0:
            self.diff_label.text = f"-{abs(diff)} kaldı"
            self.diff_label.color = GREEN
        else:
            self.diff_label.text = "tam hedefte"
            self.diff_label.color = ACCENT


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))
        bg_rect(root, BG_COLOR)

        top = BoxLayout(size_hint=(1, None), height=dp(50), spacing=dp(8))
        self.goal_label = Label(text="", font_size="17sp", bold=True, color=ACCENT,
                                 halign="left", valign="middle")
        self.goal_label.bind(size=lambda i, v: setattr(i, "text_size", v))
        top.add_widget(self.goal_label)

        stats_btn = flat_button("İstatistikler", bg=CARD_COLOR,
                                 size_hint=(None, None), width=dp(122), height=dp(44))
        stats_btn.bind(on_release=lambda *a: self.goto("stats"))
        top.add_widget(stats_btn)

        settings_btn = flat_button("Ayarlar", bg=CARD_COLOR,
                                    size_hint=(None, None), width=dp(90), height=dp(44))
        settings_btn.bind(on_release=lambda *a: self.goto("setup"))
        top.add_widget(settings_btn)

        root.add_widget(top)

        add_btn = flat_button("+ Bugünü Ekle", bg=ACCENT, fg=(1, 1, 1, 1),
                               size_hint=(1, None), height=dp(48), bold=True)
        add_btn.bind(on_release=self.add_today)
        root.add_widget(add_btn)

        self.scroll = ScrollView(size_hint=(1, 1))
        self.list_layout = GridLayout(cols=1, spacing=dp(6), size_hint_y=None)
        self.list_layout.bind(minimum_height=self.list_layout.setter("height"))
        self.scroll.add_widget(self.list_layout)
        root.add_widget(self.scroll)

        self.add_widget(root)

    def goto(self, name):
        App.get_running_app().sm.current = name

    def on_pre_enter(self):
        app = App.get_running_app()
        self.goal_label.text = f"Günlük Hedef: {app.data.get('daily_goal', 0)} kcal"
        self.refresh_list()

    def add_today(self, *args):
        app = App.get_running_app()
        today = date.today().strftime("%Y-%m-%d")
        if today not in app.data["entries"]:
            app.data["entries"][today] = None
            save_data(app.data)
        self.refresh_list()

    def refresh_list(self):
        app = App.get_running_app()
        self.list_layout.clear_widgets()
        for d in sorted(app.data["entries"].keys(), reverse=True):
            self.list_layout.add_widget(DayRow(d, app))


class StatsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical", padding=dp(24), spacing=dp(16))
        bg_rect(root, BG_COLOR)

        back_btn = flat_button("< Geri", bg=CARD_COLOR,
                                size_hint=(None, None), width=dp(90), height=dp(40))
        back_btn.bind(on_release=lambda *a: setattr(App.get_running_app().sm, "current", "main"))
        root.add_widget(back_btn)

        root.add_widget(Label(text="İstatistikler", font_size="22sp", bold=True,
                               color=TEXT_COLOR, size_hint=(1, None), height=dp(40)))

        self.total_label = Label(text="", font_size="17sp", color=TEXT_COLOR,
                                  size_hint=(1, None), height=dp(36))
        root.add_widget(self.total_label)

        self.kg_label = Label(text="", font_size="26sp", bold=True, color=ACCENT,
                               size_hint=(1, None), height=dp(46))
        root.add_widget(self.kg_label)

        self.start_w_label = Label(text="", font_size="16sp", color=MUTED,
                                    size_hint=(1, None), height=dp(28))
        root.add_widget(self.start_w_label)

        self.current_w_label = Label(text="", font_size="26sp", bold=True, color=TEXT_COLOR,
                                      size_hint=(1, None), height=dp(50))
        root.add_widget(self.current_w_label)

        root.add_widget(BoxLayout())
        self.add_widget(root)

    def on_pre_enter(self):
        app = App.get_running_app()
        goal = app.data.get("daily_goal") or 0
        start_w = app.data.get("start_weight") or 0
        filled = {k: v for k, v in app.data["entries"].items() if v is not None}
        total_diff = sum(v - goal for v in filled.values())
        kg_change = total_diff / 7700.0

        sign = "+" if total_diff > 0 else ""
        self.total_label.text = f"Toplam Kalori Farkı: {sign}{total_diff} kcal ({len(filled)} gün)"

        kg_sign = "+" if kg_change > 0 else ""
        self.kg_label.text = f"{kg_sign}{kg_change:.2f} kg"

        self.start_w_label.text = f"Başlangıç Kilonuz: {start_w:.1f} kg"
        self.current_w_label.text = f"Güncel Toplam Kilonuz: {(start_w + kg_change):.1f} kg"


class KaloriApp(App):
    def build(self):
        Window.clearcolor = BG_COLOR
        self.data = load_data()
        self.sm = ScreenManager(transition=SlideTransition())
        self.sm.add_widget(SetupScreen(name="setup"))
        self.sm.add_widget(MainScreen(name="main"))
        self.sm.add_widget(StatsScreen(name="stats"))

        if self.data.get("daily_goal") and self.data.get("start_weight") is not None:
            self.sm.current = "main"
        else:
            self.sm.current = "setup"
        return self.sm


if __name__ == "__main__":
    KaloriApp().run()
