from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes import ingest, risk, actions, twin

from contextlib import asynccontextmanager
from src.tasks.scheduler import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()

app = FastAPI(title="Drishti API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://drishti-navy.vercel.app", "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router)
app.include_router(risk.router)
app.include_router(actions.router)
app.include_router(twin.router)


@app.get("/health")
def health():
    return {"status": "ok"}
