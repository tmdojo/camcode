#!/usr/bin/python3

import os, glob
import shutil
from datetime import datetime, timedelta #, timezone
from pytz import timezone
import subprocess

from PIL import Image, ImageDraw, ImageFont

def get_yesterday():
    """
    returns string in "2018/2/7" format
    """
    today = datetime.today()
    yesterday = today - timedelta(days=1)
    return "{}/{}/{}".format(yesterday.year, yesterday.month, yesterday.day)

def get_video_name(datestring):
    """
    datestring is in "2018/2/7" format
    returns "20180207.mp4" format
    """
    d = datetime.strptime(datestring, "%Y/%m/%d")
    return "{}.mp4".format(d.strftime("%Y%m%d"))

def decode_filename(fname):
    """
    fname: full path of image file
    returns datetime object in UTC
    """
    imgname = os.path.basename(fname)
    timestamp = os.path.splitext(imgname)[0]
    dt = datetime.strptime(timestamp, "%Y%m%d%H%M%S")
    dt_utc =  timezone('UTC').localize(dt)
    return dt_utc

#BASE_DIR='/home/pi/Pictures/'
BASE_DIR='/Users/shunya/Dropbox/アプリ/dojo_picam1/home/pi/Pictures/'
target_folder = get_yesterday()
target_folder = "2018/2/7"
target_video_name = get_video_name(target_folder)
tmp_folder = "temp"

full_path = os.path.join(BASE_DIR, target_folder)
jpegs = sorted(glob.glob(full_path + "/*.jpg"))
tmp_path = os.path.join(BASE_DIR, tmp_folder)
if os.path.exists(tmp_path):
    # delete temp folder if exit
    shutil.rmtree(tmp_path, ignore_errors=True)
if not os.path.exists(tmp_path):
    os.makedirs(tmp_path)

n_images = len(jpegs)
for i, imgpath in enumerate(jpegs):
    #i=0
    #imgpath = jpegs[i]
    print("{}/{}".format(i, n_images))
    dt = decode_filename(imgpath)
    dt_jst = dt.astimezone(timezone('Asia/Tokyo'))
    timestamp = dt_jst.strftime("%Y-%m-%d %H:%M:%S")
    im = Image.open(imgpath)
    d = ImageDraw.Draw(im)
    d.text((10,im.size[1]-15), timestamp, fill=(255,255,255))
    del d
    im.save(os.path.join(tmp_path, "im{:04d}.jpg".format(i)))

#cmd = "ffmpeg -f image2 -r 15 -i im%04d.jpg -vcodec mpeg4 -y movie.mp4"
#cmd = "ffmpeg -f image2 -r 5 -i im%04d.jpg -vcodec mpeg4 -y movie5.mp4"
fps = 15
im_files = os.path.join(tmp_path, "im%04d.jpg")
#video_file = os.path.join(tmp_path, "movie{fps}.mp4".format(fps=fps))
video_file = os.path.join(tmp_path, target_video_name)
cmd = "ffmpeg -r {fps} -i {im_files} -vcodec mpeg4 -y {video_file}".format(fps=fps, im_files=im_files, video_file=video_file)
subprocess.run(cmd.split(" "), stdout=subprocess.PIPE)

#TODO: delete temp folder
