#!/usr/bin/python3

import os
from datetime import datetime, timedelta #, timezone
from pytz import timezone

import boto3
import botocore

from camcode import BASE_DIR, PICTURES, MOVIES, get_pic_dir
from camcode import prep_s3
from tovideo import get_video_dir_fname
from secret import *

#if __name__ == '__main__':
s3 = prep_s3()
bucket = s3.Bucket(BUCKET_NAME)
today = datetime.today()
yesterday = today - timedelta(days=1)
# video: just download one file
video_full_path, video_key = get_video_dir_fname(yesterday)
if not os.path.exists(video_full_path):
    print("Download: {}".format(video_full_path))
    try:
        bucket.download_file(video_key, video_full_path)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            # The object does not exist.
            print("No such file: {}".format(video_key))
        else:
            # Something else has gone wrong.
            print("Error downloading file: {}".format(video_key))
    finally:
        print("Success!")
else:
    print("File already exists: {}".format(video_full_path))
# image: download images in one folder
im_dir_full_path, im_dir_key = get_pic_dir(yesterday)
objects = bucket.objects.filter(Prefix=im_dir_key)
#im_list = [obj for obj in objects]
for obj in objects:
    bucket.download_file(obj.key, os.path.join(BASE_DIR, obj.key))
