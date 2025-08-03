from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import shutil
import os

app = FastAPI()

# Static files (to serve the latest image)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    content = await file.read()
    print(f"Ricevuto file: {file.filename}, size: {len(content)} bytes")

    with open("static/latest.jpg", "wb") as f:
        f.write(content)
    
    return {"status": "ok"}


@app.get("/viewer", response_class=HTMLResponse)
async def get_viewer(request: Request):
    return templates.TemplateResponse("viewer.html", {"request": request})


@app.get("/gallery", response_class=HTMLResponse)
async def get_gallery(request: Request):
    images = sorted(
        [f for f in os.listdir("static") if f.endswith(".jpg") and f != "latest.jpg"],
        reverse=True
    )
    return templates.TemplateResponse("gallery.html", {"request": request, "images": images})

current_command = ""

@app.post("/set-command")
async def set_command(command: str = Form(...)):
    global current_command
    current_command = command.strip().lower()
    return {"status": "ok", "command": current_command}

@app.get("/command")
async def get_command():
    global current_command
    cmd = current_command
    current_command = ""  # cancella il comando dopo la lettura (one-shot)
    return cmd


@app.get("/", response_class=HTMLResponse)
async def root():
    return '<h2>✅ Server attivo. Vai su <a href="/viewer">/viewer</a> o <a href="/gallery">/gallery</a></h2>'
