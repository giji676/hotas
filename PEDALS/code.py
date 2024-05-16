import time
import board
import math
import busio
import digitalio
from analogio import AnalogIn
from joystick_xl.inputs import Axis, Button, Hat, VirtualInput
from joystick_xl.joystick import Joystick

Lb = AnalogIn(board.A0) # 53084 40297
r = AnalogIn(board.A1) # 45675 16291
Rb = AnalogIn(board.A2) # 36392 26838

js = Joystick()

def remap(val, in_min, in_max, out_min, out_max):
    max(in_min, min(val, in_max))
    return max(out_min, min((val-in_min)*(out_max-out_min) // (in_max-in_min)+out_min, out_max))

class RollingAverage:
    def __init__(self, window_size):
        self.window_size = window_size
        self.data_buffer = []
        self.current_sum = 0
        self.current_average = None

    def add_data_point(self, new_value):
        if len(self.data_buffer) == self.window_size:
            # Remove the oldest value from the buffer
            oldest_value = self.data_buffer.pop(0)
            self.current_sum -= oldest_value
        
        # Add the new value to the buffer and update the sum
        self.data_buffer.append(new_value)
        self.current_sum += new_value
        
        # Update the current average
        self.current_average = self.current_sum / len(self.data_buffer)

        return self.current_average
  
def linear(val, in_min, in_max):
    val = val.value
    mid = in_max - in_min
    multi = 120
    offset = 33640
    base = 2.0
    n_val = val-mid-4000

    if n_val == 0:
        n_val = offset
    if n_val < 0:
        n_val = -math.pow(-n_val, 1/base)*multi+offset
    else:
        n_val = math.pow(n_val, 1/base)*multi+offset
    #print(n_val) # 18600, 46400
    return n_val


def process_axis(axis_, min_input=0, max_input=65536, min_output=0, max_output=255, invert=False, smoothing_iters=20):
    if type(axis_) == float or type(axis_) == int:
        total = axis_
    elif type(axis_) == AnalogIn:
        total = 0
        for _ in range(smoothing_iters):
            val = axis_.value
            total += val
        total = total/smoothing_iters
    else:
        pass
        
    new_val = round(remap(total, min_input, max_input, min_output, max_output))
    
    if invert:
        return max_output - new_val
    return new_val

axis_values = {"Lb": VirtualInput(value=128),
               "Rb": VirtualInput(value=128),
               "r": VirtualInput(value=128),
               "RawR": VirtualInput(value=128)}

def read_axis():
    global axis_values, rolling_avg
    axis_values["Lb"].value = process_axis(Lb, min_input=25000, max_input=34400, min_output=0, max_output=255, invert=True, smoothing_iters=20)
    axis_values["r"].value = process_axis(rolling_avg.add_data_point(linear(r, 16291, 45757)), min_input=18250, max_input=47300, min_output=0, max_output=255, invert=False, smoothing_iters=20)
    axis_values["RawR"].value = process_axis(r, min_input=16291, max_input=45675, min_output=0, max_output=255, invert=False, smoothing_iters=20)
    axis_values["Rb"].value = process_axis(Rb, min_input=40200, max_input=51600, min_output=0, max_output=255, invert=False, smoothing_iters=20)

js.add_input(
    Axis(source=axis_values["Lb"], min=0, max=255),
    Axis(source=axis_values["Rb"], min=0, max=255),
    Axis(source=axis_values["r"], min=0, max=255),
    Axis(source=axis_values["RawR"], min=0, max=255),
)

smoothing_window = 30  # Adjust the window size as needed
rolling_avg = RollingAverage(smoothing_window)

while True:
    read_axis()
    js.update()