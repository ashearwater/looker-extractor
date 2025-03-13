import looker_sdk
import time
import os
import pandas as pd
import csv
import hashlib
import warnings
import json
from datetime import datetime, timedelta

from looker_sdk.sdk.api40 import methods as methods40
from looker_sdk import models40 as models
from .worker import Worker
from io import StringIO
from .enums import (ROW_LIMIT,
                         QUERY_TIMEZONE,
                         QUERY_TIMEOUT,
                         DATETIME_FORMAT,
                         CURSOR_INITIAL_VALUE,
                         ID_CURSOR_FIELD,
                         START_ID
                         )

class LookerWorker(Worker):


    # @@@ STEP 5 @@@
    def __init__(
            self,
            table_name:str
            ) -> None:
        super().__init__(table_name = table_name)

        self.sdk = looker_sdk.init40()
        self.cursor_initial_value: str | int | None = CURSOR_INITIAL_VALUE
        self.project_mapping = None
        self.row_limit = ROW_LIMIT
        self.query_timezone= QUERY_TIMEZONE
        self.datetime_format= DATETIME_FORMAT
        self.row_count = self._fetch_rowcount()

        # @@@ STEP 7 @@@
        if self.row_count:
            self.cursor_field: str = self.table_data["cursor_field"] or (self.table_data["primary_key"] if not isinstance(self.table_data["primary_key"], list) else self.table_data["batch_cursor_field"])  # Cursor field in Looker query
            self.is_id_cursor_field = False

            if self.cursor_field and (self.cursor_field == ID_CURSOR_FIELD or self.cursor_field.split(".")[1] == ID_CURSOR_FIELD):
                print(f"Cursor field is {self.cursor_field}.")
                # cursor field is id; assigns int type
                self.is_id_cursor_field = True

            self.cursor_value = None
            self.is_last_batch = None

            # if the value days_ago_to_start_pull are filled, priorize it
            if self.days_ago_to_start_pull != None:
                self.cursor_initial_value = (datetime.today() - timedelta(days= abs(self.days_ago_to_start_pull))).strftime('%Y-%m-%d 00:00:00')
            # if the value days_ago_to_start_pull are not filled, use cursor_manual_initial_value
            elif self.cursor_manual_initial_value != None:
                self.cursor_initial_value = self.cursor_manual_initial_value
            # if none are filled, fill with initial values according to the type of the cursor
            else:
                self.cursor_initial_value = START_ID if self.is_id_cursor_field else CURSOR_INITIAL_VALUE

        # Set the initial csv number
        self.file_num = -1

    # @@@ STEP 6 @@@
    def _fetch_rowcount(self) -> int | None:
        """
        executes a rowcount query on the target view's count_measure.
        this self.row_count is the core logic of doing a full or batch extraction.
        """
        try:
            # limitation : not all systerm activity has a count_measure.
            # thus we only do rowcount on views with such attr.
            # all worker instances with row_count are set for batch extraction.
            count_measure = self.table_data["count_measure"]
            view = self.table_data["view"]
            model = self.table_data["model"]

            body = models.WriteQuery(
                            model = model,
                            view = view,
                            fields = [count_measure],
                            )

            print(f'fetching rowcount for {model}.{view} : ')
            query = self.sdk.create_query(
                body = body
            )
            query_id = query.id
            if not query_id:
                raise ValueError(f"Failed to create query for view [{view}]")
            print(f"""Successfully created query, query_id is [{query_id}]
                query url: {query.share_url}"""
                )
            row_count = self.run_query(query_id)
            row_count = int(row_count.split('\n')[1])
            return row_count
        except KeyError:
            # catches the error & assigns None row_count to the worker.
            # all worker instances without row_count are set for full extraction.

            return None

    # @@@ STEP 9 @@@
    def create_query(
            self,
            table_data,
            cursor_initial_value: str | int | None,
            ) -> str:
        """
        Create Looker Query
        Ref: https://developers.looker.com/api/explorer/4.0/methods/Query/create_query?sdk=py
        """
        model = table_data["model"]
        view = table_data["view"]
        fields = table_data["fields"]

        if self.row_count:
            cursor_field = self.cursor_field

            sorts = []
            print(f"Extracting using cursor for view [{view}] model [{model}].")
            print(f"Cursor initial value [{cursor_initial_value}]")
            sorts = [cursor_field] if cursor_field else []

            if not self.is_id_cursor_field:
                filters = {cursor_field: f"after {cursor_initial_value}"} if cursor_field else {}
            else:
                filters = {cursor_field: f">= {cursor_initial_value}"} if cursor_field else {}

            filters.update(self.table_data['filters'] if self.table_data['filters'] else {})

            print(f"Creating query on view [{view}], filters {filters}, cursor_field {cursor_field}")
                #  f" timezone [{self.query_timezone}]"
                #  f" fields [{fields}]"
                #  )

            body = models.WriteQuery(
                    model = model,
                    view = view,
                    fields = fields,
                    filters = filters,
                    sorts = sorts,
                    limit = str(self.row_limit),
                    query_timezone = self.query_timezone,
                    )
        else:
            print(f"Extracting without a cursor for view [{view}].")
            body = models.WriteQuery(
                    model = model,
                    view = view,
                    fields = fields,
                    limit = str(self.row_limit),
                    query_timezone = self.query_timezone,
                    )
            
        query = self.sdk.create_query(
            body = body
        )
        query_id = query.id

        if not query_id:
            raise ValueError(f"Failed to create query for view [{view}]")
        print(f"Successfully created query, query_id is [{query_id}]"
            f"query url: {query.share_url}"
            )
        
        return query_id



    # @@@ STEP 10 @@@
    def run_query(self,query_id: str):
        """
        Run query and save data
        """
        create_query_task = models.WriteCreateQueryTask(
            query_id=query_id, result_format=models.ResultFormat.csv
        )
        print("Creating async query")
        task = self.sdk.create_query_task(body=create_query_task)
        if not task.id:
            raise ValueError(f"Failed to create query task for query id [{query_id}]")
        query_task_id = task.id

        print(f"Created async query task id [{query_task_id}] for query id [{query_id}]"
              )

        elapsed = 0.0
        delay = 5.0  # waiting seconds
        while True:
            poll = self.sdk.query_task(query_task_id = query_task_id)

            if poll.status == "failure" or poll.status == "error":
                raise Exception(f"Query failed. Response: {poll}")
            elif poll.status == "complete":
                break

            time.sleep(delay)
            elapsed += delay
            
            if elapsed >= QUERY_TIMEOUT:
                raise Exception(
                    f"Waited for [{elapsed}] seconds, which exceeded timeout")

        print(f"Query task completed in {poll.runtime:.2f} seconds")
        print(f"Waited {elapsed} seconds")

        task_result = self.sdk.query_task_results(task.id)

        return task_result

    # @@@ STEP 8 @@@
    def fetch(self, **kwargs):
            
        query_id = self.create_query(self.table_data,
                self.cursor_initial_value,
                )

        query_results = self.run_query(query_id)
        self.query_results = query_results
        self.df = pd.read_csv(StringIO(query_results))

        self.map_fields_name_with_config()

        # @@@ STEP 11 @@@
        if self.row_count:
            # Grab the cursor val for batch extraction
            self.last_cursor_value = self.cursor_value if hasattr(self, 'cursor_value') else None
            # Grab the last value from df
            self.cursor_value = self.df[self.cursor_field.split('.')[-1]].iloc[-1]

        # If the view don't has row_count, in result don't has a count_measure, and don't has a cursor
        elif not self.row_count and len(self.df) == 50000:
            warnings.warn(f"\n\n\tWARNING : this view [{self.table_name}] has more than 50000 rows "
                  "but there's no fields we can reliably use "
                  "as a cursor for batch extraction.\n"
                  "\tThis view will be truncated to 50000 rows.\n\n",
                  category=UserWarning
                  )

    def map_fields_name_with_config(self):
        """
        uses the field name specified in the schema file instead
        of fields returned from the api.
        plus, this maps 1-1 with explore's view.
        """
        schema_info = self.schema_info
        columns = [schema_info[i]['name'] for i,_ in enumerate(schema_info)]
        self.df.columns = columns


    # @@@ STEP 12 @@@
    def dump(self, **kwargs) -> None:
        table = self.table_name

        if self.row_count:
            self.cursor_initial_value = self.cursor_value
            self.file_num += 1
            if self.file_num == 0:
                self.csv_basename = self.csv_name.split('.')[0]
            self.csv_name = self.csv_basename + f"_{self.file_num}.csv"
            
            # # last batch : kills the cursor
            # if self.is_last_batch:
            #     self.row_count = None
            #     print("End of extraction2")

        # create the dir
        if not os.path.exists(self.csv_target_path):
            os.makedirs(self.csv_target_path,exist_ok=True)

        self.df.to_csv(self.csv_name,
                index=False,
                quotechar='"',
                quoting=csv.QUOTE_MINIMAL,
                )
        
        print(f"sucessfully extracted explore table '{table}'. \n"
            f"total rows extracted: {len(self.df)}. \n"
            f"output file: '{self.csv_name}' \n"
            )

        self.total_record += len(self.df)

        # @@@ STEP 13 @@@
        if len(self.df) < self.row_limit or self.is_last_batch == True:
            self.is_last_batch = True
            self.row_count = None
            print(f"End of extraction")
            
        elif self.row_count:
            self.fetch()
            if self.last_cursor_value != self.cursor_value:
                if len(self.df) < self.row_limit:
                    self.is_last_batch = True
                self.dump()
