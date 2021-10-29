import sys
import logging
# import coloredlogs
# coloredlogs.install()

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s',
                              '%m-%d-%Y %H:%M:%S')

stdout_handler = logging.StreamHandler(sys.stdout)
# stdout_handler.setLevel(logging.DEBUG)
# stdout_handler.terminator = ""
# stdout_handler.setFormatter(formatter)

file_handler = logging.FileHandler('logs.log')
# file_handler.setLevel(logging.WARN)
file_handler.setFormatter(formatter)
# file_handler.terminator = ""

logger.addHandler(file_handler)
logger.addHandler(stdout_handler)

logger.setLevel(logging.DEBUG)