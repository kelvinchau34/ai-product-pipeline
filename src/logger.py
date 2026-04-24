"""Structured logging module for CloudWatch integration."""

from __future__ import annotations

import json
import logging
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Generator


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging compatible with CloudWatch."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Add custom fields if present in record
        if hasattr(record, "job_id"):
            log_data["job_id"] = record.job_id
        if hasattr(record, "pipeline_step"):
            log_data["pipeline_step"] = record.pipeline_step
        if hasattr(record, "status"):
            log_data["status"] = record.status
        if hasattr(record, "products_processed"):
            log_data["products_processed"] = record.products_processed
        if hasattr(record, "warnings_count"):
            log_data["warnings_count"] = record.warnings_count
        if hasattr(record, "errors_count"):
            log_data["errors_count"] = record.errors_count
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms

        # Include exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def get_logger(name: str = "pipeline") -> logging.Logger:
    """
    Get a logger configured for structured JSON output.

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()

    # Set to DEBUG to capture all levels; handlers will filter as needed
    logger.setLevel(logging.DEBUG)

    # Console handler with JSON formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = JSONFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Prevent propagation to avoid duplicate logs
    logger.propagate = False

    return logger


class PipelineLogger:
    """Context manager and utility for structured pipeline logging."""

    def __init__(self, job_id: str | None = None):
        """
        Initialize pipeline logger.

        Args:
            job_id: Unique job identifier (auto-generated if None)
        """
        self.job_id = job_id or str(uuid.uuid4())
        self.logger = get_logger("pipeline")
        self.step_timings: dict[str, float] = {}
        self.metrics = {
            "products_processed": 0,
            "warnings_count": 0,
            "errors_count": 0,
        }

    def _add_job_context(self, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        """Add job context to log record."""
        context = {"job_id": self.job_id}
        if extra:
            context.update(extra)
        return context

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message with job context."""
        extra = self._add_job_context(kwargs)
        record = self.logger.makeRecord(
            self.logger.name,
            logging.INFO,
            "()", 0,
            message,
            (),
            None,
            extra=extra,
        )
        self.logger.handle(record)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message with job context."""
        self.metrics["warnings_count"] += 1
        extra = self._add_job_context(kwargs)
        record = self.logger.makeRecord(
            self.logger.name,
            logging.WARNING,
            "()", 0,
            message,
            (),
            None,
            extra=extra,
        )
        self.logger.handle(record)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message with job context."""
        self.metrics["errors_count"] += 1
        extra = self._add_job_context(kwargs)
        record = self.logger.makeRecord(
            self.logger.name,
            logging.ERROR,
            "()", 0,
            message,
            (),
            None,
            extra=extra,
        )
        self.logger.handle(record)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message with job context."""
        extra = self._add_job_context(kwargs)
        record = self.logger.makeRecord(
            self.logger.name,
            logging.DEBUG,
            "()", 0,
            message,
            (),
            None,
            extra=extra,
        )
        self.logger.handle(record)

    @contextmanager
    def step(self, step_name: str) -> Generator[None, None, None]:
        """
        Context manager for timing and logging pipeline steps.

        Args:
            step_name: Name of the pipeline step

        Usage:
            with pipeline_logger.step("normalize"):
                # do work
        """
        start_time = time.time()
        self.info(f"Starting {step_name}", pipeline_step=step_name, status="starting")
        try:
            yield
            duration_ms = int((time.time() - start_time) * 1000)
            self.step_timings[step_name] = duration_ms
            self.info(
                f"Completed {step_name}",
                pipeline_step=step_name,
                status="completed",
                duration_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.step_timings[step_name] = duration_ms
            self.error(
                f"Failed {step_name}: {str(e)}",
                pipeline_step=step_name,
                status="failed",
                duration_ms=duration_ms,
            )
            raise

    def record_products_processed(self, count: int) -> None:
        """Record number of products processed."""
        self.metrics["products_processed"] = count
        self.info(
            f"Processed {count} products",
            products_processed=count,
        )

    def record_validation_metrics(self, valid_count: int, invalid_count: int) -> None:
        """Record validation metrics."""
        self.info(
            f"Validation complete: {valid_count} valid, {invalid_count} invalid",
            products_processed=valid_count,
            errors_count=invalid_count,
        )

    def log_pipeline_summary(self) -> dict[str, Any]:
        """
        Log final pipeline summary.

        Returns:
            Summary dict with all metrics and timings
        """
        summary = {
            "job_id": self.job_id,
            "metrics": self.metrics,
            "step_timings_ms": self.step_timings,
            "total_duration_ms": sum(self.step_timings.values()),
        }
        self.info(
            "Pipeline execution summary",
            status="completed",
            products_processed=self.metrics["products_processed"],
            warnings_count=self.metrics["warnings_count"],
            errors_count=self.metrics["errors_count"],
            duration_ms=summary["total_duration_ms"],
        )
        return summary
