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
    with open("static/latest.jpg", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"status": "ok"}

@app.get("/viewer", response_class=HTMLResponse)
async def get_viewer(request: Request):
    return templates.TemplateResponse("viewer.html", {"request": request})
