from .v2 import app
from .extensions import router as extended_router

app.include_router(extended_router)
