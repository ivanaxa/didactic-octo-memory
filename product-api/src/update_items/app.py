import boto3
import os
import json
from datetime import datetime
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):

    if ('body' not in event or
            event['httpMethod'] != 'PUT'):
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
    item_id =  event['pathParameters']['id']

    params = {
        'id': item_id
    }

    try:
        response = table.update_item(
            Key = params,
            UpdateExpression="set itemName = :in, description = :d, price = :p, isActive = :a",
            ExpressionAttributeValues = {
                ":in": activity['itemName'],
                ":d": activity['description'],
                ":p": activity['price'],
                ":a": activity['isActive']
            },
            ReturnValues = "UPDATED_NEW"
        )
    except:
        logger.error(
            "Couldn't update item %s in table %s.",
            item_id, table_name)

    print(response)

    return {
        'statusCode': 200,
        'headers': {},
        'body': json.dumps({'msg': 'Item Deleted'})
    }
