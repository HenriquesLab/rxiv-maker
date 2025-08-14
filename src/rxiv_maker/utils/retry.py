"""Enhanced retry utilities for network operations with exponential backoff and jitter."""

import logging
import random
import time
from enum import Enum
from functools import wraps
from typing import Any, Callable, Optional, Type, Union

import requests

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Different retry strategies for various failure types."""

    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    FIBONACCI = "fibonacci"


class RetryableError(Exception):
    """Exception that indicates an operation can be safely retried."""

    pass


class NonRetryableError(Exception):
    """Exception that indicates an operation should not be retried."""

    pass


# Common retryable HTTP status codes
RETRYABLE_HTTP_CODES = {
    408,  # Request Timeout
    429,  # Too Many Requests
    500,  # Internal Server Error
    502,  # Bad Gateway
    503,  # Service Unavailable
    504,  # Gateway Timeout
    507,  # Insufficient Storage
    520,  # Web Server Returned an Unknown Error
    521,  # Web Server Is Down
    522,  # Connection Timed Out
    523,  # Origin Is Unreachable
    524,  # A Timeout Occurred
}

# Non-retryable HTTP status codes
NON_RETRYABLE_HTTP_CODES = {
    400,  # Bad Request
    401,  # Unauthorized
    403,  # Forbidden
    404,  # Not Found
    405,  # Method Not Allowed
    406,  # Not Acceptable
    409,  # Conflict
    410,  # Gone
    422,  # Unprocessable Entity
}


def calculate_delay(
    attempt: int,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
) -> float:
    """Calculate delay for retry attempt.

    Args:
        attempt: Current attempt number (0-based)
        strategy: Retry strategy to use
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        jitter: Whether to add random jitter to prevent thundering herd

    Returns:
        Delay in seconds before next attempt
    """
    if strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
        delay = base_delay * (2**attempt)
    elif strategy == RetryStrategy.LINEAR_BACKOFF:
        delay = base_delay * (attempt + 1)
    elif strategy == RetryStrategy.FIXED_DELAY:
        delay = base_delay
    elif strategy == RetryStrategy.FIBONACCI:
        # Fibonacci sequence for backoff
        fib_sequence = [1, 1]
        while len(fib_sequence) <= attempt:
            fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
        delay = base_delay * fib_sequence[min(attempt, len(fib_sequence) - 1)]
    else:
        delay = base_delay

    # Cap at maximum delay
    delay = min(delay, max_delay)

    # Add jitter to prevent thundering herd problem
    if jitter:
        # Add up to 25% random jitter
        jitter_amount = delay * 0.25 * random.random()
        delay += jitter_amount

    return delay


def is_retryable_error(exception: Exception) -> bool:
    """Determine if an exception is retryable.

    Args:
        exception: The exception to check

    Returns:
        True if the exception should be retried
    """
    # Explicitly marked as non-retryable
    if isinstance(exception, NonRetryableError):
        return False

    # Explicitly marked as retryable
    if isinstance(exception, RetryableError):
        return True

    # Handle HTTP exceptions
    if isinstance(exception, requests.HTTPError):
        if hasattr(exception, "response") and exception.response:
            status_code = exception.response.status_code
            if status_code in NON_RETRYABLE_HTTP_CODES:
                return False
            if status_code in RETRYABLE_HTTP_CODES:
                return True

    # Handle common network exceptions
    if isinstance(
        exception,
        (
            requests.ConnectionError,
            requests.Timeout,
            requests.TooManyRedirects,
            ConnectionError,
            TimeoutError,
        ),
    ):
        return True

    # Handle DNS resolution errors
    if isinstance(exception, requests.exceptions.InvalidURL):
        return False

    # By default, most other exceptions are not retryable
    return False


def retry_with_backoff(
    max_attempts: int = 3,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    exceptions: Union[Type[Exception], tuple] = Exception,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None,
    raise_on_max_attempts: bool = True,
):
    """Decorator for retrying functions with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts (including initial attempt)
        strategy: Retry strategy to use
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        jitter: Whether to add random jitter
        exceptions: Exception types to catch and retry
        on_retry: Callback function called on each retry attempt
        raise_on_max_attempts: Whether to raise exception after max attempts

    Example:
        @retry_with_backoff(max_attempts=5, strategy=RetryStrategy.EXPONENTIAL_BACKOFF)
        def fetch_url(url):
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    # Check if this error should be retried
                    if not is_retryable_error(e):
                        logger.debug(f"Non-retryable error in {func.__name__}: {e}")
                        if raise_on_max_attempts:
                            raise
                        return None

                    # Don't sleep after the last attempt
                    if attempt < max_attempts - 1:
                        delay = calculate_delay(
                            attempt=attempt,
                            strategy=strategy,
                            base_delay=base_delay,
                            max_delay=max_delay,
                            jitter=jitter,
                        )

                        logger.debug(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f} seconds..."
                        )

                        # Call retry callback if provided
                        if on_retry:
                            on_retry(e, attempt + 1, delay)

                        time.sleep(delay)
                    else:
                        logger.debug(f"All {max_attempts} attempts failed for {func.__name__}. Last error: {e}")

            # All attempts exhausted
            if raise_on_max_attempts and last_exception:
                raise last_exception

            return None

        return wrapper

    return decorator


class RetryableSession:
    """Requests session with built-in retry logic."""

    def __init__(
        self,
        max_attempts: int = 3,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter: bool = True,
        timeout: int = 30,
        user_agent: str = "rxiv-maker/1.0 (https://github.com/henriqueslab/rxiv-maker)",
    ):
        """Initialize retryable session.

        Args:
            max_attempts: Maximum retry attempts
            strategy: Retry strategy
            base_delay: Base delay between retries
            max_delay: Maximum delay between retries
            jitter: Whether to add jitter
            timeout: Request timeout in seconds
            user_agent: User agent string
        """
        self.max_attempts = max_attempts
        self.strategy = strategy
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
        self.timeout = timeout

        # Create session with sensible defaults
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make HTTP request with retry logic."""
        # Set default timeout if not provided
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout

        @retry_with_backoff(
            max_attempts=self.max_attempts,
            strategy=self.strategy,
            base_delay=self.base_delay,
            max_delay=self.max_delay,
            jitter=self.jitter,
            exceptions=(requests.RequestException,),
        )
        def _request():
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response

        return _request()

    def get(self, url: str, **kwargs) -> requests.Response:
        """Make GET request with retry logic."""
        return self._make_request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        """Make POST request with retry logic."""
        return self._make_request("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> requests.Response:
        """Make PUT request with retry logic."""
        return self._make_request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs) -> requests.Response:
        """Make DELETE request with retry logic."""
        return self._make_request("DELETE", url, **kwargs)

    def json(self, method: str, url: str, **kwargs) -> dict[str, Any]:
        """Make request and return JSON response with retry logic."""
        response = self._make_request(method, url, **kwargs)
        return response.json()


# Convenience function for quick retryable requests
def get_with_retry(url: str, max_attempts: int = 3, timeout: int = 30, **kwargs) -> requests.Response:
    """Make GET request with retry logic.

    Args:
        url: URL to request
        max_attempts: Maximum retry attempts
        timeout: Request timeout
        **kwargs: Additional arguments to pass to requests.get

    Returns:
        Response object

    Example:
        response = get_with_retry("https://api.crossref.org/works/10.1000/123", max_attempts=5)
        data = response.json()
    """
    session = RetryableSession(max_attempts=max_attempts)
    return session.get(url, timeout=timeout, **kwargs)


def post_with_retry(url: str, max_attempts: int = 3, timeout: int = 30, **kwargs) -> requests.Response:
    """Make POST request with retry logic."""
    session = RetryableSession(max_attempts=max_attempts)
    return session.post(url, timeout=timeout, **kwargs)
