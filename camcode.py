#!/usr/bin/python3

from time import sleep
from datetime import datetime
import os
import base64

from PIL import Image

import boto3

# define credentials in secret.py file
# DROPBOX_ACCESS_TOKEN = ""
# AWS_ACCESS_KEY_ID = ""
# AWS_SECRET_ACCESS_KEY = ""
# AWS_REGION = "us-east-1" #US East (N. Virginia)
from secret import *

"""
Base directory for local file system and Dropbox
/home/pi/

path and file name for each pictures
Pictures/2018/2/14/20180214153416.jpg

temp path and file for making video
Pictures/temp/im0000.jpg

video output path and file name
Movies/2018/20180207.mp4
"""

if os.uname().machine.startswith("arm"):
    # run on Raspberry Pi
    import dropbox
    from dropbox.files import WriteMode
    from dropbox.exceptions import ApiError, AuthError
    from picamera import PiCamera
    BASE_DIR='/home/pi/'
else:
    BASE_DIR = MY_BASE_DIR

PICTURES = 'Pictures'
MOVIES = 'Movies'
BASE_DIR_PICTURES = os.path.join(BASE_DIR, PICTURES)
BASE_DIR_MOVIES = os.path.join(BASE_DIR, MOVIES)

def get_pic_filename(d):
    """
    d: datime.datetime instance
    reutnrs '20180205091142.jpg'
    """
    timestamp = d.strftime("%Y%m%d%H%M%S")
    return "{}.jpg".format(timestamp)

def get_pic_dir(d):
    """
    d: datetime.datetime instance
    creates prefix directries as "Pictures/2018/2/14/"
    Pictures -- year
              |- month
              |- day
    create local full path directory if not exists
    returns full path and prefix
    """
    prefix = os.path.join(PICTURES, str(d.year), str(d.month), str(d.day))
    full_path = os.path.join(BASE_DIR, prefix)
    if not os.path.exists(full_path):
        os.makedirs(full_path)
    return (full_path, prefix)

def get_pic_dir_fname(d):
    """
    d: datetime.datetime instance
    returns full path and prefix of image file
    """
    full_path, prefix = get_pic_dir(d)
    pic_filename = get_pic_filename(d)
    return (os.path.join(full_path, pic_filename),
            os.path.join(prefix, pic_filename))

def get_video_dirs(d):
    """
    d: datetime.datetime instance
    returns directory to save video
    """
    dirs = os.path.join(BASE_DIR_MOVIES, str(d.year))
    if not os.path.exists(dirs):
        os.makedirs(dirs)
    return dirs

def prep_dropbox():
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    # Check that the access token is valid
    try:
        dbx.users_get_current_account()
    except AuthError as err:
        print("ERROR: Invalid access token; try re-generating an access token from the app console on the web.")
    return dbx

def prep_s3():
    s3 = boto3.resource('s3',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    #bucket = s3.Bucket(BUCKET_NAME)
    return s3

def take_picture():
    """
    Take picture and returns full path of the image file
    """
    now = datetime.utcnow()
    pic_name_full_path, pic_name_prefix = get_pic_dir_fname(now)
    camera.capture(pic_name_full_path)
    sleep(2)
    print("Took picture: {}".format(pic_name_full_path))
    return (pic_name_full_path, pic_name_prefix)

# Uploads contents of pic_name to Dropbox
def upload_dropbox(pic_name_full_path, pic_name_prefix, dbx):
    """
    pic_name_full_path: image file name
    dbx: dropbox.Dropbox instance
    """
    with open(pic_name_full_path, 'rb') as f:
        # We use WriteMode=overwrite to make sure that the settings in the file
        # are changed on upload
        print("Uploading " + pic_name_full_path + " to Dropbox as " + pic_name_prefix + "...")
        try:
            dbx.files_upload(f.read(), pic_name_prefix, mode=WriteMode('overwrite'))
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

if __name__ == '__main__':
    if not os.uname().machine.startswith("arm"):
        print("This script can only be run on Raspberry Pi with camera!")
        print("You can still import functions")
        import sys
        sys.exit(0)

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

    (pic_name_full_path, pic_name_prefix) = take_picture()
    dbx = prep_dropbox()
    upload_dropbox(pic_name_full_path, pic_name_prefix, dbx)
    s3 = prep_s3()
    s3.Bucket(BUCKET_NAME).upload_file(pic_name_full_path, pic_name_prefix)
    # test
    #for obj in s3.Bucket(BUCKET_NAME).objects.all():
    #   print(obj.key)
    #for obj in s3.Bucket(BUCKET_NAME).objects.filter(Prefix="/home/pi/Pictures/").all():
    #    print(obj.key)
