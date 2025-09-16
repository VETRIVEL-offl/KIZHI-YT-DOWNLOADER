# Install required packages first:
# pip install streamlit yt-dlp

import os
import yt_dlp
import streamlit as st

# Download folder
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# ---------- Helper Functions ----------

def fetch_formats(url, mode):
    ydl_opts = {'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = info.get('formats', [])
        options = []

        if mode == "MP4":
            video_formats = [f for f in formats if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
            video_formats = sorted(video_formats, key=lambda x: x.get('height') or 0)
            for f in video_formats:
                res = f.get('height') or "Unknown"
                size = f.get('filesize') or f.get('filesize_approx') or 0
                size_mb = round(size/(1024*1024),2) if size else 0
                options.append(f"{f['format_id']}|{res}p ({size_mb} MB)")
        elif mode == "MP3":
            audio_formats = [f for f in formats if f.get('vcodec') == 'none' and f.get('acodec') != 'none']
            audio_formats = sorted(audio_formats, key=lambda x: x.get('abr') or 0)
            for f in audio_formats:
                abr = f.get('abr') or "Unknown"
                size = f.get('filesize') or f.get('filesize_approx') or 0
                size_mb = round(size/(1024*1024),2) if size else 0
                options.append(f"{f['format_id']}|{abr} kbps ({size_mb} MB)")
    return options

def download_media(url, format_id, mode):
    ydl_opts = {'format': format_id, 'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s'}
    if mode == "MP3":
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }]
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return f"{mode} downloaded successfully!"

# ---------- Streamlit UI ----------

st.title("YouTube Downloader")

url = st.text_input("Enter YouTube URL")

mode = st.radio("Select Mode", ["MP4", "MP3"])

if url:
    formats = fetch_formats(url, mode)
    if formats:
        selected_format = st.selectbox("Select Quality (with file size)", formats)
        if st.button("Download"):
            format_id = selected_format.split("|")[0]
            st.info(download_media(url, format_id, mode))
    else:
        st.warning("No formats found for this URL.")
