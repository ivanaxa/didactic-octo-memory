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

    table_name = os.environ.get('TABLE', 'Items')
    region = os.environ.get('REGION', 'us-west-2')

    item_table = boto3.resource(
        'dynamodb',
        region_name=region
    )

    table = item_table.Table(table_name)
    activity = json.loads(event['body'])

    params = {
        'id': str(uuid.uuid4()),
        'itemName': activity['itemName'],
        'description': activity['description'],
        'price': activity['price'],
        'isActive': activity['isActive'],
        'dateAdded': str(datetime.timestamp(datetime.now()))
    }

    response = table.put_item(
        TableName=table_name,
        Item=params
    )
    print(response)

    return {
        'statusCode': 201,
        'headers': {},
        'body': json.dumps({'msg': 'New Item  Created'})
    }
