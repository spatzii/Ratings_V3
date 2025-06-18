import sys
import logging

def setup_logging():
    """Configure basic logging settings."""
    logging.basicConfig(
        level=logging.INFO,  # Use INFO level for production
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def get_logger(name):
    """Get a logger with the specified name."""
    setup_logging()
    return logging.getLogger(name)
