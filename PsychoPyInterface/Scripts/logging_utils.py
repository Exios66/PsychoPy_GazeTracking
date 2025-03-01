# Scripts/logging_utils.py
import os
import logging
import traceback
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('logging_utils')

def create_log_file(filepath, header=None):
    """
    Create a log file with optional header.
    
    Parameters:
    -----------
    filepath : str
        Path to the log file
    header : str, optional
        Header line to write at the top of the file
        
    Returns:
    --------
    file object or None
        Opened file object or None if an error occurred
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        log_file = open(filepath, "w")
        if header:
            log_file.write(f"{header}\n")
        logger.info(f"Created log file: {filepath}")
        return log_file
    except Exception as e:
        logger.error(f"Error creating log file {filepath}: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def log_message(log_file, message, include_timestamp=True):
    """
    Write a message to the log file.
    
    Parameters:
    -----------
    log_file : file object
        Open file object to write to
    message : str
        Message to log
    include_timestamp : bool, optional
        Whether to include a timestamp (default: True)
        
    Returns:
    --------
    bool
        True if successful, False otherwise
    """
    try:
        if log_file and not log_file.closed:
            if include_timestamp:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_file.write(f"{timestamp} - {message}\n")
            else:
                log_file.write(f"{message}\n")
            log_file.flush()  # Ensure the message is written immediately
            return True
        else:
            logger.warning("Attempted to write to a closed or invalid log file")
            return False
    except Exception as e:
        logger.error(f"Error writing to log file: {str(e)}")
        return False

def log_data(log_file, data, format='csv', include_timestamp=True):
    """
    Log structured data to a file.
    
    Parameters:
    -----------
    log_file : file object
        Open file object to write to
    data : dict or list
        Data to log
    format : str, optional
        Format to use ('csv' or 'json', default: 'csv')
    include_timestamp : bool, optional
        Whether to include a timestamp (default: True)
        
    Returns:
    --------
    bool
        True if successful, False otherwise
    """
    try:
        if log_file and not log_file.closed:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if include_timestamp else None
            
            if format.lower() == 'json':
                if include_timestamp:
                    data_with_timestamp = {
                        'timestamp': timestamp,
                        'data': data
                    }
                    json.dump(data_with_timestamp, log_file)
                else:
                    json.dump(data, log_file)
                log_file.write('\n')  # Add newline for readability
            
            elif format.lower() == 'csv':
                if isinstance(data, dict):
                    # Convert dict to CSV line
                    values = [str(v) for v in data.values()]
                    if include_timestamp:
                        values.insert(0, timestamp)
                    log_file.write(','.join(values) + '\n')
                elif isinstance(data, list):
                    # Convert list to CSV line
                    values = [str(v) for v in data]
                    if include_timestamp:
                        values.insert(0, timestamp)
                    log_file.write(','.join(values) + '\n')
                else:
                    logger.warning(f"Unsupported data type for CSV logging: {type(data)}")
                    return False
            else:
                logger.warning(f"Unsupported log format: {format}")
                return False
                
            log_file.flush()  # Ensure the data is written immediately
            return True
        else:
            logger.warning("Attempted to write to a closed or invalid log file")
            return False
    except Exception as e:
        logger.error(f"Error logging data: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def close_log_file(log_file):
    """
    Safely close a log file.
    
    Parameters:
    -----------
    log_file : file object
        Open file object to close
        
    Returns:
    --------
    bool
        True if successful, False otherwise
    """
    try:
        if log_file and not log_file.closed:
            log_file.close()
            return True
        return False
    except Exception as e:
        logger.error(f"Error closing log file: {str(e)}")
        return False

def setup_logger(name, log_file=None, level=logging.INFO):
    """
    Set up a logger with optional file output.
    
    Parameters:
    -----------
    name : str
        Name of the logger
    log_file : str, optional
        Path to the log file (if None, logs to console only)
    level : int, optional
        Logging level (default: logging.INFO)
        
    Returns:
    --------
    logging.Logger
        Configured logger
    """
    try:
        # Create logger
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Add file handler if specified
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    except Exception as e:
        print(f"Error setting up logger: {str(e)}")
        # Fall back to basic logger
        return logging.getLogger(name)