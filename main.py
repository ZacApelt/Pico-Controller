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

spi0 = None
spi1 = None

spi0_baudrate = 1_000_000
spi1_baudrate = 1_000_000
spi0_polarity = 0
spi1_polarity = 0
spi0_phase = 0
spi1_phase = 0


# Track which pins are configured for SPI0 signals so we can re-init SPI safely
spi0_csn_pin =  None
spi0_mosi_pin = None
spi0_miso_pin = None
spi0_sck_pin =  None

spi1_csn_pin =  None
spi1_mosi_pin = None
spi1_miso_pin = None
spi1_sck_pin =  None

uart0 = None
uart1 = None
uart0_baud = 115200
uart1_baud = 115200
uart0_tx_pin = None
uart0_rx_pin = None
uart1_tx_pin = None
uart1_rx_pin = None

i2c0 = None
i2c1 = None
i2c0_freq = 100_000
i2c1_freq = 100_000
i2c0_sda_pin = None
i2c0_scl_pin = None
i2c1_sda_pin = None
i2c1_scl_pin = None


def reinit_spi0():
    global spi0

    # Need SCK always
    if spi0_sck_pin is None:
        # no clock => SPI unusable
        spi0 = None
        print("255,spi0_config,incomplete,no_sck")
        return

    # Need at least one data direction
    if spi0_mosi_pin is None and spi0_miso_pin is None:
        spi0 = None
        print("255,spi0_config,incomplete,no_data")
        return

    try:
        if spi0 is not None:
            spi0.deinit()
    except Exception:
        pass

    kwargs = dict(
        baudrate=spi0_baudrate,
        polarity=spi0_polarity,
        phase=spi0_phase,
        sck=pins[spi0_sck_pin],
    )

    # Only include pins that are set
    if spi0_mosi_pin is not None:
        kwargs["mosi"] = pins[spi0_mosi_pin]
    if spi0_miso_pin is not None:
        kwargs["miso"] = pins[spi0_miso_pin]

    try:
        spi0 = SPI(0, **kwargs)
        print(f"255,spi0_config,ok,sck={spi0_sck_pin},mosi={spi0_mosi_pin},miso={spi0_miso_pin},baud={spi0_baudrate}")
    except Exception as e:
        spi0 = None
        print(f"255,spi0_config,failed,{repr(e)}")

def reinit_spi1():
    global spi1

    # Need SCK always
    if spi1_sck_pin is None:
        # no clock => SPI unusable
        spi1 = None
        print("255,spi1_config,incomplete,no_sck")
        return

    # Need at least one data direction
    if spi1_mosi_pin is None and spi1_miso_pin is None:
        spi1 = None
        print("255,spi1_config,incomplete,no_data")
        return

    try:
        if spi1 is not None:
            spi1.deinit()
    except Exception:
        pass

    kwargs = dict(
        baudrate=spi1_baudrate,
        polarity=spi1_polarity,
        phase=spi1_phase,
        sck=pins[spi1_sck_pin],
    )

    # Only include pins that are set
    if spi1_mosi_pin is not None:
        kwargs["mosi"] = pins[spi1_mosi_pin]
    if spi1_miso_pin is not None:
        kwargs["miso"] = pins[spi1_miso_pin]

    try:
        spi1 = SPI(1, **kwargs)
        print(f"255,spi1_config,ok,sck={spi1_sck_pin},mosi={spi1_mosi_pin},miso={spi1_miso_pin},baud={spi1_baudrate}")
    except Exception as e:
        spi1 = None
        print(f"255,spi1_config,failed,{repr(e)}")


def reinit_uart0():
    global uart0

    # Need tx pin
    if uart0_tx_pin is None and uart0_rx_pin is None:
        # uart0 unusable
        uart0 = None
        print("255,uart0_config,incomplete,no_uart0_pins")
        return

    try:
        if uart0 is not None:
            uart0.deinit()
    except Exception:
        pass

    kwargs = dict(
        baudrate=uart0_baud,
        bits=8,
        parity=None,
        stop=1,
    )

    # Only include pins that are set
    if uart0_rx_pin is not None:
        kwargs["rx"] = pins[uart0_rx_pin]
    if uart0_tx_pin is not None:
        kwargs["tx"] = pins[uart0_tx_pin]

    try:
        uart0 = UART(0, **kwargs)
        print(f"255,uart0_config,ok,tx={uart0_tx_pin},rx={uart0_rx_pin},baud={uart0_baud}")
    except Exception as e:
        uart0 = None
        print(f"255,uart0_config,failed,{repr(e)}")

def reinit_uart1():
    global uart1

    # Need tx pin
    if uart1_tx_pin is None and uart1_rx_pin is None:
        # uart1 unusable
        uart1 = None
        print("255,uart1_config,incomplete,no_uart1_pins")
        return

    try:
        if uart1 is not None:
            uart1.deinit()
    except Exception:
        pass

    kwargs = dict(
        baudrate=uart1_baud,
        bits=8,
        parity=None,
        stop=1,
    )

    # Only include pins that are set
    if uart1_rx_pin is not None:
        kwargs["rx"] = pins[uart1_rx_pin]
    if uart1_tx_pin is not None:
        kwargs["tx"] = pins[uart1_tx_pin]

    try:
        uart1 = UART(1, **kwargs)
        print(f"255,uart1_config,ok,tx={uart1_tx_pin},rx={uart1_rx_pin},baud={uart1_baud}")
    except Exception as e:
        uart1 = None
        print(f"255,uart1_config,failed,{repr(e)}")


def reinit_i2c0():
    global i2c0

    # Need both sda and scl
    if i2c0_sda_pin is None or i2c0_scl_pin is None:
        # i2c0 unusable
        i2c0 = None
        print("255,i2c0_config,incomplete,no_i2c0_pins")
        return

    try:
        if i2c0 is not None:
            i2c0.deinit()
    except Exception:
        pass

    kwargs = dict(
        freq=i2c0_freq,
    )

    # Only include pins that are set
    if i2c0_sda_pin is not None:
        kwargs["sda"] = pins[i2c0_sda_pin]
    if i2c0_scl_pin is not None:
        kwargs["scl"] = pins[i2c0_scl_pin]

    try:
        i2c0 = I2C(0, **kwargs)
        print(f"255,i2c0_config,ok,sda={i2c0_sda_pin},scl={i2c0_scl_pin},freq={i2c0_freq}")
    except Exception as e:
        i2c0 = None
        print(f"255,i2c0_config,failed,{repr(e)}")

def reinit_i2c1():
    global i2c1

    # Need both sda and scl
    if i2c1_sda_pin is None or i2c1_scl_pin is None:
        # i2c1 unusable
        i2c1 = None
        print("255,i2c1_config,incomplete,no_i2c1_pins")
        return

    try:
        if i2c1 is not None:
            i2c1.deinit()
    except Exception:
        pass

    kwargs = dict(
        freq=i2c1_freq,
    )

    # Only include pins that are set
    if i2c1_sda_pin is not None:
        kwargs["sda"] = pins[i2c1_sda_pin]
    if i2c1_scl_pin is not None:
        kwargs["scl"] = pins[i2c1_scl_pin]

    try:
        i2c1 = I2C(1, **kwargs)
        print(f"255,i2c1_config,ok,sda={i2c1_sda_pin},scl={i2c1_scl_pin},freq={i2c1_freq}")
    except Exception as e:
        i2c1 = None
        print(f"255,i2c1_config,failed,{repr(e)}")



def poll_uart0():
    if uart0 is None:
        return
    if uart0_rx_pin is None:
        return

    try:
        n = uart0.any()
    except Exception:
        return

    if not n:
        return

    # Read at most 256 bytes per loop to avoid starving other work
    to_read = 256 if n > 256 else n
    try:
        data = uart0.read(to_read)
    except Exception:
        return

    if data:
        try:
            text = data.decode("ascii")
        except Exception:
            text = "[decode error]"
        print(f"255,uart0_recv,{text}")

def poll_uart1():
    if uart1 is None:
        return
    if uart1_rx_pin is None:
        return

    try:
        n = uart1.any()
    except Exception:
        return

    if not n:
        return

    # Read at most 256 bytes per loop to avoid starving other work
    to_read = 256 if n > 256 else n
    try:
        data = uart1.read(to_read)
    except Exception:
        return

    if data:
        try:
            text = data.decode("ascii")
        except Exception:
            text = "[decode error]"
        print(f"255,uart1_recv,{text}")


sync_start = time.ticks_ms()

spoll = uselect.poll()
spoll.register(sys.stdin, uselect.POLLIN)

while True:
    if spoll.poll(0): 
        data = sys.stdin.read(1)  # Read one byte if data is available
        if data:
            #try:
            if True:
                line = (data + sys.stdin.readline()).strip()  # Read the rest of the line
                #print(f"Received: {line}")

                parts = line.split(',')
                pin = int(parts[0])
                param = parts[1]
                value = parts[2]

                #print(parts)

                if pin != 255:
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
                    
                    elif value == "SPI0 - MOSI":
                        spi0_mosi_pin = pin
                        reinit_spi0()
                    elif value == "SPI0 - MISO":
                        spi0_miso_pin = pin
                        reinit_spi0()
                    elif value == "SPI0 - SCK":
                        spi0_sck_pin = pin
                        reinit_spi0()
                    
                    elif value == "SPI1 - MOSI":
                        spi1_mosi_pin = pin
                        reinit_spi1()
                    elif value == "SPI1 - MISO":
                        spi1_miso_pin = pin
                        reinit_spi1()
                    elif value == "SPI1 - SCK":
                        spi1_sck_pin = pin
                        reinit_spi1()
                
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

                    # If this pin is currently in DIN mode, immediately report its value
                    # so the host GUI can update without requiring a mode reselect.
                    try:
                        if pin in din_map:
                            v = p.value()
                            print(f"{pin},din,{v}")
                            # keep din_last in sync to avoid duplicate prints at the next sync
                            din_last[pin] = v
                    except Exception:
                        pass
                
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
                
                elif param == "spi0_mosi":
                    v = int(value)
                    spi0_mosi_pin = None if v == 255 else v
                    reinit_spi0()

                elif param == "spi0_miso":
                    v = int(value)
                    spi0_miso_pin = None if v == 255 else v
                    reinit_spi0()

                elif param == "spi0_sck":
                    v = int(value)
                    spi0_sck_pin = None if v == 255 else v
                    reinit_spi0()

                elif param == "spi0_csn":
                    v = int(value)
                    if v == 255:
                        spi0_csn_pin = None
                    else:
                        spi0_csn_pin = v
                        csn = pins[spi0_csn_pin]
                        csn.init(Pin.OUT)
                        csn.value(1)  # deassert

                elif param == "spi0_kbaud":
                    # e.g. value="1000" means 1,000,000 baud
                    spi0_baudrate = int(value) * 1000
                    reinit_spi0()

                elif param == "spi0_send_hex":
                    # value is hex string bytes, e.g. "F7" or "0A1B2C"
                    if spi0 is None:
                        print("255,spi0_recv,error_not_configured")
                        continue

                    try:
                        tx = bytes.fromhex(value)
                    except Exception:
                        print("255,spi0_recv,error_bad_hex")
                        continue

                    rx = bytearray(len(tx))

                    if spi0_csn_pin is not None:
                        try:
                            pins[spi0_csn_pin].value(0)
                        except Exception:
                            pass

                    try:
                        spi0.write_readinto(tx, rx)
                    except Exception as e:
                        # ensure CSN released even on error
                        if spi0_csn_pin is not None:
                            try:
                                pins[spi0_csn_pin].value(1)
                            except Exception:
                                pass
                        print(f"255,spi0_recv,error,{repr(e)}")
                        continue

                    if spi0_csn_pin is not None:
                        try:
                            pins[spi0_csn_pin].value(1)
                        except Exception:
                            pass

                    recv_hex = ''.join('{:02X}'.format(b) for b in rx)
                    print(f"255,spi0_recv,{recv_hex}")
                
                elif param == "spi0_send_ascii":
                    if spi0 is None:
                        print("255,spi0_recv,error_not_configured")
                        continue

                    # Convert ASCII string to bytes to transmit
                    tx = value.encode("utf-8")   # or "ascii" if you want strict ASCII
                    rx = bytearray(len(tx))      # mutable buffer for received bytes

                    if spi0_csn_pin is not None:
                        try:
                            pins[spi0_csn_pin].value(0)
                        except Exception:
                            pass

                    try:
                        spi0.write_readinto(tx, rx)
                    except Exception as e:
                        if spi0_csn_pin is not None:
                            try:
                                pins[spi0_csn_pin].value(1)
                            except Exception:
                                pass
                        print(f"255,spi0_recv,error,{repr(e)}")
                        continue

                    if spi0_csn_pin is not None:
                        try:
                            pins[spi0_csn_pin].value(1)
                        except Exception:
                            pass

                    recv_hex = ''.join('{:02X}'.format(b) for b in rx)
                    print(f"255,spi0_recv,{recv_hex}")

                elif param == "spi1_mosi":
                    v = int(value)
                    spi1_mosi_pin = None if v == 255 else v
                    reinit_spi1()

                elif param == "spi1_miso":
                    v = int(value)
                    spi1_miso_pin = None if v == 255 else v
                    reinit_spi1()

                elif param == "spi1_sck":
                    v = int(value)
                    spi1_sck_pin = None if v == 255 else v
                    reinit_spi1()

                elif param == "spi1_csn":
                    v = int(value)
                    if v == 255:
                        spi1_csn_pin = None
                    else:
                        spi1_csn_pin = v
                        csn = pins[spi1_csn_pin]
                        csn.init(Pin.OUT)
                        csn.value(1)  # deassert

                elif param == "spi1_kbaud":
                    # e.g. value="1000" means 1,000,000 baud
                    spi1_baudrate = int(value) * 1000
                    reinit_spi1()

                elif param == "spi1_send":
                    # value is hex string bytes, e.g. "F7" or "0A1B2C"
                    if spi1 is None:
                        print("255,spi1_recv,error_not_configured")
                        continue

                    try:
                        tx = bytes.fromhex(value)
                    except Exception:
                        print("255,spi1_recv,error_bad_hex")
                        continue

                    rx = bytearray(len(tx))

                    if spi1_csn_pin is not None:
                        try:
                            pins[spi1_csn_pin].value(0)
                        except Exception:
                            pass

                    try:
                        spi1.write_readinto(tx, rx)
                    except Exception as e:
                        # ensure CSN released even on error
                        if spi1_csn_pin is not None:
                            try:
                                pins[spi1_csn_pin].value(1)
                            except Exception:
                                pass
                        print(f"255,spi1_recv,error,{repr(e)}")
                        continue

                    if spi1_csn_pin is not None:
                        try:
                            pins[spi1_csn_pin].value(1)
                        except Exception:
                            pass

                    recv_hex = ''.join('{:02X}'.format(b) for b in rx)
                    print(f"255,spi1_recv,{recv_hex}")
                

                elif param == "uart0_tx":
                    v = int(value)
                    uart0_tx_pin = None if v == 255 else v
                    reinit_uart0()

                elif param == "uart0_rx":
                    v = int(value)
                    uart0_rx_pin = None if v == 255 else v
                    reinit_uart0()

                elif param == "uart0_baud":
                    uart0_baud = int(value)
                    reinit_uart0()

                elif param == "uart0_send":
                    # value is string
                    if uart0 is None:
                        print("255,uart0_recv,error_not_configured")
                        continue

                    if len(value) > 2 and value[:2] == "0x":
                        # interpret as hexadecimal
                        value = value[2:]
                        try:
                            hex_string = bytes.fromhex(value)
                        except Exception as e:
                            print(f"255,uart0_send,failed,{repr(e)}")
                            continue
                        uart0.write(hex_string)
                    else:
                        # interpret as an ascii string
                        uart0.write(value)
                
                elif param == "uart1_tx":
                    v = int(value)
                    uart1_tx_pin = None if v == 255 else v
                    reinit_uart1()

                elif param == "uart1_rx":
                    v = int(value)
                    uart1_rx_pin = None if v == 255 else v
                    reinit_uart1()

                elif param == "uart1_baud":
                    uart1_baud = int(value)
                    reinit_uart1()

                elif param == "uart1_send":
                    # value is string
                    if uart1 is None:
                        print("255,uart1_recv,error_not_configured")
                        continue
                    
                    if len(value) > 2 and value[:2] == "0x":
                        # interpret as hexadecimal
                        value = value[2:]
                        try:
                            hex_string = bytes.fromhex(value)
                        except Exception as e:
                            print(f"255,uart1_send,failed,{repr(e)}")
                            continue
                        uart1.write(hex_string)
                    else:
                        # interpret as an ascii string
                        uart1.write(value)


                elif param == "i2c0_sda":
                    v = int(value)
                    i2c0_sda_pin = None if v == 255 else v
                    reinit_i2c0()

                elif param == "i2c0_scl":
                    v = int(value)
                    i2c0_scl_pin = None if v == 255 else v
                    reinit_i2c0()

                elif param == "i2c0_freq":
                    i2c0_freq = int(value)
                    reinit_i2c0()

                elif "i2c0_send" in param:
                    # looks like i2c0_send:71
                    # where 71 is the address

                    address = int(param.split(":")[1])

                    # value is string
                    if i2c0 is None:
                        print("255,i2c0_recv,error_not_configured")
                        continue

                    if len(value) > 2 and value[:2] == "0x":
                        # interpret as hexadecimal
                        value = value[2:]
                        try:
                            hex_string = bytes.fromhex(value)
                        except Exception as e:
                            print(f"255,i2c0_send,failed,{repr(e)}")
                            continue
                        try:
                            i2c0.writeto(address, hex_string)
                        except Exception as e:
                            print(f"255,i2c0_error,transaction_failed,{repr(e)}")
                    else:
                        # interpret as an ascii string
                        try:
                            i2c0.writeto(address, value.encode("utf-8"))
                        except Exception as e:
                            print(f"255,i2c0_error,transaction_failed,{repr(e)}")

                elif param == "i2c0_scan":
                    if i2c0 is not None:
                        addresses = i2c0.scan()
                        print(f"0,i2c0_addresses,{addresses}")
                    else:
                        print("255, i2c0_scan,error_not_configured")
                

                elif param == "i2c1_sda":
                    v = int(value)
                    i2c1_sda_pin = None if v == 255 else v
                    reinit_i2c1()

                elif param == "i2c1_scl":
                    v = int(value)
                    i2c1_scl_pin = None if v == 255 else v
                    reinit_i2c1()

                elif param == "i2c1_freq":
                    i2c1_freq = int(value)
                    reinit_i2c1()

                elif "i2c1_send" in param:
                    # looks like i2c1_send:71
                    # where 71 is the address

                    address = int(param.split(":")[1])

                    # value is string
                    if i2c1 is None:
                        print("255,i2c1_recv,error_not_configured")
                        continue

                    if len(value) > 2 and value[:2] == "0x":
                        # interpret as hexadecimal
                        value = value[2:]
                        try:
                            hex_string = bytes.fromhex(value)
                        except Exception as e:
                            print(f"255,i2c1_send,failed,{repr(e)}")
                            continue
                        try:
                            i2c1.writeto(address, hex_string)
                        except Exception as e:
                            print(f"255,i2c1_error,transaction_failed,{repr(e)}")
                    else:
                        # interpret as an ascii string
                        try:
                            i2c1.writeto(address, value.encode("utf-8"))
                        except Exception as e:
                            print(f"255,i2c1_error,transaction_failed,{repr(e)}")

                elif param == "i2c1_scan":
                    if i2c1 is not None:
                        addresses = i2c1.scan()
                        print(f"0,i2c1_addresses,{addresses}")
                    else:
                        print("255, i2c1_scan,error_not_configured")
                    
            #except Exception as e:
            #    print(f"Error reading line: {e}")
    
    # Perform other tasks here
    poll_uart0()
    poll_uart1()
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