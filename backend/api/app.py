from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.api.reports import router as reports_router
from backend.config import DB_PATH, UPLOAD_DIR
from backend.database.database import init_db
from backend.services.report_service import ReportServiceError

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
init_db(DB_PATH)

app = FastAPI(title="Civic Eye", version="0.1.0")

app.include_router(reports_router)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.exception_handler(ReportServiceError)
async def report_service_error_handler(
    request: Request,
    exc: ReportServiceError,
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred. Please try again."
        },
    )


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}