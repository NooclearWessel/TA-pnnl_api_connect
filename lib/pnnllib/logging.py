import sys, os, time
import logging, logging.handlers
import splunk

###################################################################################################################
#
#                                               Splunk Logging Functions
#
###################################################################################################################

__all__ = [
           "setup_logging",
           "log_info", 
           "log_warn", 
           "log_error", 
           "log_error_quit",
           "log_debug"
           ]

def setup_logging(logfile):
    logger = logging.getLogger('splunk.foo')    
    SPLUNK_HOME = os.environ['SPLUNK_HOME']
    # This defintion uses the default Splunk [python] logging stanza in SPLUNK_HOME/etc/log.cfg or SPLUNK_HOME/etc/log-local.cfg
    LOGGING_DEFAULT_CONFIG_FILE = os.path.join(SPLUNK_HOME, 'etc', 'log.cfg')
    LOGGING_LOCAL_CONFIG_FILE = os.path.join(SPLUNK_HOME, 'etc', 'log-local.cfg')
    LOGGING_STANZA_NAME = 'python'
    # Remove any logging extentions that were passed in the log name, then set to .log
    LOGGING_FILE_NAME = logfile.rsplit('.',1)[0]+".log"
    # Path where Splunk logs will be written and automatically indexed in _internal
    BASE_LOG_PATH = os.path.join('var', 'log', 'splunk')
    # Log output formatting
    LOGGING_FORMAT = "%(asctime)s %(levelname)-s\t%(module)s:%(lineno)d - %(message)s"

    #Build logging handler with rotation policy
    splunk_log_handler = logging.handlers.RotatingFileHandler(os.path.join(SPLUNK_HOME, BASE_LOG_PATH, LOGGING_FILE_NAME), mode='a') 
    splunk_log_handler.setFormatter(logging.Formatter(LOGGING_FORMAT))
    logger.addHandler(splunk_log_handler)
    splunk.setupSplunkLogger(logger, LOGGING_DEFAULT_CONFIG_FILE, LOGGING_LOCAL_CONFIG_FILE, LOGGING_STANZA_NAME)
    return logger

def log_info(logging, log_props, status, message):
	# Sleep each message for better log squence writing. It is not uncommon to see duplicates at the thousandths of a milliscond.
	time.sleep(.001)
	logging.info("{0} job_status=\"{1}\" message=\"{2}\"".format(log_props, status, message))

def log_warn(logging, log_props, message):
	# Sleep each message for better log squence writing. It is not uncommon to see duplicates at the thousandths of a milliscond.
	time.sleep(.001)
	logging.warn("{0} job_status=\"Warning\" message=\"{1}\"".format(log_props, message))

def log_error(logging, log_props, message):
	# Sleep each message for better log squence writing. It is not uncommon to see duplicates at the thousandths of a milliscond.
	time.sleep(.001)
	logging.error("{0} job_status=\"Error\" message=\"{1}\"".format(log_props, message))

def log_error_quit(logging, log_props, message):
	# Sleep each message for better log squence writing. It is not uncommon to see duplicates at the thousandths of a milliscond.
	time.sleep(.001)
	logging.error("{0} job_status=\"Error\" message=\"{1}\"".format(log_props, message))
	quit()
	
def log_debug(logging, log_props, message):
	# Sleep each message for better log squence writing. It is not uncommon to see duplicates at the thousandths of a milliscond.
	time.sleep(.001)	
	logging.debug("{0} job_status=\"Debug\" message=\"{1}\"".format(log_props, message))

	