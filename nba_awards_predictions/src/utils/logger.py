# src/utils/logger.py

import logging
import os
from datetime import datetime

def get_logger(name: str, log_dir: str = "logs") -> logging.Logger:
    """
    Function for creating a logger to track and record events throughout the pipeline.

    Args:
        name (str): Name of the log file
        log_dir (str, optional): Defaults to "logs".

    Returns:
        logging.Logger: Object for logging events
    """
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{datetime.now():%Y-%m-%d}.log")

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(ch_format)
    
     # File handler
    os.makedirs("logs", exist_ok=True)
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    fh_format = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    fh.setFormatter(fh_format)

    if not logger.handlers:
        logger.addHandler(ch)
        logger.addHandler(fh)


    return logger