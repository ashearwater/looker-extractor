
from abc import ABC, abstractmethod
import pandas as pd
import yaml
import os
from .enums import CSV_DUMP_DIR
import pandas as pd

class Worker(ABC):
    # @@@ STEP 3 @@@
    @abstractmethod
    def __init__(self,
                 table_name: str,
                 schema_file: str = 'schema.yaml',
                 cursor_file: str = 'cursor.yaml',
                 *args, **kwargs) -> None:

        self.table_name = table_name
        self.total_record = 0

        self._load_cursor(cursor_file)
        self.table_cursor_data = self.cursor_data[table_name]
        self.cursor_initial_value = self.table_cursor_data['cursor_initial_value']

        self._load_schema(schema_file)
        self.table_data = self.schema_data[table_name]
        self.schema_info = self.table_data['schema']
        self.csv_target_path = os.path.join(CSV_DUMP_DIR,self.table_name)
        self.csv_name = os.path.join(self.csv_target_path,f"{self.table_name}.csv")

    # @@@ STEP 4 @@@
    def _load_schema(self,schema_file):
        with open(schema_file) as f:
            schema = yaml.safe_load(f)  # Load the schema from the file

        # Check and assign based on the condition
        if self.table_name in schema:
            self.schema_data = schema
        else:
            raise KeyError(f"Table {self.table_name} is not found in {schema_file} file.")
        
    def _load_cursor(self,cursor_file):
        with open(cursor_file) as f:
            cursor = yaml.safe_load(f)  # Load the schema from the file

        # Check and assign based on the condition
        if self.table_name in cursor:
            self.cursor_data = cursor
        else:
            raise KeyError(f"Table {self.table_name} is not found in {cursor_file} file.")

    @abstractmethod
    def fetch(self, **kwargs):
        """Fetch data (e.g., Looker API call)."""
        pass

    @abstractmethod
    def dump(self, **kwargs):
        """Save data locally (e.g., CSV file)."""
        pass
