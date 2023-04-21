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
messages_path = '/messages'
resource = '/messages/{owner}'


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
        'GET',
        'PUT',
        'DELETE'
    }

    body = event["body"] if event.get("body") else None
    path = event["path"] if event.get('path') else None
    http_method = event['httpMethod'] if event.get('httpMethod') else None
    path_params = event['pathParameters'] if event.get('pathParameters') else None  # {'owner': 'ivan'}
    resource = event['resource'] if event.get('resource') else None

    if http_method == None or http_method not in operations or path == None:
        msg = {'msg': f'Unsupported http method:{http_method} and/or path'}
        return build_response(http.HTTPStatus.BAD_REQUEST, msg)

    if body is not None:
        body = json.loads(body)

    return {
        "body": body,
        'path': path,
        'http_method': http_method,
        'path_param': path_params,
        'resource': resource
    }


def create_message(body: dict, table):
    params = {
        'id': str(uuid.uuid4()),
        'message': body['message'],
        'owner': body['owner'],
        'display_name': body['display_name'],
        'outgoing_phone': body['outgoing_phone'],
        'send_time': body['send_time'],
        'sent': 'False',
        'isDeleted': 'False',
        'dateAdded': str(datetime.timestamp(datetime.now()))
    }

    params['send_year_month_day'] = get_send_year_month_day(body['send_time'])

    try:
        response = table.put_item(
            TableName=table_name,
            Item=params
        )
        logger.info(f'AWS response:{response}')
    except Exception as e:
        build_response(http.HTTPStatus.BAD_REQUEST, e)

    logger.info(f'Successfully posted new message to db:{table_name}: {params}')

    return build_response(http.HTTPStatus.CREATED, body)


def get_all_messages(table):
    try:
        # total table scan
        response = table.scan()
    except Exception as e:
        build_response(http.HTTPStatus.BAD_REQUEST, e)

    return build_response(http.HTTPStatus.OK, response['Items'])


def put_message(input, table):
    body = input['body'] if input.get('body') else None
    message_id = input['body']['id'] if input.get('body').get('id') else None
    params = {
        'id': message_id
    }
    try:
        if message_id:
            symd = get_send_year_month_day(body['send_time'])

            response = table.update_item(
                Key=params,
                UpdateExpression="set message = :m, outgoing_phone = :o, send_time = :s, send_year_month_day = :symd, display_name= :n",
                ExpressionAttributeValues={
                    ":m": body['message'],
                    ":o": body['outgoing_phone'],
                    ":s": body['send_time'],
                    ":symd": symd,
                    ":n": body['display_name']
                },
                ReturnValues="UPDATED_NEW"
            )

            logger.info(f'Updated message: {input}')
            return build_response(http.HTTPStatus.OK, f'Message updated: {message_id}')
    except Exception as e:
        build_response(http.HTTPStatus.BAD_REQUEST, "Bad Request")


def delete_message(input, table):
    message_id = input['body']['id'] if input.get('body').get('id') else None

    params = {
        'id': message_id
    }

    try:
        response = table.delete_item(
            Key=params
        )
        return build_response(http.HTTPStatus.OK, f'Item deleted {message_id}')
    except:
        logger.error(
            "Couldn't delete item %s in table %s.",
            message_id, table_name)


def get_messages_by_user(event, table):
    owner = event['pathParameters']['owner']

    if owner:
        # query secondary index for all messages
        try:
            response = table.query(
                IndexName='owner-send_time-index',
                KeyConditionExpression=boto3.dynamodb.conditions.Key('owner').eq(owner)
            )
            logger.info(f'Updated message: {response["Items"]}')
        except Exception as e:
            logger.error(e)
        return build_response(http.HTTPStatus.OK, response['Items'])
    else:
        return build_response(http.HTTPStatus.BAD_REQUEST, 'Missing owner')


def get_send_year_month_day(date: str) -> str:
    try:
        datetime_object = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')
        send_year_month_day = datetime_object.strftime("%Y-%m-%d")
        return send_year_month_day
    except:
        return build_response(http.HTTPStatus.BAD_REQUEST,
                              "incorrectly formatted datetime. Need YYYY-MM-DDTHH:MM:SS")


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
