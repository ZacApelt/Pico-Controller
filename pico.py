import time
from machine import Pin, PWM, ADC, I2C, SPI, UART
import math
import utime
import ustruct
import sys
import uselect

'''
param: 	values:
mode	UNUSED, DOUT, DIN, PWM, ADC, MISO0, MOSI0, SCK0, MISO1, MOSI01, SCK1, SDA0, SCL0, SDA1, SCL1, TX0, RX0, TX1, RX1

TODO:
- DIN on change events
- SPI / I2C / UART functionality
'''
pins = {0: Pin(0), 1: Pin(1), 2: Pin(2), 3: Pin(3), 4: Pin(4), 5: Pin(5),
        6: Pin(6), 7: Pin(7), 8: Pin(8), 9: Pin(9), 10: Pin(10), 11: Pin(11),
        12: Pin(12), 13: Pin(13), 14: Pin(14), 15: Pin(15), 16: Pin(16),
        17: Pin(17), 18: Pin(18), 19: Pin(19), 20: Pin(20), 21: Pin(21),
        22: Pin(22), 25: Pin(25), 26: Pin(26), 27: Pin(27), 28: Pin(28)}

pwm_map = {}
adc_map = {}
din_map = {}
# track requested pull-up/down state per pin (None, 'Pull-Up', 'Pull-Down')
pud_map = {}
din_last = {}  # pin -> last_value

sync_start = time.ticks_ms()

spoll = uselect.poll()
spoll.register(sys.stdin, uselect.POLLIN)

while True:
    if spoll.poll(0): 
        data = sys.stdin.read(1)  # Read one byte if data is available
        if data:
            try:
                line = (data + sys.stdin.readline()).strip()  # Read the rest of the line
                #print(f"Received: {line}")

                parts = line.split(',')
                pin = int(parts[0])
                param = parts[1]
                value = parts[2]

                p = pins[pin]

                # Handle entering PWM/ADC modes and cleanup when switching out
                if param == "mode" and value == "PWM":
                    p.init(p.OUT)
                    pwm = pwm_map.get(pin)
                    if pwm is None:
                        pwm = PWM(p)
                        pwm_map[pin] = pwm
                    pwm.duty_u16(0)
                    pwm.freq(1000)
                elif param == "mode" and value == "ADC":
                    # Initialize ADC object for this pin so later code can read it
                    p.init(p.IN)
                    adc = adc_map.get(pin)
                    if adc is None:
                        adc = ADC(p)
                        adc_map[pin] = adc
                elif param == "mode" and value == "DIN":
                    # Use the requested pull state if it's already set; otherwise leave no pull
                    pud = pud_map.get(pin)
                    if pud == "Pull-Up":
                        p.init(p.IN, p.PULL_UP)
                    elif pud == "Pull-Down":
                        p.init(p.IN, p.PULL_DOWN)
                    else:
                        p.init(p.IN)
                    din_map[pin] = p
    
                else:
                    # when switching away from PWM/ADC: cleanup any allocated objects
                    if pin in pwm_map:
                        try:
                            pwm_map[pin].deinit()
                        except Exception:
                            pass
                        del pwm_map[pin]
                    if pin in adc_map:
                        try:
                            del adc_map[pin]
                        except Exception:
                            pass
                    if pin in din_map:
                        try:
                            del din_map[pin]
                        except Exception:
                            pass


                if param == "mode":
                    if value == "UNUSED":
                        p.init(p.IN, p.PULL_DOWN)  # Set to input as default
                    elif value == "DOUT":
                        p.init(p.OUT)
                    elif value == "DIN":
                        # Ensure the requested pull state is applied (reapply if necessary)
                        pud = pud_map.get(pin)
                        if pud == "Pull-Up":
                            p.init(p.IN, p.PULL_UP)
                        elif pud == "Pull-Down":
                            p.init(p.IN, p.PULL_DOWN)
                        else:
                            # leave input with no pull
                            p.init(p.IN)
                
                elif param == "dout":
                    p.value(int(value))
                
                elif param == "pud":
                    # Remember requested pull state so it can be reapplied when switching into DIN
                    pud_map[pin] = value if value in ("Pull-Up", "Pull-Down") else None
                    if value == "Pull-Up":
                        p.init(p.IN, p.PULL_UP)
                    elif value == "Pull-Down":
                        p.init(p.IN, p.PULL_DOWN)
                    else:
                        p.init(p.IN)  # No pull
                
                elif param == "pwm_duty":
                    # Accept integer or decimal percent values (e.g. "56.98").
                    # Parse as float then convert to the integer range expected by duty_u16.
                    raw = float(value)
                    pwm = pwm_map.get(pin)
                    if pwm is None:
                        pwm = PWM(p)
                        pwm_map[pin] = pwm

                    # If value is in 0-100 treat as percent, otherwise treat as raw duty value
                    if 0 <= raw <= 100:
                        raw = int(raw * 65535 / 100)
                    else:
                        raw = int(raw)

                    raw = max(0, min(65535, raw))
                    pwm.duty_u16(raw)
                
                elif param == "pwm_freq":
                    # Accept numeric values including decimals (e.g. "2.0").
                    # PWM.freq expects an integer Hz value, so parse as float and
                    # convert to an integer frequency (rounded) with validation.

                    freq_f = float(value)

                    freq = int(round(freq_f))

                    pwm = pwm_map.get(pin)
                    if pwm is None:
                        pwm = PWM(p)
                        pwm_map[pin] = pwm
                    pwm.freq(freq)
                    
            except Exception as e:
                print(f"Error reading line: {e}")
    
    # Perform other tasks here
    # if time > 100ms, send updates
    now = time.ticks_ms()
    if time.ticks_diff(now, sync_start) > 100:
        
        # read all ADCs and send their values
        for pin, adc in adc_map.items():
            adc_value = adc.read_u16()
            print(f"{pin},adc_value,{adc_value}")

        for pin, din_pin in din_map.items():
            v = din_pin.value()
            if din_last.get(pin) != v:
                print(f"{pin},din,{v}")
                din_last[pin] = v

        sync_start = now