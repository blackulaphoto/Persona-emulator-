"""
INTEGRATION GUIDE: Add template routes to main.py

Add these lines to your existing app/main.py to register template routes.
"""

# In your app/main.py, add this import at the top:
from app.api.routes import templates  # ADD THIS LINE

# Then in the section where you register routers, add:
app.include_router(personas.router)
app.include_router(experiences.router)
app.include_router(interventions.router)
app.include_router(timeline.router)
app.include_router(templates.router)  # ADD THIS LINE - Template routes


# That's it! The routes are now registered and protected by feature flag.
# They'll return 404 unless FEATURE_CLINICAL_TEMPLATES=true in .env

# Complete main.py structure should look like:

"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import personas, experiences, interventions, timeline, templates
from app.core.database import engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Persona Evolution Simulator API",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(personas.router)
app.include_router(experiences.router)
app.include_router(interventions.router)
app.include_router(timeline.router)
app.include_router(templates.router)  # NEW

@app.get("/health")
def health_check():
    return {"status": "healthy"}
"""
