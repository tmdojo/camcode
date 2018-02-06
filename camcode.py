#!/usr/bin/python3

from time import sleep
from datetime import datetime
import os
import base64
from PIL import Image
from Adafruit_IO import Client
from picamera import PiCamera

# define credentials in secret.py file
# SECRET = "adafruit.io AIO Key"
from secret import *

aio = Client(SECRET)
topic = 'picam1'
BASE_DIR='/home/pi/Pictures/'

camera = PiCamera()
camera.resolution = (320, 240)
# camera.resolution = (1024, 768)
# camera.sharpness = 0
# camera.contrast = 0
# camera.brightness = 50
# camera.saturation = 0
# camera.ISO = 0
# camera.video_stabilization = False
# camera.exposure_compensation = 0
# camera.exposure_mode = 'auto'
# camera.meter_mode = 'average'
# camera.awb_mode = 'auto'
# camera.image_effect = 'none'
# camera.color_effects = None
# camera.rotation = 0
# camera.hflip = False
# camera.vflip = False
# camera.crop = (0.0, 0.0, 1.0, 1.0)

#camera.start_preview()
# Camera warm-up time
sleep(2)

def get_dirs(base_dir, d):
    """
    d: datetime.datetime instance
    creates directries for
    -- year
     |- month
      |- day
    """
    dirs = os.path.join(base_dir, str(d.year), str(d.month), str(d.day))
    if not os.path.exists(dirs):
        os.makedirs(dirs)
    return dirs

def get_filename(d):
    """
    d: datime.datetime instance
    reutnrs '20180205091142.jpg'
    """
    timestamp = d.strftime("%Y%m%d%H%M%S")
    return "{}.jpg".format(timestamp)

def shoot_post(aio, topic):
    """
    aio: Adafruit_IO.Client instance
    topic: topic name to publish to
    """
    now = datetime.utcnow()
    dirs = get_dirs(BASE_DIR, now)
    pic_name = os.path.join(dirs, get_filename(now))
    camera.capture(pic_name)
    sleep(2)
    print("Took picture: {}".format(pic_name))

    with open(pic_name, "rb") as imageFile:
        encoded = base64.b64encode(imageFile.read())
        img64 = encoded.decode('ascii')
        aio.send(topic, img64 )

shoot_post(aio, topic)
