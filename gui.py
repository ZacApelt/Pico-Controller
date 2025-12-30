import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass
from enum import Enum
from turtle import width
from PIL import ImageTk, Image
import os
from serial.tools import list_ports
import time
try:
    import serial
except Exception:
    serial = None


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
    adc_count: int = 0    # for ADC: counts (reported)
    pud: str = "None"  # for DIN: up/down/none
    pwm_freq: float = 1000.0
    pwm_duty: float = 0.0
    servo_mode: bool = False
    pwm_freq: float = 1000.0  # Hz
    pwm_duty: float = 0.0  # percentage 0-100

class SPI:
    mosi_pin: int | None = None
    miso_pin: int | None = None
    sck_pin: int | None = None
    csn_pin: int | None = None
    kilobits_per_second: int = 1000
    bytes_to_send = ""
    received_bytes = ""

spi0 = SPI()
spi1 = SPI()

class I2C:
    sda_pin: int | None = None
    scl_pin: int | None = None
    frequency_khz: int = 100
    bytes_to_send: list = []
    received_bytes: bytes = b""


i2c0 = I2C()
i2c1 = I2C()

class UART:
    tx_pin: int | None = None
    rx_pin: int | None = None
    baud: int = 115200
    bytes_to_send: list = []
    received_bytes: bytes = b""

uart0 = UART()
uart1 = UART()

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
                25: [PinMode.UNUSED, PinMode.DOUT, PinMode.DIN, PinMode.PWM],
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
        # per-pin ADC readout widgets
        self.pin_adc_count_label = {}  # pin -> Label (counts)
        self.pin_adc_volt_label = {}   # pin -> Label (voltage)

        # SPI0 selections and config
        self.spi0_mosi_selected = None
        self.spi0_miso_selected = None
        self.spi0_sck_selected = None
        self.spi0_csn = None
        self.spi0_config = {"mosi": None, "miso": None, "sck": None, "csn": None, "kbps": 1000, "send_hex": None, "received_bytes": None, "bytes_to_send": []}

        # SPI1 selections and config (mirrors SPI0 behaviour)
        self.spi1_mosi_selected = None
        self.spi1_miso_selected = None
        self.spi1_sck_selected = None
        self.spi1_csn = None
        self.spi1_config = {"mosi": None, "miso": None, "sck": None, "csn": None, "kbps": 1000, "send_hex": None, "received_bytes": None, "bytes_to_send": []}

        # I2C selections and config (I2C0 and I2C1)
        self.i2c0_sda_selected = None
        self.i2c0_scl_selected = None
        self.i2c0_config = {"sda": None, "scl": None, "khz": 100, "address": None, "send_hex": None, "received_bytes": None, "bytes_to_send": []}
        self.i2c0_scan_var = tk.StringVar(value="")

        self.i2c1_sda_selected = None
        self.i2c1_scl_selected = None
        self.i2c1_config = {"sda": None, "scl": None, "khz": 100, "address": None, "send_hex": None, "received_bytes": None, "bytes_to_send": []}
        self.i2c1_scan_var = tk.StringVar(value="")

        # UART selections and config (UART0 and UART1)
        self.uart0_tx_selected = None
        self.uart0_rx_selected = None
        self.uart0_config = {"tx": None, "rx": None, "baud": 115200, "send_text": None, "received_text": None, "bytes_to_send": []}

        self.uart1_tx_selected = None
        self.uart1_rx_selected = None
        self.uart1_config = {"tx": None, "rx": None, "baud": 115200, "send_text": None, "received_text": None, "bytes_to_send": []}

        # COM port state for serial device selection
        self.com_port_selected = None
        self.com_port_var = tk.StringVar(value="None")
        self.com_port_label_var = tk.StringVar(value="")
        self.com_ports = []
        # Serial instance (None when closed). Accessible as `self.ser` per request.
        self.ser = None
        self.com_baud_var = tk.StringVar(value="115200")

        # Refresh throttling: limit UI rebuilds to at most 20Hz (50 ms)
        self._min_refresh_interval = 1.0 / 20.0
        self._last_refresh_time = 0.0
        self._refresh_pending_id = None
        # Route calls through the request method to enforce throttling
        self.refresh_function_boxes = self.request_refresh_function_boxes

        self._build_layout()
        self.refresh_function_boxes()

        # demo: set a few initial modes
        #self.set_pin_mode(0, PinMode.DOUT)
        #self.set_pin_mode(26, PinMode.ADC)
        #self.set_pin_mode(1, PinMode.PWM)
        #self.set_ADC_value(26, 32768)

    # ---------- communication ----------
    def send_pin_parameter(self, pin, param, value):
        """Send a pin parameter update to the device.

        `param` is a string indicating the parameter to set, e.g. "mode", "dout", "pwm_freq", etc.
        `value` is the new value for the parameter.
        """
        print(f"\tsend: {pin},{param},{value}")
        
        if self.ser:
            data = f"{pin},{param},{value}\n"
            self.ser.write(data.encode())
            self.ser.flush()

    # call once after opening serial port:
    def start_serial_poll(self, interval_ms=20):
        self._serial_poll_interval = interval_ms
        if getattr(self, 'ser', None):
            self._poll_serial()

    def _poll_serial(self):
        ser = getattr(self, 'ser', None)
        if ser:
            try:
                n = ser.in_waiting
                if n:
                    data = ser.read(n)  # or ser.readline()
                    self._handle_serial_bytes(data)
            except Exception:
                pass
        # schedule next poll
        self.after(self._serial_poll_interval, self._poll_serial)

    def _handle_serial_bytes(self, data: bytes):
        # parse and update UI on main thread
        text = data.decode('utf-8', errors='replace').strip()
        print(f"the following was received:\n {text}\nend of received")
        
        lines = text.split('\n')
        for line in lines:
            print(f"line: \n{line}\ndone")
            line = line.strip()
            parts = line.split(',')
            pin = int(parts[0])
            param = parts[1]
            value = parts[2]

            print(line, parts)

            if param == "adc_value":
                self.set_ADC_value(pin, int(value))
            elif param == "din":
                self.set_DIN_value(pin, int(value))
            elif param == "spi0_recv":
                spi0.received_bytes = value
                print(f"should display {value}, {spi0.received_bytes}")
                self.on_spi0_receive_bytes()
            elif param == "spi1_recv":
                spi1.received_bytes = value
                self.on_spi1_receive_bytes()
            elif param == "uart0_recv":
                uart0.received_bytes = value
                self.on_uart0_receive()
            elif param == "uart1_recv":
                uart1.received_bytes = value
                self.on_uart1_receive()

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

        #ttk.Label(right, text="Functions", font=("Segoe UI", 12, "bold")).pack(anchor="w")

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

        #print(f"\tsend: Set GP{pin} mode to {mode.value}")
        self.send_pin_parameter(pin, "mode", mode.value)

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

    
    # ---------- right pane: function boxes ----------

    def refresh_function_boxes(self):
        # clear old boxes
        for child in self.fn_container.winfo_children():
            child.destroy()

        # group pins by function-ish mode
        groups = {
            "DOUT": [p.num for p in self.pins.values() if p.mode == PinMode.DOUT],
            "DIN": [p.num for p in self.pins.values() if p.mode == PinMode.DIN],
            "ADC": [p.num for p in self.pins.values() if p.mode == PinMode.ADC],
            "PWM": [p.num for p in self.pins.values() if p.mode == PinMode.PWM],
            "SPI0": [p.num for p in self.pins.values() if p.mode in (PinMode.MOSI0, PinMode.MISO0, PinMode.SCK0)],
            "SPI1": [p.num for p in self.pins.values() if p.mode in (PinMode.MOSI1, PinMode.MISO1, PinMode.SCK1)],
            "I2C0": [p.num for p in self.pins.values() if p.mode in (PinMode.SDA0, PinMode.SCL0)],
            "I2C1": [p.num for p in self.pins.values() if p.mode in (PinMode.SDA1, PinMode.SCL1)],
            "UART0": [p.num for p in self.pins.values() if p.mode in (PinMode.TX0, PinMode.RX0)],
            "UART1": [p.num for p in self.pins.values() if p.mode in (PinMode.TX1, PinMode.RX1)],
        }

        self.update_COM()

        self.update_DOUT(sorted(groups["DOUT"]))
        self.update_DIN(sorted(groups["DIN"]))
        self.update_ADC(sorted(groups["ADC"]))
        self.update_PWM(sorted(groups["PWM"]))
        self.update_SPI(groups["SPI0"], groups["SPI1"])
        self.update_I2C(groups["I2C0"], groups["I2C1"]) 
        self.update_UART(groups["UART0"], groups["UART1"]) 
        

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

        #print(f"\tsend: Set GP{pin} DOUT to {self.pins[pin].state}")
        self.send_pin_parameter(pin, "dout", self.pins[pin].state)

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
    
    def set_DIN_value(self, pin: int, din: int):
        """Update the DIN value and refresh the indicator."""
        self.pins[pin].din = 1 if din else 0
        if pin in self.pin_din_indicator:
            self.pin_din_indicator[pin].config(
                bg="#333333" if self.pins[pin].din == 0 else "#00aa00"
            )

    def on_pud_changed(self, pin: int, pud_value: str):
        self.pins[pin].pud = pud_value
        # keep the displayed variable in sync if we have it
        if pin in self.pin_din_pud_var:
            try:
                self.pin_din_pud_var[pin].set(pud_value)
            except Exception:
                pass
        #print(f"\tsend GP{pin} PUD changed to {self.pins[pin].pud}")
        self.send_pin_parameter(pin, "pud", self.pins[pin].pud)
        self.send_pin_parameter(pin, "mode", "DIN")

    def update_ADC(self, pins: list[int]):
        box = ttk.LabelFrame(self.fn_container, text="ADC", padding=8)
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
            
            adc_v = (self.pins[pin].adc_count / 65535.0) * 3.3
            # create/stash labels so they can be updated in-place when new readings arrive
            count_lbl = ttk.Label(row, text=f"{self.pins[pin].adc_count}", width=15)
            count_lbl.pack(side="left", padx=(2, 0))
            volt_lbl = ttk.Label(row, text=f"{adc_v:.3f} V", width=15)
            volt_lbl.pack(side="left", padx=(2, 0))

            self.pin_adc_count_label[pin] = count_lbl
            self.pin_adc_volt_label[pin] = volt_lbl
    
    def set_ADC_value(self, pin: int, counts: int):
        #if self.pins[pin].mode != PinMode.ADC:
        #    return
        self.pins[pin].adc_count = counts
        print(f"Pin {pin} ADC counts set to {counts}")

        # Update any visible ADC labels immediately so the UI reflects the new reading
        try:
            if pin in self.pin_adc_count_label:
                self.pin_adc_count_label[pin].config(text=f"{counts}")
            if pin in self.pin_adc_volt_label:
                adc_v = (counts / 65535.0) * 3.3
                self.pin_adc_volt_label[pin].config(text=f"{adc_v:.3f} V")
        except Exception:
            pass

    # --- SPI0 handlers ---
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
            #print("\tsend SPI0 MOSI pin removed")
            # send a clear command (value 255) using a valid pin id (0) in the leading field
            self.send_pin_parameter(0, "spi0_mosi", 255)
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
            #print(f"\tsend: SPI0 MOSI selected: GP{pin}")
            # send selected pin number as the value (use a valid leading pin id of 0)
            self.send_pin_parameter(0, "spi0_mosi", pin)
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
            #print("\tsend: SPI0 MISO selection cleared")
            self.send_pin_parameter(0, "spi0_miso", 255)
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
            #print(f"\tsend: SPI0 MISO selected: GP{pin}")
            self.send_pin_parameter(0, "spi0_miso", pin)
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
            #print("\tsend: SPI0 SCK selection cleared")
            self.send_pin_parameter(0, "spi0_sck", 255)
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
            #print(f"\tsend: SPI0 SCK selected: GP{pin}")
            self.send_pin_parameter(0, "spi0_sck", pin)
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
            #print("\tsend: SPI0 CSn selection cleared")
            self.send_pin_parameter(0, "spi0_csn", 255)
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
            #print(f"\tsend: SPI0 CSn set to pin {pin}")
            self.send_pin_parameter(0, "spi0_csn", pin)
        else:
            self.spi0_csn = None
            self.spi0_config['csn'] = None
            if hasattr(self, "spi0_csn_var"):
                try:
                    self.spi0_csn_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            print(f"SPI0 CSn selection invalid (pin {val} not DOUT)")

    def on_spi0_send(self, text: str):
        text = str(text).strip()
        # persist the entered hex text so it survives UI refreshes
        self.spi0_config['send_hex'] = text

        if not text:
            # also clear bytes_to_send
            self.spi0_config['bytes_to_send'] = []
            spi0.bytes_to_send = []
            return

        print(f"SPI0 send: {text}")
        # store both in local config and (if available) the spi0 object
        self.spi0_config['bytes_to_send'] = text
        try:
            spi0.bytes_to_send = text
        except Exception:
            pass

        self.send_pin_parameter(255, 'spi0_send', text)

    def update_spi0_speed(self, kbps: int):
        spi0.kilobits_per_second = kbps
        #print(f"SPI0 speed set to {kbps} kbps")
        self.send_pin_parameter(255, 'spi0_kbaud', int(kbps))

    def on_spi0_receive_bytes(self):
        """Update the SPI0 received bytes display from the spi0.received_bytes and persist."""
        rx = getattr(spi0, 'received_bytes', None)
        self.spi0_receive_var.set(rx)

    # --- SPI1 handlers (mirror SPI0 behavior) ---
    def on_spi1_mosi_selected(self, val: str):
        """Handle SPI1 MOSI selection (manual only)."""
        if val == PinMode.UNUSED.value or val == "----":
            self.spi1_mosi_selected = None
            self.spi1_config['mosi'] = None
            if hasattr(self, "spi1_mosi_var"):
                try:
                    self.spi1_mosi_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            try:
                self.refresh_function_boxes()
            except Exception:
                pass
            #print("\tsend: SPI1 MOSI selection cleared")
            self.send_pin_parameter(0, "spi1_mosi", 255)
            try:
                spi1.mosi_pin = None
            except Exception:
                pass
            return
        pin_str = str(val)
        if pin_str.startswith("GP"):
            pin_str = pin_str[2:]
        try:
            pin = int(pin_str)
        except Exception:
            return
        if self.pins.get(pin) and self.pins[pin].mode == PinMode.MOSI1:
            self.spi1_mosi_selected = pin
            self.spi1_config['mosi'] = pin
            if hasattr(self, "spi1_mosi_var"):
                try:
                    self.spi1_mosi_var.set(f"GP{pin}")
                except Exception:
                    pass
            try:
                self.refresh_function_boxes()
            except Exception:
                pass
            #print(f"\tsend: SPI1 MOSI selected: GP{pin}")
            self.send_pin_parameter(0, "spi0_mosi", pin)
            try:
                spi1.mosi_pin = pin
            except Exception:
                pass
        else:
            self.spi1_mosi_selected = None
            self.spi1_config['mosi'] = None
            if hasattr(self, "spi1_mosi_var"):
                try:
                    self.spi1_mosi_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            print(f"SPI1 MOSI selection invalid for {val}")
            try:
                spi1.mosi_pin = None
            except Exception:
                pass

    def on_spi1_miso_selected(self, val: str):
        if val == PinMode.UNUSED.value or val == "----":
            self.spi1_miso_selected = None
            self.spi1_config['miso'] = None
            if hasattr(self, "spi1_miso_var"):
                try:
                    self.spi1_miso_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            try:
                self.refresh_function_boxes()
            except Exception:
                pass
            #print("\tsend: SPI1 MISO selection cleared")
            self.send_pin_parameter(0, "spi1_miso", 255)
            try:
                spi1.miso_pin = None
            except Exception:
                pass
            return
        pin_str = str(val)
        if pin_str.startswith("GP"):
            pin_str = pin_str[2:]
        try:
            pin = int(pin_str)
        except Exception:
            return
        if self.pins.get(pin) and self.pins[pin].mode == PinMode.MISO1:
            self.spi1_miso_selected = pin
            self.spi1_config['miso'] = pin
            if hasattr(self, "spi1_miso_var"):
                try:
                    self.spi1_miso_var.set(f"GP{pin}")
                except Exception:
                    pass
            try:
                self.refresh_function_boxes()
            except Exception:
                pass
            #print(f"\tsend: SPI1 MISO selected: GP{pin}")
            self.send_pin_parameter(0, "spi1_miso", pin)
            try:
                spi1.miso_pin = pin
            except Exception:
                pass
        else:
            self.spi1_miso_selected = None
            self.spi1_config['miso'] = None
            if hasattr(self, "spi1_miso_var"):
                try:
                    self.spi1_miso_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            print(f"SPI1 MISO selection invalid for {val}")
            try:
                spi1.miso_pin = None
            except Exception:
                pass

    def on_spi1_sck_selected(self, val: str):
        if val == PinMode.UNUSED.value or val == "----":
            self.spi1_sck_selected = None
            self.spi1_config['sck'] = None
            if hasattr(self, "spi1_sck_var"):
                try:
                    self.spi1_sck_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            try:
                self.refresh_function_boxes()
            except Exception:
                pass
            #print("\tsend: SPI1 SCK selection cleared")
            self.send_pin_parameter(0, "spi1_sck", 255)
            try:
                spi1.sck_pin = None
            except Exception:
                pass
            return
        pin_str = str(val)
        if pin_str.startswith("GP"):
            pin_str = pin_str[2:]
        try:
            pin = int(pin_str)
        except Exception:
            return
        if self.pins.get(pin) and self.pins[pin].mode == PinMode.SCK1:
            self.spi1_sck_selected = pin
            self.spi1_config['sck'] = pin
            if hasattr(self, "spi1_sck_var"):
                try:
                    self.spi1_sck_var.set(f"GP{pin}")
                except Exception:
                    pass
            try:
                self.refresh_function_boxes()
            except Exception:
                pass
            #print(f"\tsend: SPI1 SCK selected: GP{pin}")
            self.send_pin_parameter(0, "spi1_sck", pin)
            try:
                spi1.sck_pin = pin
            except Exception:
                pass
        else:
            self.spi1_sck_selected = None
            self.spi1_config['sck'] = None
            if hasattr(self, "spi1_sck_var"):
                try:
                    self.spi1_sck_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            print(f"\tsend: SPI1 SCK selection invalid for {val}")
            try:
                spi1.sck_pin = None
            except Exception:
                pass

    def on_spi1_csn_selected(self, val: str):
        if val == PinMode.UNUSED.value or val == "----":
            self.spi1_csn = None
            self.spi1_config['csn'] = None
            if hasattr(self, "spi1_csn_var"):
                try:
                    self.spi1_csn_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            #print("\tsend: SPI1 CSn selection cleared")
            self.send_pin_parameter(0, "spi1_csn", 255)
            try:
                spi1.csn_pin = None
            except Exception:
                pass
            return
        pin_str = str(val)
        if pin_str.startswith("GP"):
            pin_str = pin_str[2:]
        try:
            pin = int(pin_str)
        except Exception:
            return
        if self.pins.get(pin) and self.pins[pin].mode == PinMode.DOUT:
            self.spi1_csn = pin
            self.spi1_config['csn'] = pin
            if hasattr(self, "spi1_csn_var"):
                try:
                    self.spi1_csn_var.set(f"GP{pin}")
                except Exception:
                    pass
            #print(f"\tsend: SPI1 CSn set to pin {pin}")
            self.send_pin_parameter(0, "spi1_csn", pin)
            try:
                spi1.csn_pin = pin
            except Exception:
                pass
        else:
            self.spi1_csn = None
            self.spi1_config['csn'] = None
            if hasattr(self, "spi1_csn_var"):
                try:
                    self.spi1_csn_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            print(f"SPI1 CSn selection invalid (pin {val} not DOUT)")
            try:
                spi1.csn_pin = None
            except Exception:
                pass

    def on_spi1_send(self, text: str):
        text = str(text).strip()
        # persist the entered hex text so it survives UI refreshes
        self.spi1_config['send_hex'] = text

        if not text:
            # also clear bytes_to_send
            self.spi1_config['bytes_to_send'] = []
            spi1.bytes_to_send = []
            return

        print(f"SPI1 send: {text}")
        # store both in local config and (if available) the spi1 object
        self.spi1_config['bytes_to_send'] = text
        try:
            spi1.bytes_to_send = text
        except Exception:
            pass

        self.send_pin_parameter(255, 'spi1_send', text)

    def update_spi1_speed(self, kbps: int):
        spi1.kilobits_per_second = kbps
        #print(f"SPI0 speed set to {kbps} kbps")
        self.send_pin_parameter(255, 'spi1_kbaud', int(kbps))

    def on_spi1_receive_bytes(self):
        rx = getattr(spi1, 'received_bytes', None)
        self.spi1_receive_var.set(rx)

    # --- PWM handlers ---
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
            #freq_entry.bind("<FocusOut>", lambda e, p=pin: self.update_pwm_freq(p, float(freq_var.get())))

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
        # Enforce a minimum frequency: 50 Hz for servo mode, otherwise 10 Hz.
        min_freq = 10
        if freq < min_freq:
            freq = min_freq
            # update the entry to reflect the clamped value
            if pin in self.pin_pwm_freq_var:
                self.pin_pwm_freq_var[pin].set(freq)

        self.pins[pin].pwm_freq = freq
        #print(f"\tsend: GP{pin} PWM frequency set to {freq} Hz")
        self.send_pin_parameter(pin, "pwm_freq", freq)
    
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
            #print(f"Pin {pin} Servo angle set to {angle:.1f} degrees (duty: {clamped:.2f}%)")
        else:
            self.pins[pin].pwm_duty = duty
            if pin in self.pin_slider_widget:
                try:
                    self.pin_slider_widget[pin].set(duty)
                except Exception:
                    pass
            if pin in self.pin_slider_label:
                self.pin_slider_label[pin].config(text=f"{duty:.1f}%")
        #print(f"\tsend: GP{pin} PWM duty cycle set to {self.pins[pin].pwm_duty:.1f} %")
        #self.send_pin_parameter(pin, "pwm_duty", round(self.pins[pin].pwm_duty,2))
    
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
            self.send_pin_parameter(pin, "pwm_freq", 50)
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
            #print(f"Pin {pin} PWM duty cycle set to {value:.1f}%")
        self.send_pin_parameter(pin, "pwm_duty", round(self.pins[pin].pwm_duty,2))
    
    # --- GUI refreshes ---
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

            kbps_var = tk.StringVar(value=spi0.kilobits_per_second)
            ttk.Label(row, text="kbps:").pack(side="left", padx=(2, 0))
            kbps_entry = tk.Entry(row, width=6, textvariable=kbps_var)
            kbps_entry.pack(side="left", padx=(2, 0))

            kbps_entry.bind("<Return>", lambda e: self.update_spi0_speed(float(kbps_var.get())))
            kbps_entry.bind("<FocusOut>", lambda e: self.update_spi0_speed(float(kbps_var.get())))

            # Send entry on its own line below other SPI0 controls
            row2 = ttk.Frame(spi0_box)
            row2.pack(fill="x", pady=(6, 0))
            ttk.Label(row2, text="Send Hex:", width=9, anchor="w").pack(side="left", padx=(8, 0))

            # initialize or reuse StringVar so value persists across UI refreshes
            saved_send = self.spi0_config.get('send_hex', '')
            if hasattr(self, 'spi0_send_var'):
                # keep existing var but update its value to saved one if present
                try:
                    if saved_send is not None:
                        self.spi0_send_var.set(saved_send)
                except Exception:
                    pass
            else:
                self.spi0_send_var = tk.StringVar(value=saved_send if saved_send is not None else "")

            spi0_send_entry = tk.Entry(row2, width=20, textvariable=self.spi0_send_var)
            spi0_send_entry.pack(side="left", padx=(4, 0))
            spi0_send_entry.bind("<Return>", lambda e: self.on_spi0_send(self.spi0_send_var.get()))

            ttk.Label(row2, text="  Received Bytes:", width=16, anchor="w").pack(side="left", padx=(16, 0))
            # text field to show the hex of received bytes
            saved_recv = None
            if self.spi0_config.get('received_bytes'):
                saved_recv = ' '.join(f"{b:02X}" for b in self.spi0_config['received_bytes'])

            if hasattr(self, 'spi0_receive_var'):
                try:
                    if saved_recv is not None:
                        self.spi0_receive_var.set(saved_recv)
                except Exception:
                    pass
            else:
                self.spi0_receive_var = tk.StringVar(value=saved_recv if saved_recv is not None else "")

            spi0_receive_entry = tk.Entry(row2, width=50, textvariable=self.spi0_receive_var, state="readonly")
            spi0_receive_entry.pack(side="left", padx=(4, 0))


        # create a sub-box for SPI1 (mirrors SPI0 UI/behaviour)
        if spi1_pins:
            spi1_box = ttk.LabelFrame(box, text="SPI1", padding=8)
            spi1_box.pack(fill="x", pady=4)

            # MOSI
            row = ttk.Frame(spi1_box)
            row.pack(fill="x", pady=2)

            ttk.Label(row, text="MOSI:", anchor="w").pack(side="left", padx=(8, 8))
            mosi1_options = [PinMode.UNUSED.value] + [f"GP{p}" for p in spi1_pins if self.pins[p].mode == PinMode.MOSI1]
            mosi1_sel = PinMode.UNUSED.value
            if hasattr(self, 'spi1_mosi_selected') and self.spi1_mosi_selected is not None:
                sel_str = f"GP{self.spi1_mosi_selected}"
                if sel_str in mosi1_options:
                    mosi1_sel = sel_str
                else:
                    self.spi1_mosi_selected = None
                    self.spi1_config['mosi'] = None
            self.spi1_mosi_var = tk.StringVar(value=mosi1_sel)
            mosi1_menu = ttk.OptionMenu(row, self.spi1_mosi_var, self.spi1_mosi_var.get(), *mosi1_options, command=lambda _val: self.on_spi1_mosi_selected(_val))
            mosi1_menu.config(width=6)
            mosi1_menu.pack(side="left", padx=(6, 6))

            # MISO
            ttk.Label(row, text="MISO:", anchor="w").pack(side="left", padx=(8, 8))
            miso1_options = [PinMode.UNUSED.value] + [f"GP{p}" for p in spi1_pins if self.pins[p].mode == PinMode.MISO1]
            miso1_sel = PinMode.UNUSED.value
            if hasattr(self, 'spi1_miso_selected') and self.spi1_miso_selected is not None:
                sel_str = f"GP{self.spi1_miso_selected}"
                if sel_str in miso1_options:
                    miso1_sel = sel_str
                else:
                    self.spi1_miso_selected = None
                    self.spi1_config['miso'] = None
            self.spi1_miso_var = tk.StringVar(value=miso1_sel)
            miso1_menu = ttk.OptionMenu(row, self.spi1_miso_var, self.spi1_miso_var.get(), *miso1_options, command=lambda _val: self.on_spi1_miso_selected(_val))
            miso1_menu.config(width=6)
            miso1_menu.pack(side="left", padx=(6, 6))

            # SCK
            ttk.Label(row, text="SCK:", anchor="w").pack(side="left", padx=(8, 8))
            sck1_options = [PinMode.UNUSED.value] + [f"GP{p}" for p in spi1_pins if self.pins[p].mode == PinMode.SCK1]
            sck1_sel = PinMode.UNUSED.value
            if hasattr(self, 'spi1_sck_selected') and self.spi1_sck_selected is not None:
                sel_str = f"GP{self.spi1_sck_selected}"
                if sel_str in sck1_options:
                    sck1_sel = sel_str
                else:
                    self.spi1_sck_selected = None
                    self.spi1_config['sck'] = None
            self.spi1_sck_var = tk.StringVar(value=sck1_sel)
            sck1_menu = ttk.OptionMenu(row, self.spi1_sck_var, self.spi1_sck_var.get(), *sck1_options, command=lambda _val: self.on_spi1_sck_selected(_val))
            sck1_menu.config(width=6)
            sck1_menu.pack(side="left", padx=(6, 6))

            # CSn (choose any pin currently in DOUT mode)
            ttk.Label(row, text="CSn:", anchor="w").pack(side="left", padx=(8, 8))
            csn1_candidates = [p.num for p in self.pins.values() if p.mode == PinMode.DOUT]
            csn1_options = [PinMode.UNUSED.value] + [f"GP{p}" for p in csn1_candidates]
            csn1_sel = PinMode.UNUSED.value
            if getattr(self, 'spi1_csn', None) is not None:
                sel_str = f"GP{self.spi1_csn}"
                if sel_str in csn1_options:
                    csn1_sel = sel_str
                else:
                    self.spi1_csn = None
                    self.spi1_config['csn'] = None
            self.spi1_csn_var = tk.StringVar(value=csn1_sel)
            csn1_menu = ttk.OptionMenu(row, self.spi1_csn_var, self.spi1_csn_var.get(), *csn1_options, command=lambda _val: self.on_spi1_csn_selected(_val))
            csn1_menu.config(width=6)
            csn1_menu.pack(side="left", padx=(6, 6))

            kbps1_var = tk.StringVar(value=getattr(spi1, 'kilobits_per_second', self.spi1_config.get('kbps', 1000)))
            ttk.Label(row, text="kbps:").pack(side="left", padx=(2, 0))
            kbps1_entry = tk.Entry(row, width=6, textvariable=kbps1_var)
            kbps1_entry.pack(side="left", padx=(2, 0))

            kbps1_entry.bind("<Return>", lambda e: self.update_spi1_speed(float(kbps1_var.get())))
            kbps1_entry.bind("<FocusOut>", lambda e: self.update_spi1_speed(float(kbps1_var.get())))

            # Send entry on its own line below other SPI1 controls
            row2 = ttk.Frame(spi1_box)
            row2.pack(fill="x", pady=(6, 0))
            ttk.Label(row2, text="Send Hex:", width=9, anchor="w").pack(side="left", padx=(8, 0))

            # initialize or reuse StringVar so value persists across UI refreshes
            saved1_send = self.spi1_config.get('send_hex', '')
            if hasattr(self, 'spi1_send_var'):
                # keep existing var but update its value to saved one if present
                try:
                    if saved1_send is not None:
                        self.spi1_send_var.set(saved1_send)
                except Exception:
                    pass
            else:
                self.spi1_send_var = tk.StringVar(value=saved1_send if saved1_send is not None else "")

            spi1_send_entry = tk.Entry(row2, width=20, textvariable=self.spi1_send_var)
            spi1_send_entry.pack(side="left", padx=(4, 0))
            spi1_send_entry.bind("<Return>", lambda e: self.on_spi1_send(self.spi1_send_var.get()))

            ttk.Label(row2, text="  Received Bytes:", width=16, anchor="w").pack(side="left", padx=(16, 0))
            # text field to show the hex of received bytes
            saved1_recv = None
            if self.spi1_config.get('received_bytes'):
                saved1_recv = ' '.join(f"{b:02X}" for b in self.spi1_config['received_bytes'])

            if hasattr(self, 'spi1_receive_var'):
                try:
                    if saved1_recv is not None:
                        self.spi1_receive_var.set(saved1_recv)
                except Exception:
                    pass
            else:
                self.spi1_receive_var = tk.StringVar(value=saved1_recv if saved1_recv is not None else "")

            spi1_receive_entry = tk.Entry(row2, width=50, textvariable=self.spi1_receive_var, state="readonly")
            spi1_receive_entry.pack(side="left", padx=(4, 0))

    def update_I2C(self, i2c0_pins: list[int], i2c1_pins: list[int]):
        box = ttk.LabelFrame(self.fn_container, text="I2C", padding=8)
        box.pack(fill="x", pady=8)

        if not i2c0_pins and not i2c1_pins:
            ttk.Label(box, text="No pins assigned.").pack(anchor="w")
            return

        # I2C0
        if i2c0_pins:
            i2c0_box = ttk.LabelFrame(box, text="I2C0", padding=8)
            i2c0_box.pack(fill="x", pady=4)

            row = ttk.Frame(i2c0_box)
            row.pack(fill="x", pady=2)

            ttk.Label(row, text="SDA:", anchor="w").pack(side="left", padx=(8, 8))
            sda0_options = [PinMode.UNUSED.value] + [f"GP{p}" for p in i2c0_pins if self.pins[p].mode == PinMode.SDA0]
            sda0_sel = PinMode.UNUSED.value
            if hasattr(self, 'i2c0_sda_selected') and self.i2c0_sda_selected is not None:
                sel_str = f"GP{self.i2c0_sda_selected}"
                if sel_str in sda0_options:
                    sda0_sel = sel_str
                else:
                    self.i2c0_sda_selected = None
                    self.i2c0_config['sda'] = None
            self.i2c0_sda_var = tk.StringVar(value=sda0_sel)
            sda0_menu = ttk.OptionMenu(row, self.i2c0_sda_var, self.i2c0_sda_var.get(), *sda0_options, command=lambda _val: self.on_i2c0_sda_selected(_val))
            sda0_menu.config(width=6)
            sda0_menu.pack(side="left", padx=(6, 6))

            ttk.Label(row, text="SCL:", anchor="w").pack(side="left", padx=(8, 8))
            scl0_options = [PinMode.UNUSED.value] + [f"GP{p}" for p in i2c0_pins if self.pins[p].mode == PinMode.SCL0]
            scl0_sel = PinMode.UNUSED.value
            if hasattr(self, 'i2c0_scl_selected') and self.i2c0_scl_selected is not None:
                sel_str = f"GP{self.i2c0_scl_selected}"
                if sel_str in scl0_options:
                    scl0_sel = sel_str
                else:
                    self.i2c0_scl_selected = None
                    self.i2c0_config['scl'] = None
            self.i2c0_scl_var = tk.StringVar(value=scl0_sel)
            scl0_menu = ttk.OptionMenu(row, self.i2c0_scl_var, self.i2c0_scl_var.get(), *scl0_options, command=lambda _val: self.on_i2c0_scl_selected(_val))
            scl0_menu.config(width=6)
            scl0_menu.pack(side="left", padx=(6, 6))

            # frequency
            khz0_var = tk.StringVar(value=self.i2c0_config.get('khz', 100))
            ttk.Label(row, text="freq [kHz]:").pack(side="left", padx=(2, 0))
            khz0_entry = tk.Entry(row, width=6, textvariable=khz0_var)
            khz0_entry.pack(side="left", padx=(2, 0))
            khz0_entry.bind("<Return>", lambda e: self.update_i2c0_speed(int(khz0_var.get())))
            khz0_entry.bind("<FocusOut>", lambda e: self.update_i2c0_speed(int(khz0_var.get())))

            # Scan button and label
            scan_btn = ttk.Button(row, text="Scan", command=lambda: self.on_i2c0_scan())
            scan_btn.pack(side="left", padx=(12, 8))
            if not hasattr(self, 'i2c0_scan_var'):
                self.i2c0_scan_var = tk.StringVar(value="")
            ttk.Label(row, textvariable=self.i2c0_scan_var).pack(side="left", padx=(6,8))

            # Row2: addr + send / received
            row2 = ttk.Frame(i2c0_box)
            row2.pack(fill="x", pady=(6, 0))
            ttk.Label(row2, text="Addr [hex]:", width=9, anchor="w").pack(side="left", padx=(8, 0))

            saved_addr = self.i2c0_config.get('address', '')
            if hasattr(self, 'i2c0_addr_var'):
                try:
                    if saved_addr is not None:
                        self.i2c0_addr_var.set(saved_addr)
                except Exception:
                    pass
            else:
                self.i2c0_addr_var = tk.StringVar(value=saved_addr if saved_addr is not None else "")

            i2c0_addr_entry = tk.Entry(row2, width=8, textvariable=self.i2c0_addr_var)
            i2c0_addr_entry.pack(side="left", padx=(4, 0))
            i2c0_addr_entry.bind("<Return>", lambda e: self.on_i2c0_send(self.i2c0_addr_var.get(), self.i2c0_send_var.get()))

            ttk.Label(row2, text="Send Hex:", width=9, anchor="w").pack(side="left", padx=(8, 0))

            saved_send = self.i2c0_config.get('send_hex', '')
            if hasattr(self, 'i2c0_send_var'):
                try:
                    if saved_send is not None:
                        self.i2c0_send_var.set(saved_send)
                except Exception:
                    pass
            else:
                self.i2c0_send_var = tk.StringVar(value=saved_send if saved_send is not None else "")

            i2c0_send_entry = tk.Entry(row2, width=20, textvariable=self.i2c0_send_var)
            i2c0_send_entry.pack(side="left", padx=(4, 0))
            i2c0_send_entry.bind("<Return>", lambda e: self.on_i2c0_send(self.i2c0_addr_var.get(), self.i2c0_send_var.get()))

            ttk.Label(row2, text="  Received Bytes:", width=16, anchor="w").pack(side="left", padx=(16, 0))
            saved_recv = None
            if self.i2c0_config.get('received_bytes'):
                saved_recv = ' '.join(f"{b:02X}" for b in self.i2c0_config['received_bytes'])

            if hasattr(self, 'i2c0_receive_var'):
                try:
                    if saved_recv is not None:
                        self.i2c0_receive_var.set(saved_recv)
                except Exception:
                    pass
            else:
                self.i2c0_receive_var = tk.StringVar(value=saved_recv if saved_recv is not None else "")

            i2c0_receive_entry = tk.Entry(row2, width=50, textvariable=self.i2c0_receive_var, state="readonly")
            i2c0_receive_entry.pack(side="left", padx=(4, 0))

        # I2C1 (mirror)
        if i2c1_pins:
            i2c1_box = ttk.LabelFrame(box, text="I2C1", padding=8)
            i2c1_box.pack(fill="x", pady=4)

            row = ttk.Frame(i2c1_box)
            row.pack(fill="x", pady=2)

            ttk.Label(row, text="SDA:", anchor="w").pack(side="left", padx=(8, 8))
            sda1_options = [PinMode.UNUSED.value] + [f"GP{p}" for p in i2c1_pins if self.pins[p].mode == PinMode.SDA1]
            sda1_sel = PinMode.UNUSED.value
            if hasattr(self, 'i2c1_sda_selected') and self.i2c1_sda_selected is not None:
                sel_str = f"GP{self.i2c1_sda_selected}"
                if sel_str in sda1_options:
                    sda1_sel = sel_str
                else:
                    self.i2c1_sda_selected = None
                    self.i2c1_config['sda'] = None
            self.i2c1_sda_var = tk.StringVar(value=sda1_sel)
            sda1_menu = ttk.OptionMenu(row, self.i2c1_sda_var, self.i2c1_sda_var.get(), *sda1_options, command=lambda _val: self.on_i2c1_sda_selected(_val))
            sda1_menu.config(width=6)
            sda1_menu.pack(side="left", padx=(6, 6))

            ttk.Label(row, text="SCL:", anchor="w").pack(side="left", padx=(8, 8))
            scl1_options = [PinMode.UNUSED.value] + [f"GP{p}" for p in i2c1_pins if self.pins[p].mode == PinMode.SCL1]
            scl1_sel = PinMode.UNUSED.value
            if hasattr(self, 'i2c1_scl_selected') and self.i2c1_scl_selected is not None:
                sel_str = f"GP{self.i2c1_scl_selected}"
                if sel_str in scl1_options:
                    scl1_sel = sel_str
                else:
                    self.i2c1_scl_selected = None
                    self.i2c1_config['scl'] = None
            self.i2c1_scl_var = tk.StringVar(value=scl1_sel)
            scl1_menu = ttk.OptionMenu(row, self.i2c1_scl_var, self.i2c1_scl_var.get(), *scl1_options, command=lambda _val: self.on_i2c1_scl_selected(_val))
            scl1_menu.config(width=6)
            scl1_menu.pack(side="left", padx=(6, 6))

            khz1_var = tk.StringVar(value=self.i2c1_config.get('khz', 100))
            ttk.Label(row, text="freq [kHz]:").pack(side="left", padx=(2, 0))
            khz1_entry = tk.Entry(row, width=6, textvariable=khz1_var)
            khz1_entry.pack(side="left", padx=(2, 0))
            khz1_entry.bind("<Return>", lambda e: self.update_i2c1_speed(int(khz1_var.get())))
            khz1_entry.bind("<FocusOut>", lambda e: self.update_i2c1_speed(int(khz1_var.get())))

            scan1_btn = ttk.Button(row, text="Scan", command=lambda: self.on_i2c1_scan())
            scan1_btn.pack(side="left", padx=(12, 8))
            if not hasattr(self, 'i2c1_scan_var'):
                self.i2c1_scan_var = tk.StringVar(value="")
            ttk.Label(row, textvariable=self.i2c1_scan_var).pack(side="left", padx=(6,8))

            row2 = ttk.Frame(i2c1_box)
            row2.pack(fill="x", pady=(6, 0))
            ttk.Label(row2, text="Addr [hex]:", width=9, anchor="w").pack(side="left", padx=(8, 0))

            saved1_addr = self.i2c1_config.get('address', '')
            if hasattr(self, 'i2c1_addr_var'):
                try:
                    if saved1_addr is not None:
                        self.i2c1_addr_var.set(saved1_addr)
                except Exception:
                    pass
            else:
                self.i2c1_addr_var = tk.StringVar(value=saved1_addr if saved1_addr is not None else "")

            i2c1_addr_entry = tk.Entry(row2, width=8, textvariable=self.i2c1_addr_var)
            i2c1_addr_entry.pack(side="left", padx=(4, 0))
            i2c1_addr_entry.bind("<Return>", lambda e: self.on_i2c1_send(self.i2c1_addr_var.get(), self.i2c1_send_var.get()))

            ttk.Label(row2, text="Send Hex:", width=9, anchor="w").pack(side="left", padx=(8, 0))

            saved1_send = self.i2c1_config.get('send_hex', '')
            if hasattr(self, 'i2c1_send_var'):
                try:
                    if saved1_send is not None:
                        self.i2c1_send_var.set(saved1_send)
                except Exception:
                    pass
            else:
                self.i2c1_send_var = tk.StringVar(value=saved1_send if saved1_send is not None else "")

            i2c1_send_entry = tk.Entry(row2, width=20, textvariable=self.i2c1_send_var)
            i2c1_send_entry.pack(side="left", padx=(4, 0))
            i2c1_send_entry.bind("<Return>", lambda e: self.on_i2c1_send(self.i2c1_addr_var.get(), self.i2c1_send_var.get()))

            ttk.Label(row2, text="  Received Bytes:", width=16, anchor="w").pack(side="left", padx=(16, 0))
            saved1_recv = None
            if self.i2c1_config.get('received_bytes'):
                saved1_recv = ' '.join(f"{b:02X}" for b in self.i2c1_config['received_bytes'])

            if hasattr(self, 'i2c1_receive_var'):
                try:
                    if saved1_recv is not None:
                        self.i2c1_receive_var.set(saved1_recv)
                except Exception:
                    pass
            else:
                self.i2c1_receive_var = tk.StringVar(value=saved1_recv if saved1_recv is not None else "")

            i2c1_receive_entry = tk.Entry(row2, width=50, textvariable=self.i2c1_receive_var, state="readonly")
            i2c1_receive_entry.pack(side="left", padx=(4, 0))

    def update_UART(self, uart0_pins: list[int], uart1_pins: list[int]):
        box = ttk.LabelFrame(self.fn_container, text="UART", padding=8)
        box.pack(fill="x", pady=8)

        if not uart0_pins and not uart1_pins:
            ttk.Label(box, text="No pins assigned.").pack(anchor="w")
            return

        # UART0
        if uart0_pins:
            uart0_box = ttk.LabelFrame(box, text="UART0", padding=8)
            uart0_box.pack(fill="x", pady=4)

            row = ttk.Frame(uart0_box)
            row.pack(fill="x", pady=2)

            ttk.Label(row, text="TX:", anchor="w").pack(side="left", padx=(8, 8))
            tx0_options = [PinMode.UNUSED.value] + [f"GP{p}" for p in uart0_pins if self.pins[p].mode == PinMode.TX0]
            tx0_sel = PinMode.UNUSED.value
            if hasattr(self, 'uart0_tx_selected') and self.uart0_tx_selected is not None:
                sel_str = f"GP{self.uart0_tx_selected}"
                if sel_str in tx0_options:
                    tx0_sel = sel_str
                else:
                    self.uart0_tx_selected = None
                    self.uart0_config['tx'] = None
            self.uart0_tx_var = tk.StringVar(value=tx0_sel)
            tx0_menu = ttk.OptionMenu(row, self.uart0_tx_var, self.uart0_tx_var.get(), *tx0_options, command=lambda _val: self.on_uart0_tx_selected(_val))
            tx0_menu.config(width=6)
            tx0_menu.pack(side="left", padx=(6, 6))

            ttk.Label(row, text="RX:", anchor="w").pack(side="left", padx=(8, 8))
            rx0_options = [PinMode.UNUSED.value] + [f"GP{p}" for p in uart0_pins if self.pins[p].mode == PinMode.RX0]
            rx0_sel = PinMode.UNUSED.value
            if hasattr(self, 'uart0_rx_selected') and self.uart0_rx_selected is not None:
                sel_str = f"GP{self.uart0_rx_selected}"
                if sel_str in rx0_options:
                    rx0_sel = sel_str
                else:
                    self.uart0_rx_selected = None
                    self.uart0_config['rx'] = None
            self.uart0_rx_var = tk.StringVar(value=rx0_sel)
            rx0_menu = ttk.OptionMenu(row, self.uart0_rx_var, self.uart0_rx_var.get(), *rx0_options, command=lambda _val: self.on_uart0_rx_selected(_val))
            rx0_menu.config(width=6)
            rx0_menu.pack(side="left", padx=(6, 6))

            # baud
            baud0_var = tk.StringVar(value=self.uart0_config.get('baud', 115200))
            ttk.Label(row, text="baud:").pack(side="left", padx=(2, 0))
            baud0_entry = tk.Entry(row, width=8, textvariable=baud0_var)
            baud0_entry.pack(side="left", padx=(2, 0))
            baud0_entry.bind("<Return>", lambda e: self.update_uart0_baud(int(baud0_var.get())))
            baud0_entry.bind("<FocusOut>", lambda e: self.update_uart0_baud(int(baud0_var.get())))

            # Row2: send / received (text)
            row2 = ttk.Frame(uart0_box)
            row2.pack(fill="x", pady=(6, 0))
            ttk.Label(row2, text="Send Text:", width=9, anchor="w").pack(side="left", padx=(8, 0))

            saved_send = self.uart0_config.get('send_text', '')
            if hasattr(self, 'uart0_send_var'):
                try:
                    if saved_send is not None:
                        self.uart0_send_var.set(saved_send)
                except Exception:
                    pass
            else:
                self.uart0_send_var = tk.StringVar(value=saved_send if saved_send is not None else "")

            uart0_send_entry = tk.Entry(row2, width=40, textvariable=self.uart0_send_var)
            uart0_send_entry.pack(side="left", padx=(4, 0))
            uart0_send_entry.bind("<Return>", lambda e: self.on_uart0_send(self.uart0_send_var.get()))

            ttk.Label(row2, text="  Received:", width=9, anchor="w").pack(side="left", padx=(12, 0))
            saved_recv = self.uart0_config.get('received_text', '')
            if hasattr(self, 'uart0_receive_var'):
                try:
                    if saved_recv is not None:
                        self.uart0_receive_var.set(saved_recv)
                except Exception:
                    pass
            else:
                self.uart0_receive_var = tk.StringVar(value=saved_recv if saved_recv is not None else "")

            uart0_receive_entry = tk.Entry(row2, width=40, textvariable=self.uart0_receive_var, state="readonly")
            uart0_receive_entry.pack(side="left", padx=(4, 0))

        # UART1 (mirror)
        if uart1_pins:
            uart1_box = ttk.LabelFrame(box, text="UART1", padding=8)
            uart1_box.pack(fill="x", pady=4)

            row = ttk.Frame(uart1_box)
            row.pack(fill="x", pady=2)

            ttk.Label(row, text="TX:", anchor="w").pack(side="left", padx=(8, 8))
            tx1_options = [PinMode.UNUSED.value] + [f"GP{p}" for p in uart1_pins if self.pins[p].mode == PinMode.TX1]
            tx1_sel = PinMode.UNUSED.value
            if hasattr(self, 'uart1_tx_selected') and self.uart1_tx_selected is not None:
                sel_str = f"GP{self.uart1_tx_selected}"
                if sel_str in tx1_options:
                    tx1_sel = sel_str
                else:
                    self.uart1_tx_selected = None
                    self.uart1_config['tx'] = None
            self.uart1_tx_var = tk.StringVar(value=tx1_sel)
            tx1_menu = ttk.OptionMenu(row, self.uart1_tx_var, self.uart1_tx_var.get(), *tx1_options, command=lambda _val: self.on_uart1_tx_selected(_val))
            tx1_menu.config(width=6)
            tx1_menu.pack(side="left", padx=(6, 6))

            ttk.Label(row, text="RX:", anchor="w").pack(side="left", padx=(8, 8))
            rx1_options = [PinMode.UNUSED.value] + [f"GP{p}" for p in uart1_pins if self.pins[p].mode == PinMode.RX1]
            rx1_sel = PinMode.UNUSED.value
            if hasattr(self, 'uart1_rx_selected') and self.uart1_rx_selected is not None:
                sel_str = f"GP{self.uart1_rx_selected}"
                if sel_str in rx1_options:
                    rx1_sel = sel_str
                else:
                    self.uart1_rx_selected = None
                    self.uart1_config['rx'] = None
            self.uart1_rx_var = tk.StringVar(value=rx1_sel)
            rx1_menu = ttk.OptionMenu(row, self.uart1_rx_var, self.uart1_rx_var.get(), *rx1_options, command=lambda _val: self.on_uart1_rx_selected(_val))
            rx1_menu.config(width=6)
            rx1_menu.pack(side="left", padx=(6, 6))

            baud1_var = tk.StringVar(value=self.uart1_config.get('baud', 115200))
            ttk.Label(row, text="baud:").pack(side="left", padx=(2, 0))
            baud1_entry = tk.Entry(row, width=8, textvariable=baud1_var)
            baud1_entry.pack(side="left", padx=(2, 0))
            baud1_entry.bind("<Return>", lambda e: self.update_uart1_baud(int(baud1_var.get())))
            baud1_entry.bind("<FocusOut>", lambda e: self.update_uart1_baud(int(baud1_var.get())))

            row2 = ttk.Frame(uart1_box)
            row2.pack(fill="x", pady=(6, 0))
            ttk.Label(row2, text="Send Text:", width=9, anchor="w").pack(side="left", padx=(8, 0))

            saved1_send = self.uart1_config.get('send_text', '')
            if hasattr(self, 'uart1_send_var'):
                try:
                    if saved1_send is not None:
                        self.uart1_send_var.set(saved1_send)
                except Exception:
                    pass
            else:
                self.uart1_send_var = tk.StringVar(value=saved1_send if saved1_send is not None else "")

            uart1_send_entry = tk.Entry(row2, width=40, textvariable=self.uart1_send_var)
            uart1_send_entry.pack(side="left", padx=(4, 0))
            uart1_send_entry.bind("<Return>", lambda e: self.on_uart1_send(self.uart1_send_var.get()))

            ttk.Label(row2, text="  Received:", width=9, anchor="w").pack(side="left", padx=(12, 0))
            saved1_recv = self.uart1_config.get('received_text', '')
            if hasattr(self, 'uart1_receive_var'):
                try:
                    if saved1_recv is not None:
                        self.uart1_receive_var.set(saved1_recv)
                except Exception:
                    pass
            else:
                self.uart1_receive_var = tk.StringVar(value=saved1_recv if saved1_recv is not None else "")

            uart1_receive_entry = tk.Entry(row2, width=40, textvariable=self.uart1_receive_var, state="readonly")
            uart1_receive_entry.pack(side="left", padx=(4, 0))

    def update_COM(self):
        """Display COM port selection dropdown and Refresh button."""
        box = ttk.LabelFrame(self.fn_container, text="Connection", padding=8)
        box.pack(fill="x", pady=8)

        row = ttk.Frame(box)
        row.pack(fill="x", pady=2)

        ttk.Label(row, text="COM Port:", anchor="w").pack(side="left", padx=(8, 8))

        # try to enumerate system ports (requires pyserial). Fall back to empty list if not available.
        ports = []
        try:
            ports = [p.device for p in list_ports.comports()]
        except Exception:
            ports = []

        options = ["None"] + ports if ports else ["None"]

        current_sel = "None"
        if getattr(self, 'com_port_selected', None) is not None:
            if self.com_port_selected in options:
                current_sel = self.com_port_selected
            else:
                self.com_port_selected = None

        if not hasattr(self, 'com_port_var'):
            self.com_port_var = tk.StringVar(value=current_sel)
        else:
            try:
                self.com_port_var.set(current_sel)
            except Exception:
                pass

        # Destroy any existing widgets that were parented to old frames to avoid "bad window path name" errors
        if hasattr(self, 'com_port_menu'):
            try:
                self.com_port_menu.destroy()
            except Exception:
                pass

        self.com_port_menu = ttk.OptionMenu(row, self.com_port_var, self.com_port_var.get(), *options, command=lambda v: self.on_com_selected(v))
        self.com_port_menu.config(width=20)
        self.com_port_menu.pack(side="left", padx=(6, 6))

        ttk.Button(row, text="Refresh", command=self.refresh_com_ports).pack(side="left", padx=(8, 0))

        # Baud entry for opening serial ports
        ttk.Label(row, text="Baud:").pack(side="left", padx=(8, 0))
        baud_entry = tk.Entry(row, width=8, textvariable=self.com_baud_var)
        baud_entry.pack(side="left", padx=(2, 0))

        # Open/Close button: always recreate to avoid reparenting a destroyed widget
        if hasattr(self, 'com_open_btn'):
            try:
                self.com_open_btn.destroy()
            except Exception:
                pass
        self.com_open_btn = ttk.Button(row, text=("Close" if self.ser else "Open"), command=self.on_com_open_toggle)
        self.com_open_btn.pack(side="left", padx=(8, 0))

        # Status label with background color (use tk.Label so bg shows). Recreate each refresh.
        if hasattr(self, 'com_status_label'):
            try:
                self.com_status_label.destroy()
            except Exception:
                pass
        status_bg = "#aaddaa" if self.ser else "#dddddd"
        if not hasattr(self, 'com_port_label_var'):
            self.com_port_label_var = tk.StringVar(value=self.com_port_selected or "")
        self.com_status_label = tk.Label(row, textvariable=self.com_port_label_var, bg=status_bg, width=24, anchor="w")
        self.com_status_label.pack(side="left", padx=(8, 0))

    def refresh_com_ports(self):
        try:
            ports = [p.device for p in list_ports.comports()]
        except Exception:
            ports = []
        opts = ["None"] + ports if ports else ["None"]
        if hasattr(self, 'com_port_menu'):
            try:
                menu = self.com_port_menu["menu"]
                menu.delete(0, 'end')
                for p in opts:
                    menu.add_command(label=p, command=lambda v=p: self.on_com_selected(v))
            except Exception:
                pass
        # pick a sensible current selection
        if getattr(self, 'com_port_selected', None) and self.com_port_selected in ports:
            sel = self.com_port_selected
        else:
            sel = ports[0] if ports else "None"
            self.com_port_selected = None if sel == "None" else sel
        try:
            self.com_port_var.set(sel)
        except Exception:
            pass
        # update status label and color
        if hasattr(self, 'com_port_label_var'):
            try:
                self.com_port_label_var.set(self.com_port_selected or "")
            except Exception:
                pass
        if hasattr(self, 'com_status_label'):
            try:
                bg = "#aaddaa" if self.ser else "#dddddd"
                self.com_status_label.config(bg=bg)
            except Exception:
                pass
        print(f"COM ports refreshed: {opts}")

    def set_com_status(self, text: str, color: str = "#dddddd"):
        try:
            if hasattr(self, 'com_port_label_var'):
                self.com_port_label_var.set(text)
        except Exception:
            pass
        try:
            if hasattr(self, 'com_status_label'):
                self.com_status_label.config(bg=color)
        except Exception:
            pass

    def on_com_selected(self, val: str):
        if val == "None":
            self.com_port_selected = None
            try:
                self.com_port_var.set("None")
            except Exception:
                pass
            print("COM port cleared")
        else:
            self.com_port_selected = str(val)
            try:
                self.com_port_var.set(self.com_port_selected)
            except Exception:
                pass
            print(f"COM port selected: {self.com_port_selected}")
        # update status label text but reset color
        try:
            self.set_com_status(self.com_port_selected or "", "#dddddd")
        except Exception:
            pass

    def on_com_open_toggle(self):
        """Open or close the selected COM port (stores instance in self.ser)."""
        # If already open, close it
        if getattr(self, 'ser', None) is not None:
            try:
                self.ser.close()
            except Exception:
                pass
            self.ser = None
            try:
                if hasattr(self, 'com_open_btn'):
                    self.com_open_btn.config(text="Open")
            except Exception:
                pass
            self.set_com_status("Closed", "#dddddd")
            print("COM port closed")
            return

        # Not open: try to open
        if not getattr(self, 'com_port_selected', None):
            self.set_com_status("No port", "#ffcccc")
            print("No COM port selected to open")
            return

        if serial is None:
            self.set_com_status("pyserial missing", "#ffcccc")
            print("pyserial module not available; cannot open COM ports")
            return

        try:
            baud = int(self.com_baud_var.get())
        except Exception:
            baud = 115200
        # attempt open
        try:
            self.set_com_status("Opening...", "#ffffaa")
            ser = serial.Serial(self.com_port_selected, baudrate=baud, timeout=0.1)
            self.ser = ser
            self.start_serial_poll()
            try:
                if hasattr(self, 'com_open_btn'):
                    self.com_open_btn.config(text="Close")
            except Exception:
                pass
            self.set_com_status(f"Opened {self.com_port_selected}", "#aaddaa")
            print(f"Opened COM port {self.com_port_selected} at {baud} bps")
        except Exception as e:
            self.set_com_status(f"Error", "#ffaaaa")
            print(f"Failed to open {self.com_port_selected}: {e}")

    def request_refresh_function_boxes(self):
        """Throttle refreshes to at most 20Hz. If called more frequently, a single
        pending refresh is scheduled to run after the remaining wait time."""
        now = time.time()
        elapsed = now - getattr(self, '_last_refresh_time', 0.0)
        if elapsed >= getattr(self, '_min_refresh_interval', 0.05):
            # do immediate refresh
            try:
                # cancel any pending scheduled refresh
                if getattr(self, '_refresh_pending_id', None) is not None:
                    try:
                        self.after_cancel(self._refresh_pending_id)
                    except Exception:
                        pass
                    self._refresh_pending_id = None
            except Exception:
                pass
            # call the original implementation (from the class) to avoid recursion
            try:
                type(self).refresh_function_boxes(self)
            finally:
                self._last_refresh_time = time.time()
        else:
            # schedule a single refresh after the remaining interval if not already scheduled
            rem = getattr(self, '_min_refresh_interval', 0.05) - elapsed
            if getattr(self, '_refresh_pending_id', None) is None:
                try:
                    delay_ms = max(1, int(rem * 1000))
                    self._refresh_pending_id = self.after(delay_ms, self._scheduled_refresh_callback)
                except Exception:
                    pass

    def _scheduled_refresh_callback(self):
        try:
            self._refresh_pending_id = None
        except Exception:
            pass
        try:
            type(self).refresh_function_boxes(self)
        finally:
            self._last_refresh_time = time.time()

    # --- I2C0 handlers ---
    def on_i2c0_sda_selected(self, val: str):
        """Select SDA pin for I2C0 (only pins currently in SDA0 appear in menu)."""
        if val == PinMode.UNUSED.value or val == "----":
            self.i2c0_sda_selected = None
            self.i2c0_config['sda'] = None
            if hasattr(self, "i2c0_sda_var"):
                try:
                    self.i2c0_sda_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            try:
                self.refresh_function_boxes()
            except Exception:
                pass
            try:
                i2c0.sda_pin = None
            except Exception:
                pass
            print("I2C0 SDA selection cleared")
            return
        pin_str = str(val)
        if pin_str.startswith("GP"):
            pin_str = pin_str[2:]
        try:
            pin = int(pin_str)
        except Exception:
            return
        if self.pins.get(pin) and self.pins[pin].mode == PinMode.SDA0:
            self.i2c0_sda_selected = pin
            self.i2c0_config['sda'] = pin
            if hasattr(self, "i2c0_sda_var"):
                try:
                    self.i2c0_sda_var.set(f"GP{pin}")
                except Exception:
                    pass
            try:
                self.refresh_function_boxes()
            except Exception:
                pass
            try:
                i2c0.sda_pin = pin
            except Exception:
                pass
            print(f"I2C0 SDA selected: GP{pin}")
        else:
            self.i2c0_sda_selected = None
            self.i2c0_config['sda'] = None
            if hasattr(self, "i2c0_sda_var"):
                try:
                    self.i2c0_sda_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            print(f"I2C0 SDA selection invalid for {val}")

    def on_i2c0_scl_selected(self, val: str):
        """Select SCL pin for I2C0."""
        if val == PinMode.UNUSED.value or val == "----":
            self.i2c0_scl_selected = None
            self.i2c0_config['scl'] = None
            if hasattr(self, "i2c0_scl_var"):
                try:
                    self.i2c0_scl_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            try:
                self.refresh_function_boxes()
            except Exception:
                pass
            try:
                i2c0.scl_pin = None
            except Exception:
                pass
            print("I2C0 SCL selection cleared")
            return
        pin_str = str(val)
        if pin_str.startswith("GP"):
            pin_str = pin_str[2:]
        try:
            pin = int(pin_str)
        except Exception:
            return
        if self.pins.get(pin) and self.pins[pin].mode == PinMode.SCL0:
            self.i2c0_scl_selected = pin
            self.i2c0_config['scl'] = pin
            if hasattr(self, "i2c0_scl_var"):
                try:
                    self.i2c0_scl_var.set(f"GP{pin}")
                except Exception:
                    pass
            try:
                self.refresh_function_boxes()
            except Exception:
                pass
            try:
                i2c0.scl_pin = pin
            except Exception:
                pass
            print(f"I2C0 SCL selected: GP{pin}")
        else:
            self.i2c0_scl_selected = None
            self.i2c0_config['scl'] = None
            if hasattr(self, "i2c0_scl_var"):
                try:
                    self.i2c0_scl_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            print(f"I2C0 SCL selection invalid for {val}")

    def on_i2c0_scan(self):
        """Simulate a simple I2C scan and show found addresses in hex."""
        # Simple simulation: if both SDA and SCL are selected, pretend we found a couple of devices
        found = []
        if self.i2c0_sda_selected is not None and self.i2c0_scl_selected is not None:
            found = [0x3C, 0x50]
        elif self.i2c0_sda_selected is not None or self.i2c0_scl_selected is not None:
            found = [0x50]
        if not found:
            txt = "No devices found"
        else:
            txt = 'Found: ' + ' '.join(f"0x{a:02X}" for a in found)
        try:
            self.i2c0_scan_var.set(txt)
        except Exception:
            pass
        print(f"I2C0 scan result: {txt}")

    def on_i2c0_send(self, addr_text: str, text: str):
        """Send bytes to an I2C address (persist address and send hex)."""
        addr_text = str(addr_text).strip()
        text = str(text).strip()
        # persist address and send text
        self.i2c0_config['address'] = addr_text
        self.i2c0_config['send_hex'] = text

        if not text:
            self.i2c0_config['bytes_to_send'] = []
            try:
                i2c0.bytes_to_send = []
            except Exception:
                pass
            return

        # parse send hex similar to SPI
        bytes_list = []
        for part in text.split():
            try:
                byte = int(part, 16)
                if 0 <= byte <= 255:
                    bytes_list.append(byte)
            except Exception:
                pass
        self.i2c0_config['bytes_to_send'] = bytes_list
        try:
            i2c0.bytes_to_send = bytes_list
        except Exception:
            pass

        # simulate response: invert bits of each byte
        try:
            i2c0.received_bytes = [b ^ 0xFF for b in bytes_list]
        except Exception:
            pass

        # update recv display and persist
        if hasattr(self, 'i2c0_receive_var'):
            try:
                hex_str = ' '.join(f"{b:02X}" for b in (getattr(i2c0, 'received_bytes', []) or self.i2c0_config.get('received_bytes') or []))
                self.i2c0_receive_var.set(hex_str)
            except Exception:
                pass
        try:
            self.i2c0_config['received_bytes'] = list(getattr(i2c0, 'received_bytes', self.i2c0_config.get('received_bytes') or []))
        except Exception:
            pass
        print(f"I2C0 send to {addr_text}: {text}")

    def update_i2c0_speed(self, khz: int):
        try:
            i2c0.frequency_khz = khz
        except Exception:
            pass
        self.i2c0_config['khz'] = khz
        print(f"I2C0 frequency set to {khz} kHz")

    def on_i2c0_receive_bytes(self):
        rx = getattr(i2c0, 'received_bytes', None)
        if rx is None:
            return
        hex_str = ' '.join(f"{b:02X}" for b in rx)
        try:
            self.i2c0_config['received_bytes'] = list(rx)
        except Exception:
            pass
        if hasattr(self, "i2c0_receive_var"):
            try:
                self.i2c0_receive_var.set(hex_str)
            except Exception:
                pass

    # --- I2C1 handlers (mirror I2C0) ---
    def on_i2c1_sda_selected(self, val: str):
        if val == PinMode.UNUSED.value or val == "----":
            self.i2c1_sda_selected = None
            self.i2c1_config['sda'] = None
            if hasattr(self, "i2c1_sda_var"):
                try:
                    self.i2c1_sda_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            try:
                self.refresh_function_boxes()
            except Exception:
                pass
            try:
                i2c1.sda_pin = None
            except Exception:
                pass
            print("I2C1 SDA selection cleared")
            return
        pin_str = str(val)
        if pin_str.startswith("GP"):
            pin_str = pin_str[2:]
        try:
            pin = int(pin_str)
        except Exception:
            return
        if self.pins.get(pin) and self.pins[pin].mode == PinMode.SDA1:
            self.i2c1_sda_selected = pin
            self.i2c1_config['sda'] = pin
            if hasattr(self, "i2c1_sda_var"):
                try:
                    self.i2c1_sda_var.set(f"GP{pin}")
                except Exception:
                    pass
            try:
                self.refresh_function_boxes()
            except Exception:
                pass
            try:
                i2c1.sda_pin = pin
            except Exception:
                pass
            print(f"I2C1 SDA selected: GP{pin}")
        else:
            self.i2c1_sda_selected = None
            self.i2c1_config['sda'] = None
            if hasattr(self, "i2c1_sda_var"):
                try:
                    self.i2c1_sda_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            print(f"I2C1 SDA selection invalid for {val}")

    def on_i2c1_scl_selected(self, val: str):
        if val == PinMode.UNUSED.value or val == "----":
            self.i2c1_scl_selected = None
            self.i2c1_config['scl'] = None
            if hasattr(self, "i2c1_scl_var"):
                try:
                    self.i2c1_scl_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            try:
                self.refresh_function_boxes()
            except Exception:
                pass
            try:
                i2c1.scl_pin = None
            except Exception:
                pass
            print("I2C1 SCL selection cleared")
            return
        pin_str = str(val)
        if pin_str.startswith("GP"):
            pin_str = pin_str[2:]
        try:
            pin = int(pin_str)
        except Exception:
            return
        if self.pins.get(pin) and self.pins[pin].mode == PinMode.SCL1:
            self.i2c1_scl_selected = pin
            self.i2c1_config['scl'] = pin
            if hasattr(self, "i2c1_scl_var"):
                try:
                    self.i2c1_scl_var.set(f"GP{pin}")
                except Exception:
                    pass
            try:
                self.refresh_function_boxes()
            except Exception:
                pass
            try:
                i2c1.scl_pin = pin
            except Exception:
                pass
            print(f"I2C1 SCL selected: GP{pin}")
        else:
            self.i2c1_scl_selected = None
            self.i2c1_config['scl'] = None
            if hasattr(self, "i2c1_scl_var"):
                try:
                    self.i2c1_scl_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            print(f"I2C1 SCL selection invalid for {val}")

    def on_i2c1_scan(self):
        found = []
        if self.i2c1_sda_selected is not None and self.i2c1_scl_selected is not None:
            found = [0x3C, 0x50]
        elif self.i2c1_sda_selected is not None or self.i2c1_scl_selected is not None:
            found = [0x50]
        if not found:
            txt = "No devices found"
        else:
            txt = 'Found: ' + ' '.join(f"0x{a:02X}" for a in found)
        try:
            self.i2c1_scan_var.set(txt)
        except Exception:
            pass
        print(f"I2C1 scan result: {txt}")

    def on_i2c1_send(self, addr_text: str, text: str):
        addr_text = str(addr_text).strip()
        text = str(text).strip()
        self.i2c1_config['address'] = addr_text
        self.i2c1_config['send_hex'] = text
        if not text:
            self.i2c1_config['bytes_to_send'] = []
            try:
                i2c1.bytes_to_send = []
            except Exception:
                pass
            return
        bytes_list = []
        for part in text.split():
            try:
                byte = int(part, 16)
                if 0 <= byte <= 255:
                    bytes_list.append(byte)
            except Exception:
                pass
        self.i2c1_config['bytes_to_send'] = bytes_list
        try:
            i2c1.bytes_to_send = bytes_list
        except Exception:
            pass
        try:
            i2c1.received_bytes = [b ^ 0xFF for b in bytes_list]
        except Exception:
            pass
        try:
            hex_str = ' '.join(f"{b:02X}" for b in (getattr(i2c1, 'received_bytes', []) or self.i2c1_config.get('received_bytes') or []))
            if hasattr(self, 'i2c1_receive_var'):
                self.i2c1_receive_var.set(hex_str)
        except Exception:
            pass
        try:
            self.i2c1_config['received_bytes'] = list(getattr(i2c1, 'received_bytes', self.i2c1_config.get('received_bytes') or []))
        except Exception:
            pass
        print(f"I2C1 send to {addr_text}: {text}")

    def update_i2c1_speed(self, khz: int):
        try:
            i2c1.frequency_khz = khz
        except Exception:
            pass
        self.i2c1_config['khz'] = khz
        print(f"I2C1 frequency set to {khz} kHz")

    def on_i2c1_receive_bytes(self):
        rx = getattr(i2c1, 'received_bytes', None)
        if rx is None:
            return
        hex_str = ' '.join(f"{b:02X}" for b in rx)
        try:
            self.i2c1_config['received_bytes'] = list(rx)
        except Exception:
            pass
        if hasattr(self, "i2c1_receive_var"):
            try:
                self.i2c1_receive_var.set(hex_str)
            except Exception:
                pass

    # --- UART0 Handlers ---
    def on_uart0_tx_selected(self, val: str):
        """Select TX pin for UART0 (only pins currently in TX0 appear in menu)."""
        if val == PinMode.UNUSED.value or val == "----":
            self.uart0_tx_selected = None
            self.uart0_config['tx'] = None
            if hasattr(self, "uart0_tx_var"):
                try:
                    self.uart0_tx_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            try:
                self.refresh_function_boxes()
            except Exception:
                pass
            try:
                uart0.tx_pin = None
            except Exception:
                pass
            #print("UART0 TX selection cleared")
            self.send_pin_parameter(0, "uart0_tx", 255)
            return
        pin_str = str(val)
        if pin_str.startswith("GP"):
            pin_str = pin_str[2:]
        try:
            pin = int(pin_str)
        except Exception:
            return
        if self.pins.get(pin) and self.pins[pin].mode == PinMode.TX0:
            self.uart0_tx_selected = pin
            self.uart0_config['tx'] = pin
            if hasattr(self, "uart0_tx_var"):
                try:
                    self.uart0_tx_var.set(f"GP{pin}")
                except Exception:
                    pass
            try:
                self.refresh_function_boxes()
            except Exception:
                pass
            try:
                uart0.tx_pin = pin
            except Exception:
                pass
            #print(f"UART0 TX selected: GP{pin}")
            self.send_pin_parameter(0, "uart0_tx", pin)
        else:
            self.uart0_tx_selected = None
            self.uart0_config['tx'] = None
            if hasattr(self, "uart0_tx_var"):
                try:
                    self.uart0_tx_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            print(f"UART0 TX selection invalid for {val}")

    def on_uart0_rx_selected(self, val: str):
        """Select RX pin for UART0 (only pins currently in RX0 appear in menu)."""
        if val == PinMode.UNUSED.value or val == "----":
            self.uart0_rx_selected = None
            self.uart0_config['rx'] = None
            if hasattr(self, "uart0_rx_var"):
                try:
                    self.uart0_rx_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            try:
                self.refresh_function_boxes()
            except Exception:
                pass
            try:
                uart0.rx_pin = None
            except Exception:
                pass
            #print("UART0 RX selection cleared")
            self.send_pin_parameter(0, "uart0_rx", 255)
            return
        pin_str = str(val)
        if pin_str.startswith("GP"):
            pin_str = pin_str[2:]
        try:
            pin = int(pin_str)
        except Exception:
            return
        if self.pins.get(pin) and self.pins[pin].mode == PinMode.RX0:
            self.uart0_rx_selected = pin
            self.uart0_config['rx'] = pin
            if hasattr(self, "uart0_rx_var"):
                try:
                    self.uart0_rx_var.set(f"GP{pin}")
                except Exception:
                    pass
            try:
                self.refresh_function_boxes()
            except Exception:
                pass
            try:
                uart0.rx_pin = pin
            except Exception:
                pass
            #print(f"UART0 RX selected: GP{pin}")
            self.send_pin_parameter(0, "uart0_rx", pin)
        else:
            self.uart0_rx_selected = None
            self.uart0_config['rx'] = None
            if hasattr(self, "uart0_rx_var"):
                try:
                    self.uart0_rx_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            print(f"UART0 RX selection invalid for {val}")

    def on_uart0_send(self, text: str):
        """Send text over UART0 (persist and show simulated response)."""
        text = str(text or "")
        self.uart0_config['send_text'] = text
        if not text:
            self.uart0_config['bytes_to_send'] = []
            uart0.bytes_to_send = []
            return
        #try:
        #    data = text.encode('utf-8')
        #    uart0.bytes_to_send = list(data)
        #    self.uart0_config['bytes_to_send'] = list(data)
        #except Exception:
        #    data = b""
        # simulate a response: echo back the same bytes
        #try:
        #    uart0.received_bytes = data
        #except Exception:
        #    pass
        # update received text display and persist
        # try:
        #     recv_text = (getattr(uart0, 'received_bytes', b'') or b'').decode('utf-8', errors='replace')
        #     if hasattr(self, 'uart0_receive_var'):
        #         self.uart0_receive_var.set(recv_text)
        #     self.uart0_config['received_text'] = recv_text
        # except Exception:
        #     pass
        print(f"UART0 send: {text}")
        self.uart0_config['bytes_to_send'] = text
        try:
            uart0.bytes_to_send = text
        except Exception:
            pass

        self.send_pin_parameter(255, 'uart0_send', text)


    def update_uart0_baud(self, baud: int):
        #try:
        uart0.baud = baud
        #except Exception:
        #    pass
        self.uart0_config['baud'] = baud
        #print(f"UART0 baud set to {baud}")
        self.send_pin_parameter(255, 'uart0_baud', int(baud))

    def on_uart0_receive(self):
        rx = getattr(uart0, 'received_bytes', None)
        self.uart0_receive_var.set(rx)

        # if rx is None:
        #     return
        # try:
        #     txt = ' '.join(f"{b:02X}" for b in rx)
        # except Exception:
        #     txt = ''
        # try:
        #     self.uart0_config['received_text'] = (rx.decode('utf-8', errors='replace') if isinstance(rx, (bytes, bytearray)) else str(rx))
        #     if hasattr(self, 'uart0_receive_var'):
        #         self.uart0_receive_var.set(self.uart0_config['received_text'])
        # except Exception:
        #     pass

    # --- UART1 handlers (mirror UART0) ---
    def on_uart1_tx_selected(self, val: str):
        if val == PinMode.UNUSED.value or val == "----":
            self.uart1_tx_selected = None
            self.uart1_config['tx'] = None
            if hasattr(self, "uart1_tx_var"):
                try:
                    self.uart1_tx_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            try:
                self.refresh_function_boxes()
            except Exception:
                pass
            try:
                uart1.tx_pin = None
            except Exception:
                pass
            #print("UART1 TX selection cleared")
            self.send_pin_parameter(0, "uart1_tx", 255)
            return
        pin_str = str(val)
        if pin_str.startswith("GP"):
            pin_str = pin_str[2:]
        try:
            pin = int(pin_str)
        except Exception:
            return
        if self.pins.get(pin) and self.pins[pin].mode == PinMode.TX1:
            self.uart1_tx_selected = pin
            self.uart1_config['tx'] = pin
            if hasattr(self, "uart1_tx_var"):
                try:
                    self.uart1_tx_var.set(f"GP{pin}")
                except Exception:
                    pass
            try:
                self.refresh_function_boxes()
            except Exception:
                pass
            try:
                uart1.tx_pin = pin
            except Exception:
                pass
            #print(f"UART1 TX selected: GP{pin}")
            self.send_pin_parameter(0, "uart1_tx", pin)
        else:
            self.uart1_tx_selected = None
            self.uart1_config['tx'] = None
            if hasattr(self, "uart1_tx_var"):
                try:
                    self.uart1_tx_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            print(f"UART1 TX selection invalid for {val}")

    def on_uart1_rx_selected(self, val: str):
        if val == PinMode.UNUSED.value or val == "----":
            self.uart1_rx_selected = None
            self.uart1_config['rx'] = None
            if hasattr(self, "uart1_rx_var"):
                try:
                    self.uart1_rx_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            try:
                self.refresh_function_boxes()
            except Exception:
                pass
            try:
                uart1.rx_pin = None
            except Exception:
                pass
            #print("UART1 RX selection cleared")
            self.send_pin_parameter(0, "uart1_rx", 255)
            return
        pin_str = str(val)
        if pin_str.startswith("GP"):
            pin_str = pin_str[2:]
        try:
            pin = int(pin_str)
        except Exception:
            return
        if self.pins.get(pin) and self.pins[pin].mode == PinMode.RX1:
            self.uart1_rx_selected = pin
            self.uart1_config['rx'] = pin
            if hasattr(self, "uart1_rx_var"):
                try:
                    self.uart1_rx_var.set(f"GP{pin}")
                except Exception:
                    pass
            try:
                self.refresh_function_boxes()
            except Exception:
                pass
            try:
                uart1.rx_pin = pin
            except Exception:
                pass
            #print(f"UART1 RX selected: GP{pin}")
            self.send_pin_parameter(0, "uart1_rx", pin)
        else:
            self.uart1_rx_selected = None
            self.uart1_config['rx'] = None
            if hasattr(self, "uart1_rx_var"):
                try:
                    self.uart1_rx_var.set(PinMode.UNUSED.value)
                except Exception:
                    pass
            print(f"UART1 RX selection invalid for {val}")

    def on_uart1_send(self, text: str):
        """Send text over UART1 (persist and show simulated response)."""
        text = str(text or "")
        self.uart1_config['send_text'] = text
        if not text:
            self.uart1_config['bytes_to_send'] = []
            uart1.bytes_to_send = []
            return
        print(f"UART1 send: {text}")
        self.uart1_config['bytes_to_send'] = text
        try:
            uart1.bytes_to_send = text
        except Exception:
            pass

        self.send_pin_parameter(255, 'uart1_send', text)

    def update_uart1_baud(self, baud: int):
        #try:
        uart1.baud = baud
        #except Exception:
        #    pass
        self.uart1_config['baud'] = baud
        self.send_pin_parameter(255, 'uart1_baud', int(baud))

    def on_uart1_receive(self):
        rx = getattr(uart1, 'received_bytes', None)
        self.uart1_receive_var.set(rx)




if __name__ == "__main__":
    app = PicoGUI()
    app.mainloop()
