import uvicorn
from fastapi import FastAPI
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware

from app.api.errors.http_error import http_error_handler
from app.api.routers import api
from app.core.config import APPLICATION_NAME, DEBUG, VERSION
from app.core.database import engine
from app.models import models


def create_application() -> FastAPI:
    application = FastAPI(title=APPLICATION_NAME, debug=DEBUG, version=VERSION)

    # Add a middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    models.Base.metadata.create_all(bind=engine)

    # Add exception handlers to application
    application.add_exception_handler(HTTPException, http_error_handler)

    # Add API to application
    application.include_router(api.router)

    return application


app = create_application()

# Only for local testing purposes
if __name__ == '__main__':
    uvicorn.run(app, port=8000)
