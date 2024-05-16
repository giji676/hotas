"""boot.py"""
import usb_hid
from joystick_xl.hid import create_joystick

usb_hid.enable((create_joystick(axes=3, buttons=6, hats=4),))
usb_hid.device.device_name = "MyCustomDevice"