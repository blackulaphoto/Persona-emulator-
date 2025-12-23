# CORS FIX FOR SNAPSHOTS

In backend/app/main.py, verify CORS middleware allows all routes:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local dev
        "https://persona-emulator.vercel.app",  # Production
        "https://*.vercel.app",  # Preview deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, OPTIONS)
    allow_headers=["*"],  # Allow all headers
)
```

The key is:
- allow_methods=["*"]  ← Must include OPTIONS for CORS preflight
- allow_headers=["*"]  ← Must allow all headers

If this is already set, the issue is that the endpoint is returning 500 BEFORE CORS headers are added.

The real fix: Make sure the endpoint doesn't crash (check Railway logs for the actual error).
