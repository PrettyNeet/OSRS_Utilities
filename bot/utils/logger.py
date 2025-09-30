import logging
import yaml
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    # Change log directory to be inside /app where we know we have permissions
    log_dir = '/app/logs'
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create logger (idempotent)
    logger = logging.getLogger('bot')
    if logger.handlers:
        # Already configured
        return logger

    logger.setLevel(logging.INFO)
    
    try:
        # Try to create log directory
        os.makedirs(log_dir, exist_ok=True)
        
        # File handler
        log_file = os.path.join(log_dir, 'bot.log')
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=1024 * 1024,  # 1MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except PermissionError:
        # Fallback to console only logging if we can't create/write to log file
        logger.warning("Could not create log directory. Logging to console only.")

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger
