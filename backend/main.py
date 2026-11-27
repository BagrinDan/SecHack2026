from fastapi import FastAPI

app = FastAPI(title="SecHack2026")


@app.get("/")
async def root():
    return {"status": "ok"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
