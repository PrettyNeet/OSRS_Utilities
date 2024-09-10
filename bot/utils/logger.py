import logging
import yaml
import os


def setup_logging():
    # load config
    with open("config/config.yaml", "r") as file:
        config = yaml.safe_load(file)
    
    logging_level = getattr(logging, config["logging"]["level"].upper(), logging.info)
    
    # create logger
    logger = logging.getLogger()
    logger.setLevel(logging_level)
    
    # create handlers based on config
    for handler_config in config["logging"]["handlers"]:
        if handler_config["type"] == "console":
            handler = logging.StreamHandler()
        elif handler_config["type"] == "file":
            log_dir = os.path.dirname(handler_config["filename"])
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            handler = logging.FileHandler(handler_config["filename"])
        else:
            continue
        
        # creating formatter and add to handler
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s')
        handler.setFormatter(formatter)
        
        # add handler to logger
        logger.addHandler(handler)
    
    return logger
