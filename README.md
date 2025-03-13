# Looker System Activity Extraction Steps
This is a python script that extracts:

1. The following Looker System Activity views using [Looker API](https://cloud.google.com/looker/docs/api-intro):
    - user
    - user_facts
    - user_facts_role
    - role
    - group_user
    - group
    - dashboard
    - look
    - explore_label
    - history
    - query
    - lookml_fields
    - query_metrics

# 1. Prerequisite
## 1.1. Roles and permissions
### Looker
This script extract [Looker System Activity](https://cloud.google.com/looker/docs/system-activity-pages) data so at the minimum [the API client ID and secret](#263-replace-the-your_api3_client_id--and-your_api3_client_secret-with-your-api-client-id-and-secret) need to have `see_system_activity` permission.
# 2. Setting up
## 2.1. Set up Python environment and install requirements

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
## 2.2. Configuring `looker.ini`
### 2.2.1. Make a copy of `sample.looker.ini` and name it `looker.ini`
### 2.2.2. Update the _&lt;your_looker_endpoint&gt;_ in `base_url` with your instance url.

Example:
```
base_url=https://example.cloud.looker.com:19999
```

### 2.2.3. Replace the _&lt;your_API3_client_id&gt;_  and _&lt;your_API3_client_secret&gt;_ with your API client ID and secret.

Refer to [this guide](https://cloud.google.com/looker/docs/api-auth#authentication_with_an_sdk) to create client ID and secret for this step.

### 3 Run `main.py`
For extracting all tables run
```bash
python main.py
```
For extracting 1 specific table run
```bash
python main.py -t <table_name>
```

> [!CAUTION]
> The script is running on full refresh mode so old data will be purged!!!


