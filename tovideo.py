#!/usr/bin/python3

import os, glob
import shutil
from datetime import datetime, timedelta #, timezone
from pytz import timezone
import subprocess

from PIL import Image, ImageDraw, ImageFont
import boto3

from camcode import BASE_DIR, PICTURES, MOVIES, get_pic_dir
from camcode import upload_s3
from secret import *

def get_pic_dir_yesterday():
    """
    returns string in "Pictures/2018/2/7" format
    """
    today = datetime.today()
    yesterday = today - timedelta(days=1)
    return get_pic_dir(yesterday)[1]

def get_video_filename(d):
    """
    datestring is in "2018/2/7" format
    returns "Movies/2018/20180207.mp4" format
    """
    return d.strftime("%Y%m%d.mp4")

def get_video_dir(d):
    """
    d: datetime.datetime instance
    creates prefix directries as "Movie/2018/"
    create local full path directory if not exists
    returns full path and prefix
    """
    prefix = os.path.join(MOVIES, str(d.year))
    full_path = os.path.join(BASE_DIR, prefix)
    if not os.path.exists(full_path):
        print("Make folder: ".format(full_path))
        os.makedirs(full_path)
    return (full_path, prefix)

def get_video_dir_fname(d):
    """
    d: datetime.datetime instance
    returns "Movies/2018/20180207.mp4" format
    """
    full_path, prefix = get_video_dir(d)
    video_filename = get_video_filename(d)
    return (os.path.join(full_path, video_filename),
            os.path.join(prefix, video_filename))

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

if __name__ == '__main__':
    target_folder = get_pic_dir_yesterday()
    #target_folder = "Pictures/2018/2/15"

    d = datetime.strptime(target_folder, PICTURES+"/"+"%Y/%m/%d")
    (video_name_full_path, video_name_prefix) = get_video_dir_fname(d)
    # read pictures, add timestamp and make temp files
    tmp_folder = "temp"
    full_path = os.path.join(BASE_DIR, target_folder)
    jpegs = sorted(glob.glob(full_path + "/*.jpg"))
    tmp_path = os.path.join(BASE_DIR, tmp_folder)
    # abort if no image is available
    if len(jpegs) == 0:
        print("No image in folder!: {}".format(target_folder))
        import sys
        sys.exit(0)
    if os.path.exists(tmp_path):
        # delete temp folder if exit
        print("Delete folder: {}".format(tmp_path))
        shutil.rmtree(tmp_path, ignore_errors=True)
    if not os.path.exists(tmp_path):
        print("Make folder: {}".format(tmp_path))
        os.makedirs(tmp_path)

    n_images = len(jpegs)
    for i, imgpath in enumerate(jpegs):
        #i=0
        #imgpath = jpegs[i]
        if i % 10 == 0:
            print("{}/{}".format(i, n_images))
        dt = decode_filename(imgpath)
        dt_jst = dt.astimezone(timezone('Asia/Tokyo'))
        timestamp = dt_jst.strftime("%Y-%m-%d %H:%M:%S")
        im = Image.open(imgpath)
        d = ImageDraw.Draw(im)
        d.text((10,im.size[1]-15), timestamp, fill=(255,255,255))
        del d
        im.save(os.path.join(tmp_path, "im{:04d}.jpg".format(i)))

    # make video
    # -movflags faststart: https://rigor.com/blog/2016/01/optimizing-mp4-video-for-fast-streaming
    # quality is good but takes time to encode on Pi
    #ffmpeg -r 15 -i im%04d.jpg -an -vcodec libx264 -preset slow -s 320x240 -b:v 370K -movflags faststart -y movie.mp4
    #ffmpeg -r 15 -i im%04d.jpg -an -vcodec libx264 -f mp4 -crf 22 -s 320x240 movie.mp4
    #cmd = "ffmpeg -f image2 -r 15 -i im%04d.jpg -vcodec libx264 -an -movflags faststart -y movie.mp4"
    #cmd = "ffmpeg -f image2 -r 15 -i im%04d.jpg -vcodec libx264 -an -movflags faststart -y movie.mp4"
    #cmd = "ffmpeg -f image2 -r 15 -i im%04d.jpg -vcodec mpeg4 -movflags faststart -y movie.mp4"
    #cmd = "ffmpeg -f image2 -r 5 -i im%04d.jpg -vcodec mpeg4 -y movie5.mp4"
    fps = 15
    im_files = os.path.join(tmp_path, "im%04d.jpg")
    cmd = "ffmpeg -r {fps} -i {im_files} -an -vcodec libx264 -preset slow -s 320x240 -b:v 370K -movflags faststart -y {video_file}".format(fps=fps, im_files=im_files, video_file=video_name_full_path)
    subprocess.run(cmd.split(" "), stdout=subprocess.PIPE)

    # upload
    if os.uname().machine.startswith("arm"):
        # run on Raspberry Pi
        from camcode import upload_dropbox
        upload_dropbox(video_name_full_path, video_name_prefix)
    print("Upload to s3: {}".format(video_name_full_path))
    upload_success_s3 = upload_s3(video_name_full_path, video_name_prefix)
    print("DONE!")

    # clean up
    if os.path.exists(tmp_path):
        # delete temp folder if exit
        print("Delete folder: {}".format(tmp_path))
        shutil.rmtree(tmp_path, ignore_errors=True)
    if os.uname().machine.startswith("arm") and upload_success_s3:
        # run on Raspberry Pi
        # delete picture folder
        print("Delete folder: {}".format(full_path))
        shutil.rmtree(full_path, ignore_errors=True)
        # delete movie file
        print("Delete file: {}".format(video_name_full_path))
        os.remove(video_name_full_path)
