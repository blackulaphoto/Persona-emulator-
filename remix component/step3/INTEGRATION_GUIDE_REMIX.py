"""
INTEGRATION GUIDE: Add remix routes to main.py

Add these lines to register remix endpoints.
"""

# In your app/main.py, update the imports:
from app.api.routes import personas, experiences, interventions, timeline, templates, remix  # ADD remix

# Then in the router registration section, add:
app.include_router(personas.router)
app.include_router(experiences.router)
app.include_router(interventions.router)
app.include_router(timeline.router)
app.include_router(templates.router)
app.include_router(remix.router)  # ADD THIS LINE - Remix routes


# That's it! The remix routes are now registered and protected by FEATURE_REMIX_TIMELINE flag.
# They'll return 404 unless FEATURE_REMIX_TIMELINE=true in .env

# Also update your .env file:
"""
# In .env, add:
FEATURE_CLINICAL_TEMPLATES=false
FEATURE_REMIX_TIMELINE=false  # ADD THIS LINE
FEATURE_COMPARE_PERSONAS=false
"""
