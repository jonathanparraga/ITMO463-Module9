import json
import boto3
import os
from io import BytesIO
from PIL import Image
from botocore.exceptions import ClientError
from botocore.config import Config
from urllib.parse import urlparse
import logging

logger = logging.getLogger()
logger.setLevel("INFO")


def lambda_handler(event, context):
    # Todo add your app.py code here
    # remove the if logic to check if there are messages on the queue
    # If the lambda event is triggered, then there is a message in the queue
    region = 'us-east-2'

    client_sqs = boto3.client('sqs', region_name=region)
    client_dynamo = boto3.client('dynamodb', region_name=region)
    client_sns = boto3.client('sns', region_name=region)
    client_s3 = boto3.client(
        's3',
        region_name=region,
        config=Config(s3={'addressing_style': 'path'}, signature_version='s3v4'),
    )

    print("Getting a list of SQS queues...")
    response_url = client_sqs.list_queues()

    if 'QueueUrls' not in response_url or not response_url['QueueUrls']:
        raise ValueError('No SQS queues found')

    print("Retrieving the message on the queue...")
    response_messages = client_sqs.receive_message(
        QueueUrl=response_url['QueueUrls'][0],
        VisibilityTimeout=180,
    )

    if 'Messages' not in response_messages or not response_messages['Messages']:
        raise ValueError('No messages received from SQS')

    body = response_messages['Messages'][0]['Body']
    print("Message body content: " + str(body) + "...")
    print("Proceeding assuming there are messages on the queue...")

    print("Getting a list of DynamoDB tables...")
    response_dynamo_tables = client_dynamo.list_tables()
    if 'TableNames' not in response_dynamo_tables or not response_dynamo_tables['TableNames']:
        raise ValueError('No DynamoDB tables found')

    response_get_dynamo_item = client_dynamo.get_item(
        TableName=response_dynamo_tables['TableNames'][0],
        Key={'RecordNumber': {'S': body}},
        ConsistentRead=True,
    )

    print("Printing out all the fields in the record...")
    print(response_get_dynamo_item.get('Item', {}))

    url = urlparse(response_get_dynamo_item['Item']['RAWS3URL']['S'])
    key = url.path.lstrip('/')
    print("S3 Object Key name: " + key)

    response_s3 = client_s3.list_buckets()
    bucket_name = None
    fin_bucket_name = None
    for bucket in response_s3.get('Buckets', []):
        bucket_name_lower = bucket['Name'].lower()
        if 'raw' in bucket_name_lower and bucket_name is None:
            bucket_name = bucket['Name']
        if 'finished' in bucket_name_lower and fin_bucket_name is None:
            fin_bucket_name = bucket['Name']

    if bucket_name is None:
        raise ValueError('No raw S3 bucket found')
    if fin_bucket_name is None:
        raise ValueError('No finished S3 bucket found')

    response_get_object = client_s3.get_object(Bucket=bucket_name, Key=key)

    print("Saving S3 byte stream to local byte stream...")
    file_byte_string = response_get_object['Body'].read()

    print("Converting local byte stream to an image...")
    im = Image.open(BytesIO(file_byte_string))

    print("Printing Image size meta-data...")
    print(im.format, im.size, im.mode)

    print("Converting image to grayscale...")
    im = im.convert('L')

    file_name = '/tmp/grayscale-' + os.path.basename(key)
    print("Saving newly created image to disk...")
    im.save(file_name)

    print("Printing Grayscale Image size meta-data...")
    print(im.format, im.size, im.mode)

    print("Pushing modified image to Finished S3 bucket...")
    try:
        client_s3.upload_file(file_name, fin_bucket_name, key)
    except ClientError as e:
        logger.error(e)
        raise

    print("Generating presigned S3 URL...")
    response_presigned = None
    try:
        response_presigned = client_s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': fin_bucket_name, 'Key': key},
            ExpiresIn=7200,
        )
    except ClientError as e:
        logger.error(e)

    print(str(response_presigned))

    print("Listing SNS Topic ARNs...")
    response_topics = client_sns.list_topics()
    if 'Topics' not in response_topics or not response_topics['Topics']:
        raise ValueError('No SNS topics found')

    topic_arn = response_topics['Topics'][0]['TopicArn']
    print(topic_arn)

    message_to_send = (
        'Your image: ' + str(file_name) + ' is ready for download at: ' + str(response_presigned)
    )
    print("Message we will be sending: " + str(message_to_send))
    client_sns.publish(
        TopicArn=topic_arn,
        Subject='Your image is ready for download!',
        Message=message_to_send,
    )
    print("Message published to SNS Topic, all who are subscribed will receive it...")

    print("Now deleting the message off of the queue...")
    response_del_message = client_sqs.delete_message(
        QueueUrl=response_url['QueueUrls'][0],
        ReceiptHandle=response_messages['Messages'][0]['ReceiptHandle'],
    )
    print(response_del_message)

    print("Now deleting the Image object from the Raw S3 bucket...")
    response_del_object = client_s3.delete_object(Bucket=bucket_name, Key=key)
    print(response_del_object)

    print("Updating DynamoDB record with done status and presigned URL...")
    response_update = client_dynamo.update_item(
        TableName=response_dynamo_tables['TableNames'][0],
        Key={
            'RecordNumber': {
                'S': str(body)
            }
        },
        UpdateExpression='SET RAWS3URL = :rawdone, FINISHED_S3_URL = :finishedurl',
        ExpressionAttributeValues={
            ':rawdone': {
                'S': 'done'
            },
            ':finishedurl': {
                'S': str(response_presigned)
            }
        }
    )

    print("DynamoDB update response:")
    print(response_update)

    return {'statusCode': 200, 'body': json.dumps(response_presigned)}
