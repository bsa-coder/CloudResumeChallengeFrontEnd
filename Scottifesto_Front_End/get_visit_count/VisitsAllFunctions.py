from pprint import pprint
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
from decimal import Decimal
import json

def delete_visits_table(dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")

    try:
        table = dynamodb.Table('Visits')
        table.delete()
    except:
        pass

def create_visits_table(dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")
    try:
        if dynamodb.Table('Visits').table_status == 'ACTIVE':
            print('table Visits exists')
            return dynamodb.Table('Visits')
        pass
    except:
        pass
    
    table = dynamodb.create_table(
        TableName='Visits',
        KeySchema=[
            {
                'AttributeName': 'id',
                'KeyType': 'HASH'  # Partition key
            },
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'id',
                'AttributeType': 'S'
            },
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )

    init_new_table(table)
    
    return table

def init_new_table(table):
    if not table.item_count == 0:
        response = table.update_item(

            Key={
                'id': 'site_visits'
            },
            UpdateExpression="set visit_count=:c, recent_visits=:v, current_month=:m, last_visit_datetime=:d",
            ExpressionAttributeValues={
                ':c': 0,
                ':v': [0,0,0,0,0,0,0,0,0,0,0,0],
                ':m': 0,
                ':d': 0
            },
            ReturnValues="UPDATED_NEW"
        )
        return
    # create initial site_visits record
    # put initial site_visits record
    # current_month = 1 ... 12, 0 initialize only
    response = table.put_item(
       Item={
            'id': 'site_visits',
            'visit_count': 0,
            'recent_visits': [0,0,0,0,0,0,0,0,0,0,0,0],
            'current_month': 0,
            'last_visit_datetime': 0
        }
    )
    # create initial current_visit record
    # put initial current_visit record
    response = table.put_item(
       Item={
            'id': 'current_visit',
            'visit_datetime': 0
        }
    )

def put_visit(the_date_time, dynamodb=None): #01
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")

    table = dynamodb.Table('ScottifestoVisits')
    response = table.put_item(
       Item={
            'id': 'current_visit',
            'value': the_date_time
        }
    )
    return response

def get_record(record_id, dynamodb=None): #02
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")

    table = dynamodb.Table('Visits')

    try:
        response = table.get_item(Key={'id': record_id})
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return response['Item']

def update_visit(current_visit_datetime, dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")

    table = dynamodb.Table('Visits')

    cvd = current_visit_datetime.__str__()
    #print(cvd)

    response = table.update_item(
        Key={
            'id': 'current_visit'
        },
        UpdateExpression="set visit_datetime=:r",
        ExpressionAttributeValues={
            ':r': cvd
        },
        ReturnValues="UPDATED_NEW"
    )
    return response

def new_visits_count(old_count):
    return old_count+1

def update_visits(current_visit_datetime, dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")

    table = dynamodb.Table('Visits')

    new_visit = 0
    visits_item = 0

    try:
        new_visit = get_record('current_visit')
        visits_item = get_record('site_visits')

    except ClientError as e:
        print(e.new_visit['Error']['Message'])
        print(e.visits_item['Error']['Message'])

    if new_visit['visit_datetime'] == visits_item['last_visit_datetime']:
        #print("nothing to do ... already updated count")
        return

    visit_datetime = datetime.strptime(new_visit['visit_datetime'], '%Y-%m-%d %H:%M:%S.%f')
    now_datetime = datetime.now()

    if visit_datetime > now_datetime:
        print("we have an error in visit record")
        return

    new_site_visit_count = new_visits_count(visits_item['visit_count'])
    #print('new_site_visit_count=', new_site_visit_count)

    # get the current month
    # get the month of the visit and now
    now_month = now_datetime.strftime("%m")
    visit_month = visit_datetime.strftime("%m")
    site_month = visits_item['current_month']

    rec_visits = [0,0,0,0,0,0,0,0,0,0,0,0]
    lastcount = 0

    # get site_records record (has all the visit data)
    rec_visits = visits_item['recent_visits']
    # increment visit_count
    # is this the first visit for the month?
    if visit_month == site_month:
    # no - increment month total
        lastcount = rec_visits[int(site_month)-1]
    else:
    # yes - reset month total to 1
        site_month = now_month

    rec_visits[int(site_month)-1] = lastcount + 1

    response = table.update_item(
        Key={
            'id': 'site_visits'
        },
        UpdateExpression="set last_visit_datetime=:d, visit_count=:c, current_month=:m, recent_visits=:v",
        ExpressionAttributeValues={
            ':d': new_visit['visit_datetime'],
            ':c': new_site_visit_count,
            ':m': site_month,
            ':v': rec_visits
        },
        ReturnValues="UPDATED_NEW"
    )
    return response

def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "987",
            # "location": ip.text.replace("\n", "")
        })}

