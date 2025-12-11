from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/batch.html", response_class=HTMLResponse)
async def get_batch_html():
    with open("frontend/batch.html", "r") as file:
        return HTMLResponse(content=file.read())


@app.post("/batch-job")
async def batch_job(request: Request):
    data = await request.json()
    return {"job_id": str(uuid.uuid4()), "received": data}


@app.post("/run")
async def run_simulation(request: Request):
    data = await request.json()
    return {"status": "ok", "data": data}


@app.get("/job-result")
async def job_result(job_id: str):
    return {"job_id": job_id, "result": "Job completed"}