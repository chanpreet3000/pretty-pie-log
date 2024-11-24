class PieLogLevel:
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

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
