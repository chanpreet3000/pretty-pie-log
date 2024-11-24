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
- **Minimal Dependencies**: Only requires `colorama` and `pytz`

## Quick Start

```python
from pretty_pie_log import PieLogger

# Create a logger instance
logger = PieLogger(
    logger_name="my_app",
    timezone="America/New_York"  # Optional: defaults to UTC
)

# Basic logging
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
    logger_name="my_app",  # Required: Unique identifier
    timezone="America/New_York",  # Optional: Timezone for timestamps
    timestamp_padding=30,  # Optional: Width of timestamp field
    log_level_padding=10,  # Optional: Width of log level field
    file_path_padding=30,  # Optional: Width of file path field
    debug_log_color=Fore.CYAN,  # Optional: Color for debug messages
    info_log_color=Fore.GREEN,  # Optional: Color for info messages
    warning_log_color=Fore.YELLOW,  # Optional: Color for warning messages
    error_log_color=Fore.RED,  # Optional: Color for error messages
    critical_log_color=Fore.MAGENTA,  # Optional: Color for critical messages
    timestamp_log_color=Fore.LIGHTBLUE_EX,  # Optional: Color for timestamp
    file_path_log_color=Fore.WHITE,  # Optional: Color for file path
    details_log_color=Fore.LIGHTWHITE_EX,  # Optional: Color for JSON details
    colorful=True,  # Optional: Enable/disable colors
    minimum_log_level=PieLogLevel.INFO,  # Optional: Minimum logging level
    default_log_color=Fore.WHITE,  # Optional: Default color when colorful=False
    details_indent=2  # Optional: JSON indentation spaces
)
```

![image](https://github.com/user-attachments/assets/24fe9c46-1108-4381-a1d0-60c870b1832a)


### Log Levels

The package provides five standard log levels through the `PieLogLevel` class:

```python
PieLogLevel.DEBUG  # Level 0
PieLogLevel.INFO  # Level 1
PieLogLevel.WARNING  # Level 2
PieLogLevel.ERROR  # Level 3
PieLogLevel.CRITICAL  # Level 4
```

![image](https://github.com/user-attachments/assets/a2bac36f-33a6-4f4e-83f1-9fed6976bdd2)


### Logging Methods

All logging methods support the following parameters:

```python
logger.info(
    message="Main log message",
    details={"key": "value"},  # Optional: Additional structured data
    exec_info=False,  # Optional: Include stack trace
    colorful=True  # Optional: Apply colors to this message
)
```

### Function Execution Tracking

The `log_execution` decorator provides detailed monitoring of function execution:

```python
from pretty_pie_log import PieLogger, PieLogLevel

logger = PieLogger("my_logger")


@logger.log_execution(
    start_message="Custom start message",  # Optional: Message at function start
    end_message="Custom end message",  # Optional: Message at function end
    print_args_at_start=True,  # Optional: Log function arguments
    print_result_at_end=True,  # Optional: Log function result
    start_message_log_level=PieLogLevel.INFO,  # Optional: Log level for start
    end_message_log_level=PieLogLevel.INFO  # Optional: Log level for end
)
def my_function(arg1, arg2):
    return "result"


my_function("arg1", "arg2")
```

![image](https://github.com/user-attachments/assets/40fc19e2-89b5-4fc7-9437-7acc9f98c6a2)


## Output Format

The logger produces formatted output with the following components:

```
[Timestamp] [Log Level] [File:Line] : Message
{
  "detailed": "json data"  # If details provided
}
Stack trace               # If exec_info=True
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

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[This project is licensed under the MIT License - see the LICENSE file for details.](LICENSE)