# backend/backend.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp

app = FastAPI()

# Allow requests from GitHub Pages or anywhere
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DownloadRequest(BaseModel):
    url: str
    mode: str
    format_id: str

@app.get("/formats")
def get_formats(url: str, mode: str):
    try:
        ydl_opts = {"quiet": True, "format": "bestvideo+bestaudio/best"} if mode == "mp4" else {"quiet": True, "format": "bestaudio/best"}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []
            for f in info.get("formats", []):
                if mode == "mp3" and f.get("acodec") != "none":
                    formats.append({"format_id": f["format_id"], "label": f"{f.get('abr', '128')} kbps"})
                elif mode == "mp4" and f.get("vcodec") != "none":
                    label = f'{f.get("height", "best")}p {f.get("fps", "")}fps'
                    formats.append({"format_id": f["format_id"], "label": label})
            return formats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/download")
def download(req: DownloadRequest):
    try:
        ydl_opts = {
            "format": req.format_id,
            "outtmpl": "%(title)s.%(ext)s",
        }
        if req.mode == "mp3":
            ydl_opts.update({
                "format": req.format_id,
                "postprocessors": [{"key": "FFmpegExtractAudio","preferredcodec": "mp3","preferredquality": "192"}]
            })
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([req.url])
        return {"status": "Download completed!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
