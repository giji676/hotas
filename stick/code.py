import board
import digitalio
from analogio import AnalogIn
from joystick_xl.inputs import Axis, Button, Hat, VirtualInput
from joystick_xl.joystick import Joystick
import time

js = Joystick()

Jx = AnalogIn(board.A1)
Jy = AnalogIn(board.A0)

load_pin = digitalio.DigitalInOut(board.GP2)
clockIn_pin = digitalio.DigitalInOut(board.GP3)
dataIn_pin = digitalio.DigitalInOut(board.GP4)

load_pin.direction = digitalio.Direction.OUTPUT
clockIn_pin.direction = digitalio.Direction.OUTPUT
dataIn_pin.direction = digitalio.Direction.INPUT

raw_num_buttons = 8*3
num_buttons = 8*3-2
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
    data = list(bin(data))[4:]
    data = [int(i) for i in data]
    
    for i, b in enumerate(data):
        result[i].value = b*(-1)+1

def process_axis(axis_, min_input=0, max_input=65536, min_output=0, max_output=255, invert=False, smoothing_iters=20):
    total = 0
    for _ in range(smoothing_iters):
        val = axis_.value
        total += val
        
    new_val = round(remap(total/smoothing_iters, min_input, max_input, min_output, max_output))
    
    if invert:
        return max_output - new_val
    return new_val
    
    
axis_values = {"X": VirtualInput(value=128),
               "Y": VirtualInput(value=128)}

def read_axis():
    global axis_values
    axis_values["X"].value = process_axis(Jx, min_input=27852, max_input=41502, min_output=0, max_output=255, invert=False, smoothing_iters=20)
    axis_values["Y"].value = process_axis(Jy, min_input=25180, max_input=40243, min_output=0, max_output=255, invert=False, smoothing_iters=20)
    
js.add_input(
    Axis(source=axis_values["X"], min=0, max=255),
    Axis(source=axis_values["Y"], min=0, max=255),
    Button(active_low=False),
    Button(active_low=False),
    Button(active_low=False),
    Button(active_low=False),
    Button(active_low=False),
    Button(active_low=False),
    Hat(),
    Hat(),
    Hat(),
    Hat(),
)

offset = 6
hat = list()
num_hats = 4

hat.append(Hat())
hat.append(Hat())
hat.append(Hat())
hat.append(Hat())
hat[0].down = result[6]
hat[0].right = result[7]
hat[0].up = result[8]
hat[0].left = result[9]

hat[1].right = result[10]
hat[1].up = result[11]
hat[1].left = result[12]
hat[1].down = result[13]

hat[2].right = result[14]
hat[2].down = result[15]
hat[2].left = result[16]
hat[2].up = result[17]

hat[3].up = result[18]
hat[3].right = result[19]
hat[3].down = result[20]
hat[3].left = result[21]

while True:
    read_74hc165()
    read_axis()
    
    for x in range(offset):
        js.button[x].source_value = result[x].value
    
    for i in range(num_hats):
        hat[i]._update()
    
    js.hat = hat
    
    js.update()
