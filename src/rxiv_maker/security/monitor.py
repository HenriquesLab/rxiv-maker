"""Security monitoring and alerting module.

This module provides real-time security monitoring, logging, and alerting
for potential security incidents in the rxiv-maker system.
"""

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class SecurityEventType(Enum):
    """Types of security events to monitor."""

    PATH_TRAVERSAL_ATTEMPT = "path_traversal_attempt"
    SYMLINK_ATTACK = "symlink_attack"
    PERMISSION_VIOLATION = "permission_violation"
    DISK_EXHAUSTION = "disk_exhaustion"
    LARGE_FILE_ATTEMPT = "large_file_attempt"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    AUTHENTICATION_FAILURE = "authentication_failure"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    CHECKSUM_MISMATCH = "checksum_mismatch"
    UNSAFE_OPERATION = "unsafe_operation"


class SecuritySeverity(Enum):
    """Security event severity levels."""

    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"  # Potential security breach
    MEDIUM = "medium"  # Security concern
    LOW = "low"  # Informational
    INFO = "info"  # Audit trail


@dataclass
class SecurityEvent:
    """Represents a security event."""

    event_type: SecurityEventType
    severity: SecuritySeverity
    timestamp: float = field(default_factory=time.time)
    description: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    user: Optional[str] = None
    ip_address: Optional[str] = None
    action_taken: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp,
            "datetime": datetime.fromtimestamp(self.timestamp).isoformat(),
            "description": self.description,
            "details": self.details,
            "source": self.source,
            "user": self.user,
            "ip_address": self.ip_address,
            "action_taken": self.action_taken,
        }


class SecurityMonitor:
    """Main security monitoring system."""

    def __init__(
        self,
        log_dir: Optional[Path] = None,
        alert_threshold: SecuritySeverity = SecuritySeverity.HIGH,
        max_events: int = 10000,
        rate_limit_window: int = 60,  # seconds
        rate_limit_max: int = 100,  # max events per window
    ):
        """Initialize security monitor.

        Args:
            log_dir: Directory for security logs
            alert_threshold: Minimum severity to trigger alerts
            max_events: Maximum events to keep in memory
            rate_limit_window: Time window for rate limiting (seconds)
            rate_limit_max: Maximum events allowed per window
        """
        self.log_dir = log_dir or Path.home() / ".rxiv-maker" / "security"
        self.alert_threshold = alert_threshold
        self.max_events = max_events
        self.rate_limit_window = rate_limit_window
        self.rate_limit_max = rate_limit_max

        # In-memory event storage
        self.events: List[SecurityEvent] = []
        self.event_counts: Dict[str, int] = {}
        self.rate_limit_tracker: Dict[str, List[float]] = {}

        # Blocked entities
        self.blocked_paths: Set[str] = set()
        self.blocked_ips: Set[str] = set()

        # Statistics
        self.stats: Dict[str, Any] = {
            "total_events": 0,
            "events_by_type": {},
            "events_by_severity": {},
            "blocked_attempts": 0,
            "alerts_sent": 0,
        }

        # Initialize typed dictionaries to help mypy
        self.events_by_type: Dict[str, int] = self.stats["events_by_type"]
        self.events_by_severity: Dict[str, int] = self.stats["events_by_severity"]

        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

        # Initialize security log file
        self.security_log = self.log_dir / f"security_{datetime.now().strftime('%Y%m%d')}.log"

    def log_event(self, event: SecurityEvent) -> None:
        """Log a security event.

        Args:
            event: Security event to log
        """
        # Update statistics
        self.stats["total_events"] += 1
        self.events_by_type[event.event_type.value] = self.events_by_type.get(event.event_type.value, 0) + 1
        self.events_by_severity[event.severity.value] = self.events_by_severity.get(event.severity.value, 0) + 1

        # Add to in-memory storage
        self.events.append(event)

        # Trim if exceeded max events
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events :]

        # Write to log file
        self._write_to_log(event)

        # Check if alert needed
        if self._should_alert(event):
            self._send_alert(event)

        # Check for patterns requiring action
        self._analyze_patterns(event)

        # Log to standard logger
        log_level = self._severity_to_log_level(event.severity)
        logger.log(log_level, f"Security Event: {event.description}")

    def check_path_traversal(self, path: str, base_dir: str) -> bool:
        """Check for path traversal attempts.

        Args:
            path: Path to check
            base_dir: Base directory that should contain path

        Returns:
            True if path is safe, False if traversal detected
        """
        try:
            resolved_path = Path(path).resolve()
            resolved_base = Path(base_dir).resolve()

            # Check if path is within base
            resolved_path.relative_to(resolved_base)
            return True

        except (ValueError, RuntimeError):
            # Log security event
            self.log_event(
                SecurityEvent(
                    event_type=SecurityEventType.PATH_TRAVERSAL_ATTEMPT,
                    severity=SecuritySeverity.HIGH,
                    description="Path traversal attempt detected",
                    details={"path": path, "base_dir": base_dir},
                    source="path_check",
                    action_taken="Blocked access",
                )
            )

            # Block the path
            self.blocked_paths.add(path)
            self.stats["blocked_attempts"] += 1

            return False

    def check_rate_limit(self, identifier: str) -> bool:
        """Check if rate limit exceeded for identifier.

        Args:
            identifier: Unique identifier (IP, user, etc.)

        Returns:
            True if within limits, False if exceeded
        """
        current_time = time.time()

        # Initialize tracker if needed
        if identifier not in self.rate_limit_tracker:
            self.rate_limit_tracker[identifier] = []

        # Remove old entries outside window
        self.rate_limit_tracker[identifier] = [
            t for t in self.rate_limit_tracker[identifier] if current_time - t < self.rate_limit_window
        ]

        # Check if limit exceeded
        if len(self.rate_limit_tracker[identifier]) >= self.rate_limit_max:
            self.log_event(
                SecurityEvent(
                    event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
                    severity=SecuritySeverity.MEDIUM,
                    description=f"Rate limit exceeded for {identifier}",
                    details={
                        "identifier": identifier,
                        "requests": len(self.rate_limit_tracker[identifier]),
                        "window": self.rate_limit_window,
                    },
                    source="rate_limiter",
                    action_taken="Request blocked",
                )
            )
            return False

        # Add current request
        self.rate_limit_tracker[identifier].append(current_time)
        return True

    def verify_file_integrity(self, file_path: Path, expected_hash: Optional[str] = None) -> bool:
        """Verify file integrity using checksums.

        Args:
            file_path: Path to file to verify
            expected_hash: Expected SHA256 hash (if known)

        Returns:
            True if file is valid, False otherwise
        """
        try:
            if not file_path.exists():
                return False

            # Calculate current hash
            current_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()

            if expected_hash and current_hash != expected_hash:
                self.log_event(
                    SecurityEvent(
                        event_type=SecurityEventType.CHECKSUM_MISMATCH,
                        severity=SecuritySeverity.HIGH,
                        description="File integrity check failed",
                        details={"file": str(file_path), "expected_hash": expected_hash, "actual_hash": current_hash},
                        source="integrity_check",
                        action_taken="File quarantined",
                    )
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Integrity check failed: {e}")
            return False

    def detect_suspicious_patterns(self, content: str) -> List[str]:
        """Detect suspicious patterns in content.

        Args:
            content: Content to analyze

        Returns:
            List of detected suspicious patterns
        """
        suspicious_patterns = [
            (r"rm\s+-rf\s+/", "Dangerous rm command"),
            (r"curl.*\|.*sh", "Curl pipe to shell"),
            (r"wget.*\|.*bash", "Wget pipe to bash"),
            (r"/etc/passwd", "System file access"),
            (r"/etc/shadow", "Password file access"),
            (r"\.ssh/id_rsa", "SSH key access"),
            (r"eval\s*\(", "Eval usage"),
            (r"exec\s*\(", "Exec usage"),
            (r"os\.system", "System command execution"),
            (r"subprocess.*shell=True", "Shell injection risk"),
        ]

        import re

        detected = []
        for pattern, description in suspicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                detected.append(description)

                self.log_event(
                    SecurityEvent(
                        event_type=SecurityEventType.SUSPICIOUS_PATTERN,
                        severity=SecuritySeverity.MEDIUM,
                        description=f"Suspicious pattern detected: {description}",
                        details={"pattern": pattern},
                        source="pattern_detector",
                        action_taken="Flagged for review",
                    )
                )

        return detected

    def get_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report.

        Returns:
            Dictionary containing security metrics and events
        """
        now = time.time()

        # Calculate time-based metrics
        last_hour_events = [e for e in self.events if now - e.timestamp < 3600]

        last_day_events = [e for e in self.events if now - e.timestamp < 86400]

        # Group events by type for last hour
        recent_by_type: Dict[str, int] = {}
        for event in last_hour_events:
            event_type = event.event_type.value
            recent_by_type[event_type] = recent_by_type.get(event_type, 0) + 1

        # Find most common security issues
        top_issues = sorted(self.events_by_type.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "summary": {
                "total_events": self.stats["total_events"],
                "blocked_attempts": self.stats["blocked_attempts"],
                "alerts_sent": self.stats["alerts_sent"],
                "events_last_hour": len(last_hour_events),
                "events_last_day": len(last_day_events),
            },
            "events_by_severity": self.events_by_severity,
            "events_by_type": self.events_by_type,
            "recent_activity": recent_by_type,
            "top_issues": top_issues,
            "blocked_entities": {
                "paths": len(self.blocked_paths),
                "ips": len(self.blocked_ips),
            },
            "recent_critical_events": [
                e.to_dict()
                for e in self.events[-10:]
                if e.severity in [SecuritySeverity.CRITICAL, SecuritySeverity.HIGH]
            ],
        }

    def _write_to_log(self, event: SecurityEvent) -> None:
        """Write event to log file."""
        try:
            with open(self.security_log, "a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict()) + "\n")
        except Exception as e:
            logger.error(f"Failed to write security log: {e}")

    def _should_alert(self, event: SecurityEvent) -> bool:
        """Determine if event should trigger an alert."""
        severity_order = {
            SecuritySeverity.INFO: 0,
            SecuritySeverity.LOW: 1,
            SecuritySeverity.MEDIUM: 2,
            SecuritySeverity.HIGH: 3,
            SecuritySeverity.CRITICAL: 4,
        }

        return severity_order[event.severity] >= severity_order[self.alert_threshold]

    def _send_alert(self, event: SecurityEvent) -> None:
        """Send security alert."""
        self.stats["alerts_sent"] += 1

        # Log alert with high priority
        logger.critical(f"SECURITY ALERT: {event.description}")

        # In production, this would send notifications via:
        # - Email
        # - Slack/Discord webhooks
        # - SMS for critical events
        # - SIEM integration

    def _analyze_patterns(self, event: SecurityEvent) -> None:
        """Analyze patterns in security events."""
        # Check for repeated attempts from same source
        if event.source:
            key = f"{event.event_type.value}:{event.source}"
            self.event_counts[key] = self.event_counts.get(key, 0) + 1

            # Block after threshold
            if self.event_counts[key] > 10:
                if event.ip_address:
                    self.blocked_ips.add(event.ip_address)
                    logger.warning(f"Blocked IP after repeated attempts: {event.ip_address}")

    def _severity_to_log_level(self, severity: SecuritySeverity) -> int:
        """Convert severity to Python log level."""
        mapping = {
            SecuritySeverity.INFO: logging.INFO,
            SecuritySeverity.LOW: logging.INFO,
            SecuritySeverity.MEDIUM: logging.WARNING,
            SecuritySeverity.HIGH: logging.ERROR,
            SecuritySeverity.CRITICAL: logging.CRITICAL,
        }
        return mapping[severity]


# Global security monitor instance
_monitor: Optional[SecurityMonitor] = None


def get_security_monitor() -> SecurityMonitor:
    """Get or create global security monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = SecurityMonitor()
    return _monitor


def log_security_event(event_type: SecurityEventType, severity: SecuritySeverity, description: str, **kwargs) -> None:
    """Convenience function to log security events.

    Args:
        event_type: Type of security event
        severity: Event severity
        description: Human-readable description
        **kwargs: Additional event details
    """
    monitor = get_security_monitor()
    monitor.log_event(
        SecurityEvent(
            event_type=event_type,
            severity=severity,
            description=description,
            details=kwargs.get("details", {}),
            source=kwargs.get("source", ""),
            user=kwargs.get("user"),
            ip_address=kwargs.get("ip_address"),
            action_taken=kwargs.get("action_taken", ""),
        )
    )
