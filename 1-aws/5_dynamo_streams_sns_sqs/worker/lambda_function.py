"""
it-onboarding-worker — (optional part) takes IT tasks off the SQS queue, one batch at a time.

FLOW
  SQS queue it-onboarding ──> this Lambda (Lambda polls the queue and calls it)
        event["Records"] = [ {"body": "<SNS envelope JSON>"}, ... ]
        │
        ▼
  STEP 1  open the SNS envelope: the body is SNS's wrapper, our message is inside "Message"
  STEP 2  read our employee JSON from it
  STEP 3  do the IT task — here: print it to the logs
        │
        ▼
  function returns without error → Lambda DELETES the messages from the queue
  function raises an error       → messages go back to the queue and are tried again
  Receiving and deleting                            ← needs sqs:ReceiveMessage … (IAM policy)

What this does NOT do:
  - order a real laptop — it prints the task, to keep the lab small
  - delete messages itself — Lambda does that after a successful run
"""
import json


def lambda_handler(event, context):
    for record in event["Records"]:
        # STEP 1 — SNS wraps our message in its own JSON envelope
        envelope = json.loads(record["body"])

        # STEP 2 — our message, as published by new-employee-publisher
        employee = json.loads(envelope["Message"])

        # STEP 3 — the IT task
        print(f"IT task: prepare a laptop for {employee['name']} "
              f"({employee['emp_id']}, {employee['department']}, {employee['city']})")

    return {"tasks_done": len(event["Records"])}
