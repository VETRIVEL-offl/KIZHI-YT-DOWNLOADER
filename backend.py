from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
from pathlib import Path
from platformdirs import user_downloads_dir
DOWNLOADS_DIR = Path(user_downloads_dir())

DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_ydl_opts(mode, format_id=None):
    opts = {"outtmpl": str(DOWNLOADS_DIR / "%(title)s.%(ext)s")}
    if mode == "mp3":
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    elif mode == "mp4":
        opts["format"] = format_id if format_id else "bestvideo+bestaudio/best"
    return opts

@app.get("/formats")
def get_formats(url: str, mode: str):
    if "post/" in url:  # no community posts
        return []
    with yt_dlp.YoutubeDL({}) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = []
        for f in info.get("formats", []):
            if mode == "mp4" and f.get("vcodec") != "none":
                size = f.get("filesize") or 0
                label = f"{f.get('format_note','')} - {round(size/1024/1024,2)} MB" if size else f.get("format_note","")
                formats.append({"format_id": f["format_id"], "label": label})
            elif mode == "mp3" and f.get("acodec") != "none":
                abr = f.get("abr", "Unknown")
                size = f.get("filesize") or 0
                label = f"{abr} kbps - {round(size/1024/1024,2)} MB" if size else f"{abr} kbps"
                formats.append({"format_id": f["format_id"], "label": label})
        return formats

@app.post("/download")
async def download(request: Request):
    data = await request.json()
    url, mode, format_id = data["url"], data["mode"], data.get("format_id")
    if "post/" in url:
        return {"status": "Community posts not supported"}
    ydl_opts = get_ydl_opts(mode, format_id)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return {"status": f"File saved to {DOWNLOADS_DIR}"}
