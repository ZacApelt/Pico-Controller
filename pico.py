import time
from machine import Pin, PWM, ADC, I2C, SPI, UART
import math
import utime
import ustruct
import sys
import uselect


pins = {0: Pin(0), 1: Pin(1), 2: Pin(2), 3: Pin(3), 4: Pin(4), 5: Pin(5),
        6: Pin(6), 7: Pin(7), 8: Pin(8), 9: Pin(9), 10: Pin(10), 11: Pin(11),
        12: Pin(12), 13: Pin(13), 14: Pin(14), 15: Pin(15), 16: Pin(16),
        17: Pin(17), 18: Pin(18), 19: Pin(19), 20: Pin(20), 21: Pin(21),
        22: Pin(22), 25: Pin(25), 26: Pin(26), 27: Pin(27), 28: Pin(28)}

pwm_map = {}

spoll = uselect.poll()
spoll.register(sys.stdin, uselect.POLLIN)

while True:
    if spoll.poll(0): 
        data = sys.stdin.read(1)  # Read one byte if data is available
        if data:
            try:
                line = (data + sys.stdin.readline()).strip()  # Read the rest of the line
                print(f"Received: {line}")

                parts = line.split(',')
                pin = int(parts[0])
                param = parts[1]
                value = parts[2]

                p = pins[pin]


                if param == "mode" and value == "PWM":
                    p.init(p.OUT)
                    pwm = pwm_map.get(pin)
                    if pwm is None:
                        pwm = PWM(p)
                        pwm_map[pin] = pwm
                    pwm.duty_u16(0)
                    pwm.freq(1000)
                # when switching away from PWM (cleanup)
                else:
                    # on any non-PWM mode set, deinit if exists
                    if pin in pwm_map:
                        try:
                            pwm_map[pin].deinit()
                        except Exception:
                            pass
                        del pwm_map[pin]


                if param == "mode":
                    if value == "UNUSED":
                        p.init(p.IN, p.PULL_DOWN)  # Set to input as default
                    elif value == "DOUT":
                        p.init(pin, p.OUT)
                    elif value == "DIN":
                        p.init(pin, p.IN)
                
                elif param == "dout":
                    p.value(int(value))
                
                elif param == "pud":
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