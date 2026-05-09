# Module 06 Autograder
import boto3
import json
import requests
import hashlib
import sys
import datetime
import os.path
import time
from tqdm import tqdm
import mysql.connector
from bs4 import BeautifulSoup
import re

# Assignment grand total
grandtotal = 0
totalPoints = 10
assessmentName = "module-06-assessment"
correctNumberOfDBAcrossSubnets   = 3
correctNumOfDBSubnetGroups       = 1
correctNumberOfRolePolicies      = 4
correctNumberOfLts               = 1
correctNumberOfSnsTopics         = 1
correctNumberOfTargetGroups      = 1
correctNumberOfAutoScalingGroups = 1
correctNumberOfELBs              = 1
correctNumberOfEBS               = 3
correctNumberOfVpcs              = 2
correctNumberOfS3Buckets         = 2
correctNumberOfSGs               = 1
correctNumberOfInternetGateways  = 1
correctNumberOfRouteTables       = 1
correctNumberOfDHCPOptions       = 1
correctNumberOfObjectsInFinishedBucket = 2
tag = "module-06"
ec2tag = "backend"
dynamoTableName                   = "company"

# Function to print out current points progress
def currentPoints():
  print("Current Points: " + str(grandtotal) + " out of " + str(totalPoints) + ".")

# Documentation Links
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/autoscaling.html
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/rds.html

##############################################################################
# 5 tasks to cover
##############################################################################
# Check for presence of DynamoDB table names company
# Check for at least 5 Items inserted
# Check for the existence of the value 'done' in the RAWS3URL attribute
# Check for the presence of the 'https://' in the FINSHIEDURL attribute
# Check for the existence of a DynamoDB full access policy

clientec2 = boto3.client('ec2')
clientelbv2 = boto3.client('elbv2')
clientasg = boto3.client('autoscaling')
clients3 = boto3.client('s3')
clientdynamodb = boto3.client('dynamodb')
clientiam = boto3.client('iam')
clientsns = boto3.client('sns')
clientsqs = boto3.client('sqs')

# SQS get Queue URL and COunt Messages
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs/client/list_queues.html
responseSQSQueueList = clientsqs.list_queues()

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/list_tables.html
responseDynamoListTables = clientdynamodb.list_tables()

# EC2 describe images
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_images.html
responseEC2AMI=clientec2.describe_images(    
  Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
                tag,
            ]
        },
    ],
)
responseEC2IAMProfile=clientec2.describe_instances(    
  Filters=[ {
            'Name': 'tag:Type',
            'Values': [
                ec2tag,
            ]
        },
    ],
)
# Describe security groups
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_security_groups.html
responsesg = clientec2.describe_security_groups(
    Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
                tag,
            ]
        },
    ],
)

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sns/client/list_topics.html

responsesns = clientsns.list_topics()

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam/client/list_role_policies.html

responseiam = clientiam.list_role_policies(
     RoleName='project_role' 
)

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_vpcs.html

responseVPC = clientec2.describe_vpcs()

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_subnets.html

responseSubnets = clientec2.describe_subnets(
    Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
                tag,
            ]
        },
    ],
)

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_route_tables.html

responseRouteTables = clientec2.describe_route_tables(
    Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
            tag,
            ]
        },
    ],
)

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_dhcp_options.html

responseDHCP = clientec2.describe_dhcp_options(
    Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
            tag,
            ]
        },
    ],
)

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_security_groups.html
responseSG = clientec2.describe_security_groups(
    Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
                tag,
            ]
        },
    ],
)

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_internet_gateways.html
responseIG = clientec2.describe_internet_gateways(
  Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
                tag,
            ]
        },
    ],
)
# hello from will
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_subnets.html
responseSubnets = clientec2.describe_subnets(
  Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
                tag,
            ]
        },
    ],
)

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_route_tables.html
responseRT = clientec2.describe_route_tables(
  Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
                tag,
            ]
        },
    ],
)

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_dhcp_options.html
responseDhcpOptions = clientec2.describe_dhcp_options(
  Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
                tag,
            ]
        },
    ],
)

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_instances.html
responseEC2 = clientec2.describe_instances(
 Filters=[
     {
         'Name': 'instance-state-name',
         'Values':['running']
     }
],
) # End of function

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/list_buckets.html
# Get a Dict of all bucket names
responseS3 = clients3.list_buckets()

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2/client/describe_load_balancers.html
responseELB = clientelbv2.describe_load_balancers()

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2/client/describe_target_groups.html
responseTG = clientelbv2.describe_target_groups()

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/autoscaling/client/describe_auto_scaling_groups.html
responseasg = clientasg.describe_auto_scaling_groups()

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/autoscaling/client/describe_auto_scaling_instances.html
responseasgi = clientasg.describe_auto_scaling_instances()

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/autoscaling/client/describe_auto_scaling_groups.html
responseasg = clientasg.describe_auto_scaling_groups()

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_launch_templates.html
responselt = clientec2.describe_launch_templates()

##############################################################################
print('*' * 79)
print("Begin tests for " + tag + " Assessment...")
##############################################################################

##############################################################################
# Check for presence of DynamoDB table named: company...
# 
##############################################################################
print('*' * 79)
print("Check for presence of DynamoDB table named: " + dynamoTableName +  "...") 

try: 
  responseDynamoListTables['TableNames'][0]

  if dynamoTableName == responseDynamoListTables['TableNames'][0]:
    print("You have the correct DynamoDB table name: " + str(responseDynamoListTables['TableNames'][0]) + "...")
    grandtotal += 2
    currentPoints()
  else:
    print("The DynamoDB table name: " +  str(responseDynamoListTables['TableNames'][0]) + " does not match the required name: " + dynamoTableName + "...")
    print("Go back and check your Terraform.tfvars file and make sure the correct name has been supplied...")
    currentPoints()
except:
  print("No DynamoDB tables found, check your main.tf to see if you have correctly created one...")
  currentPoints()

print('*' * 79)
print("\r")
##############################################################################
# Check for at least 5 Items inserted in the DynamoDB
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/scan.html
##############################################################################
print('*' * 79)
print("Testing to make sure at least 5 images have been inserted in the DynamoDB table...")

responseScanDynamoTable = clientdynamodb.scan(TableName=responseDynamoListTables['TableNames'][0])

try: 
  responseDynamoListTables['TableNames'][0]

  if responseScanDynamoTable['Count'] >= 5:
    print("You have the correct number of Items: " + str(responseScanDynamoTable['Count']))
    print("In your DynamoDB table named: " + str(responseDynamoListTables['TableNames'][0]) + "...")
    grandtotal += 2
    currentPoints()
  else:
    print("You have the incorrect number of Items: " + str(responseScanDynamoTable['Count']))
    print("In your DynamoDB table named: " + str(responseDynamoListTables['TableNames'][0]) + "...")
    print("Double check that you have run the module-06-test.py after uploading 5 images via the form...")
    currentPoints()
except:
  print("No DynamoDB tables found, check your main.tf to see if you have correctly created one...")
  currentPoints()

print('*' * 79)
print("\r")
##############################################################################
# Check for the existence of the value 'done' in the RAWS3URL attribute
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/scan.html
##############################################################################
print('*' * 79)
print("Check for the existence of the value 'done' in the RAWS3URL attribute...")

try: 
  responseDynamoListTables['TableNames'][0]

  responseQueryItems = clientdynamodb.scan(
    TableName=responseDynamoListTables['TableNames'][0],
    ProjectionExpression='RAWS3URUL',
    ExpressionAttributeValues={':a': {'S': 'done'}},
    FilterExpression='RAWS3URL = :a'
    )

  if responseQueryItems['Count'] >= 1:
    print("You have the correct number of 'done' statuses in the RAWS3URL field: " + str(responseQueryItems['Count']))
    print("In your DynamoDB table named: " + str(responseDynamoListTables['TableNames'][0]) + "...")
    grandtotal += 2
    currentPoints()
  else:
    print("You have the incorrect number of 'done' statuses in the RAWS3URL field: " + str(responseQueryItems['Count']))
    print("In your DynamoDB table named: " + str(responseDynamoListTables['TableNames'][0]) + "...")
    print("Double check that you have built the code in the app.py that will change the RAWS3URL to 'done'")
    print("after successfully processing the images...")
    currentPoints()
except:
  print("No DynamoDB tables found, check your main.tf to see if you have correctly created one...")
  currentPoints()

print('*' * 79)
print("\r")
##############################################################################
# Check for the presence of the 'https://' in the FINSHIEDURL attribute
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/scan.html
# https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Scan.html#Scan.FilterExpression
##############################################################################
print('*' * 79)
print("Check for the existence of the value 'done' in the RAWS3URL attribute...")

try: 
  responseDynamoListTables['TableNames'][0]

  responseQueryItems = clientdynamodb.scan(
    TableName=responseDynamoListTables['TableNames'][0],
    ExpressionAttributeNames = {'#cl': 'FINSIHEDS3URL'},
    ExpressionAttributeValues = {':val': {'S': 'https://'}},
    FilterExpression = 'contains(#cl, :val)'
    )

  if responseQueryItems['Count'] >= 1:
    print("You have the correct number of presigned URLs in the FINSIHEDS3URL field: " + str(responseQueryItems['Count']))
    print("In your DynamoDB table named: " + str(responseDynamoListTables['TableNames'][0]) + "...")
    grandtotal += 2
    currentPoints()
  else:
    print("You have the incorrect number of presigned URLs in the FINSIHEDS3URL field: " + str(responseQueryItems['Count']))
    print("In your DynamoDB table named: " + str(responseDynamoListTables['TableNames'][0]) + "...")
    print("Double check that you have built the code in the app.py that will change the FINSIHEDS3URL to be presigned url...")
    print("after successfully processing the images...")
    currentPoints()
except:
  print("No DynamoDB tables found, check your main.tf to see if you have correctly created one...")
  currentPoints()

print('*' * 79)
print("\r")
##############################################################################
# Check that EC2 instance has an iam_role_policy named: dynamodb_fullaccess_policy 
# and is attached to the IAM Role and grants the EC2 entity DynamoDb full access.
##############################################################################
print('*' * 79)
print("Check that EC2 instance has an iam_role_policy named: dynamodb_fullaccess_policy") 
print("and is attached to the IAM Role and grants the EC2 entity DynamoDB full access.")

responseIAMRolePolicies = clientiam.list_role_policies(RoleName="project_role")
policyPresent = False

try:
  print("Printing IAM Role Policies attached to the IAM Role: project_role...")
  for n in range(0,len(responseIAMRolePolicies['PolicyNames'])):
    print("IAM Policy attached to IAM Role: " + responseIAMRolePolicies['PolicyNames'][n])
    if responseIAMRolePolicies['PolicyNames'][n] == "dynamodb_fullaccess_policy":
      print("The IAM Role Policy: dynamodb_fullaccess_policy is present...")
      policyPresent = True

  if policyPresent == False:
    print("The IAM Role Policy: dynamodb_fullaccess_policy is not present...")  

except:
  print("No IAM Role policies that match the required: dynamodb_fullaccess_policy attached to the IAM Role...")
  print("Perhaps look back in the main.tf and at the structure of the additional IAM Role Policies...")
  print("Watch out that it is spelled: dynamodb_fullaccess_policy...")  

if policyPresent == True:
  grandtotal += 2
  currentPoints()
else:
  currentPoints()

print('*' * 79)
print("\r")
##############################################################################
# Print out the grandtotal and the grade values to result.txt
##############################################################################
print('*' * 79)
print("Your result is: " + str(grandtotal) + " out of " + str(totalPoints) + " points.")
print("You can retry any items that need adjustment and retest...")

# Write results to a text file for import to the grade system
# https://www.geeksforgeeks.org/sha-in-python/
f = open('module-06-results.txt', 'w', encoding="utf-8")

# Gather sha256 of module-name and grandtotal
# https://stackoverflow.com/questions/70498432/how-to-hash-a-string-in-python
# Create datetime timestamp
dt='{:%Y%m%d%H%M%S}'.format(datetime.datetime.now())
resultToHash=(assessmentName + str(grandtotal/totalPoints) + dt)
h = hashlib.new('sha256')
h.update(resultToHash.encode())

resultsdict = {
  'Name': assessmentName,
  'gtotal' : grandtotal/totalPoints,
  'datetime': dt,
  'sha': h.hexdigest() 
}

listToHash=[assessmentName,grandtotal,dt,h.hexdigest()]
print("Writing assessment grade to text file...")
json.dump(resultsdict,f)
print("Write successful! Ready to submit your Assessment...")
print("You should now see a module-06-results.txt file has been generated on your CLI...")
print("Submit this to Coursera as your deliverable...")
f.close
print('*' * 79)
print("\r")
