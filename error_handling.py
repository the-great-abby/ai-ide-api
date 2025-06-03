import logging
import traceback
import uuid
from datetime import datetime

from fastapi import Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from db import ApiErrorLog, SessionLocal

logger = logging.getLogger(__name__)


async def error_logging_middleware(request: Request, call_next):
    """Middleware to log errors and return error IDs."""
    try:
        return await call_next(request)
    except Exception as exc:
        error_id = str(uuid.uuid4())
        stack = traceback.format_exc()
        logger.error(f"[ERROR] Middleware caught exception: {exc}\n{stack}")
        # Log to DB
        db = SessionLocal()
        try:
            log = ApiErrorLog(
                id=error_id,
                timestamp=datetime.utcnow(),
                path=str(request.url.path),
                method=request.method,
                status_code=500,
                message=str(exc),
                stack_trace=stack,
                user_id=None,  # Optionally extract from request if available
            )
            db.add(log)
            db.commit()
        except Exception as log_exc:
            db.rollback()
        finally:
            db.close()
        # Return error ID to client
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error. Reference ID: {error_id}"},
        )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors and log them."""
    error_id = str(uuid.uuid4())
    db = SessionLocal()
    try:
        log = ApiErrorLog(
            id=error_id,
            timestamp=datetime.utcnow(),
            path=str(request.url.path),
            method=request.method,
            status_code=422,
            message=f"Validation error: {exc.errors()}",
            stack_trace=traceback.format_exc(),
            user_id=None,
        )
        db.add(log)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
    # Only include serializable info in the response
    # exc.body may be FormData or bytes; try to decode or omit
    body_str = None
    try:
        if hasattr(exc, "body"):
            if isinstance(exc.body, (str, bytes)):
                body_str = (
                    exc.body.decode("utf-8", errors="ignore")
                    if isinstance(exc.body, bytes)
                    else exc.body
                )
            else:
                body_str = str(type(exc.body))
    except Exception:
        body_str = "<unavailable>"
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": body_str,
            "path": str(request.url.path),
            "message": "Validation failed. Please check your input and try again.",
            "error_id": error_id,
        },
    )
