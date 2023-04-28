import http

import boto3
import os
import json
import uuid
from datetime import datetime

import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

table_name = os.environ.get('TABLE', 'Messages')
region = os.environ.get('REGION', 'us-west-2')
register_path = '/register'
login_path ='/login'
verify_path='/verify'


def build_response(status_code, body=None):
    response = {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }
    }
    if body is not None:
        response['body'] = json.dumps(body)
    return response


def parse_input(event: json) -> dict:
    operations = {
        'POST',
        'GET'
    }

    body = event["body"] if event.get("body") else None
    path = event["path"] if event.get('path') else None
    http_method = event['httpMethod'] if event.get('httpMethod') else None

    if http_method == None or http_method not in operations or path == None:
        msg = {'msg': f'Unsupported http method:{http_method} and/or path'}
        return build_response(http.HTTPStatus.BAD_REQUEST, msg)

    if body is not None:
        body = json.loads(body)

    return {
        "body": body,
        'path': path,
        'http_method': http_method
    }



def lambda_handler(event, context):
    logger.info(event)
    input = parse_input(event)

    messages_table = boto3.resource(
        'dynamodb',
        region_name=region
    )

    table = messages_table.Table(table_name)

    # post
    if input['body'] and input['path'] == messages_path and input['http_method'] == 'POST':
        return create_message(input['body'], table)
    # get by user
    elif input['resource'] == resource and input['http_method'] == 'GET':
        return get_messages_by_user(event, table)
    # get all
    elif input['path'] == messages_path and input['http_method'] == 'GET':
        return get_all_messages(table)
    # put
    elif input['path'] == messages_path and input['http_method'] == 'PUT' and input['body']:
        return put_message(input, table)
    # delete
    elif input['path'] == messages_path and input['http_method'] == 'DELETE':
        return delete_message(input, table)
    else:
        msg = {'msg': f'Unsupported endpoint invocations: {json.dumps(event)}'}
        return build_response(http.HTTPStatus.BAD_REQUEST, msg)
