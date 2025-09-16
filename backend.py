from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import yt_dlp
import os

app = FastAPI()

# Allow requests from GitHub Pages and localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can also set ["https://vetrivel-offl.github.io"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Serve frontend if needed
@app.get("/")
async def root():
    return FileResponse("index.html")

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
        return JSONResponse(status_code=400, content={"error": str(e)})
    return formats

@app.post("/download")
async def download(request: Request):
    data = await request.json()
    url = data.get("url")
    format_id = data.get("format_id")
    mode = data.get("mode")

    if not url or not format_id or not mode:
        return JSONResponse(status_code=400, content={"status": "Missing parameters"})

    output_template = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
    ydl_opts = {"format": format_id, "outtmpl": output_template, "quiet": True}

    if mode == "mp3":
        ydl_opts["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        return JSONResponse(status_code=400, content={"status": f"Error: {e}"})

    return {"status": "Download completed!"}
