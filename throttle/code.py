import board
import busio
import digitalio
from analogio import AnalogIn
from joystick_xl.inputs import Axis, Button, Hat, VirtualInput
from joystick_xl.joystick import Joystick
import adafruit_ads7830.ads7830 as ADC
from adafruit_ads7830.analog_in import AnalogIn as adsAnalogIn
import time

i2c = busio.I2C(board.GP1, board.GP0)
adc = ADC.ADS7830(i2c, address=0x4B)
Lt = adsAnalogIn(adc, 0) # Left Throttle
Rt = adsAnalogIn(adc, 1) # Right Throttle
Rp = adsAnalogIn(adc, 2) # Right Pot
Lp = adsAnalogIn(adc, 3) # Left Pot
Jx = adsAnalogIn(adc, 4) # Joystick X
Jy = adsAnalogIn(adc, 5) # Joystick Y


js = Joystick()

load_pin = digitalio.DigitalInOut(board.GP2)
clockIn_pin = digitalio.DigitalInOut(board.GP3)
dataIn_pin = digitalio.DigitalInOut(board.GP4)

load_pin.direction = digitalio.Direction.OUTPUT
clockIn_pin.direction = digitalio.Direction.OUTPUT
dataIn_pin.direction = digitalio.Direction.INPUT

unused = [0,1,2,8,9,10,11,13]
raw_num_buttons = 8*3
num_buttons = 8*3 - len(unused)

result = list()
for _ in range(num_buttons):
    result.append(VirtualInput(value=True))

def remap(val, in_min, in_max, out_min, out_max):
    return max(out_min, min((val-in_min)*(out_max-out_min) // (in_max-in_min)+out_min, out_max))

def read_74hc165():
    global result
    load_pin.value = False
    time.sleep(0.001)
    load_pin.value = True
    time.sleep(0.001)
    
    data = 0
    for _ in range(raw_num_buttons):
        data = (data << 1) | dataIn_pin.value
        clockIn_pin.value = True
        time.sleep(0.001)
        clockIn_pin.value = False
        time.sleep(0.001)
    # bin(data) is in the format: "0b000000...00"
    # [4:] removes the "0b" and first 2 inputs as they are not wired/used in the stick
    # :6 buttons
    # 6: hats
    data = list(bin(data))[2:]
    data = [int(i) for i in data]
    
    # Removing unused spots --------
    for i in range(len(unused)):
        data.pop(unused[i]-i)
    
    for i, b in enumerate(data):
        result[i].value = b*(-1)+1
    #return result

def process_axis(axis_, min_input=0, max_input=65536, min_output=0, max_output=255, invert=False, smoothing_iters=20):
    total = 0
    for _ in range(smoothing_iters):
        val = axis_.value
        total += val
        
    new_val = round(remap(total/smoothing_iters, min_input, max_input, min_output, max_output))
    
    if invert:
        return max_output - new_val
    return new_val
    
    
axis_values = {"Rt": VirtualInput(value=128),
               "Lt": VirtualInput(value=128),
               "Lp": VirtualInput(value=128),
               "Rp": VirtualInput(value=128),
               "Jx": VirtualInput(value=128),
               "Jy": VirtualInput(value=128)}

def read_axis():
    global axis_values
    axis_values["Lt"].value = process_axis(Lt, min_input=35572, max_input=49420, min_output=0, max_output=255, invert=False, smoothing_iters=20)
    axis_values["Rt"].value = process_axis(Rt, min_input=32500, max_input=47116, min_output=0, max_output=255, invert=True, smoothing_iters=20)
    axis_values["Jx"].value = process_axis(Jx, min_input=22516, max_input=64780, min_output=0, max_output=255, invert=False, smoothing_iters=20)
    axis_values["Jy"].value = process_axis(Jy, min_input=2548, max_input=64780, min_output=0, max_output=255, invert=True, smoothing_iters=20)
    axis_values["Lp"].value = process_axis(Lp, min_input=0, max_input=65280, min_output=0, max_output=255, invert=False, smoothing_iters=1)
    axis_values["Rp"].value = process_axis(Rp, min_input=0, max_input=65280, min_output=0, max_output=255, invert=False, smoothing_iters=1)
    

js.add_input(
    Button(active_low=True),
    Button(active_low=True),
    Button(active_low=True),
    Button(active_low=True),
    Button(active_low=True),
    Button(active_low=False),
    Button(active_low=False),
    Button(active_low=False),
    Hat(),
    Hat(),
    Axis(source=axis_values["Jx"], min=0, max=255),
    Axis(source=axis_values["Jy"], min=0, max=255),
    Axis(source=axis_values["Lt"], min=0, max=255),
    Axis(source=axis_values["Rt"], min=0, max=255),
    Axis(source=axis_values["Lp"], min=0, max=255),
    Axis(source=axis_values["Rp"], min=0, max=255),
)

num_hats = 2
offset = num_buttons - 4*num_hats
hat = list()

hat.append(Hat())
hat.append(Hat())

hat[0].down = result[-8]
hat[0].right = result[-7]
hat[0].up = result[-6]
hat[0].left = result[-5]

hat[1].right = result[-4]
hat[1].up = result[-3]
hat[1].left = result[-2]
hat[1].down = result[-1]


while True:
    read_74hc165()
    #[print(i.value, end="") for i in result]
    #print()
    
    read_axis()
    for x in range(offset):
        js.button[x].source_value = result[x].value
    
    for i in range(num_hats):
        hat[i]._update()
        
    js.hat = hat
    
    js.update()
