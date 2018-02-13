#!/usr/bin/python3

from time import sleep
from datetime import datetime
import os
import base64

from PIL import Image
from picamera import PiCamera
from Adafruit_IO import Client
import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError
import boto3

# define credentials in secret.py file
# SECRET = "adafruit.io AIO Key"
# DROPBOX_ACCESS_TOKEN = ""
# AWS_ACCESS_KEY_ID = ""
# AWS_SECRET_ACCESS_KEY = ""
# AWS_REGION = "us-east-1" #US East (N. Virginia)
from secret import *

BASE_DIR='/home/pi/Pictures/'

aio = Client(SECRET)
topic = 'picam1'

dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
# Check that the access token is valid
try:
    dbx.users_get_current_account()
except AuthError as err:
    print("ERROR: Invalid access token; try re-generating an access token from the app console on the web.")

s3 = boto3.resource('s3',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
#bucket = s3.Bucket(BUCKET_NAME)

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

def take_picture():
    """
    Take picture and returns full path of the image file
    """
    now = datetime.utcnow()
    dirs = get_dirs(BASE_DIR, now)
    pic_name = os.path.join(dirs, get_filename(now))
    camera.capture(pic_name)
    sleep(2)
    print("Took picture: {}".format(pic_name))
    return pic_name

def upload_adafruitio(pic_name, aio, topic):
    """
    pic_name: image file name
    aio: Adafruit_IO.Client instance
    topic: topic name to publish to
    """
    with open(pic_name, "rb") as imageFile:
        img64 = base64.b64encode(imageFile.read()).decode('ascii')
        aio.send(topic, img64 )

# Uploads contents of pic_name to Dropbox
def upload_dropbox(pic_name, dbx):
    """
    pic_name: image file name
    dbx: dropbox.Dropbox instance
    """
    with open(pic_name, 'rb') as f:
        # We use WriteMode=overwrite to make sure that the settings in the file
        # are changed on upload
        BACKUPPATH = pic_name
        print("Uploading " + pic_name + " to Dropbox as " + BACKUPPATH + "...")
        try:
            dbx.files_upload(f.read(), BACKUPPATH, mode=WriteMode('overwrite'))
        except ApiError as err:
            # This checks for the specific error where a user doesn't have enough Dropbox space quota to upload this file
            if (err.error.is_path() and
                    err.error.get_path().error.is_insufficient_space()):
                print("ERROR: Cannot back up; insufficient space.")
            elif err.user_message_text:
                print(err.user_message_text)
                #sys.exit()
            else:
                print(err)
                #sys.exit()

pic_name = take_picture()
upload_dropbox(pic_name, dbx)
#upload_adafruitio(pic_name, aio, topic)
#pic_name = "/Users/shunya/Dropbox/アプリ/dojo_picam1/home/pi/Pictures/2018/2/12/20180212000016.jpg"
#pic_name2 = "/home/pi/Pictures/2018/2/12/20180212000016.jpg"
s3.Bucket(BUCKET_NAME).upload_file(pic_name, pic_name.split("/home/pi/")[1])
# test
#for obj in s3.Bucket(BUCKET_NAME).objects.all():
#   print(obj.key)
#for obj in s3.Bucket(BUCKET_NAME).objects.filter(Prefix="/home/pi/Pictures/").all():
#    print(obj.key)
