# Pretty Pie Log

A feature-rich, thread-safe Python logging utility that provides colorized console output with customizable formatting,
JSON details support, and function execution tracking.

<div align="center">

[![PyPI version](https://badge.fury.io/py/pretty-pie-log.svg)](https://badge.fury.io/py/pretty-pie-log)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

## Installation

```bash
pip install pretty-pie-log
```

## Features

- **Colorized Output**: Customizable colors for different log levels and components
- **Thread-Safe**: Built-in thread safety for reliable logging in multi-threaded applications
- **Timezone Support**: Configurable timezone for timestamp display
- **Structured Logging**: JSON formatting for detailed logging information
- **Smart Path Detection**: Automatic relative file path detection from project root
- **Stack Trace Integration**: Optional exception stack trace inclusion
- **Function Execution Tracking**: Decorator for monitoring function entry/exit with customizable details
- **File Logging**: Configurable file logging with rotating file handler
- **Minimal Dependencies**: Only requires `colorama`, `pytz`

## Quick Start

```python
from pretty_pie_log import PieLogger, PieLogLevel

# Create a logger instance
logger = PieLogger(
    logger_name="my_app",
    timezone="America/New_York",  # Optional: Set specific timezone
    minimum_log_level=PieLogLevel.INFO  # Optional: Set minimum log level
)

# Basic logging methods
logger.info("Application started")
logger.debug("Debug message", details={"user_id": 123})
logger.warning("Warning message")
try:
    raise ValueError("Something went wrong")
except:
    logger.error("Error occurred", exec_info=True)  # Includes error trace
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

![image](https://github.com/user-attachments/assets/57f7474d-21d5-4beb-9f67-6054d330e5a6)


## Detailed Configuration

### Logger Initialization

```python
from pretty_pie_log import PieLogger, PieLogLevel
from colorama import Fore

logger = PieLogger(
    # Required Parameters
    logger_name="my_app",  # Unique identifier for the logger

    # Optional Timezone and Formatting Parameters
    timezone="America/New_York",  # Defaults to UTC if not specified
    timestamp_padding=30,  # Width of timestamp field
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

    # Logging Control
    colorful=True,  # Enable/disable color output
    minimum_log_level=PieLogLevel.INFO,  # Minimum logging level
    default_log_color=Fore.WHITE,  # Color when colorful is False
    details_indent=2,  # JSON indentation spaces

    # File Logging Options
    log_to_file=True,  # Enable/disable file logging
    log_directory='logs',  # Directory for log files
    log_file_size_limit=32 * 1024 * 1024,  # 32 MB max log file size
    max_backup_files=10  # Number of backup log files to keep
)
```

![image](https://github.com/user-attachments/assets/a2bac36f-33a6-4f4e-83f1-9fed6976bdd2)


### Logging Methods

All logging methods support the following parameters:

```python
logger.info(
    message="Main log message",
    details={"key": "value"},  # Optional: Additional structured data
    exec_info=False,  # Optional: Include stack trace
    colorful=True  # Optional: Override global color setting
)
```

## Log Levels

The package provides five standard log levels:

- `PieLogLevel.DEBUG` (10)
- `PieLogLevel.INFO` (20)
- `PieLogLevel.WARNING` (30)
- `PieLogLevel.ERROR` (40)
- `PieLogLevel.CRITICAL` (50)

## Function Execution Tracking

The `log_execution` decorator provides detailed monitoring of function execution:

```python
from pretty_pie_log import PieLogger, PieLogLevel

logger = PieLogger("my_logger")


@logger.log_execution(
    start_message="Custom start message",  # Optional
    end_message="Custom end message",  # Optional
    print_args_at_start=True,  # Optional: Log function arguments
    print_result_at_end=True,  # Optional: Log function result
    start_message_log_level=PieLogLevel.INFO,  # Optional: Start log level
    end_message_log_level=PieLogLevel.INFO  # Optional: End log level
)
def my_function(arg1, arg2):
    return "result"


my_function("arg1", "arg2")
```

![image](https://github.com/user-attachments/assets/40fc19e2-89b5-4fc7-9437-7acc9f98c6a2)


## Output Format

```
[Timestamp]                [LogLevel]  [File:Line]                 : Message
{Optional JSON details}
{Optional stack trace}
```

Example output:

![image](https://github.com/user-attachments/assets/7bf4908c-469b-44a1-82bd-b51f54e85071)


## Project Root Detection

The logger automatically detects the project root by looking for a `main.py` file. If not found, it uses the current
directory as the root. This affects how relative file paths are displayed in log messages.

## Thread Safety

All logging operations are thread-safe, protected by an internal lock mechanism. This ensures that log messages from
different threads don't get interleaved.

## Exception Handling

When `exec_info=True`, the logger will include the full stack trace of the current exception:

```python
try:
    raise ValueError("Something went wrong")
except Exception:
    logger.error("Error processing data", exec_info=True)
```

![image](https://github.com/user-attachments/assets/644375fd-f7ba-4371-a809-cebff5f9c907)


## Dependencies

- Python 3.7+
- colorama
- pytz

## Contributing

Contributions are welcome! Please submit a Pull Request.

## License

[MIT License](LICENSE)