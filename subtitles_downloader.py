"""
This module downloads subtitles file for all video files in the current directory.
The subtitles are first tried to be downloaded from http://thesubdb.com/ 
and if not found there, then https://subscene.com/ is tried.
"""

import os
import hashlib
import sys
import requests
import zipfile
import StringIO
from bs4 import BeautifulSoup

video_extensions = [".avi", ".mp4", ".mkv", ".mpg", ".mpeg",
                    ".mov", ".rm", ".vob", ".wmv", ".flv", ".3gp", ".3g2"]


def get_all_files():
    """
    Return all video files in the current directory.
    """

    current_working_directory = os.getcwd()
    file_names = os.listdir(current_working_directory)
    file_paths = []
    for file_name in file_names:
        _, extension = os.path.splitext(file_name)
        if extension in video_extensions:
            file_paths.append(os.path.abspath(file_name))

    return file_paths


def get_hash(file_path):
    """
    Get hash of the file needed for downloading the subtitles.

    Arguments:
        file_path -- absolute path of the video file.

    Returns:
        hash of the file.
    """

    read_size = 64 * 1024
    with open(file_path, 'rb') as f:
        data = f.read(read_size)
        f.seek(-read_size, os.SEEK_END)
        data += f.read(read_size)
    return hashlib.md5(data).hexdigest()


def get_subtitle(file_path):
    """
    Download the subtitle file from http://thesubdb.com/. If not found, then
    use https://subscene.com/

    Arguments:
        file_path -- absolute path of the video file.
    """

    _, file_name = os.path.split(file_path)
    file_name,_ = os.path.splitext(file_name)
    if os.path.exists(file_name + '.srt'):
        return
    headers = {
        'User-Agent': 'SubDB/1.0 (subtitle-downloader/1.0; test)'}
    url = 'http://api.thesubdb.com/?action=download&hash=' + \
        get_hash(file_path) + '&language=en'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        with open(file_name + '.srt', 'wb') as subtitle_file:
            subtitle_file.write(response.content)
    else:
        get_subtitle_retry(file_path)


def get_subtitle_retry(file_path):
    """
    Download the subtitle file from https://subscene.com/.

    Arguments:
        file_path -- absolute path of the video file.
    """

    _, file_name = os.path.split(file_path)
    file_name,_ = os.path.splitext(file_name)
    url = "http://subscene.com/subtitles/release?q=" + file_name
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'lxml')
    atags = soup.find_all("a")
    for atag in atags:
        a_spans = atag.find_all("span")
        if(len(a_spans) == 2 and a_spans[0].get_text().strip() == "English"):
            sub_link = atag.get('href').strip()
            break

    if(len(sub_link) > 0):
        r = requests.get("http://subscene.com" + sub_link)
        soup = BeautifulSoup(r.content, 'lxml')
        download_link = soup.find_all("a", attrs={'id': 'downloadButton'})[
            0].get("href")
        r = requests.get("http://subscene.com" + download_link)
        if r.ok:
            subtitle_file = zipfile.ZipFile(StringIO.StringIO(r.content))
            subtitle_file.extractall()


if __name__ == '__main__':
    file_paths = get_all_files()
    for file_path in file_paths:
        get_subtitle(file_path)
