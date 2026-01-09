from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, projects, time_entries

app= FastAPI(title="timetracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(time_entries.router)
@app.get("/")
async def root():
    return {"message": "timetracker API server is up and running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}    

