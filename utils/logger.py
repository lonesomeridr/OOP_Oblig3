import datetime
import inspect
import os

# Log levels
DEBUG = 10
INFO = 20
WARNING = 30
ERROR = 40
CRITICAL = 50

# Default configuration
_config = {
    'level': INFO,
    'format': '[{time}] {level}: {message}',
    'time_format': '%Y-%m-%d %H:%M:%S',
    'file': None,
    'show_source': False
}

# Level names for display
_level_names = {
    DEBUG: 'DEBUG',
    INFO: 'INFO',
    WARNING: 'WARNING',
    ERROR: 'ERROR',
    CRITICAL: 'CRITICAL'
}


def configure(level=None, format=None, time_format=None, file=None, show_source=None):
    """Configure the logger settings"""
    if level is not None:
        _config['level'] = level
    if format is not None:
        _config['format'] = format
    if time_format is not None:
        _config['time_format'] = time_format
    if file is not None:
        _config['file'] = file
    if show_source is not None:
        _config['show_source'] = show_source


def log(msg, level=INFO):
    """
    Log a message at the specified level.

    For backward compatibility, defaults to INFO level.
    All existing code calling log(msg) will continue to work.
    """
    # Skip logging if message level is below configured level
    if level < _config['level']:
        return

    # Get caller information if enabled
    source = ""
    if _config['show_source']:
        frame = inspect.currentframe().f_back
        filename = os.path.basename(frame.f_code.co_filename)
        lineno = frame.f_lineno
        source = f" ({filename}:{lineno})"

    # Format the message
    timestamp = datetime.datetime.now().strftime(_config['time_format'])
    level_name = _level_names.get(level, 'INFO')
    formatted_msg = _config['format'].format(
        time=timestamp,
        level=level_name,
        message=msg
    ) + source

    # Print to console
    print(formatted_msg)

    # Write to file if configured
    if _config['file']:
        try:
            with open(_config['file'], 'a') as f:
                f.write(formatted_msg + '\n')
        except Exception as e:
            print(f"Error writing to log file: {e}")


# Convenience methods for different log levels
def debug(msg):
    """Log a DEBUG level message"""
    log(msg, DEBUG)


def info(msg):
    """Log an INFO level message"""
    log(msg, INFO)


def warning(msg):
    """Log a WARNING level message"""
    log(msg, WARNING)


def error(msg):
    """Log an ERROR level message"""
    log(msg, ERROR)


def critical(msg):
    """Log a CRITICAL level message"""
    log(msg, CRITICAL)