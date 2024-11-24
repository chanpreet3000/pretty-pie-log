class PieLogLevel:
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4

    @staticmethod
    def get_level_str(level: int):
        if level == PieLogLevel.DEBUG:
            return "DEBUG"
        elif level == PieLogLevel.INFO:
            return "INFO"
        elif level == PieLogLevel.WARNING:
            return "WARNING"
        elif level == PieLogLevel.ERROR:
            return "ERROR"
        elif level == PieLogLevel.CRITICAL:
            return "CRITICAL"
        else:
            return "UNKNOWN"
