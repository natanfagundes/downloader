import httpx
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from subprocess import Popen, PIPE

app = FastAPI()

# CORS liberado para o frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def validate_url(url: str):
    return re.match(r"^https?:\/\/", url) is not None

async def download_stream(url: str):
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", url) as r:
            if r.status_code != 200:
                raise HTTPException(status_code=400, detail="URL inacessível.")
            async for chunk in r.aiter_bytes():
                yield chunk

@app.post("/api/download")
async def download_file(data: dict):
    url = data.get("url")
    fmt = data.get("format")

    if not url or not validate_url(url):
        raise HTTPException(status_code=400, detail="URL inválida.")

    if fmt not in ("mp3", "mp4"):
        raise HTTPException(status_code=400, detail="Formato inválido.")

    cmd = [
        "ffmpeg",
        "-i", "pipe:0",
        "-f", fmt,
        "-codec:a", "libmp3lame" if fmt == "mp3" else "aac",
        "-codec:v", "copy" if fmt == "mp4" else "none",
        "pipe:1",
        "-y"
    ]

    process = Popen(cmd, stdin=PIPE, stdout=PIPE)

    async def ffmpeg_gen():
        async for chunk in download_stream(url):
            process.stdin.write(chunk)
        process.stdin.close()

        while True:
            out = process.stdout.read(1024)
            if not out:
                break
            yield out

    return StreamingResponse(
        ffmpeg_gen(),
        headers={"Content-Disposition": f'attachment; filename="download.{fmt}"'}
    )
