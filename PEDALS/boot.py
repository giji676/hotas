"""boot.py"""
import usb_hid
from joystick_xl.hid import create_joystick
import supervisor
supervisor.set_usb_identification(pid=0x90)
usb_hid.enable((create_joystick(axes=4),))