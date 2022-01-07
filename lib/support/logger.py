from genericpath import exists
import os, logging, logging.handlers
from datetime import datetime
from pytz import timezone, utc
"""
ConsoleColor.Black => "\x1B[30m",
            ConsoleColor.DarkRed => "\x1B[31m",
            ConsoleColor.DarkGreen => "\x1B[32m",
            ConsoleColor.DarkYellow => "\x1B[33m",
            ConsoleColor.DarkBlue => "\x1B[34m",
            ConsoleColor.DarkMagenta => "\x1B[35m",
            ConsoleColor.DarkCyan => "\x1B[36m",
            ConsoleColor.Gray => "\x1B[37m",
            ConsoleColor.Red => "\x1B[1m\x1B[31m",
            ConsoleColor.Green => "\x1B[1m\x1B[32m",
            ConsoleColor.Yellow => "\x1B[1m\x1B[33m",
            ConsoleColor.Blue => "\x1B[1m\x1B[34m",
            ConsoleColor.Magenta => "\x1B[1m\x1B[35m",
            ConsoleColor.Cyan => "\x1B[1m\x1B[36m",
            ConsoleColor.White => "\x1B[1m\x1B[37m",
"""

class CustomFormatter(logging.Formatter):
    """Logging Formatter to add colors and count warning / errors"""

    grey = "\x1b[38;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    green = "\x1B[32m"
    #format = "[%(asctime)s|%(name)s|%(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    format = u'[%(asctime)s|%(levelname)s|%(name)s|%(pathname)s:%(lineno)s] %(message)s'

    FORMATS = {
        logging.DEBUG: green + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def get_logger(name, log_path=None):
    logger = logging.getLogger(name)
    if not logger.handlers:
        level = logging.DEBUG
        logger.setLevel(level)
        formatter = logging.Formatter(u'[%(asctime)s|%(levelname)s|%(filename)s:%(lineno)s] %(message)s')
        def customTime(*args):
            utc_dt = utc.localize(datetime.utcnow())
            my_tz = timezone("Asia/Seoul")
            converted = utc_dt.astimezone(my_tz)
            return converted.timetuple()

        formatter.converter = customTime
        file_max_bytes = 1 * 1024 * 1024 
        if log_path == None:
            log_path = os.path.join(os.getcwd(), 'tmp')
            os.makedirs(log_path, exist_ok=True)
        fileHandler = logging.handlers.RotatingFileHandler(filename=os.path.join(log_path, f'{name}.log'), maxBytes=file_max_bytes, backupCount=5, encoding='utf8', delay=True)
        streamHandler = logging.StreamHandler() 

        fileHandler.setFormatter(formatter)
        streamHandler.setFormatter(CustomFormatter()) 
        
        logger.addHandler(fileHandler)
        logger.addHandler(streamHandler)
    return logger

