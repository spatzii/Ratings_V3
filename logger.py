import os
import sys
import logging

def setup_logger():
    """Configure and return a logger instance."""
    logging.basicConfig(
        level=logging.INFO,  # Use INFO level for production
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

# Create a logger instance that can be imported by other modules
logger = setup_logger()