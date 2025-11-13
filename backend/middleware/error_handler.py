"""
Global error handling middleware
Catches all exceptions and returns consistent error responses
"""
import traceback
import time
from fastapi import Request, status
from fastapi.responses import JSONResponse
from loguru import logger
from typing import Union
import jwt


class ErrorResponse:
    """Standard error response format"""

    @staticmethod
    def create(
        error_code: str,
        message: str,
        status_code: int,
        details: Union[dict, None] = None,
        request_id: Union[str, None] = None
    ) -> JSONResponse:
        """
        Create standardized error response

        Args:
            error_code: Machine-readable error code
            message: Human-readable error message
            status_code: HTTP status code
            details: Additional error details
            request_id: Request ID for tracking

        Returns:
            JSONResponse with error details
        """
        response_body = {
            "error": {
                "code": error_code,
                "message": message,
                "status": status_code
            }
        }

        if details:
            response_body["error"]["details"] = details

        if request_id:
            response_body["request_id"] = request_id

        return JSONResponse(
            status_code=status_code,
            content=response_body
        )


async def error_handler_middleware(request: Request, call_next):
    """
    Global error handling middleware

    Catches all exceptions and returns consistent error responses
    Logs errors with full context
    """
    request_id = request.headers.get("x-request-id", f"req_{int(time.time() * 1000)}")
    start_time = time.time()

    try:
        response = await call_next(request)
        return response

    except jwt.ExpiredSignatureError:
        logger.warning(f"[{request_id}] JWT token expired")
        return ErrorResponse.create(
            error_code="TOKEN_EXPIRED",
            message="Your authentication token has expired. Please login again.",
            status_code=status.HTTP_401_UNAUTHORIZED,
            request_id=request_id
        )

    except jwt.InvalidTokenError as e:
        logger.warning(f"[{request_id}] Invalid JWT token: {e}")
        return ErrorResponse.create(
            error_code="INVALID_TOKEN",
            message="Invalid authentication token.",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details={"reason": str(e)},
            request_id=request_id
        )

    except PermissionError as e:
        logger.warning(f"[{request_id}] Permission denied: {e}")
        return ErrorResponse.create(
            error_code="PERMISSION_DENIED",
            message="You don't have permission to perform this action.",
            status_code=status.HTTP_403_FORBIDDEN,
            request_id=request_id
        )

    except FileNotFoundError as e:
        logger.warning(f"[{request_id}] File not found: {e}")
        return ErrorResponse.create(
            error_code="FILE_NOT_FOUND",
            message="The requested file was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"path": str(e)},
            request_id=request_id
        )

    except ValueError as e:
        logger.warning(f"[{request_id}] Validation error: {e}")
        return ErrorResponse.create(
            error_code="VALIDATION_ERROR",
            message="Invalid input data.",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"reason": str(e)},
            request_id=request_id
        )

    except TimeoutError as e:
        logger.error(f"[{request_id}] Request timeout: {e}")
        return ErrorResponse.create(
            error_code="TIMEOUT",
            message="The request took too long to complete.",
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            details={"reason": str(e)},
            request_id=request_id
        )

    except ConnectionError as e:
        logger.error(f"[{request_id}] Connection error: {e}")
        return ErrorResponse.create(
            error_code="CONNECTION_ERROR",
            message="Failed to connect to external service.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"reason": str(e)},
            request_id=request_id
        )

    except Exception as e:
        # Unexpected error - log full traceback
        duration_ms = (time.time() - start_time) * 1000
        error_trace = traceback.format_exc()

        logger.error(
            f"[{request_id}] Unhandled exception after {duration_ms:.0f}ms:\n"
            f"Path: {request.method} {request.url.path}\n"
            f"Error: {type(e).__name__}: {str(e)}\n"
            f"Traceback:\n{error_trace}"
        )

        # Don't expose internal error details in production
        return ErrorResponse.create(
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred. Please try again later.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={
                "error_type": type(e).__name__,
                # Only include error message in development
                # "error_message": str(e)
            },
            request_id=request_id
        )


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded"""
    pass


class QuotaExceeded(Exception):
    """Raised when user quota is exceeded"""
    pass


class ServiceUnavailable(Exception):
    """Raised when service is temporarily unavailable"""
    pass


# Custom exception handlers for specific error types


def register_exception_handlers(app):
    """
    Register custom exception handlers with FastAPI app

    Args:
        app: FastAPI application instance
    """
    from fastapi import FastAPI
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic validation errors"""
        request_id = request.headers.get("x-request-id")

        logger.warning(f"[{request_id}] Validation error: {exc.errors()}")

        return ErrorResponse.create(
            error_code="VALIDATION_ERROR",
            message="Invalid request data.",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={
                "errors": exc.errors()
            },
            request_id=request_id
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions"""
        request_id = request.headers.get("x-request-id")

        return ErrorResponse.create(
            error_code="HTTP_ERROR",
            message=exc.detail,
            status_code=exc.status_code,
            request_id=request_id
        )

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        """Handle rate limit exceeded"""
        request_id = request.headers.get("x-request-id")

        return ErrorResponse.create(
            error_code="RATE_LIMIT_EXCEEDED",
            message="Too many requests. Please slow down.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"retry_after": 60},
            request_id=request_id
        )

    @app.exception_handler(QuotaExceeded)
    async def quota_exceeded_handler(request: Request, exc: QuotaExceeded):
        """Handle quota exceeded"""
        request_id = request.headers.get("x-request-id")

        return ErrorResponse.create(
            error_code="QUOTA_EXCEEDED",
            message=str(exc),
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            details={"upgrade_url": "/billing/plans"},
            request_id=request_id
        )

    @app.exception_handler(ServiceUnavailable)
    async def service_unavailable_handler(request: Request, exc: ServiceUnavailable):
        """Handle service unavailable"""
        request_id = request.headers.get("x-request-id")

        return ErrorResponse.create(
            error_code="SERVICE_UNAVAILABLE",
            message=str(exc),
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"retry_after": 120},
            request_id=request_id
        )

    logger.info("Custom exception handlers registered")
