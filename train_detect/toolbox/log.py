# -*- coding: utf-8 -*-
"""
Logging utilities
"""
import os
import logging
from logging import handlers


class LogTxt:
    """Text-based logging class"""
    def __init__(self, logger_name='ErayLog', file_path='./logs/Log.txt', 
                 stream_level=logging.DEBUG, file_level=logging.DEBUG, backupCount=0):
        """
        Universal logger, automatically switches to new log file at midnight
        
        Args:
            logger_name(str): Logger name, can be used across files
            file_path(str): Log file path
            stream_level(logging.level): Console output log level
            file_level(logging.level): File output log level
            backupCount(int): Maximum number of log files to keep, 0 means unlimited
        """
        dir_path = os.path.dirname(file_path)
        os.makedirs(dir_path, exist_ok=True)

        self.logger_name = logger_name
        self.file_path = file_path
        self.stream_level = stream_level
        self.file_level = file_level
        self.backupCount = backupCount

        logger = logging.getLogger(logger_name)
        if not logger.handlers:
            stream_handler = self._create_streamHandler(self.stream_level)
            file_handler = self._create_fileHandler(self.file_path, self.file_level, self.backupCount)
            
            # Add handler
            logger.setLevel(logging.DEBUG)
            logger.addHandler(stream_handler)
            logger.addHandler(file_handler)
                
        self.logger = logger

    def _get_formatter(self):
        """Get log formatter"""
        stream_format = "%(asctime)s %(filename)s %(funcName)s -> line:%(lineno)d [%(levelname)s]: %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(stream_format, datefmt=date_format)
        return formatter

    def _create_streamHandler(self, stream_level):
        """Create stream handler for console output"""
        stream_handler = logging.StreamHandler()
        formatter = self._get_formatter()
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(stream_level)
        return stream_handler

    def _create_fileHandler(self, file_path, file_level, backUpCount=0):
        """Create file handler for file output"""
        formatter = self._get_formatter()
        file_handler = handlers.TimedRotatingFileHandler(file_path, when='midnight', backupCount=backUpCount)
        file_handler.suffix = "%Y%m%d-%H%M.log"
        file_handler.setFormatter(formatter)
        file_handler.setLevel(file_level)
        return file_handler

    def getLogger(self):
        """Get logger instance"""
        return self.logger
