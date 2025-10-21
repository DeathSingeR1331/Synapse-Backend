# Synapse-Backend/app/main.py

import sys
import os

# Add project root to sys.path so "src" imports work when running from app/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from src.api.endpoints import processing

app = FastAPI(title="Synapse Backend API")

@app.get("/")
def read_root():
    return {"message": "Hello, Synapse Backend is running!"}

# Register the processing router
app.include_router(processing.router, prefix="/jobs", tags=["Processing"])
