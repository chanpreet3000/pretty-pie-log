import time
from typing import List, Dict, Any
import random

# Import the PieLogger and PieLogLevel
from pretty_pie_log import PieLogger, PieLogLevel

# Create a logger instance with custom configuration
logger = PieLogger(
    logger_name="TestLogger",
    minimum_log_level=PieLogLevel.DEBUG,
    colorful=True
)


# Example class with complex data for testing details logging
class TestDataClass:
    def __init__(self, name: str, value: int):
        self.name = name
        self.value = value

    def __repr__(self):
        return f"TestDataClass(name={self.name}, value={self.value})"


# Function decorated with log_execution to demonstrate function logging
@logger.log_execution(
    start_message="Starting complex data processing",
    end_message="Data processing completed",
    print_args_at_start=True,
    print_result_at_end=True
)
def process_complex_data(data: List[int]) -> Dict[str, Any]:
    """Simulate some data processing with a complex return"""
    time.sleep(1)  # Simulate processing time
    return {
        "original_length": len(data),
        "sum": sum(data),
        "max": max(data),
        "min": min(data),
        "processed_object": TestDataClass("result", len(data))
    }


def main():
    # Demonstrate different log levels
    logger.debug("This is a debug message", details={"key": "debug_value"})
    logger.info("This is an info message", details={"user_id": 12345})
    logger.warning("This is a warning message", details={"warning_code": "W001"})

    # Demonstrate error logging with exception trace
    try:
        x = 1 / 0  # Intentional division by zero
    except ZeroDivisionError as e:
        logger.error("An error occurred during division",
                     details={"operation": "1/0", "error_type": type(e).__name__},
                     print_exception=True)

    # Demonstrate critical logging
    logger.critical("This is a critical message",
                    details={"critical_event": "System failure simulation"})

    # Test log with complex nested details
    complex_details = {
        "nested_dict": {
            "list": [1, 2, 3],
            "dict_in_dict": {"a": 1, "b": 2},
            "set": {4, 5, 6}
        },
        "object": TestDataClass("test", 42)
    }
    logger.info("Logging complex nested details", details=complex_details)

    # Demonstrate log_execution decorator
    sample_data = [random.randint(1, 100) for _ in range(10)]
    result = process_complex_data(sample_data)

    # Test different color settings
    logger.debug("Colored debug message", colorful=True)
    logger.info("Black and white info message", colorful=False)

    # Log with colorful override
    logger.warning("Colorful warning even if global color is off", colorful=True)


if __name__ == "__main__":
    main()
