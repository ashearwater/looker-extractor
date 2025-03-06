from dotenv import load_dotenv
import os
load_dotenv()

CSV_DUMP_DIR = os.environ.get('CSV_DUMP_DIR','out')
START_TIME = os.environ.get('START_TIME',"2015-01-01 00:00:00")
LOOKER_REPO_PATH = os.environ.get('LOOKER_REPO_PATH', 'repo')
LOOKER_PROJECT_MAPPING_PATH = os.environ.get('LOOKER_PROJECT_MAPPING_PATH', "looker_project.json")

ROW_LIMIT = 50000
QUERY_TIMEZONE = 'UTC'
QUERY_TIMEOUT = 600
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
IGNORE_FILES = ['']
JOINS_KEYS = {}
DEFAULT_TIMEFRAMES = ['']
DEFAULT_INTERVALS = ['']
FOLDERS_TO_SKIP = ['']




ID_CURSOR_FIELD = 'id'
NULL_CURSOR_FIELD = 'null_cursor_field'
START_ID = -1
CURSOR_FIELD_NOT_PICKED = "please_choose"
NULL_CURSOR_VALUE = "null_cursor_value"

