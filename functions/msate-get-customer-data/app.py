import json
import os
from functools import lru_cache
import boto3
from intelix_python_layer_utils import LoggerBuilderHelper, DatabaseWrapperManager  # type: ignore
from postgresutils import get_postgres_connection  # type: ignore

def lambda_handler(event, context):
    pass