from collections import namedtuple

# store kv object names
KVNames = namedtuple(
    "KVNames",
    [
        "kv_name",
        "kv_client_id",
        "kv_client_secret",
        "kv_certificate",
        "db_name",
        "db_user",
        "db_pass",
        "db_host",
        "db_port",
    ],
)
# store credentials
Credentials = namedtuple(
    "Credentials",
    [
        "adp_user",
        "adp_pass",
        "edw_user",
        "edw_pass",
        "edw_port",
        "edw_host",
        "edw_name",
        "edw_driver",
    ],
)
# store api endpoints
Endpoints = namedtuple("Endpoints", ["auth_url", "select_url"])
# store oAuth queries
Queries = namedtuple(
    "Queries",
    ["base_select", "custom_select"],
)
