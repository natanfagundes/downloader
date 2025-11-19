from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import yt_dlp
import uuid
import os

app = FastAPI()

# CORS liberado
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pasta temporária para download
DOWNLOAD_DIR = "/tmp/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.get("/")
def home():
    return {"status": "backend online"}

@app.post("/api/download")
async def download(data: dict):
    url = data.get("url")
    fmt = data.get("format")

    if not url:
        raise HTTPException(status_code=400, detail="URL inválida.")

    file_id = str(uuid.uuid4())

    if fmt == "mp3":
        output = f"{DOWNLOAD_DIR}/{file_id}.mp3"
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }

    elif fmt == "mp4":
        output = f"{DOWNLOAD_DIR}/{file_id}.mp4"
        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "outtmpl": output,
            "merge_output_format": "mp4",
        }

    else:
        raise HTTPException(status_code=400, detail="Formato inválido.")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if not os.path.isfile(output):
            raise HTTPException(status_code=500, detail="Erro ao gerar arquivo.")

        return FileResponse(
            output,
            filename=os.path.basename(output),
            media_type="application/octet-stream"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
