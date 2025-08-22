#!/usr/bin/env python3
"""
Common utility functions for GitHub Actions scripts.

Provides HTTP helpers, retry logic, validation, and external API interactions.
"""

import os
import subprocess
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


class RetryConfig:
    """Configuration for retry logic."""

    def __init__(
        self, max_retries: int = 3, backoff_factor: float = 2.0, initial_delay: float = 1.0, max_delay: float = 60.0
    ):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.initial_delay = initial_delay
        self.max_delay = max_delay


def retry_with_backoff(func: Callable, retry_config: RetryConfig = None, logger=None) -> Any:
    """
    Execute function with exponential backoff retry logic.

    Args:
        func: Function to execute
        retry_config: Retry configuration
        logger: Optional logger for retry attempts

    Returns:
        Function result

    Raises:
        Last exception if all retries fail
    """
    if retry_config is None:
        retry_config = RetryConfig()

    last_exception = None
    delay = retry_config.initial_delay

    for attempt in range(retry_config.max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e

            if attempt < retry_config.max_retries:
                if logger:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s...")
                time.sleep(delay)
                delay = min(delay * retry_config.backoff_factor, retry_config.max_delay)
            else:
                if logger:
                    logger.error(f"All {retry_config.max_retries + 1} attempts failed")

    raise last_exception


def create_http_session(timeout: int = 30) -> requests.Session:
    """
    Create HTTP session with retry strategy.

    Args:
        timeout: Request timeout in seconds

    Returns:
        Configured requests session
    """
    session = requests.Session()

    # Configure retry strategy
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],  # Updated from method_whitelist
        backoff_factor=1,
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.timeout = timeout

    return session


def check_pypi_package_available(package_name: str, version: str) -> bool:
    """
    Check if package version is available on PyPI.

    Args:
        package_name: Package name
        version: Package version (with or without 'v' prefix)

    Returns:
        True if package is available, False otherwise
    """
    # Clean version (remove 'v' prefix if present)
    clean_version = version.lstrip("v")

    session = create_http_session()

    try:
        # Check PyPI JSON API
        url = f"https://pypi.org/pypi/{package_name}/{clean_version}/json"
        response = session.get(url)

        if response.status_code == 200:
            return True
        elif response.status_code == 404:
            return False
        else:
            response.raise_for_status()

    except requests.RequestException:
        return False


def check_github_release_exists(owner: str, repo: str, tag: str, github_token: str) -> bool:
    """
    Check if GitHub release exists.

    Args:
        owner: Repository owner
        repo: Repository name
        tag: Release tag
        github_token: GitHub API token

    Returns:
        True if release exists, False otherwise
    """
    session = create_http_session()

    headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"}

    try:
        url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag}"
        response = session.get(url, headers=headers)

        if response.status_code == 200:
            return True
        elif response.status_code == 404:
            return False
        else:
            response.raise_for_status()

    except requests.RequestException:
        return False


def trigger_workflow(
    owner: str, repo: str, workflow_id: str, ref: str, inputs: Dict[str, Any], github_token: str
) -> bool:
    """
    Trigger GitHub Actions workflow.

    Args:
        owner: Repository owner
        repo: Repository name
        workflow_id: Workflow ID or filename
        ref: Git reference (branch/tag)
        inputs: Workflow inputs
        github_token: GitHub API token

    Returns:
        True if workflow was triggered successfully
    """
    session = create_http_session()

    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }

    data = {"ref": ref, "inputs": inputs}

    try:
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches"
        response = session.post(url, headers=headers, json=data)

        if response.status_code == 204:
            return True
        else:
            response.raise_for_status()

    except requests.RequestException:
        return False


def run_command(
    command: List[str], cwd: Optional[Path] = None, timeout: int = 300, logger=None
) -> subprocess.CompletedProcess:
    """
    Run shell command with proper error handling.

    Args:
        command: Command and arguments as list
        cwd: Working directory
        timeout: Timeout in seconds
        logger: Optional logger

    Returns:
        Completed process result

    Raises:
        subprocess.CalledProcessError on failure
    """
    if logger:
        logger.info(f"Running command: {' '.join(command)}")

    try:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=True)

        if logger and result.stdout:
            logger.debug(f"Command output: {result.stdout}")

        return result

    except subprocess.CalledProcessError as e:
        if logger:
            logger.error(f"Command failed with exit code {e.returncode}")
            if e.stdout:
                logger.error(f"stdout: {e.stdout}")
            if e.stderr:
                logger.error(f"stderr: {e.stderr}")
        raise

    except subprocess.TimeoutExpired:
        if logger:
            logger.error(f"Command timed out after {timeout}s")
        raise


def validate_environment(required_vars: List[str]) -> Dict[str, str]:
    """
    Validate required environment variables are present.

    Args:
        required_vars: List of required environment variable names

    Returns:
        Dictionary of environment variables

    Raises:
        ValueError if any required variables are missing
    """
    missing_vars = []
    env_vars = {}

    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            env_vars[var] = value

    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    return env_vars


def wait_for_condition(condition_func: Callable[[], bool], timeout: int, check_interval: int = 10, logger=None) -> bool:
    """
    Wait for condition to become true with timeout.

    Args:
        condition_func: Function that returns bool
        timeout: Maximum wait time in seconds
        check_interval: Check interval in seconds
        logger: Optional logger

    Returns:
        True if condition met, False if timeout
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        if condition_func():
            return True

        if logger:
            elapsed = int(time.time() - start_time)
            logger.info(f"Condition not met after {elapsed}s, waiting...")

        time.sleep(check_interval)

    return False
