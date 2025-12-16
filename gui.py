import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass
from enum import Enum
from turtle import width
from PIL import ImageTk, Image
import os

from torch import fill


# ----------------------------
# Model
# ----------------------------

class PinMode(str, Enum):
    UNUSED =    "----"
    DIN =       "DIN"
    DOUT =      "DOUT"
    ADC =       "ADC"
    PWM =       "PWM"
    MOSI0 =     "SPI0 - MOSI"
    MISO0 =     "SPI0 - MISO"
    SCK0 =      "SPI0 - SCK"
    MOSI1 =     "SPI1 - MOSI"
    MISO1 =     "SPI1 - MISO"
    SCK1 =      "SPI1 - SCK"
    SDA0 =      "I2C0 - SDA"
    SCL0 =      "I2C0 - SCL"
    SDA1 =      "I2C1 - SDA"
    SCL1 =      "I2C1 - SCL"
    TX0 =       "UART0 - TX"
    RX0 =       "UART0 - RX"
    TX1 =       "UART1 - TX"
    RX1 =       "UART1 - RX"


@dataclass
class Pin:
    num: int
    alias: str = ""
    mode: PinMode = PinMode.UNUSED
    state: int = 0        # for DOUT: 0/1
    din: int = 0          # for DIN: 0/1 (reported)
    adc_v: float = 0.0    # for ADC: volts (reported)
    pud: str = "None"  # for DIN: up/down/none
    pwm_freq: float = 1000.0
    pwm_duty: float = 0.0
    servo_mode: bool = False
    pwm_freq: float = 1000.0  # Hz
    pwm_duty: float = 0.0  # percentage 0-100

class SPI0:
    mosi_pin: int | None = None
    miso_pin: int | None = None
    sck_pin: int | None = None
    csn_pin: int | None = None
spi0 = SPI0()

class SPI1:
    mosi_pin: int | None = None
    miso_pin: int | None = None
    sck_pin: int | None = None
    csn_pin: int | None = None
spi1 = SPI1()


#GPIO = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 26, 27, 28]
FUNCTIONS = ["DOUT", "DIN", "PWM", "SPI", "I2C", "UART"]
PIN_MODES = {   0:  [PinMode.UNUSED, PinMode.DOUT, PinMode.DIN, PinMode.PWM, PinMode.MISO0, PinMode.SDA0, PinMode.TX0],
                1:  [PinMode.UNUSED, PinMode.DOUT, PinMode.DIN, PinMode.PWM, PinMode.SCL0, PinMode.RX0],
                2:  [PinMode.UNUSED, PinMode.DOUT, PinMode.DIN, PinMode.PWM, PinMode.SCK0,  PinMode.SDA1],
                3:  [PinMode.UNUSED, PinMode.DOUT, PinMode.DIN, PinMode.PWM, PinMode.MOSI0, PinMode.SCL1],
                4:  [PinMode.UNUSED, PinMode.DOUT, PinMode.DIN, PinMode.PWM, PinMode.MISO0, PinMode.SDA0, PinMode.TX1],
                5:  [PinMode.UNUSED, PinMode.DOUT, PinMode.DIN, PinMode.PWM, PinMode.SCL0, PinMode.RX1],
                6:  [PinMode.UNUSED, PinMode.DOUT, PinMode.DIN, PinMode.PWM, PinMode.SCK0,  PinMode.SDA1],
                7:  [PinMode.UNUSED, PinMode.DOUT, PinMode.DIN, PinMode.PWM, PinMode.MOSI0, PinMode.SCL1],
                8:  [PinMode.UNUSED, PinMode.DOUT, PinMode.DIN, PinMode.PWM, PinMode.MISO1, PinMode.SDA0, PinMode.TX1],
                9:  [PinMode.UNUSED, PinMode.DOUT, PinMode.DIN, PinMode.PWM, PinMode.SCL0, PinMode.RX1],
                10: [PinMode.UNUSED, PinMode.DOUT, PinMode.DIN, PinMode.PWM, PinMode.SCK1,  PinMode.SDA1],
                11: [PinMode.UNUSED, PinMode.DOUT, PinMode.DIN, PinMode.PWM, PinMode.MOSI1, PinMode.SCL1],
                12: [PinMode.UNUSED, PinMode.DOUT, PinMode.DIN, PinMode.PWM, PinMode.MISO1, PinMode.SDA0, PinMode.TX0],
                13: [PinMode.UNUSED, PinMode.DOUT, PinMode.DIN, PinMode.PWM, PinMode.SCL0, PinMode.RX0],
                14: [PinMode.UNUSED, PinMode.DOUT, PinMode.DIN, PinMode.PWM, PinMode.SCK1,  PinMode.SDA1],
                15: [PinMode.UNUSED, PinMode.DOUT, PinMode.DIN, PinMode.PWM, PinMode.MOSI1, PinMode.SCL1],
                16: [PinMode.UNUSED, PinMode.DOUT, PinMode.DIN, PinMode.PWM, PinMode.MISO0, PinMode.SDA0, PinMode.TX0],
                17: [PinMode.UNUSED, PinMode.DOUT, PinMode.DIN, PinMode.PWM, PinMode.SCL0, PinMode.RX0],
                18: [PinMode.UNUSED, PinMode.DOUT, PinMode.DIN, PinMode.PWM, PinMode.SCK0,  PinMode.SDA1],
                19: [PinMode.UNUSED, PinMode.DOUT, PinMode.DIN, PinMode.PWM, PinMode.MOSI0, PinMode.SCL1],
                20: [PinMode.UNUSED, PinMode.DOUT, PinMode.DIN, PinMode.PWM, PinMode.MISO0, PinMode.SDA0],
                21: [PinMode.UNUSED, PinMode.DOUT, PinMode.DIN, PinMode.PWM, PinMode.SCL0],
                22: [PinMode.UNUSED, PinMode.DOUT, PinMode.DIN, PinMode.PWM],
                26: [PinMode.UNUSED, PinMode.DOUT, PinMode.DIN, PinMode.PWM, PinMode.ADC],
                27: [PinMode.UNUSED, PinMode.DOUT, PinMode.DIN, PinMode.PWM, PinMode.ADC],
                28: [PinMode.UNUSED, PinMode.DOUT, PinMode.DIN, PinMode.PWM, PinMode.ADC]}

# Compute a fixed character width for mode dropdowns so they align nicely
MODE_MENU_WIDTH = max(len(m.value) for modes in PIN_MODES.values() for m in modes) + 1


# ----------------------------
# Scrollable frame helper
# ----------------------------

class ScrollableFrame(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.content = ttk.Frame(self.canvas)
        self.window_id = self.canvas.create_window((0, 0), window=self.content, anchor="nw")

        self.content.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Make scrolling work from anywhere inside this widget (incl. children)
        self.bind("<Enter>", self._bind_mousewheel)
        self.bind("<Leave>", self._unbind_mousewheel)

        # Ensure enter/leave triggers even when moving over children
        for w in (self, self.canvas, self.content):
            w.bind("<Enter>", self._bind_mousewheel, add="+")
            w.bind("<Leave>", self._unbind_mousewheel, add="+")

    # -------- layout helpers --------

    def _on_frame_configure(self, _event=None):
        bbox = self.canvas.bbox("all") or (0, 0, 0, 0)
        x0, y0, x1, y1 = bbox
        self.canvas.configure(scrollregion=(0, 0, x1, y1))
        self._clamp_yview()

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self.window_id, width=event.width)
        self._clamp_yview()

    def _clamp_yview(self):
        first, last = self.canvas.yview()
        page = last - first

        if page >= 1.0:
            self.canvas.yview_moveto(0.0)
            return

        if first < 0.0:
            self.canvas.yview_moveto(0.0)
        elif last > 1.0:
            self.canvas.yview_moveto(max(0.0, 1.0 - page))

    # -------- mousewheel binding --------

    def _bind_mousewheel(self, _event=None):
        # Windows/macOS
        self.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
        # Linux
        self.bind_all("<Button-4>", self._on_mousewheel_linux, add="+")
        self.bind_all("<Button-5>", self._on_mousewheel_linux, add="+")

    def _unbind_mousewheel(self, _event=None):
        # Remove only our bindings
        self.unbind_all("<MouseWheel>")
        self.unbind_all("<Button-4>")
        self.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        # Only scroll if the pointer is currently inside *this* ScrollableFrame
        widget = self.winfo_containing(event.x_root, event.y_root)
        if widget is None:
            return
        # If pointer isn't inside this frame, ignore (prevents left/right fighting)
        if not str(widget).startswith(str(self)):
            return

        delta = event.delta
        if delta == 0:
            return
        steps = int(-1 * (delta / 120)) if abs(delta) >= 120 else (-1 if delta > 0 else 1)

        self.canvas.yview_scroll(steps, "units")
        self._clamp_yview()

    def _on_mousewheel_linux(self, event):
        widget = self.winfo_containing(event.x_root, event.y_root)
        if widget is None:
            return
        if not str(widget).startswith(str(self)):
            return

        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        self._clamp_yview()




# ----------------------------
# App
# ----------------------------

class PicoGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Pico GPIO Control")
        self.geometry("1150x650")

        # state: pin number -> Pin
        self.pins = {n: Pin(num=n) for n in PIN_MODES.keys()}

        # per-pin UI refs
        self.pin_mode_var = {}   # pin -> StringVar
        self.pin_value_var = {}  # pin -> StringVar (readout display)
        self.pin_dout_btn = {}        # pin -> Button
        self.pin_din_indicator = {}   # pin -> Label
        self.pin_din_pud_menu = {}      # pin -> OptionMenu
        self.pin_din_pud_var = {}      # pin -> StringVar for PUD OptionMenu
        self.pin_alias_var = {}  # pin -> StringVar (alias text input)
        self.pin_pwm_freq_var = {}  # pin -> StringVar (PWM freq input)
        self.pin_pwm_duty_var = {}  # pin -> StringVar (PWM duty input)

        # per-pin servo var storage
        self.pin_servo_var = {}  # pin -> IntVar for servo checkbox

        self.pin_slider_widget = {}  # pin -> Scale widget (PWM duty/servo angle)
        self.pin_slider_label = {}  # pin -> Label widget for slider value

        # SPI0 selections and config
        self.spi0_mosi_selected = None
        self.spi0_miso_selected = None
        self.spi0_sck_selected = None
        self.spi0_csn = None
        self.spi0_config = {"mosi": None, "miso": None, "sck": None, "csn": None}

        self._build_layout()
        self.refresh_function_boxes()

        # demo: set a few initial modes
        self.set_pin_mode(0, PinMode.DOUT)
        self.set_pin_mode(26, PinMode.ADC)
        self.set_pin_mode(1, PinMode.PWM)
        self.update_gpio_readout(26, adc_v=1.234)
        self.update_din(12, 1)

    # ---------- layout ----------

    def _build_layout(self):
        self.columnconfigure(0, weight=0)  # left fixed width
        self.columnconfigure(1, weight=1)  # right expand
        self.rowconfigure(0, weight=1)

        # Left fixed pane container (doesn't scroll as a whole; only its internal list scrolls)
        left = ttk.Frame(self, padding=8)
        left.grid(row=0, column=0, sticky="nsw")
        left.configure(width=400)
        left.grid_propagate(False)

        ttk.Label(left, text="GPIO Configuration", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=(16, 0))

        # Scrollable list of GPIO rows
        self.left_scroll = ScrollableFrame(left)
        self.left_scroll.pack(fill="both", expand=True, pady=(8, 0), padx=(32, 0))

        # Build GPIO rows
        for pin in PIN_MODES.keys():
            self._add_gpio_row(self.left_scroll.content, pin)

        # Right pane (scrollable function boxes)
        right = ttk.Frame(self, padding=8)
        right.grid(row=0, column=1, sticky="nsew")

        ttk.Label(right, text="Functions", font=("Segoe UI", 12, "bold")).pack(anchor="w")

        self.right_scroll = ScrollableFrame(right)
        self.right_scroll.pack(fill="both", expand=True, pady=(8, 0))

        # container for function boxes
        self.fn_container = ttk.Frame(self.right_scroll.content)
        self.fn_container.pack(fill="both", expand=True)


    def _add_gpio_row(self, parent, pin: int):
        row = ttk.Frame(parent, padding=(0, 2))
        row.pack(fill="x")

        # GP label
        ttk.Label(row, text=f"GP{pin}", width=6).pack(side="left")

        # Alias text input
        alias_var = tk.StringVar(value=self.pins[pin].alias)
        self.pin_alias_var[pin] = alias_var

        alias = tk.Entry(row, width=8, textvariable=alias_var)
        alias.pack(side="left", padx=(0,8))

        # Commit alias on Enter or when focus leaves the field. When Enter is pressed
        # move focus away so the entry loses the text cursor.
        alias.bind("<Return>", lambda e, p=pin: self.on_alias_changed(p, e))
        alias.bind("<FocusOut>", lambda e, p=pin: self.on_alias_changed(p))

        # Mode dropdown
        mode_var = tk.StringVar(value=self.pins[pin].mode.value)
        self.pin_mode_var[pin] = mode_var

        mode_menu = ttk.OptionMenu(
            row,
            mode_var,
            mode_var.get(),
            *[m.value for m in PIN_MODES[pin]],
            command=lambda _val, p=pin: self.on_mode_changed(p),
        )
        # force a fixed character width so all dropdowns line up
        mode_menu.config(width=MODE_MENU_WIDTH)
        mode_menu.pack(side="left", padx=(6, 6))

    # ---------- logic / UI updates ----------

    def on_mode_changed(self, pin: int):
        mode = PinMode(self.pin_mode_var[pin].get())
        self.set_pin_mode(pin, mode)
        self.refresh_function_boxes()


    def on_alias_changed(self, pin: int, event=None):
        """Called when the user presses Enter or leaves the alias entry.

        If `event` is provided (e.g. Enter key), move focus away from the
        Entry so the text cursor is removed.
        """
        new_alias = self.pin_alias_var[pin].get().strip()
        self.pins[pin].alias = new_alias

        # If triggered via Enter, move focus to the main window to remove cursor
        if event is not None:
            try:
                # move focus to root window
                self.focus_set()
            except Exception:
                pass
        
        self.refresh_function_boxes()

    def set_pin_mode(self, pin: int, mode: PinMode):
        self.pins[pin].mode = mode
        self.pin_mode_var[pin].set(mode.value)

        
        #self.handle_DOUT_change(pin, self.pins[pin].state, mode)
        #self.handle_DIN_change(pin, self.pins[pin].din, mode)
        
    
    def handle_DOUT_change(self, pin: int, state: int, mode: PinMode):
        # enable/disable toggle button based on mode
        if mode == PinMode.DOUT:
            #self.pin_dout_btn[pin].config(state="normal")
            # add an on/off button to the row
            if pin not in self.pin_dout_btn:
                row = self.left_scroll.content.winfo_children()[pin]
                btn = tk.Button(
                    row,
                    text="OFF",
                    relief="raised",
                    command=lambda p=pin: self.toggle_pin(p),
                    bg="#333333",
                    fg="white",
                    activebackground="#444444",
                    activeforeground="white",
                )
                btn.pack(side="left", expand=True, fill="x")
                self.pin_dout_btn[pin] = btn
                self.pins[pin].state = 0
                self._render_toggle(pin)
            else:
                self.pin_dout_btn[pin].config(state="normal")

        else:
            # remove the on/off button if it exists
            if pin in self.pin_dout_btn:
                self.pin_dout_btn[pin].destroy()
                del self.pin_dout_btn[pin]

    def handle_DIN_change(self, pin: int, din: int, mode: PinMode):
        if mode == PinMode.DIN:
            if pin not in self.pin_din_indicator:
                # add a color indicator for DIN
                row = self.left_scroll.content.winfo_children()[pin]
                label = tk.Label(
                    row,
                    bg="#333333" if self.pins[pin].din == 0 else "#00aa00",
                )
                label.pack(side="left", expand=True, fill="x")
                self.pin_din_indicator[pin] = label

                # add a dropdown for pull-up/down/none
                pud = ttk.OptionMenu(
                    row,
                    tk.StringVar(value="None"),
                    "None",
                    *["None", "Pull-Up", "Pull-Down"],
                    command=lambda _val, p=pin: self.on_pud_changed(p)
                )
                pud.config(width=8)
                pud.pack(side="left", padx=(6, 0))
                self.pin_din_pud_menu[pin] = pud

        else:
            # remove the DIN indicator if it exists
            #row = self.left_scroll.content.winfo_children()[pin]
            if pin in self.pin_din_indicator:
                self.pin_din_indicator[pin].destroy()
                del self.pin_din_indicator[pin]
            if pin in self.pin_din_pud_menu:
                self.pin_din_pud_menu[pin].destroy()
                del self.pin_din_pud_menu[pin]

        

    def _render_readout(self, pin: int):
        p = self.pins[pin]
        if p.mode == PinMode.DOUT:
            self.pin_value_var[pin].set("HIGH" if p.state else "LOW")
        elif p.mode == PinMode.DIN:
            self.pin_value_var[pin].set("HIGH" if p.din else "LOW")
        elif p.mode == PinMode.ADC:
            self.pin_value_var[pin].set(f"{p.adc_v:.3f} V")
        else:
            self.pin_value_var[pin].set("—")

    def update_gpio_readout(self, pin: int, din: int | None = None, adc_v: float | None = None):
        """Call this from your polling loop when you read the Pico."""
        if din is not None:
            self.pins[pin].din = 1 if din else 0
        if adc_v is not None:
            self.pins[pin].adc_v = float(adc_v)
        #self._render_readout(pin)
    
    def update_din(self, pin: int, din: int):
        """Update the DIN value and refresh the indicator."""
        self.pins[pin].din = 1 if din else 0
        if pin in self.pin_din_indicator:
            self.pin_din_indicator[pin].config(
                bg="#333333" if self.pins[pin].din == 0 else "#00aa00"
            )

    # ---------- right pane: function boxes ----------

    def refresh_function_boxes(self):
        # clear old boxes
        for child in self.fn_container.winfo_children():
            child.destroy()

        # group pins by function-ish mode
        groups = {
            "DOUT": [p.num for p in self.pins.values() if p.mode == PinMode.DOUT],
            "DIN": [p.num for p in self.pins.values() if p.mode == PinMode.DIN],
            "PWM": [p.num for p in self.pins.values() if p.mode == PinMode.PWM],
            "SPI0": [p.num for p in self.pins.values() if p.mode in (PinMode.MOSI0, PinMode.MISO0, PinMode.SCK0)],
            "SPI1": [p.num for p in self.pins.values() if p.mode in (PinMode.MOSI1, PinMode.MISO1, PinMode.SCK1)],
            "I2C": [], #[p.num for p in self.pins.values() if p.mode == PinMode.I2C],
            "UART": [], #[p.num for p in self.pins.values() if p.mode == PinMode.UART],
        }

        #for title in FUNCTIONS:
        #    pins = sorted(groups[title])
        #    self._add_function_box(self.fn_container, title, pins)
        self.update_DOUT(sorted(groups["DOUT"]))
        self.update_DIN(sorted(groups["DIN"]))
        self.update_PWM(sorted(groups["PWM"]))
        self.update_SPI(groups["SPI0"], groups["SPI1"])


    def update_DOUT(self, pins: list[int]):
        box = ttk.LabelFrame(self.fn_container, text="DOUT", padding=8)
        box.pack(fill="x", pady=8)

        if not pins:
            ttk.Label(box, text="No pins assigned.").pack(anchor="w")
            return

        for pin in pins:
            row = ttk.Frame(box)
            row.pack(fill="x", pady=2)

            # Display alias truncated to 8 chars and padded so it doesn't push controls
            display_alias = (self.pins[pin].alias[:10]).ljust(10)
            ttk.Label(row, text=f"GP{pin}  -  {display_alias}", width=20, anchor="w").pack(side="left", padx=(16, 0))

            btn = tk.Button(
                row,
                text=("ON" if self.pins[pin].state == 1 else "OFF"),
                relief="raised",
                command=lambda p=pin: self.toggle_pin(p),
                bg="#333333" if self.pins[pin].state == 0 else "#00aa00",
                fg="white" if self.pins[pin].state == 0 else "black",
                activebackground="#444444" if self.pins[pin].state == 0 else "#22cc22",
                activeforeground="white" if self.pins[pin].state == 0 else "black",
                width=20,
            )
            btn.pack(side="left", padx=(2, 0))
            self.pin_dout_btn[pin] = btn
    
    def toggle_pin(self, pin: int):
        # only meaningful for DOUT
        if self.pins[pin].mode != PinMode.DOUT:
            return

        self.pins[pin].state ^= 1

        is_on = self.pins[pin].state == 1
        if is_on:
            self.pin_dout_btn[pin].config(text="ON", bg="#00aa00", fg="black",
                                     activebackground="#22cc22", activeforeground="black")
        else:
            self.pin_dout_btn[pin].config(text="OFF", bg="#333333", fg="white",
                                     activebackground="#444444", activeforeground="white")

    def update_DIN(self, pins: list[int]):
        box = ttk.LabelFrame(self.fn_container, text="DIN", padding=8)
        box.pack(fill="x", pady=8)

        if not pins:
            ttk.Label(box, text="No pins assigned.").pack(anchor="w")
            return

        for pin in pins:
            row = ttk.Frame(box)
            row.pack(fill="x", pady=2)

            # Display alias truncated to 8 chars and padded so it doesn't push controls
            display_alias = (self.pins[pin].alias[:10]).ljust(10)
            ttk.Label(row, text=f"GP{pin}  -  {display_alias}", width=20, anchor="w").pack(side="left", padx=(16, 0))

            label = tk.Label(
                row,
                bg="#333333" if self.pins[pin].din == 0 else "#00aa00",
                width=20,
            )
            label.pack(side="left", padx=(2, 0))
            self.pin_din_indicator[pin] = label

            # add a dropdown for pull-up/down/none
            pud_var = tk.StringVar(value=self.pins[pin].pud)
            pud = ttk.OptionMenu(
                row,
                pud_var,
                pud_var.get(),
                "None",
                "Pull-Up",
                "Pull-Down",
                command=lambda _val, p=pin: self.on_pud_changed(p, _val)
            )
            pud.config(width=8)
            pud.pack(side="left", padx=(6, 0))
            self.pin_din_pud_menu[pin] = pud
            self.pin_din_pud_var[pin] = pud_var
    
    def on_pud_changed(self, pin: int, pud_value: str):
        self.pins[pin].pud = pud_value
        # keep the displayed variable in sync if we have it
        if pin in self.pin_din_pud_var:
            try:
                self.pin_din_pud_var[pin].set(pud_value)
            except Exception:
                pass
        print(f"Pin {pin} PUD changed to {self.pins[pin].pud}")

    def on_spi0_mosi_selected(self, val: str):
        """Handle MOSI selection: store which MOSI pin is active. Does not change pin modes.
        `val` is either the string '----' or 'GP<n>' matching one of the options.
        """
        if val == PinMode.UNUSED.value or val == "----":
            # clear selection (do not modify pin modes)
            self.spi0_mosi_selected = None
            self.spi0_config['mosi'] = None
            if hasattr(self, "spi0_mosi_var"):
                try:
                    self.spi0_mosi_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            try:
                self.refresh_function_boxes()
            except Exception:
                pass
            print("SPI0 MOSI selection cleared")
            return

        pin_str = str(val)
        if pin_str.startswith("GP"):
            pin_str = pin_str[2:]
        try:
            pin = int(pin_str)
        except Exception:
            return

        # Only allow selecting a pin that is currently configured as MOSI0
        if self.pins.get(pin) and self.pins[pin].mode == PinMode.MOSI0:
            self.spi0_mosi_selected = pin
            self.spi0_config['mosi'] = pin
            if hasattr(self, "spi0_mosi_var"):
                try:
                    self.spi0_mosi_var.set(f"GP{pin}")
                except Exception:
                    pass
            try:
                self.refresh_function_boxes()
            except Exception:
                pass
            print(f"SPI0 MOSI selected: GP{pin}")
        else:
            # invalid selection (shouldn't happen with filtered options) - clear
            self.spi0_mosi_selected = None
            self.spi0_config['mosi'] = None
            if hasattr(self, "spi0_mosi_var"):
                try:
                    self.spi0_mosi_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            print(f"SPI0 MOSI selection invalid for {val}")

    def on_spi0_miso_selected(self, val: str):
        """Select MISO pin for SPI0 (only pins currently in MISO0 appear in menu)."""
        if val == PinMode.UNUSED.value or val == "----":
            self.spi0_miso_selected = None
            self.spi0_config['miso'] = None
            if hasattr(self, "spi0_miso_var"):
                try:
                    self.spi0_miso_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            try:
                self.refresh_function_boxes()
            except Exception:
                pass
            print("SPI0 MISO selection cleared")
            return
        pin_str = str(val)
        if pin_str.startswith("GP"):
            pin_str = pin_str[2:]
        try:
            pin = int(pin_str)
        except Exception:
            return
        if self.pins.get(pin) and self.pins[pin].mode == PinMode.MISO0:
            self.spi0_miso_selected = pin
            self.spi0_config['miso'] = pin
            if hasattr(self, "spi0_miso_var"):
                try:
                    self.spi0_miso_var.set(f"GP{pin}")
                except Exception:
                    pass
            try:
                self.refresh_function_boxes()
            except Exception:
                pass
            print(f"SPI0 MISO selected: GP{pin}")
        else:
            self.spi0_miso_selected = None
            self.spi0_config['miso'] = None
            if hasattr(self, "spi0_miso_var"):
                try:
                    self.spi0_miso_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            print(f"SPI0 MISO selection invalid for {val}")

    def on_spi0_sck_selected(self, val: str):
        """Select SCK pin for SPI0 (only pins currently in SCK0 appear in menu)."""
        if val == PinMode.UNUSED.value or val == "----":
            self.spi0_sck_selected = None
            self.spi0_config['sck'] = None
            if hasattr(self, "spi0_sck_var"):
                try:
                    self.spi0_sck_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            try:
                self.refresh_function_boxes()
            except Exception:
                pass
            print("SPI0 SCK selection cleared")
            return
        pin_str = str(val)
        if pin_str.startswith("GP"):
            pin_str = pin_str[2:]
        try:
            pin = int(pin_str)
        except Exception:
            return
        if self.pins.get(pin) and self.pins[pin].mode == PinMode.SCK0:
            self.spi0_sck_selected = pin
            self.spi0_config['sck'] = pin
            if hasattr(self, "spi0_sck_var"):
                try:
                    self.spi0_sck_var.set(f"GP{pin}")
                except Exception:
                    pass
            try:
                self.refresh_function_boxes()
            except Exception:
                pass
            print(f"SPI0 SCK selected: GP{pin}")
        else:
            self.spi0_sck_selected = None
            self.spi0_config['sck'] = None
            if hasattr(self, "spi0_sck_var"):
                try:
                    self.spi0_sck_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            print(f"SPI0 SCK selection invalid for {val}")

    def on_spi0_csn_selected(self, val: str):
        """Select CSn pin for SPI0 (only pins currently in DOUT appear in menu)."""
        if val == PinMode.UNUSED.value or val == "----":
            self.spi0_csn = None
            self.spi0_config['csn'] = None
            if hasattr(self, "spi0_csn_var"):
                try:
                    self.spi0_csn_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            print("SPI0 CSn selection cleared")
            return
        pin_str = str(val)
        if pin_str.startswith("GP"):
            pin_str = pin_str[2:]
        try:
            pin = int(pin_str)
        except Exception:
            return
        # ensure it's DOUT
        if self.pins.get(pin) and self.pins[pin].mode == PinMode.DOUT:
            self.spi0_csn = pin
            self.spi0_config['csn'] = pin
            if hasattr(self, "spi0_csn_var"):
                try:
                    self.spi0_csn_var.set(f"GP{pin}")
                except Exception:
                    pass
            print(f"SPI0 CSn set to pin {pin}")
        else:
            self.spi0_csn = None
            self.spi0_config['csn'] = None
            if hasattr(self, "spi0_csn_var"):
                try:
                    self.spi0_csn_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            print(f"SPI0 CSn selection invalid (pin {val} not DOUT)")

    def update_PWM(self, pins: list[int]):
        box = ttk.LabelFrame(self.fn_container, text="PWM", padding=8)
        box.pack(fill="x", pady=8)

        if not pins:
            ttk.Label(box, text="No pins assigned.").pack(anchor="w")
            return

        for pin in pins:
            row = ttk.Frame(box)
            row.pack(fill="x", pady=2)

            # Display alias truncated to 8 chars and padded so it doesn't push controls
            display_alias = (self.pins[pin].alias[:10]).ljust(10)
            ttk.Label(row, text=f"GP{pin}  -  {display_alias}", width=20, anchor="w").pack(side="left", padx=(16, 0))

            freq_var = tk.StringVar(value=self.pins[pin].pwm_freq)
            duty_var = tk.StringVar(value=self.pins[pin].pwm_duty)

            ttk.Label(row, text="Freq [Hz]:").pack(side="left", padx=(2, 0))
            freq_entry = tk.Entry(row, width=8, textvariable=freq_var)
            freq_entry.pack(side="left", padx=(2, 10))
            ttk.Label(row, text="Duty Cycle [%]:").pack(side="left", padx=(2, 0))
            duty_entry = tk.Entry(row, width=6, textvariable=duty_var)
            duty_entry.pack(side="left", padx=(2, 0))

            self.pin_pwm_freq_var[pin] = freq_var
            self.pin_pwm_duty_var[pin] = duty_var

            freq_entry.bind("<Return>", lambda e, p=pin: self.update_pwm_freq(p, float(freq_var.get())))
            freq_entry.bind("<FocusOut>", lambda e, p=pin: self.update_pwm_freq(p, float(freq_var.get())))

            duty_entry.bind("<Return>", lambda e, p=pin: self.update_pwm_duty(p, float(duty_var.get())))
            duty_entry.bind("<FocusOut>", lambda e, p=pin: self.update_pwm_duty(p, float(duty_var.get())))

            # add checkbox for servo mode
            # add checkbox for servo mode (initialized from model)
            servo_var = tk.IntVar(value=1 if self.pins[pin].servo_mode else 0)
            servo_check = ttk.Checkbutton(row, text="Servo", variable=servo_var,
                                          command=lambda p=pin, v=servo_var: self.update_servo_mode(p, bool(v.get())))
            servo_check.pack(side="left", padx=(10, 0))
            self.pin_servo_var[pin] = servo_var

            # add slider underneath
            slider = ttk.Scale(row, from_=0, to=100, orient="horizontal", command=lambda val, p=pin: self.update_duty_slider(p, float(val)))
            # set initial slider position based on model
            if self.pins[pin].servo_mode:
                # map pwm_duty (5-10%) to slider 0-100
                initial = (self.pins[pin].pwm_duty - 5.0) * 20.0
            else:
                initial = self.pins[pin].pwm_duty
            slider.set(initial)
            slider.pack(fill="x", padx=(16, 16), pady=(4, 0), side="left")
            self.pin_slider_widget[pin] = slider

            # add label to print duty cycle value or angle
            value_label = ttk.Label(row, text="0")
            if self.pins[pin].servo_mode:
                angle = (self.pins[pin].pwm_duty - 5.0) / 5.0 * 180.0
                value_label.config(text=f"{angle:.1f}°")
            else:
                value_label.config(text=f"{self.pins[pin].pwm_duty:.1f}%")
            value_label.pack(side="left", padx=(0, 0))
            self.pin_slider_label[pin] = value_label

    def update_pwm_freq(self, pin: int, freq: float):
        self.pins[pin].pwm_freq = freq
        print(f"Pin {pin} PWM frequency set to {freq} Hz")
    
    def update_pwm_duty(self, pin: int, duty: float):
        # If servo mode is enabled, clamp duty to servo-safe range (5-10%)
        if self.pins[pin].servo_mode:
            clamped = max(5.0, min(10.0, duty))
            self.pins[pin].pwm_duty = clamped
            angle = (clamped - 5.0) / 5.0 * 180.0
            # update slider position (map angle to 0-100)
            if pin in self.pin_slider_widget:
                try:
                    self.pin_slider_widget[pin].set((angle / 180) * 100)
                except Exception:
                    pass
            if pin in self.pin_slider_label:
                self.pin_slider_label[pin].config(text=f"{angle:.1f}°")
            # update duty entry to show clamped value
            if pin in self.pin_pwm_duty_var:
                try:
                    self.pin_pwm_duty_var[pin].set(round(clamped, 2))
                except Exception:
                    pass
            print(f"Pin {pin} Servo angle set to {angle:.1f} degrees (duty: {clamped:.2f}%)")
        else:
            self.pins[pin].pwm_duty = duty
            if pin in self.pin_slider_widget:
                try:
                    self.pin_slider_widget[pin].set(duty)
                except Exception:
                    pass
            if pin in self.pin_slider_label:
                self.pin_slider_label[pin].config(text=f"{duty:.1f}%")
        print(f"Pin {pin} PWM duty cycle set to {self.pins[pin].pwm_duty:.1f} %")
    
    def update_servo_mode(self, pin: int, enabled: bool):
        # store per-pin servo mode
        self.pins[pin].servo_mode = enabled
        # keep the checkbox variable in sync if it exists
        if pin in self.pin_servo_var:
            try:
                self.pin_servo_var[pin].set(1 if enabled else 0)
            except Exception:
                pass

        if enabled:
            self.pins[pin].pwm_freq = 50.0  # typical servo frequency
            self.pins[pin].pwm_duty = 7.5   # neutral position
            if pin in self.pin_pwm_freq_var:
                self.pin_pwm_freq_var[pin].set(50.0)
            if pin in self.pin_pwm_duty_var:
                self.pin_pwm_duty_var[pin].set(7.5)
            # update the slider position to match neutral
            if pin in self.pin_slider_widget:
                try:
                    self.pin_slider_widget[pin].set(50.0)  # 50% corresponds to 90 degrees
                except Exception:
                    pass
            if pin in self.pin_slider_label:
                try:
                    self.pin_slider_label[pin].config(text="90.0°")
                except Exception:
                    pass
        print(f"Pin {pin} Servo mode set to {enabled}")
    
    def update_duty_slider(self, pin, value):
        if self.pins[pin].servo_mode:
            angle = (value / 100) * 180  # map 0-100 to 0-180 degrees
            # update the value label
            if pin in self.pin_slider_label:
                try:
                    self.pin_slider_label[pin].config(text=f"{angle:.1f}°")
                except Exception:
                    pass
            self.pins[pin].pwm_duty = 5.0 + (angle / 180) * 5.0  # map to duty cycle
            if pin in self.pin_pwm_duty_var:
                try:
                    self.pin_pwm_duty_var[pin].set(round(self.pins[pin].pwm_duty,2))
                except Exception:
                    pass
            print(f"Pin {pin} Servo angle set to {angle:.1f} degrees (duty: {self.pins[pin].pwm_duty:.2f}%)")
        else:
            if pin in self.pin_slider_label:
                try:
                    self.pin_slider_label[pin].config(text=f"{value:.1f}%")
                except Exception:
                    pass
            self.pins[pin].pwm_duty = value
            if pin in self.pin_pwm_duty_var:
                try:
                    self.pin_pwm_duty_var[pin].set(round(value,2))
                except Exception:
                    pass
            print(f"Pin {pin} PWM duty cycle set to {value:.1f}%")
    
    def update_SPI(self, spi0_pins: list[int], spi1_pins: list[int]):
        
        box = ttk.LabelFrame(self.fn_container, text="SPI", padding=8)
        box.pack(fill="x", pady=8)

        if not spi0_pins and not spi1_pins:
            ttk.Label(box, text="No pins assigned.").pack(anchor="w")
            return

        # create a sub-box for SPI0 (show MOSI selection only for pins currently set to MOSI0)
        # spi0_pins contains any pin participating in SPI0 (MOSI/MISO/SCK). We only want
        # options that are currently MODE == MOSI0 so selection is manual and explicit.
        if spi0_pins:
            spi0_box = ttk.LabelFrame(box, text="SPI0", padding=8)
            spi0_box.pack(fill="x", pady=4)

            # MOSI
            row = ttk.Frame(spi0_box)
            row.pack(fill="x", pady=2)

            ttk.Label(row, text="MOSI:", anchor="w").pack(side="left", padx=(8, 8))

            # options: default '----' plus GP<n> for pins currently configured as MOSI0
            mosi_options = [PinMode.UNUSED.value] + [f"GP{p}" for p in spi0_pins if self.pins[p].mode == PinMode.MOSI0]

            # determine current selection: keep previous explicit selection if valid, otherwise '----'
            current_sel = PinMode.UNUSED.value
            if hasattr(self, 'spi0_mosi_selected') and self.spi0_mosi_selected is not None:
                sel_str = f"GP{self.spi0_mosi_selected}"
                if sel_str in mosi_options:
                    current_sel = sel_str
                else:
                    # previously selected pin is no longer valid
                    self.spi0_mosi_selected = None
                    self.spi0_config['mosi'] = None
            # otherwise leave as '----' (user must manually choose)

            self.spi0_mosi_var = tk.StringVar(value=current_sel)
            mosi_menu = ttk.OptionMenu(row, self.spi0_mosi_var, self.spi0_mosi_var.get(), *mosi_options, command=lambda _val: self.on_spi0_mosi_selected(_val))
            mosi_menu.config(width=6)
            mosi_menu.pack(side="left", padx=(6, 6))

            # MISO (only pins currently set to MISO0)
            ttk.Label(row, text="MISO:", anchor="w").pack(side="left", padx=(8, 8))
            miso_options = [PinMode.UNUSED.value] + [f"GP{p}" for p in spi0_pins if self.pins[p].mode == PinMode.MISO0]
            miso_sel = PinMode.UNUSED.value
            if hasattr(self, 'spi0_miso_selected') and self.spi0_miso_selected is not None:
                sel_str = f"GP{self.spi0_miso_selected}"
                if sel_str in miso_options:
                    miso_sel = sel_str
                else:
                    self.spi0_miso_selected = None
                    self.spi0_config['miso'] = None
            self.spi0_miso_var = tk.StringVar(value=miso_sel)
            miso_menu = ttk.OptionMenu(row, self.spi0_miso_var, self.spi0_miso_var.get(), *miso_options, command=lambda _val: self.on_spi0_miso_selected(_val))
            miso_menu.config(width=6)
            miso_menu.pack(side="left", padx=(6, 6))

            # SCK (only pins currently set to SCK0)
            ttk.Label(row, text="SCK:", anchor="w").pack(side="left", padx=(8, 8))
            sck_options = [PinMode.UNUSED.value] + [f"GP{p}" for p in spi0_pins if self.pins[p].mode == PinMode.SCK0]
            sck_sel = PinMode.UNUSED.value
            if hasattr(self, 'spi0_sck_selected') and self.spi0_sck_selected is not None:
                sel_str = f"GP{self.spi0_sck_selected}"
                if sel_str in sck_options:
                    sck_sel = sel_str
                else:
                    self.spi0_sck_selected = None
                    self.spi0_config['sck'] = None
            self.spi0_sck_var = tk.StringVar(value=sck_sel)
            sck_menu = ttk.OptionMenu(row, self.spi0_sck_var, self.spi0_sck_var.get(), *sck_options, command=lambda _val: self.on_spi0_sck_selected(_val))
            sck_menu.config(width=6)
            sck_menu.pack(side="left", padx=(6, 6))

            # CSn (choose any pin currently in DOUT mode)
            ttk.Label(row, text="CSn:", anchor="w").pack(side="left", padx=(8, 8))
            csn_candidates = [p.num for p in self.pins.values() if p.mode == PinMode.DOUT]
            csn_options = [PinMode.UNUSED.value] + [f"GP{p}" for p in csn_candidates]
            csn_sel = PinMode.UNUSED.value
            if getattr(self, 'spi0_csn', None) is not None:
                sel_str = f"GP{self.spi0_csn}"
                if sel_str in csn_options:
                    csn_sel = sel_str
                else:
                    self.spi0_csn = None
                    self.spi0_config['csn'] = None
            self.spi0_csn_var = tk.StringVar(value=csn_sel)
            csn_menu = ttk.OptionMenu(row, self.spi0_csn_var, self.spi0_csn_var.get(), *csn_options, command=lambda _val: self.on_spi0_csn_selected(_val))
            csn_menu.config(width=6)
            csn_menu.pack(side="left", padx=(6, 6))

        # create a sub-box for SPI1
        if spi1_pins:
            spi1_box = ttk.LabelFrame(box, text="SPI1", padding=8)
            spi1_box.pack(fill="x", pady=4)

            for pin in spi1_pins:
                row = ttk.Frame(spi1_box)
                row.pack(fill="x", pady=2)

                ttk.Label(row, text=f"MOSI", width=20, anchor="w").pack(side="left", padx=(16, 0))

            

if __name__ == "__main__":
    app = PicoGUI()
    app.mainloop()
