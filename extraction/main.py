import argparse
import os
import shutil

from utils.looker_worker import  LookerWorker
from utils.enums import  CSV_DUMP_DIR

hardcoded_list = [
                  'user',
                  'user_facts',
                  'user_facts_role',
                  'role',
                  'group_user',
                  'group',
                  'dashboard',
                  'look',
                  'history',
                  'query',
                  'query_metrics'
                 ]


parser = argparse.ArgumentParser(
                    prog='thetool_extractor',
                    description='This script helps you extract data from looker system activity.'
                    )


parser.add_argument('-t', '--table', help='table name from the explore')
parser.add_argument('-m', '--mapping-file', help='Path to Looker project mapping JSON file.')

args = parser.parse_args()

# @@@ STEP 2 @@@
def extract(table_name:str):
    print("=" * 30 + '\n\n' +
                f"Start extracting {table_name} table" + '\n\n' +
                "=" * 30
                )
    table = table_name
    try:
        looker_worker = LookerWorker(table_name = table)
        looker_worker.fetch()
        looker_worker.dump()

    except Exception as e:
        print(e)
        print(f"Error while extracting {table_name} table")

# @@@ STEP 1 @@@
if __name__ == "__main__":
    # make output path if not exist
    if not os.path.exists(CSV_DUMP_DIR):
        os.makedirs(CSV_DUMP_DIR)
    # clear the output path
    for filename in os.listdir(CSV_DUMP_DIR):
        file_path = os.path.join(CSV_DUMP_DIR, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)

    if not (args.table):
        for table_name in hardcoded_list:
            try:
                extract(table_name)
            except Exception as e:
                raise Exception(f"Error while extracting {table_name} table.\nError: {e}")
    else:
        table_name = args.table
        try:
            extract(args.table)
        except Exception as e:
            print(e)
            print(f"Error while extracting {table_name} table")
