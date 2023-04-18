import boto3
import os
import json
import uuid
from datetime import datetime

def lambda_handler(event, context):

    if ('body' not in event or
            event['httpMethod'] != 'POST'):
        return {
            'statusCode': 400,
            'headers': {},
            'body': json.dumps({'msg': 'Bad Request'})
        }

    table_name = os.environ.get('TABLE', 'Messages')
    region = os.environ.get('REGION', 'us-west-2')

    messages_table = boto3.resource(
        'dynamodb',
        region_name=region
    )

    table = messages_table.Table(table_name)
    activity = json.loads(event['body'])
    entries = parse_input(json.loads(event['body']))
    
    params = {
        'id': str(uuid.uuid4()),
        'message': entries['message'],
        'owner': entries['owner'],
        'outgoing_phone': entries['outgoing_phone'],
        'send_time': entries['send_time'],
        'sent': 0,
        'isDeleted': 0,
        'dateAdded': str(datetime.timestamp(datetime.now()))
    }
    # params = {
    #     'id': str(uuid.uuid4()),
    #     'message': activity['message'],
    #     'owner': activity['owner'],
    #     'outgoing_phone': activity['outgoing_phone'],
    #     'send_time':activity['send_time'],
    #     'sent': 0,
    #     'isDeleted': 0,
    #     'dateAdded': str(datetime.timestamp(datetime.now()))
    # }

    response = table.put_item(
        TableName=table_name,
        Item=params
    )
    print(response)

    return {
        'statusCode': 201,
        'headers': {},
        'body': json.dumps({'msg': 'Message added'})
    }

def parse_input(event):

    http_method = event["body"] if event.get("httpMethod") else None
    path = event["path"] if event.get('path') else None

    if http_method == None or path==None:
        return {
            'statusCode': 401,
            'headers': {},
            'body': json.dumps({'msg': 'Missing http method and/or path'})
        }
    message = event["method"] if event.get("httpMethod") else None
    owner = event["owner"] if event.get("owner") else None
    outgoing_phone = event["outgoing_phone"] if event.get(
        "outgoing_phone") else None
    send_time = event["send_time"] if event.get("send_time") else None
    return{
        http_method,
        path,
        message,
        owner,
        outgoing_phone,
        send_time
    }


