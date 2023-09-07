import logging
import os
import sys

from opencensus.ext.azure.log_exporter import AzureLogHandler

# set logging level and target
func_log_level = logging.INFO + 1
logging.addLevelName(func_log_level, "FUNC")
insight_key = os.environ["APPINSIGHTS_INSTRUMENTATIONKEY"]
application_insights_connection_string = f"InstrumentationKey={insight_key}"
# log with new logging name
def log_func_message(self, message, *args, **kwargs):
    if self.isEnabledFor(func_log_level):
        self._log(func_log_level, message, args, **kwargs)


# customize what level the log comes into application insights at
class ApplicationInsightsFilter(logging.Filter):
    def filter(self, record):
        if record.levelname == "FUNC":
            record.levelno = logging.INFO + 1
        return True


# configure the root logger
logger = logging.getLogger("func")
logger.setLevel(func_log_level)
debug_logger = logging.getLogger("func.debug")
debug_logger.setLevel(logging.DEBUG)
# configure Azure Handler for FUNC, WARNING, ERROR, CRITICAL LEVELS
azure_handler = AzureLogHandler(
    connection_string=application_insights_connection_string
)
azure_handler.setLevel(func_log_level)
azure_handler.addFilter(ApplicationInsightsFilter())
# configure the debug handler
debug_handler = logging.StreamHandler(sys.stderr)
debug_handler.setLevel(logging.DEBUG)
debug_handler.addFilter(lambda record: record.levelno == logging.DEBUG)
# add handlers
# logger.addHandler(console_handler)
logging.Logger.func = log_func_message
logger.addHandler(azure_handler)
debug_logger.addHandler(debug_handler)
