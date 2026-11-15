import inspect
import json
import logging
import os
import re
import sys
import traceback
from contextvars import ContextVar
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar

import pytz
from colorama import Fore, Style
from concurrent_log_handler import ConcurrentRotatingFileHandler

from .pie_log_level import PieLogLevel

T = TypeVar('T')

_JSON_SCALARS = (str, int, float, bool, type(None))

# Frames belonging to this file are skipped when resolving the caller location. Taken from a local code
# object rather than __file__ so it matches co_filename exactly and works when __file__ is absent
# (frozen builds); this mirrors how the stdlib logging module identifies its own frames.
_PIE_LOGGER_FILE = os.path.normcase((lambda: None).__code__.co_filename)


class PieLogger:
    """
    A thread-safe, feature-rich logging utility that provides colorized console output with customizable formatting.

    Features:
    - Thread-safe logging operations
    - Colored console output with configurable color schemes
    - Timezone-aware timestamps
    - Structured logging with formatted JSON output
    - Automatic source code location detection
    - Error stack trace integration for debugging
    - Rotating file logs with size limits and backups, safe to share between processes
    - Customizable field padding and indentation
    """

    def __init__(
            self,
            logger_name: str,
            timezone: Optional[str] = None,
            timestamp_padding: int = 25,
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
            details_indent: int = 2,
            log_to_file: bool = True,
            relative_log_directory_path: str = 'logs',
            log_file_size_limit: int = 32 * 1024 * 1024,
            max_backup_files: int = 1,
            global_context: bool = False,
    ) -> None:
        """
        Initialize a new Logger instance with customizable formatting, color and output options.

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
            log_to_file (bool): Enable/disable file logging (default: True)
            relative_log_directory_path (str): Directory for log files (default: 'logs')
            log_file_size_limit (int): Maximum size for log files in bytes (default: 32 MB = 32 * 1024 * 1024)
            max_backup_files (int): Number of backup log files to keep (default: 1). With 0 the file is
                never rotated and log_file_size_limit is ignored
            global_context (bool): Include the context set with add_context in every message (default: False)
        """
        self._start_timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

        self._logger_name = logger_name
        # Resolved here so an unknown timezone fails at construction instead of on every log call
        self._tz = pytz.timezone(timezone) if timezone else pytz.utc
        self._timestamp_padding = timestamp_padding
        self._log_level_padding = log_level_padding
        self._file_path_padding = file_path_padding
        self._colorful = colorful
        self._minimum_log_level = minimum_log_level
        self._default_log_color = default_log_color
        self._details_indent = details_indent
        # Caches absolute filename -> display path, so os.path.relpath runs once per source file.
        self._relative_path_cache: Dict[str, str] = {}

        frame = inspect.currentframe()
        caller_frame = frame.f_back if frame else None
        if caller_frame:
            caller_file = caller_frame.f_code.co_filename
            self._initialization_directory = os.path.dirname(os.path.abspath(caller_file))
        else:
            self._initialization_directory = os.getcwd()

        self._project_root = self._initialization_directory

        self.console_logger: logging.Logger
        self._debug_log_color = debug_log_color
        self._info_log_color = info_log_color
        self._warning_log_color = warning_log_color
        self._error_log_color = error_log_color
        self._critical_log_color = critical_log_color
        self._timestamp_log_color = timestamp_log_color
        self._file_path_log_color = file_path_log_color
        self._details_log_color = details_log_color

        self._log_to_file = log_to_file
        self._relative_log_directory_path = relative_log_directory_path
        self._log_file_size_limit = log_file_size_limit
        self._max_backup_files = max_backup_files
        self._global_context = global_context
        # A ContextVar gives every thread and asyncio task its own context, so concurrent requests cannot
        # log each other's values. The dict is replaced on every change, never mutated: the default is shared.
        self._context: ContextVar[Dict[str, Any]] = ContextVar(f"{logger_name}_context", default={})

        self.__initialize_logger()

    def __initialize_logger(self) -> None:
        """
        Set up console and file logging handlers with appropriate formatting and rotation policies.
        Creates log directory structure if needed and configures rotating file handler if file
        logging is enabled.
        """
        self.console_logger = logging.getLogger(f"{self._logger_name}_console")
        self.console_logger.setLevel(self._minimum_log_level)
        # Root handlers installed by the app or a framework would print every line a second time
        self.console_logger.propagate = False
        # getLogger returns one object per name, so a second PieLogger with this name must not stack handlers
        if not self.console_logger.handlers:
            self.console_logger.addHandler(logging.StreamHandler(sys.stdout))

        if self._log_to_file:
            logs_dir = os.path.join(self._project_root, self._relative_log_directory_path)
            os.makedirs(logs_dir, exist_ok=True)
            # Separators would escape logs_dir, and ':' on Windows writes to an NTFS alternate stream
            log_file_name = re.sub(r'[\\/:*?"<>|]', '_', self._logger_name)
            log_file_path = os.path.join(logs_dir, f"{log_file_name}.log")

            self.file_logger = logging.getLogger(f"{self._logger_name}_file")
            self.file_logger.setLevel(self._minimum_log_level)
            self.file_logger.propagate = False

            if not self.file_logger.handlers:
                # The stdlib RotatingFileHandler breaks when several processes share the file (gunicorn
                # workers): after one rotates, each of the others rotates again, so near-empty files push
                # the real ones out of the backups. This handler locks the file around writes and rotation.
                self.file_logger.addHandler(ConcurrentRotatingFileHandler(
                    filename=log_file_path,
                    # With no backups this handler would empty the file at the limit, where the stdlib one
                    # never rotated. 0 turns rotation off and keeps that behaviour.
                    maxBytes=self._log_file_size_limit if self._max_backup_files > 0 else 0,
                    backupCount=self._max_backup_files,
                    # The Windows locale default (cp1252) silently drops every character it cannot encode
                    encoding="utf-8"
                ))

    def __extract_caller_location(self) -> str:
        """
        Extract file path and line number information from the call stack.

        Walks the frame chain directly (as `logging.Logger.findCaller` does) instead of materialising the
        whole stack via `inspect.stack()`, which would build a FrameInfo - module lookup, source file
        resolution and a `linecache` stat - for every frame just to read two attributes off one of them.

        The first frame outside this module is treated as the caller, so wrappers around the logger are
        attributed to their own caller rather than to a hardcoded stack depth.

        Returns:
            str: Formatted string containing relative file path and line number
        """
        frame = sys._getframe(1) if hasattr(sys, '_getframe') else inspect.currentframe()

        while frame is not None and os.path.normcase(frame.f_code.co_filename) == _PIE_LOGGER_FILE:
            frame = frame.f_back

        if frame is None:
            return "<unknown>:0"

        file_name = frame.f_code.co_filename
        line_number = frame.f_lineno

        relative_file_name = self._relative_path_cache.get(file_name)
        if relative_file_name is None:
            try:
                relative_file_name = os.path.relpath(file_name, self._project_root)
            except ValueError:
                # Different drive on Windows - relpath is not expressible, fall back to the absolute path.
                relative_file_name = file_name
            relative_file_name = f"./{relative_file_name.replace(os.sep, '/')}"
            self._relative_path_cache[file_name] = relative_file_name

        return f"{relative_file_name}:{line_number}"

    def __get_timestamp(self) -> str:
        """
        Generate a formatted timestamp string in the configured timezone.

        Returns:
            str: Formatted timestamp string with millisecond precision
        """
        return datetime.now(self._tz).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    def __get_color_from_level(self, level: int) -> Fore:
        """
        Map logging levels to their corresponding console colors.

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
        """
        Determine the final color to use based on global and per-message color settings.

        Args:
            color: Desired color from Colorama Fore
            colorful: Override for global color setting (None uses global setting)

        Returns:
            Final color to use, accounting for color enable/disable settings
        """
        is_colorful = self._colorful
        if colorful is not None:
            is_colorful = colorful
        return color if is_colorful else self._default_log_color

    def __make_serializable(self, obj: Any):
        """
        Recursively convert non-serializable objects in a nested structure
        (e.g., dict, list, tuple) into JSON-serializable equivalents.
        """
        if isinstance(obj, dict):
            return {
                key if isinstance(key, _JSON_SCALARS) else str(key): self.__make_serializable(value)
                for key, value in obj.items()
            }
        elif isinstance(obj, (list, tuple)):
            return [self.__make_serializable(item) for item in obj]
        elif isinstance(obj, set):
            return list(self.__make_serializable(item) for item in obj)
        elif isinstance(obj, _JSON_SCALARS):
            return obj

        return str(obj)

    def __to_json(self, obj: Any) -> str:
        """
        Serialize details or context for output. Never raises: a log call must not take the caller down.
        """
        try:
            return json.dumps(self.__make_serializable(obj), indent=self._details_indent)
        except Exception as error:
            # Circular or very deep structures (RecursionError) and objects whose __str__ raises
            return f"<not serializable: {type(error).__name__}: {error}>"

    def add_context(self, key: str, value: Any) -> None:
        """
        Add or update a key-value pair in the logger's context for the current thread or asyncio task.

        Args:
            key (str): The key to add or update
            value (Any): The value to associate with the key
        """
        self._context.set({**self._context.get(), key: value})

    def remove_context(self, key: str) -> None:
        """
        Remove a key from the logger's context for the current thread or asyncio task.

        Args:
            key (str): The key to remove
        """
        self._context.set({k: v for k, v in self._context.get().items() if k != key})

    def clear_context(self) -> None:
        """Clear all context for the current thread or asyncio task."""
        self._context.set({})

    def __console_log(
            self,
            level: int,
            message: str,
            timestamp: str,
            file_path_info: str,
            formatted_details: Optional[str],
            formatted_context: Optional[str],
            exec_details: Optional[str],
            colorful: Optional[bool]
    ) -> str:
        """
        Format a log message for console output with optional color and styling.

        Args:
            level (int): Logging level
            message (str): Main log message
            timestamp (str): Pre-formatted timestamp, shared with the file output
            file_path_info (str): Pre-resolved caller location, shared with the file output
            formatted_details (Optional[str]): Pre-serialized JSON details, or None
            formatted_context (Optional[str]): Pre-serialized JSON global context, or None
            exec_details (Optional[str]): Pre-formatted stack trace, or None
            colorful (Optional[bool]): Override for color output settings

        Returns:
            str: Formatted log message string with color codes and styling
        """
        timestamp_log_color = self.__get_final_color(self._timestamp_log_color, colorful)
        file_path_log_color = self.__get_final_color(self._file_path_log_color, colorful)
        details_log_color = self.__get_final_color(self._details_log_color, colorful)
        level_color = self.__get_final_color(self.__get_color_from_level(level), colorful)
        level_name = PieLogLevel.get_level_str(level)

        console_log_parts = [
            f"{timestamp_log_color}{timestamp:<{self._timestamp_padding}}",
            f"{level_color}{level_name:<{self._log_level_padding}}",
            f"{file_path_log_color}{file_path_info:<{self._file_path_padding}}",
            f": {level_color}{message}"
        ]
        console_log = " ".join(console_log_parts)

        if formatted_details is not None:
            console_log += f"\n{details_log_color}{formatted_details}"

        if formatted_context is not None:
            console_log += f"\n{details_log_color}Context: {formatted_context}"

        if exec_details is not None:
            console_log += f"\n{level_color}{exec_details}"

        return console_log + f"{Style.RESET_ALL}"

    def __file_log(
            self,
            level: int,
            message: str,
            timestamp: str,
            file_path_info: str,
            formatted_details: Optional[str],
            formatted_context: Optional[str],
            exec_details: Optional[str]
    ) -> str:
        """
        Format a log message for file output without color codes or styling.

        Args:
            level (int): Logging severity level
            message (str): Main log message text
            timestamp (str): Pre-formatted timestamp, shared with the console output
            file_path_info (str): Pre-resolved caller location, shared with the console output
            formatted_details (Optional[str]): Pre-serialized JSON details, or None
            formatted_context (Optional[str]): Pre-serialized JSON global context, or None
            exec_details (Optional[str]): Pre-formatted stack trace, or None

        Returns:
            Formatted log message string suitable for file output
        """
        level_name = PieLogLevel.get_level_str(level)

        file_log_parts = [
            f"{timestamp:<{self._timestamp_padding}}",
            f"{level_name:<{self._log_level_padding}}",
            f"{file_path_info:<{self._file_path_padding}}",
            f": {message}"
        ]
        file_log = " ".join(file_log_parts)

        if formatted_details is not None:
            file_log += f"\n{formatted_details}"

        if formatted_context is not None:
            file_log += f"\nContext: {formatted_context}"

        if exec_details is not None:
            file_log += f"\n{exec_details}"

        return file_log

    def __log(
            self,
            level: int,
            message: str,
            details: Optional[Any] = None,
            print_exception: bool = False,
            colorful: Optional[bool] = None
    ) -> None:
        """
        Process and output a log message to all configured destinations.

        The level is checked before any formatting work happens, so suppressed messages cost almost
        nothing. Everything shared by the console and file outputs - caller location, timestamp,
        serialized details, context and stack trace - is computed exactly once here, which also
        guarantees both destinations report the same timestamp for a given call.

        Args:
            level (int): Logging level
            message (str): Main log message
            details (Optional[Any]): Additional structured data to include as JSON
            print_exception (bool): Whether to include error trace
            colorful (Optional[bool]): Whether to apply colors to this specific message
        """
        if level < self._minimum_log_level:
            return

        timestamp = self.__get_timestamp()
        file_path_info = self.__extract_caller_location()

        formatted_details: Optional[str] = None
        if details is not None:
            formatted_details = self.__to_json(details)

        formatted_context: Optional[str] = None
        context = self._context.get() if self._global_context else None
        if context:
            formatted_context = self.__to_json(context)

        exec_details: Optional[str] = None
        if print_exception and sys.exc_info()[0] is not None:
            exec_details = ''.join(traceback.format_exc())

        console_log = self.__console_log(
            level, message, timestamp, file_path_info,
            formatted_details, formatted_context, exec_details, colorful
        )
        self.console_logger.log(level, console_log)

        if self._log_to_file:
            file_log = self.__file_log(
                level, message, timestamp, file_path_info,
                formatted_details, formatted_context, exec_details
            )
            self.file_logger.log(level, file_log)

    def log(
            self,
            level: int,
            message: str,
            details: Optional[Any] = None,
            print_exception: bool = False,
            colorful: Optional[bool] = None
    ) -> None:
        """
        Log a message at the specified level.

        Args:
            level (int): Logging level
            message (str): Main log message
            details (Optional[Any]): Additional structured data to include as JSON
            print_exception (bool): Whether to include error trace
            colorful (Optional[bool]): Whether to apply colors to this specific message
        """
        self.__log(level, message, details, print_exception, colorful)

    def debug(
            self,
            message: str,
            details: Optional[Any] = None,
            print_exception: bool = False,
            colorful: Optional[bool] = None
    ) -> None:
        """
        Log a debug level message.

        Args:
            message (str): Main log message
            details (Optional[Any]): Additional structured data to include as JSON
            print_exception (bool): Whether to include error trace
            colorful (Optional[bool]): Whether to apply colors to this specific message
        """
        self.__log(PieLogLevel.DEBUG, message, details, print_exception, colorful)

    def info(
            self,
            message: str,
            details: Optional[Any] = None,
            print_exception: bool = False,
            colorful: Optional[bool] = None
    ) -> None:
        """
        Log an info level message.

        Args:
            message (str): Main log message
            details (Optional[Any]): Additional structured data to include as JSON
            print_exception (bool): Whether to include error trace
            colorful (Optional[bool]): Whether to apply colors to this specific message
        """
        self.__log(PieLogLevel.INFO, message, details, print_exception, colorful)

    def warning(
            self,
            message: str,
            details: Optional[Any] = None,
            print_exception: bool = False,
            colorful: Optional[bool] = None
    ) -> None:
        """
        Log a warning level message.

        Args:
            message (str): Main log message
            details (Optional[Any]): Additional structured data to include as JSON
            print_exception (bool): Whether to include error trace
            colorful (Optional[bool]): Whether to apply colors to this specific message
        """
        self.__log(PieLogLevel.WARNING, message, details, print_exception, colorful)

    def error(
            self,
            message: str,
            details: Optional[Any] = None,
            print_exception: bool = False,
            colorful: Optional[bool] = None
    ) -> None:
        """
        Log an error level message.

        Args:
            message (str): Main log message
            details (Optional[Any]): Additional structured data to include as JSON
            print_exception (bool): Whether to include error trace
            colorful (Optional[bool]): Whether to apply colors to this specific message
        """
        self.__log(PieLogLevel.ERROR, message, details, print_exception, colorful)

    def critical(
            self,
            message: str,
            details: Optional[Any] = None,
            print_exception: bool = False,
            colorful: Optional[bool] = None
    ) -> None:
        """
        Log a critical level message.

        Args:
            message (str): Main log message
            details (Optional[Any]): Additional structured data to include as JSON
            print_exception (bool): Whether to include error trace
            colorful (Optional[bool]): Whether to apply colors to this specific message
        """
        self.__log(PieLogLevel.CRITICAL, message, details, print_exception, colorful)

    def exception(
            self,
            message: str,
            details: Optional[Any] = None,
            colorful: Optional[bool] = None
    ) -> None:
        """
        Log an error message with stack trace.

        Args:
            message (str): Main log message
            details (Optional[Any]): Additional structured data to include as JSON
            colorful (Optional[bool]): Whether to apply colors to this specific message
        """
        self.__log(PieLogLevel.ERROR, message, details, print_exception=True, colorful=colorful)

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
            def log_start(args: Any, kwargs: Any) -> None:
                start_details: Optional[Dict[str, str]] = None
                if print_args_at_start:
                    start_details = {
                        "function": func.__name__,
                        "args": str(args),
                        "kwargs": str(kwargs)
                    }
                self.__log(
                    level=start_message_log_level,
                    message=start_message or f"Start of {func.__name__}",
                    details=start_details,
                    colorful=self._colorful
                )

            def log_end(result: Any) -> None:
                end_details: Optional[Dict[str, str]] = None
                if print_result_at_end:
                    end_details = {
                        "function": func.__name__,
                        "result": str(result)
                    }
                self.__log(
                    level=end_message_log_level,
                    message=end_message or f"End of {func.__name__}",
                    details=end_details,
                    colorful=self._colorful
                )

            def log_failure() -> None:
                self.__log(
                    level=PieLogLevel.ERROR,
                    message=f"Exception in {func.__name__}",
                    print_exception=True,
                    colorful=self._colorful
                )

            if inspect.iscoroutinefunction(func):
                # A sync wrapper would log the end, and the coroutine object as the result, before the body ran
                @wraps(func)
                async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                    log_start(args, kwargs)
                    try:
                        result = await func(*args, **kwargs)
                    except Exception:
                        log_failure()
                        raise
                    log_end(result)
                    return result

                return async_wrapper  # type: ignore[return-value]

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> T:
                log_start(args, kwargs)
                try:
                    result: T = func(*args, **kwargs)
                except Exception:
                    log_failure()
                    raise
                log_end(result)
                return result

            return wrapper

        return decorator
