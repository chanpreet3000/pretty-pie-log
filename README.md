# Pretty Pie Log

A feature-rich, thread-safe Python logging utility that provides colorized console output with customizable formatting,
JSON details support, and function execution tracking.

[![PyPI version](https://badge.fury.io/py/pretty-pie-log.svg)](https://badge.fury.io/py/pretty-pie-log)
[![Downloads](https://static.pepy.tech/badge/pretty-pie-log/month)](https://pepy.tech/project/pretty-pie-log)
[![Supported Versions](https://img.shields.io/pypi/pyversions/pretty-pie-log.svg)](https://pypi.org/project/pretty-pie-log)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install pretty-pie-log
```

---

## Features

- **Colorized Output**: Customizable colors for different log levels and components, including `timestamp`, `file path`,
  and `details`.
- **Thread-Safe**: Built-in thread safety for reliable logging in multi-threaded applications.
- **Timezone Support**: Configurable timezone for timestamp display (default: UTC).
- **Automatic Path Detection**: Detects relative file paths based on the project root.
- **Error Trace Integration**: Optionally include full error trace details for exceptions.
- **Function Execution Tracking**: Decorator for logging function entry, exit, arguments, and results with configurable
  log levels.
- **File Logging**: Configurable rotating file logging with size limits and backup files.
- **Customizable Formatting**: Adjust padding for timestamps, log levels, file paths, and other components.
- **Enhanced Log Details Serialization**: Handles non-serializable objects in logs by converting them into readable
  formats.
- **Default Colors and Settings**: New fields for default log colors and detailed customization.

---

## Quick Start

```python
from pretty_pie_log import PieLogger, PieLogLevel

# Create a logger instance
logger = PieLogger(
    logger_name="my_app",
    timezone="America/New_York",  # Optional: Set specific timezone
    minimum_log_level=PieLogLevel.INFO,  # Optional: Set minimum log level
    log_to_file=True,  # Optional: Enable file logging
)

# Basic logging methods
logger.info("Application started")
logger.debug("Debug message", details={"user_id": 123})
logger.warning("Warning message")
try:
    raise ValueError("Something went wrong")
except ValueError:
    logger.error("Error occurred", print_exception=True)  # Includes error trace
logger.critical("Critical error", details={"error_code": 500})


# Function execution tracking
@logger.log_execution(
    start_message="Starting data processing",
    end_message="Processing complete",
    print_args_at_start=True,
    print_result_at_end=True
)
def process_data(data):
    return {"processed": len(data)}


process_data([1, 2, 3, 4, 5])
```

### Output

![image](https://github.com/user-attachments/assets/06cfb79d-8900-4116-a00a-47502f54a386)

---

## Detailed Configuration

### Logger Initialization

The logger is highly customizable with numerous options:

```python
from pretty_pie_log import PieLogger, PieLogLevel
from colorama import Fore

logger = PieLogger(
    logger_name="my_app",  # Unique identifier for the logger

    # Optional Timezone and Formatting Parameters
    timezone="America/New_York",  # Defaults to UTC if not specified
    timestamp_padding=25,  # Width of timestamp field
    log_level_padding=10,  # Width of log level field
    file_path_padding=30,  # Width of file path field

    # Optional Color Configuration
    debug_log_color=Fore.CYAN,
    info_log_color=Fore.GREEN,
    warning_log_color=Fore.YELLOW,
    error_log_color=Fore.RED,
    critical_log_color=Fore.MAGENTA,
    timestamp_log_color=Fore.WHITE,
    file_path_log_color=Fore.WHITE,
    details_log_color=Fore.LIGHTWHITE_EX,

    # Enhanced Logging Options
    colorful=True,  # Enable/disable colored output
    default_log_color=Fore.WHITE,  # Fallback color when colorful is False
    details_indent=2,  # JSON indentation spaces
    minimum_log_level=PieLogLevel.INFO,  # Minimum logging level

    # Rotating File Logging
    log_to_file=True,  # Enable/disable file logging
    log_directory="logs",  # Directory for log files
    log_file_size_limit=32 * 1024 * 1024,  # Max log file size (32 MB)
    max_backup_files=10  # Number of backup log files to keep
)
```

### Output using the above configuration

![image](https://github.com/user-attachments/assets/24fe9c46-1108-4381-a1d0-60c870b1832a)
---

## Logging Methods

All logging methods support the following parameters:

```python
logger.info(
    message="Main log message",  # Required: Main text of the log
    details={"key": "value"},  # Optional: Additional data to include (now supports any data type)
    print_exception=True,  # Optional: Include stack trace if an exception occurred
    colorful=False  # Optional: Override global color settings for this log
)
```

### Enhanced `details` Parameter

The `details` parameter, which previously supported only `dict`, now supports **any data type**, making it more
versatile for structured and unstructured data logging.

- **Supported Data Types**:
    - `dict`: Ideal for key-value pairs or structured data (e.g., `{"user_id": 123, "status": "active"}`)
    - `list`/`tuple`: For sequences of data (e.g., `[1, 2, 3]`)
    - `set`: For unique collections (e.g., `{"item1", "item2"}`)
    - `str`, `int`, `float`, `bool`: Simple data types
    - `None`: To explicitly log the absence of details
    - **Custom Objects**: Non-serializable objects will automatically be converted into readable strings.

### Example Usage

```python
# Logging structured data
logger.info(
    message="User login attempt",
    details={"user_id": 123, "status": "success"}
)

# Logging a list of items
logger.debug(
    message="Processing items",
    details=[1, 2, 3, 4, 5]
)


# Logging a custom object
class User:
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name

    def __str__(self):
        return f"User(user_id={self.user_id}, name={self.name})"


user = User(123, "John Doe")

logger.warning(
    message="Custom object logged",
    details=user
)

# Logging without additional details
logger.error(
    message="Critical failure occurred",
    details=None
)
```

### Output:

![image](https://github.com/user-attachments/assets/0fe71acd-e831-434e-83a6-8faf59a5fba0)

### Automatic Serialization

If the `details` contain non-serializable objects (e.g., custom classes), the logger will automatically convert them
into strings, ensuring the logs remain readable without raising serialization errors.

### For example:

```python
class ComplexObject:
    pass


logger.debug(
    message="Logging complex object",
    details=ComplexObject()
)
```

### Console Output

```
2024-11-30 10:52:00.125   DEBUG      ./../example.py:17             : Logging complex object
"<__main__.ComplexObject object at 0x0000020FD4484A90>"
```

This enhancement ensures compatibility with diverse use cases while maintaining structured logging capabilities.

---

## Log Levels

The package provides five standard log levels:

- `PieLogLevel.DEBUG` (10)
- `PieLogLevel.INFO` (20)
- `PieLogLevel.WARNING` (30)
- `PieLogLevel.ERROR` (40)
- `PieLogLevel.CRITICAL` (50)

---

## Function Execution Tracking

The `log_execution` decorator provides detailed monitoring of function execution:

```python
@logger.log_execution(
    start_message="Starting task...",  # Optional: Custom start message
    end_message="Task complete.",  # Optional: Custom end message
    print_args_at_start=True,  # Log function arguments
    print_result_at_end=True,  # Log function return values
    start_message_log_level=PieLogLevel.DEBUG,  # Customizable log levels
    end_message_log_level=PieLogLevel.INFO
)
def task(arg1, arg2):
    return "result"
```

### Console Output

![image](https://github.com/user-attachments/assets/15c5ccac-6808-4543-ad1c-7f6895593244)

---

## Dependencies

- Python 3.7+
- colorama
- pytz

---

## Contributing

Contributions are welcome! Submit your ideas or pull requests.

---

## License

[MIT License](LICENSE)
