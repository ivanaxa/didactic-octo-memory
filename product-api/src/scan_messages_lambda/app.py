import json

import boto3
import os
from boto3.dynamodb.conditions import Key, Attr

from datetime import datetime, timezone
from twilio.rest import Client
import logging

account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
twilio_number = os.environ.get('TWILIO_NUMBER')
table_name = os.environ.get('TABLE', 'Messages')
region = os.environ.get('REGION', 'us-west-2')

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def invoke_twilio_api(message: dict, client: Client):
    message = client.messages \
        .create(
        body=f'{message.get("message")} -{message.get("display_name")}',
        from_=twilio_number,
        to=message.get('outgoing_phone')
    )
    # logger.info(message)


def get_messages_to_send(table):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    send_ymd = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        response = table.query(
            IndexName='send_year_month_day-send_time-index',
            KeyConditionExpression=Key('send_year_month_day').eq(send_ymd) & Key('send_time').lte(now),
            FilterExpression=Attr('sent').eq("False")
        )
        logger.info(response['Items'])

        if len(response['Items']) > 0:
            client = Client(account_sid, auth_token)
            for message in response['Items']:
                invoke_twilio_api(message, client)

            for message in response['Items']:
                params = {
                    'id': message['id']
                }
                response = table.update_item(
                    Key=params,
                    UpdateExpression="set sent = :s",
                    ExpressionAttributeValues={
                        ":s": "True"
                    },
                    ReturnValues="UPDATED_NEW"
                )
                logger.info(response)
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': {
                'Message': 'SUCCESS'
            }
        }
    except Exception as e:
        return {
            'statusCode': 400,
            'headers': {},
            'body': json.dumps('Error in sending message')
        }


def get_current_time():
    return datetime.now().isoformat(timespec='seconds')


def lambda_handler(event, context):
    logger.info(event)
    logger.info(account_sid)
    logger.info(auth_token)
    logger.info(twilio_number)

    messages_table = boto3.resource(
        'dynamodb',
        region_name=region
    )

    table = messages_table.Table(table_name)

    # check the GSI 'send_year_month_day
    return get_messages_to_send(table)
