"""Logging configuration."""

import logging
import os


def setup_logging() -> None:
    """Set up logging configuration."""
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    # Custom formatter for clean startup output
    class StartupFormatter(logging.Formatter):
        """Custom formatter for clean startup messages."""

        def format(self, record):
            # For startup messages, use clean format without timestamp/logger name
            if hasattr(record, 'startup') and record.startup:
                return record.getMessage()
            # For regular messages, use standard format
            return super().format(record)

    # Configure console handler with custom formatter
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(StartupFormatter())

    # Configure file handler with detailed format
    file_handler = logging.FileHandler("logs/app.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Suppress verbose third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.ERROR)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


def startup_log(message: str, level: int = logging.INFO) -> None:
    """Log a startup message with clean formatting."""
    logger = logging.getLogger("startup")
    record = logger.makeRecord(
        logger.name, level, "", 0, message, (), None
    )
    record.startup = True  # Mark as startup message
    logger.handle(record)
