import logging

def setup_logger():
    """Configure and return a logger that outputs to stdout."""
    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create stdout handler if it doesn't exist
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        
        # Create formatter and add it to the handler
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)

    # Also setup pydiscourse logger specifically
    pydiscourse_logger = logging.getLogger('pydiscourse.client')
    pydiscourse_logger.setLevel(logging.INFO)

    return logger 