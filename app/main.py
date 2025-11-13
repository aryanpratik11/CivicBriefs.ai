# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.agents import router as agents_router
from app.api.routes.auth import router as auth_router

app = FastAPI(title="CivicBriefs.AI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the News Agent router
app.include_router(agents_router)
app.include_router(auth_router)


@app.get("/")
def home():
    return {"message": "Welcome to CivicBriefs.AI 🚀 - FastAPI is running!"}
