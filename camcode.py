#!/usr/bin/python3

from time import sleep
import base64
from PIL import Image
from Adafruit_IO import Client
from picamera import PiCamera

# define credentials in secret.py file
import .secret

aio = Client('SECRET')
BASE_DIR='/home/pi/Pictures/'
DST_FILE=BASE_DIR+'snap.jpg'

camera = PiCamera()
camera.resolution = (320, 240)
#camera.resolution = (1024, 768)
#camera.start_preview()
# Camera warm-up time
sleep(2)
camera.capture(DST_FILE)

with open(DST_FILE, "rb") as imageFile:
    str = base64.b64encode(imageFile.read())

aio.send('pic', str )
