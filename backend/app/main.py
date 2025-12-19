"""
FastAPI main application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import personas, experiences, interventions, timeline, chat, templates, remix, narratives
from app.core.database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Persona Evolution Simulator API",
    description="AI-powered personality evolution and therapy outcome simulation",
    version="1.0.0"
)

# CORS middleware
# Note: When allow_credentials=True, you cannot use allow_origins=["*"]
# Must specify exact origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",  # Alternative frontend port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",  # Alternative frontend port
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(personas.router)
app.include_router(experiences.router)
app.include_router(interventions.router)
app.include_router(timeline.router)
app.include_router(chat.router)
app.include_router(templates.router)
app.include_router(remix.router)
app.include_router(narratives.router)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Persona Evolution Simulator API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
