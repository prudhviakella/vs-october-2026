"""
new-employee-publisher — when a new employee lands in DynamoDB, announce it on the SNS topic.

FLOW
  DynamoDB table Employees ── stream record ──> this Lambda (started by Lambda, not by you)
        event["Records"] = [ {"eventName": "INSERT", "dynamodb": {"NewImage": {...}}}, ... ]
        │
        ▼
  STEP 1  skip anything that is not a NEW item (MODIFY / REMOVE)
  STEP 2  read the new item — stream records use DynamoDB JSON: {"name": {"S": "Kiran"}}
  STEP 3  publish one message to SNS                 ← needs sns:Publish          (IAM policy)
        │
        ▼
  SNS topic new-employee ──> email to HR   and   ──> SQS queue it-onboarding
  Reading the stream itself                          ← needs dynamodb:GetRecords … (IAM policy)

What this does NOT do:
  - crash on a missing field — a missing "city" becomes "". A stream function that crashes is called again
    with the SAME records for up to 24 hours, and later changes wait behind it.
  - send email or touch the queue directly — SNS delivers to every subscriber
  - react to updates or deletes — only INSERT (a brand-new emp_id)
  - run when you press nothing: Lambda polls the stream and calls this function itself

Setting (Lambda environment variable):
  TOPIC_ARN   e.g. arn:aws:sns:us-east-1:123456789012:new-employee
"""
import json
import os

import boto3

TOPIC_ARN = os.environ["TOPIC_ARN"]
sns = boto3.client("sns")


def text(item, field):
    """One text value from DynamoDB JSON: {"city": {"S": "Kolkata"}} → "Kolkata". Missing → ""."""
    return item.get(field, {}).get("S", "")


def lambda_handler(event, context):
    published = 0
    for record in event["Records"]:
        # STEP 1 — only brand-new items
        if record["eventName"] != "INSERT":
            print(f"Skipping {record['eventName']}")
            continue

        # STEP 2 — the new item, written in DynamoDB JSON ("S" = string)
        item = record["dynamodb"]["NewImage"]
        employee = {
            "emp_id": text(item, "emp_id"),
            "name": text(item, "name"),
            "department": text(item, "department"),
            "city": text(item, "city"),
        }

        # STEP 3 — one message to the topic; SNS sends it to every subscriber
        sns.publish(
            TopicArn=TOPIC_ARN,
            Subject=f"New employee: {employee['name']}",
            Message=json.dumps(employee),
        )
        print(f"Published {employee['emp_id']} {employee['name']}")
        published += 1

    return {"published": published}
