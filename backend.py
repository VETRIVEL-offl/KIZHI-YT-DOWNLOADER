from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import yt_dlp
import os

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Serve frontend HTML at root
@app.get("/", response_class=HTMLResponse)
async def root():
    with open("index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/formats")
async def get_formats(url: str, mode: str):
    ydl_opts = {"quiet": True, "skip_download": True}
    formats = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            for f in info.get("formats", []):
                if mode == "mp3" and "audio" in f.get("acodec", ""):
                    formats.append({"format_id": f["format_id"], "label": f.get("format_note", f.get("ext"))})
                elif mode == "mp4" and f.get("vcodec") != "none":
                    formats.append({"format_id": f["format_id"], "label": f.get("format_note", f.get("ext"))})
    except Exception as e:
        return {"error": str(e)}
    return formats

@app.post("/download")
async def download(request):
    data = await request.json()
    url = data.get("url")
    format_id = data.get("format_id")
    mode = data.get("mode")

    if not url or not format_id or not mode:
        return {"status": "Missing parameters"}

    output_template = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
    ydl_opts = {"format": format_id, "outtmpl": output_template, "quiet": True}

    if mode == "mp3":
        ydl_opts["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        return {"status": f"Error: {e}"}

    return {"status": "Download completed!"}
