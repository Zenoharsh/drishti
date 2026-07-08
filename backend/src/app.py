from fastapi import FastAPI
from src.routes import ingest, risk, actions, twin

app = FastAPI(title="Drishti API")

app.include_router(ingest.router)
app.include_router(risk.router)
app.include_router(actions.router)
app.include_router(twin.router)


@app.get("/health")
def health():
    return {"status": "ok"}
