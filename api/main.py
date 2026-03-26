"""API application entrypoint.

TODO: Configure middleware, auth, and startup dependencies.
"""

from fastapi import FastAPI

from api.routes import router


app = FastAPI(title="OpenGraph AI API", version="0.1.0")
app.include_router(router)
