"""
Run by:
export FLASK_DEBUG=1
export FLASK_APP=app.py
flask run --host=0.0.0.0
Then go:
http://127.0.0.1:5000/
"""
import os, glob
import base64
from io import BytesIO
from datetime import datetime

from flask import Flask, render_template, abort

from camcode import BASE_DIR, PICTURES, MOVIES, NOW_PICTURE
from camcode import get_pic_dir, prep_s3
from tovideo import get_video_dir_fname
from secret import *

app = Flask(__name__, static_url_path='/static', static_folder=BASE_DIR)

def list_child_dir(parentpath):
    return next(os.walk(parentpath))[1]

def get_pic_list():
    pic_full_path = os.path.join(BASE_DIR, PICTURES)
    jpegs = sorted(glob.glob(pic_full_path + "/**/*.jpg", recursive=True), reverse=True)
    return [jpeg.split(BASE_DIR)[1] for jpeg in jpegs]

def get_latest_pic_dir():
    """
    Find latest picture file in /home/pi/Pictures
    note that sorted function use key=int in order to make a natural alphabetical sort.
    """
    search_path = os.path.join(BASE_DIR, PICTURES)
    search_path = os.path.join(search_path, sorted(list_child_dir(search_path), key=int)[-1]) #year
    search_path = os.path.join(search_path, sorted(list_child_dir(search_path), key=int)[-1]) #month
    search_path = os.path.join(search_path, sorted(list_child_dir(search_path), key=int)[-1]) #day
    return search_path

def get_latest_pic():
    search_path = get_latest_pic_dir()
    return sorted(glob.glob(search_path + '/*.jpg'))[-1]

def get_video_list():
    video_full_path = os.path.join(BASE_DIR, MOVIES)
    videos = sorted(glob.glob(video_full_path + "/**/*.mp4", recursive=True), reverse=True)
    return [video.split(BASE_DIR)[1] for video in videos]

@app.route("/")
def index():
    videos = get_video_list()
    # get latest picture from local file
    #pic0 = get_latest_pic().split(BASE_DIR)[1]
    # get latest picture from s3
    s3 = prep_s3()
    imgBytes = BytesIO()
    s3.Bucket(BUCKET_NAME).download_fileobj(NOW_PICTURE, imgBytes)
    imgBytes.seek(0)
    #im = Image.open(imgBytes)
    imValue = imgBytes.getvalue()
    imB64 = 'data:image/jpeg;base64,' + base64.b64encode(imValue).decode()

    return render_template('index.html',
                            pic0_B64 = imB64,
                            video0 = videos[0],
                            videos=videos[1:11])

@app.route("/yyyymmdd/<string:yyyymmdd>")
def aday(yyyymmdd):
    try:
        d = datetime.strptime(yyyymmdd, "%Y%m%d")
    except ValueError:
        abort(404)
    video_full_path, video_path = get_video_dir_fname(d)
    if not os.path.exists(video_full_path):
        video_path = ""
    return render_template('yyyymmdd.html',
                            day = str(d),
                            video = video_path)
