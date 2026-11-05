"""
s3-to-dynamodb — read a JSON file from S3 and save every employee in it to DynamoDB.

FLOW
  you press "Test" with the event  {"bucket": "vs-lab-employees-123456789012", "key": "employees.json"}
        │
        ▼
  STEP 1  read the bucket name and file name from the event
  STEP 2  download the file from S3                    ← needs s3:GetObject      (IAM policy)
  STEP 3  turn the JSON text into a list of employees
  STEP 4  save each employee as one item in DynamoDB    ← needs dynamodb:PutItem  (IAM policy)
        │
        ▼
  returns {"file": "employees.json", "items_written": 3}
  print() lines go to CloudWatch Logs                  ← needs logs:* actions    (IAM policy)

What this does NOT do:
  - create the bucket or the table (you create them in the lab steps)
  - read CSV or other formats — only a JSON list of objects, each with an "emp_id"
  - run by itself when a file is uploaded — you run it with the Test button (or `aws lambda invoke`)
  - keep old values: saving an emp_id that already exists replaces that item

Setting (Lambda environment variable):
  TABLE_NAME   the DynamoDB table to write to, e.g. Employees
"""
import json
import os
from decimal import Decimal

import boto3

# Created once when the function starts, then reused every time it runs.
TABLE_NAME = os.environ["TABLE_NAME"]
s3 = boto3.client("s3")
table = boto3.resource("dynamodb").Table(TABLE_NAME)


def lambda_handler(event, context):
    # STEP 1 — which file?
    bucket = event["bucket"]
    key = event["key"]
    print(f"Reading s3://{bucket}/{key}")

    # STEP 2 — download the file content from S3
    response = s3.get_object(Bucket=bucket, Key=key)
    text = response["Body"].read().decode("utf-8")

    # STEP 3 — JSON text → list of dicts.
    # DynamoDB does not accept Python floats, so numbers like 4.5 are read as Decimal.
    employees = json.loads(text, parse_float=Decimal)

    # STEP 4 — save each employee as one item
    for employee in employees:
        table.put_item(Item=employee)
        print(f"Saved {employee['emp_id']} {employee['name']}")

    print(f"{len(employees)} employees written to {TABLE_NAME}")
    return {"file": key, "items_written": len(employees)}
