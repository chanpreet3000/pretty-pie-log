# Copyright (c) 2024 Chanpreet Singh
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import json
import logging
import inspect
from functools import wraps
from threading import Lock

import pytz
import os
import sys
import traceback
from datetime import datetime
from colorama import Fore, Style
from typing import Any, Callable, Dict, Optional, TypeVar, Union

from .pie_log_level import PieLogLevel

T = TypeVar('T')  # For generic return type in decorator


class PieLogger:
    """
    A thread-safe, feature-rich logging utility that provides colorized console output with customizable formatting.

    The Logger class extends Python's built-in logging functionality with additional features such as:
    - Colored output using colorama
    - Timezone support
    - Structured logging with JSON formatting
    - Automatic file path detection
    - Stack trace inclusion
    - Thread-safe logging operations
    """

    def __init__(
            self,
            logger_name: str,
            timezone: Optional[str] = None,
            timestamp_padding: int = 30,
            log_level_padding: int = 10,
            file_path_padding: int = 30,
            debug_log_color: Fore = Fore.CYAN,
            info_log_color: Fore = Fore.GREEN,
            warning_log_color: Fore = Fore.YELLOW,
            error_log_color: Fore = Fore.RED,
            critical_log_color: Fore = Fore.MAGENTA,
            timestamp_log_color: Fore = Fore.WHITE,
            file_path_log_color: Fore = Fore.WHITE,
            details_log_color: Fore = Fore.LIGHTWHITE_EX,
            colorful: bool = True,
            minimum_log_level: int = PieLogLevel.INFO,
            default_log_color: Fore = Fore.WHITE,
            details_indent: int = 2
    ) -> None:
        """
        Initialize a new Logger instance with customizable formatting and color options.

        Args:
            logger_name (str): Unique identifier for the logger instance
            timezone (Optional[str]): Timezone for timestamp display (default: None, using UTC)
            timestamp_padding (int): Minimum width of timestamp field (default: 30)
            log_level_padding (int): Minimum width of log level field (default: 10)
            file_path_padding (int): Minimum width of file path field (default: 30)
            debug_log_color (Fore): Color for debug level messages (default: Fore.CYAN)
            info_log_color (Fore): Color for info level messages (default: Fore.GREEN)
            warning_log_color (Fore): Color for warning level messages (default: Fore.YELLOW)
            error_log_color (Fore): Color for error level messages (default: Fore.RED)
            critical_log_color (Fore): Color for critical level messages (default: Fore.MAGENTA)
            timestamp_log_color (Fore): Color for timestamp (default: Fore.WHITE)
            file_path_log_color (Fore): Color for file path (default: Fore.WHITE)
            details_log_color (Fore): Color for JSON details (default: Fore.LIGHTWHITE_EX)
            colorful (bool): Enable/disable colored output (default: True)
            minimum_log_level (int): Minimum logging level (default: PieLogLevel.INFO)
            default_log_color (Fore): Fallback color when colorful is False (default: Fore.WHITE)
            details_indent (int): Spaces for JSON indentation (default: 2)
        """
        self._logger_name = logger_name
        self._timezone = timezone
        self._timestamp_padding = timestamp_padding
        self._log_level_padding = log_level_padding
        self._file_path_padding = file_path_padding
        self._colorful = colorful
        self._project_root = PieLogger.__get_project_root()
        self._minimum_log_level = minimum_log_level
        self._default_log_color = default_log_color
        self._details_indent = details_indent
        self._log_lock = Lock()

        self.console_logger: logging.Logger
        self._debug_log_color = debug_log_color
        self._info_log_color = info_log_color
        self._warning_log_color = warning_log_color
        self._error_log_color = error_log_color
        self._critical_log_color = critical_log_color
        self._timestamp_log_color = timestamp_log_color
        self._file_path_log_color = file_path_log_color
        self._details_log_color = details_log_color

        self.__initialize_logger()

    def __initialize_logger(self) -> None:
        """
        Initialize the console logger with the specified minimum log level and stdout handler.
        """
        self.console_logger = logging.getLogger(f"{self._logger_name}_console")
        self.console_logger.setLevel(self._minimum_log_level)
        self.console_logger.addHandler(logging.StreamHandler(sys.stdout))

    @staticmethod
    def __get_project_root() -> str:
        """
        Determine the project root directory by looking for main.py file. If not found, use the current directory.

        Returns:
            str: Absolute path to the project root directory
        """
        current_path = os.path.abspath(os.path.dirname(__file__))
        while True:
            if os.path.exists(os.path.join(current_path, 'main.py')):
                return current_path
            parent_path = os.path.dirname(current_path)
            if parent_path == current_path:
                return os.path.abspath(os.path.dirname(__file__))
            current_path = parent_path

    def __get_log_details(self) -> str:
        """
        Extract file path and line number information from the call stack.

        Returns:
            str: Formatted string containing relative file path and line number
        """
        frame = inspect.stack()[4]
        file_name = frame.filename
        line_number = frame.lineno

        project_root = self._project_root
        relative_file_name = os.path.relpath(file_name, project_root)
        relative_file_name = f"./{relative_file_name.replace(os.sep, '/')}"

        file_path_info = f"{relative_file_name}:{line_number}"
        return file_path_info

    def __get_timestamp(self) -> str:
        """
        Generate a formatted timestamp string in the configured timezone.

        Returns:
            str: Formatted timestamp string with millisecond precision
        """
        current_time = datetime.now(pytz.utc)
        if self._timezone:
            tz = pytz.timezone(self._timezone)
            current_time = current_time.astimezone(tz)
        return current_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    def __get_color_from_level(self, level: int) -> Fore:
        """
        Determine the appropriate color for a given log level.

        Args:
            level (int): Logging level (DEBUG, INFO, WARNING, ERROR, or CRITICAL)

        Returns:
            Fore: Colorama color code for the specified log level
        """
        if level == PieLogLevel.DEBUG:
            return self._debug_log_color
        elif level == PieLogLevel.INFO:
            return self._info_log_color
        elif level == PieLogLevel.WARNING:
            return self._warning_log_color
        elif level == PieLogLevel.ERROR:
            return self._error_log_color
        elif level == PieLogLevel.CRITICAL:
            return self._critical_log_color

        return self._default_log_color

    def __get_final_color(self, color: Fore, colorful: Optional[bool]) -> Fore:
        is_colorful = self._colorful
        if colorful is not None:
            is_colorful = colorful
        return color if is_colorful else self._default_log_color

    def __console_log(
            self,
            level: int,
            message: str,
            details: Optional[Dict[str, Any]],
            exec_info: Optional[Union[bool, Exception]],
            colorful: Optional[bool]
    ) -> str:
        """
        Format a log message with all configured components in a thread-safe manner.

        Args:
            level (int): Logging level
            message (str): Main log message
            details (Optional[Dict[str, Any]]): Additional structured data to include as JSON
            exec_info (Optional[Union[bool, Exception]]): Exception object or boolean for stack trace inclusion
            colorful (Optional[bool]): Whether to apply colors to this specific message

        Returns:
            str: Formatted log message string
        """
        with self._log_lock:
            timestamp_log_color = self.__get_final_color(self._timestamp_log_color, colorful)
            file_path_log_color = self.__get_final_color(self._file_path_log_color, colorful)
            details_log_color = self.__get_final_color(self._details_log_color, colorful)
            level_color = self.__get_final_color(self.__get_color_from_level(level), colorful)
            level_name = PieLogLevel.get_level_str(level)

            file_path_info = self.__get_log_details()
            timestamp = self.__get_timestamp()

            console_log_parts = [
                f"{timestamp_log_color}{timestamp:<{self._timestamp_padding}}",
                f"{level_color}{level_name:<{self._log_level_padding}}",
                f"{file_path_log_color}{file_path_info:<{self._file_path_padding}}",
                f": {level_color}{message}"
            ]
            console_log = " ".join(console_log_parts)

            if details:
                formatted_details = json.dumps(details, indent=self._details_indent)
                console_log += f"\n{details_log_color}{formatted_details}"

            if exec_info:
                exec_details = ''.join(traceback.format_exc())
                console_log += f"\n{level_color}{exec_details}"

            return console_log + f"{Style.RESET_ALL}"

    def __log(
            self,
            level: int,
            message: str,
            details: Optional[Dict[str, Any]] = None,
            exec_info: bool = False,
            colorful: Optional[bool] = None
    ) -> None:
        """
        Internal method to process and output a log message.

        Args:
            level (int): Logging level
            message (str): Main log message
            details (Optional[Dict[str, Any]]): Additional structured data to include as JSON
            exec_info (bool): Whether to include stack trace
            colorful (Optional[bool]): Whether to apply colors to this specific message
        """
        console_log = self.__console_log(level, message, details, exec_info, colorful)
        self.console_logger.log(level, console_log)

    def log(
            self,
            level: int,
            message: str,
            details: Optional[Dict[str, Any]] = None,
            exec_info: bool = False,
            colorful: Optional[bool] = None
    ) -> None:
        """
        Log a message at the specified level.

        Args:
            level (int): Logging level
            message (str): Main log message
            details (Optional[Dict[str, Any]]): Additional structured data to include as JSON
            exec_info (bool): Whether to include stack trace
            colorful (Optional[bool]): Whether to apply colors to this specific message
        """
        self.__log(level, message, details, exec_info, colorful)

    def debug(
            self,
            message: str,
            details: Optional[Dict[str, Any]] = None,
            exec_info: bool = False,
            colorful: Optional[bool] = None
    ) -> None:
        """
        Log a debug level message.

        Args:
            message (str): Main log message
            details (Optional[Dict[str, Any]]): Additional structured data to include as JSON
            exec_info (bool): Whether to include stack trace
            colorful (Optional[bool]): Whether to apply colors to this specific message
        """
        self.__log(PieLogLevel.DEBUG, message, details, exec_info, colorful)

    def info(
            self,
            message: str,
            details: Optional[Dict[str, Any]] = None,
            exec_info: bool = False,
            colorful: Optional[bool] = None
    ) -> None:
        """
        Log an info level message.

        Args:
            message (str): Main log message
            details (Optional[Dict[str, Any]]): Additional structured data to include as JSON
            exec_info (bool): Whether to include stack trace
            colorful (Optional[bool]): Whether to apply colors to this specific message
        """
        self.__log(PieLogLevel.INFO, message, details, exec_info, colorful)

    def warning(
            self,
            message: str,
            details: Optional[Dict[str, Any]] = None,
            exec_info: bool = False,
            colorful: Optional[bool] = None
    ) -> None:
        """
        Log a warning level message.

        Args:
            message (str): Main log message
            details (Optional[Dict[str, Any]]): Additional structured data to include as JSON
            exec_info (bool): Whether to include stack trace
            colorful (Optional[bool]): Whether to apply colors to this specific message
        """
        self.__log(PieLogLevel.WARNING, message, details, exec_info, colorful)

    def error(
            self,
            message: str,
            details: Optional[Dict[str, Any]] = None,
            exec_info: bool = False,
            colorful: Optional[bool] = None
    ) -> None:
        """
        Log an error level message.

        Args:
            message (str): Main log message
            details (Optional[Dict[str, Any]]): Additional structured data to include as JSON
            exec_info (bool): Whether to include stack trace
            colorful (Optional[bool]): Whether to apply colors to this specific message
        """
        self.__log(PieLogLevel.ERROR, message, details, exec_info, colorful)

    def critical(
            self,
            message: str,
            details: Optional[Dict[str, Any]] = None,
            exec_info: bool = False,
            colorful: Optional[bool] = None
    ) -> None:
        """
        Log a critical level message.

        Args:
            message (str): Main log message
            details (Optional[Dict[str, Any]]): Additional structured data to include as JSON
            exec_info (bool): Whether to include stack trace
            colorful (Optional[bool]): Whether to apply colors to this specific message
        """
        self.__log(PieLogLevel.CRITICAL, message, details, exec_info, colorful)

    def log_execution(
            self,
            start_message: Optional[str] = None,
            end_message: Optional[str] = None,
            print_args_at_start: bool = False,
            print_result_at_end: bool = False,
            start_message_log_level: int = PieLogLevel.INFO,
            end_message_log_level: int = PieLogLevel.INFO
    ) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """
        Creates a decorator that logs function entry and exit with timestamps.

        Args:
            start_message (Optional[str]): Custom message for function start
            end_message (Optional[str]): Custom message for function end
            print_args_at_start (bool): Include function arguments in start message
            print_result_at_end (bool): Include function result in end message
            start_message_log_level (int): Log level for start message
            end_message_log_level (int): Log level for end message

        Returns:
            Callable[[Callable[..., T]], Callable[..., T]]: A decorator function that wraps the original
                function with logging functionality while preserving its return type

        Example:
            ```python
            logger = PieLogger("my_logger")

            @logger.log_execution(
                start_message="Starting task",
                end_message="Task completed",
                print_args_at_start=True,
                print_result_at_end=True
            )
            def process_data(data: List[str]) -> Dict[str, Any]:
                # Function implementation
                return {"status": "success"}
            ```
        """

        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> T:
                # Use custom start message or default
                start_msg = start_message or f"Start of {func.__name__}"
                start_details: Optional[Dict[str, str]] = None
                if print_args_at_start:
                    start_details = {
                        "function": func.__name__,
                        "args": str(args),
                        "kwargs": str(kwargs)
                    }
                self.__log(
                    level=start_message_log_level,
                    message=start_msg,
                    details=start_details,
                )

                # Execute function
                result: T = func(*args, **kwargs)

                # Use custom end message or default
                end_msg = end_message or f"End of {func.__name__}"
                end_details: Optional[Dict[str, str]] = None
                if print_result_at_end:
                    end_details = {
                        "function": func.__name__,
                        "result": str(result)
                    }

                self.__log(
                    level=end_message_log_level,
                    message=end_msg,
                    details=end_details,
                )

                return result

            return wrapper

        return decorator
