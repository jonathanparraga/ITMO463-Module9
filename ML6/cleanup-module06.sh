#!/bin/bash

REGION="us-east-2"

IAM_ROLE="project_role"
INSTANCE_PROFILE="coursera_profile"
SQS_QUEUE_NAME="jp-sqs"
SNS_TOPIC_NAME="jp-sns-topic"

echo "===================================================="
echo " Cleaning Module 06 conflicting AWS resources"
echo " Region: $REGION"
echo "===================================================="

echo ""
echo "1) Deleting SQS queue if it exists: $SQS_QUEUE_NAME"

QUEUE_URL=$(aws sqs get-queue-url \
  --queue-name "$SQS_QUEUE_NAME" \
  --region "$REGION" \
  --query 'QueueUrl' \
  --output text 2>/dev/null)

if [ -n "$QUEUE_URL" ] && [ "$QUEUE_URL" != "None" ]; then
  echo "Found SQS queue: $QUEUE_URL"
  aws sqs delete-queue \
    --queue-url "$QUEUE_URL" \
    --region "$REGION"
  echo "SQS queue deleted."
else
  echo "SQS queue not found. Skipping."
fi


echo ""
echo "2) Deleting SNS topic if it exists: $SNS_TOPIC_NAME"

TOPIC_ARN=$(aws sns list-topics \
  --region "$REGION" \
  --query "Topics[?ends_with(TopicArn, ':$SNS_TOPIC_NAME')].TopicArn | [0]" \
  --output text 2>/dev/null)

if [ -n "$TOPIC_ARN" ] && [ "$TOPIC_ARN" != "None" ]; then
  echo "Found SNS topic: $TOPIC_ARN"
  aws sns delete-topic \
    --topic-arn "$TOPIC_ARN" \
    --region "$REGION"
  echo "SNS topic deleted."
else
  echo "SNS topic not found. Skipping."
fi


echo ""
echo "3) Cleaning IAM role if it exists: $IAM_ROLE"

aws iam get-role --role-name "$IAM_ROLE" >/dev/null 2>&1

if [ $? -eq 0 ]; then
  echo "Found IAM role: $IAM_ROLE"

  echo ""
  echo "3a) Deleting inline role policies..."

  INLINE_POLICIES=$(aws iam list-role-policies \
    --role-name "$IAM_ROLE" \
    --query 'PolicyNames[]' \
    --output text 2>/dev/null)

  if [ -n "$INLINE_POLICIES" ]; then
    for POLICY in $INLINE_POLICIES; do
      echo "Deleting inline policy: $POLICY"
      aws iam delete-role-policy \
        --role-name "$IAM_ROLE" \
        --policy-name "$POLICY"
    done
  else
    echo "No inline policies found."
  fi


  echo ""
  echo "3b) Detaching managed policies..."

  ATTACHED_POLICIES=$(aws iam list-attached-role-policies \
    --role-name "$IAM_ROLE" \
    --query 'AttachedPolicies[].PolicyArn' \
    --output text 2>/dev/null)

  if [ -n "$ATTACHED_POLICIES" ]; then
    for POLICY_ARN in $ATTACHED_POLICIES; do
      echo "Detaching managed policy: $POLICY_ARN"
      aws iam detach-role-policy \
        --role-name "$IAM_ROLE" \
        --policy-arn "$POLICY_ARN"
    done
  else
    echo "No managed policies attached."
  fi


  echo ""
  echo "3c) Removing role from instance profiles..."

  INSTANCE_PROFILES=$(aws iam list-instance-profiles-for-role \
    --role-name "$IAM_ROLE" \
    --query 'InstanceProfiles[].InstanceProfileName' \
    --output text 2>/dev/null)

  if [ -n "$INSTANCE_PROFILES" ]; then
    for PROFILE in $INSTANCE_PROFILES; do
      echo "Removing role from instance profile: $PROFILE"
      aws iam remove-role-from-instance-profile \
        --instance-profile-name "$PROFILE" \
        --role-name "$IAM_ROLE"

      echo "Deleting instance profile: $PROFILE"
      aws iam delete-instance-profile \
        --instance-profile-name "$PROFILE"
    done
  else
    echo "No instance profiles attached to role."
  fi


  echo ""
  echo "3d) Deleting IAM role: $IAM_ROLE"

  aws iam delete-role \
    --role-name "$IAM_ROLE"

  echo "IAM role deleted."

else
  echo "IAM role not found. Skipping."
fi


echo ""
echo "4) Deleting standalone instance profile if it still exists: $INSTANCE_PROFILE"

aws iam get-instance-profile \
  --instance-profile-name "$INSTANCE_PROFILE" >/dev/null 2>&1

if [ $? -eq 0 ]; then
  echo "Found leftover instance profile: $INSTANCE_PROFILE"
  aws iam delete-instance-profile \
    --instance-profile-name "$INSTANCE_PROFILE"
  echo "Instance profile deleted."
else
  echo "Instance profile not found. Skipping."
fi


echo ""
echo "===================================================="
echo " Cleanup completed."
echo " Wait 30-60 seconds before running Terraform again."
echo "===================================================="
