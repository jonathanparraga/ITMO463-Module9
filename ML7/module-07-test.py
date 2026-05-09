# Module 07 Autograder
import boto3
import json
import requests
import hashlib
import sys
import datetime
import os.path
import time
from tqdm import tqdm
from bs4 import BeautifulSoup
import re

# Assignment grand total
grandtotal = 0
totalPoints = 10
assessmentName = "module-07-assessment"
correctNumberOfRolePolicies      = 4
correctNumberOfLts               = 1
correctNumberOfSnsTopics         = 1
correctNumberOfLambdaFunctions   = 1
correctNumberOfObjectsInFinishedBucket = 2
tag = "module-07"
ec2tag = "backend"
dynamoTableName = "company"
runtime = "python3.10"
lambdaEventValue = "s3:ObjectCreated:*"

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
# 10 tasks to cover
##############################################################################
# Check for the presence of a Lambda Function 
# Check for presence of an IAM Role named: iam_for_lambda 
# Check the Lambda function to have the Python 3.12 runtime 
# Check for the existence of the value 'done' in the RAWS3URL attribute 
# Check for the presence of the 'https://' in the FINSHIEDURL attribute 
# Check for the existence of a DynamoDB IAM Role Access policy for the iam_for_lambda role 
# Check for the existence of a S3 IAM Role Access policy for the iam_for_lambda role 
# Check for the existence of a SQS IAM Role Access policy for the iam_for_lambda rol 
# Check for the existence of a SNS IAM Role Access policy for the iam_for_lambda role 
# Check the s3 Raw bucket notification configuration has Events values of s3:ObjectCreated:* 

clientec2 = boto3.client('ec2')
clientelbv2 = boto3.client('elbv2')
clientasg = boto3.client('autoscaling')
clients3 = boto3.client('s3')
clientdynamodb = boto3.client('dynamodb')
clientiam = boto3.client('iam')
clientsns = boto3.client('sns')
clientsqs = boto3.client('sqs')
clientlambda = boto3.client('lambda')

# List Lambda functions
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda/client/list_functions.html
responseListLambda = clientlambda.list_functions()

# SQS get Queue URL and COunt Messages
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs/client/list_queues.html
responseSQSQueueList = clientsqs.list_queues()

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/list_tables.html
responseDynamoListTables = clientdynamodb.list_tables()

responseEC2IAMProfile=clientec2.describe_instances(    
  Filters=[ {'Name': 'tag:Type','Values': [ec2tag]}])

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sns/client/list_topics.html

responsesns = clientsns.list_topics()

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam/client/list_role_policies.html

responseiam = clientiam.list_role_policies(
     RoleName='project_role' 
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
# Check for the presence of a Lambda Function 
##############################################################################
print('*' * 79)
print("Check for the presence of a Lambda function...") 

try: 
  functionName = responseListLambda['Functions'][0]['FunctionName']

  if len(responseListLambda['Functions']) >= correctNumberOfLambdaFunctions:
    print("You have the correct number of Lambda functions: " + str(len(responseListLambda['Functions'])))
    print("Function is named: " + functionName + "...")
    grandtotal += 1
    currentPoints()
  else:
    print("You have the incorrect number of Lambda functions: " + str(len(responseListLambda['Functions'])))
    print("Go back and check your Terraform.tfvars file and make sure the correct code to declare a Lambda function...")
    currentPoints()
except:
  print("No AWS Lambda functions were found, check your main.tf to see if you have correctly created one...")
  currentPoints()

print('*' * 79)
print("\r")
##############################################################################
# Testing for the presence of an IAM Role named: iam_for_lambda
##############################################################################
print('*' * 79)
print("Testing for the presence of an IAM Role named: iam_for_lambda") 

responseIAMRoles = clientiam.list_roles()
rolePresent = False

try:
  print("Printing IAM Roles: iam_for_lambda...")
  for n in range(0,len(responseIAMRoles['Roles'])):
    print("IAM Roles: " + responseIAMRoles['Roles'][n]['RoleName'])
    if responseIAMRoles['Roles'][n]['RoleName'] == "iam_for_lambda":
      print('*' * 79)
      print("Found a match: " + str(responseIAMRoles['Roles'][n]['RoleName']) + "...")
      print('*' * 79)
      rolePresent = True

  if rolePresent == False:
    print("The IAM Role: iam_for_lambda is not present...")  

except:
  print("No IAM Roles found...")
  print("Perhaps look back in the main.tf and at your code to generate an a second IAM Role named: iam_for_lambda...")
  print("Watch out that the Role is spelled: iam_for_lambda...")  

if rolePresent == True:
  grandtotal += 1
  currentPoints()
else:
  currentPoints()

print('*' * 79)
print("\r")
##############################################################################
# Check the Lambda function if it has the Python 3.10 runtime 
##############################################################################
print('*' * 79)
print("Checking for the presence of the runtime: " + str(runtime) + " in your Lambda function...") 

try: 
  functionRuntime = responseListLambda['Functions'][0]['Runtime']
  functionName = responseListLambda['Functions'][0]['FunctionName']

  if functionRuntime == runtime:
    print("You have the correct Lambda function runtime: " + str(functionRuntime) + "...")
    print("For your Lambda function named: " + functionName + "...")
    grandtotal += 1
    currentPoints()
  else:
    print("You have the incorrect Lambda function runtime: " + str(functionRuntime) + "...")
    print("Go back and check your main.tf and make sure your aws_lambda_function has the value: runtime = " + str(runtime) + "...")
    currentPoints()
except:
  print("No AWS Lambda functions were found, check your main.tf to see if you have correctly created one...")
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
    grandtotal += 1
    currentPoints()
  else:
    print("You have the incorrect number of 'done' statuses in the RAWS3URL field: " + str(responseQueryItems['Count']))
    print("In your DynamoDB table named: " + str(responseDynamoListTables['TableNames'][0]) + "...")
    print("Double check that you have built the code in the lambda_handler.py Lambda function ")
    print("that will change the RAWS3URL to 'done' after successfully processing the images...")
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
    grandtotal += 1
    currentPoints()
  else:
    print("You have the incorrect number of presigned URLs in the FINSIHEDS3URL field: " + str(responseQueryItems['Count']))
    print("In your DynamoDB table named: " + str(responseDynamoListTables['TableNames'][0]) + "...")
    print("Double check that you have built the code in the lambda_handler.py Lambda function that will change the FINSIHEDS3URL to be presigned url...")
    print("after successfully processing the images...")
    currentPoints()
except:
  print("No DynamoDB tables found, check your main.tf to see if you have correctly created one...")
  currentPoints()

print('*' * 79)
print("\r")
##############################################################################
# Check that the Lambda entity has an iam_role_policy named: dynamodb_fullaccess_lambda_policy
# and is attached to the IAM Role granting the Lambda function access.
##############################################################################
print('*' * 79)
print("Check that the Lambda entity has an iam_role_policy named: dynamodb_fullaccess_lambda_policy") 
print("and is attached to the IAM Role granting the Lambda function access.")

responseIAMRolePolicies = clientiam.list_role_policies(RoleName="iam_for_lambda")
policyPresent = False

try:
  print("Printing IAM Role Policies attached to the IAM Role: iam_for_lambda...")
  for n in range(0,len(responseIAMRolePolicies['PolicyNames'])):
    print("IAM Policy attached to IAM Role: " + responseIAMRolePolicies['PolicyNames'][n])
    if responseIAMRolePolicies['PolicyNames'][n] == "dynamodb_fullaccess_lambda_policy":
      print('*' * 79)
      print("The IAM Role Policy: dynamodb_fullaccess_lambda_policy is present...")
      print('*' * 79)
      policyPresent = True

  if policyPresent == False:
    print("The IAM Role Policy: dynamodb_fullaccess_lambda_policy is not present...")  

except:
  print("No IAM Role policies that match the required: dynamodb_fullaccess_lambda_policy attached to the IAM Role...")
  print("Perhaps look back in the main.tf and at the structure of the additional IAM Role Policies...")
  print("Watch out that it is spelled: dynamodb_fullaccess_lambda_policy...")  

if policyPresent == True:
  grandtotal += 1
  currentPoints()
else:
  currentPoints()

print('*' * 79)
print("\r")
##############################################################################
# Check that Lambda entity has an iam_role_policy named: s3_fullaccess_lambda_policy
# and is attached to the IAM Role granting the Lambda function access.
##############################################################################
print('*' * 79)
print("Check that the Lambda entity has an iam_role_policy named: s3_fullaccess_lambda_policy") 
print("and is attached to the IAM Role granting the Lambda function access.")

responseIAMRolePolicies = clientiam.list_role_policies(RoleName="iam_for_lambda")
policyPresent = False

try:
  print("Printing IAM Role Policies attached to the IAM Role: iam_for_lambda...")
  for n in range(0,len(responseIAMRolePolicies['PolicyNames'])):
    print("IAM Policy attached to IAM Role: " + responseIAMRolePolicies['PolicyNames'][n])
    if responseIAMRolePolicies['PolicyNames'][n] == "s3_fullaccess_lambda_policy":
      print('*' * 79)
      print("The IAM Role Policy: s3_fullaccess_lambda_policy is present...")
      print('*' * 79)
      policyPresent = True

  if policyPresent == False:
    print("The IAM Role Policy: s3_fullaccess_lambda_policy is not present...")  

except:
  print("No IAM Role policies that match the required: s3_fullaccess_lambda_policy attached to the IAM Role...")
  print("Perhaps look back in the main.tf and at the structure of the additional IAM Role Policies...")
  print("Watch out that it is spelled: s3_fullaccess_lambda_policy...")  

if policyPresent == True:
  grandtotal += 1
  currentPoints()
else:
  currentPoints()

print('*' * 79)
print("\r")
##############################################################################
# Check that Lambda entity has an iam_role_policy named: sqs_fullaccess_lambda_policy
# and is attached to the IAM Role granting the Lambda function access.
##############################################################################
print('*' * 79)
print("Check that Lambda entity has an iam_role_policy named: sqs_fullaccess_lambda_policy") 
print("and is attached to the IAM Role granting the Lambda function access.")

responseIAMRolePolicies = clientiam.list_role_policies(RoleName="iam_for_lambda")
policyPresent = False

try:
  print("Printing IAM Role Policies attached to the IAM Role: iam_for_lambda...")
  for n in range(0,len(responseIAMRolePolicies['PolicyNames'])):
    print("IAM Policy attached to IAM Role: " + responseIAMRolePolicies['PolicyNames'][n])
    if responseIAMRolePolicies['PolicyNames'][n] == "sqs_fullaccess_lambda_policy":
      print('*' * 79)
      print("The IAM Role Policy: sqs_fullaccess_lambda_policy is present...")
      print('*' * 79)
      policyPresent = True

  if policyPresent == False:
    print("The IAM Role Policy: sqs_fullaccess_lambda_policy is not present...")  

except:
  print("No IAM Role policies that match the required: sqs_fullaccess_lambda_policy attached to the IAM Role...")
  print("Perhaps look back in the main.tf and at the structure of the additional IAM Role Policies...")
  print("Watch out that it is spelled: sqs_fullaccess_lambda_policy...")  

if policyPresent == True:
  grandtotal += 1
  currentPoints()
else:
  currentPoints()

print('*' * 79)
print("\r")
##############################################################################
# Check that Lambda entity has an iam_role_policy named: sns_fullaccess_lambda_policy
# and is attached to the IAM Role granting the Lambda function access.
##############################################################################
print('*' * 79)
print("Check that Lambda entity has an iam_role_policy named: sns_fullaccess_lambda_policy") 
print("and is attached to the IAM Role granting the Lambda function access.")

responseIAMRolePolicies = clientiam.list_role_policies(RoleName="iam_for_lambda")
policyPresent = False

try:
  print("Printing IAM Role Policies attached to the IAM Role: iam_for_lambda...")
  for n in range(0,len(responseIAMRolePolicies['PolicyNames'])):
    print("IAM Policy attached to IAM Role: " + responseIAMRolePolicies['PolicyNames'][n])
    if responseIAMRolePolicies['PolicyNames'][n] == "sns_fullaccess_lambda_policy":
      print('*' * 79)
      print("The IAM Role Policy: sns_fullaccess_lambda_policy is present...")
      print('*' * 79)
      policyPresent = True

  if policyPresent == False:
    print("The IAM Role Policy: sns_fullaccess_lambda_policy is not present...")  

except:
  print("No IAM Role policies that match the required: sqs_fullaccess_lambda_policy attached to the IAM Role...")
  print("Perhaps look back in the main.tf and at the structure of the additional IAM Role Policies...")
  print("Watch out that it is spelled: sns_fullaccess_lambda_policy...")  

if policyPresent == True:
  grandtotal += 1
  currentPoints()
else:
  currentPoints()

print('*' * 79)
print("\r")
##############################################################################
# Check the s3 Raw bucket notification configuration has Events values 
# of s3:ObjectCreated:*
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/get_bucket_notification_configuration.html
##############################################################################
print('*' * 79)
print("Check the S3 Raw bucket notification configuration has an Events values" )
print("of: " + lambdaEventValue + "...")

for n in range(0,len(responseS3['Buckets'])):
    if "raw" in responseS3['Buckets'][n]['Name']:
        RAW_BUCKET_NAME = responseS3['Buckets'][n]['Name']

try:
  responseGetBucketNotification = clients3.get_bucket_notification_configuration(
    Bucket=RAW_BUCKET_NAME
  )
  if responseGetBucketNotification['LambdaFunctionConfigurations'][0]['Events'][0] == lambdaEventValue:
    print("In the bucket named: " + RAW_BUCKET_NAME + " you have the correct lambda event of ")
    print(lambdaEventValue + " created and attached...")
    grandtotal += 1
    currentPoints()
  else:
    print("In the bucket named: " + RAW_BUCKET_NAME + " you have an incorrect lambda event value of ")
    print(lambdaEventValue + " created and attached...")
    currentPoints()
except:
  print("You do not have any S3 bucket notifications present...")
  print("Please go back to your main.tf and make sure you have an aws_s3_bucket_notification declared...")
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
f = open('module-07-results.txt', 'w', encoding="utf-8")

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
print("You should now see a module-07-results.txt file has been generated on your CLI...")
print("Submit this to Coursera as your deliverable...")
f.close
print('*' * 79)
print("\r")
