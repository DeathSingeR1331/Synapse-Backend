import logging
import sys
import structlog

def setup_logging():
    """
    Configures structured logging for the application.
    This should be called once at application startup.
    """
    # These processors will be applied to all log entries
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    structlog.configure(
        processors=shared_processors + [
            # Prepare log entry for the renderer
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure the renderer for log entries
    formatter = structlog.stdlib.ProcessorFormatter(
        # These run after the shared processors
        processor=structlog.processors.JSONRenderer(),
        # These run before the shared processors
        foreign_pre_chain=shared_processors,
    )

    # Configure Python's standard logging to use our structlog formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    print("Structured logging configured.")