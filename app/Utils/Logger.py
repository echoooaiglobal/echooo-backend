# app/Utils/Logger.py
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
import time

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logger
logger = logging.getLogger("influencer_marketing_api")
logger.setLevel(logging.INFO)

# Log format
log_format = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_format)
logger.addHandler(console_handler)

# File handler with rotation
file_handler = RotatingFileHandler(
    f"logs/app_{time.strftime('%Y-%m-%d')}.log",
    maxBytes=10485760,  # 10MB
    backupCount=10
)
file_handler.setFormatter(log_format)
logger.addHandler(file_handler)