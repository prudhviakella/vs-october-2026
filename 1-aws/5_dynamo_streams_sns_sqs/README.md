# Lab: DynamoDB Streams → SNS → SQS (new-employee notifications)

**VidyaSankalp · AWS Series** · Tutor: Prudhvi Akella · Region: `us-east-1`

```
week2-hires.json ─> s3-to-dynamodb (last lab) ─> DynamoDB Employees
                                                     │ stream: "E1006 was added"
                                                     ▼
                                     Lambda new-employee-publisher ─ sns:Publish ─> SNS topic new-employee
                                                                                    │            │
                                                                         email to HR (you)   SQS it-onboarding
                                                                                               │ (optional)
                                                                                Lambda it-onboarding-worker
```

Needs the previous lab (**Lambda loads a file from S3 into DynamoDB**): table `Employees`, your bucket, and the `s3-to-dynamodb` function.

## Files

```
lab_streams_sns_sqs/
├── publisher/lambda_function.py   reads the stream, publishes new employees to SNS (Step 6)
├── worker/lambda_function.py      optional: takes IT tasks off the queue (Step 9)
├── data/week2-hires.json          2 new employees: E1006, E1007 (Step 7)
└── policies/
    ├── trust-policy.json          who may use the roles: the Lambda service
    ├── publisher-policy.json      what the publisher may do (Step 5 — replace ACCOUNT_ID)
    ├── worker-policy.json         what the worker may do (Step 9 — replace ACCOUNT_ID)
    ├── queue-policy.json          lets the topic send to the queue (Step 4, to read)
    └── queue-attributes.json      the same policy in the shape the CLI needs (Step 4)
```

## Names used

| Thing | Name |
|---|---|
| DynamoDB stream | on table `Employees` (from the last lab), view type **New image** |
| SNS topic | `new-employee` |
| SQS queue | `it-onboarding` |
| IAM policy + role (publisher) | `new-employee-publisher-policy`, `new-employee-publisher-role` |
| Lambda (publisher) | `new-employee-publisher` — started by the stream |
| Optional: IAM policy + role (worker) | `it-onboarding-worker-policy`, `it-onboarding-worker-role` |
| Optional: Lambda (worker) | `it-onboarding-worker` — started by the queue |

## Before you start

- Do each step **either** in the console **or** with the commands — not both.
- Commands: **PyCharm Terminal** (Mac: zsh, Windows: PowerShell), **same window** for all steps.

---

## Step 0 · Check the last lab and set variables

This lab adds to the last one. The table, the bucket and the s3-to-dynamodb function must still exist.

**Console**

1. Region (top right): **US East (N. Virginia) us-east-1**.
2. **DynamoDB** → **Tables**: `Employees` is there (with E1001–E1005).
3. **S3**: your bucket `vs-lab-employees-<account id>` is there. **Lambda**: `s3-to-dynamodb` is there.
4. Cleaned up last time? Do Steps 0–6 of the last lab again first.

**Mac**

```bash
cd ~/Downloads/lab_streams_sns_sqs
aws configure set region us-east-1

ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
BUCKET="vs-lab-employees-$ACCOUNT"
EMAIL="you@example.com"          # ← your real email address

aws dynamodb scan --table-name Employees --select COUNT
aws lambda get-function --function-name s3-to-dynamodb --query Configuration.FunctionName --output text
```

**Windows (PowerShell)**

```powershell
cd ~\Downloads\lab_streams_sns_sqs
aws configure set region us-east-1

$ACCOUNT = aws sts get-caller-identity --query Account --output text
$BUCKET = "vs-lab-employees-$ACCOUNT"
$EMAIL = "you@example.com"        # ← your real email address

aws dynamodb scan --table-name Employees --select COUNT
aws lambda get-function --function-name s3-to-dynamodb --query Configuration.FunctionName --output text
```

**You should see:** `"Count": 5` (or 3 if you skipped Step 8 last time) and `s3-to-dynamodb`.

---

## Step 1 · Turn on the DynamoDB stream

From now on, every change to the table is written to its stream.

**Console**

1. **DynamoDB** → **Tables** → `Employees` → **Exports and streams** tab.
2. Under **DynamoDB stream details** → **Turn on**.
3. View type: **New image** (the whole item after the change) → **Turn on stream**.

**Mac**

```bash
aws dynamodb update-table --table-name Employees --stream-specification "StreamEnabled=true,StreamViewType=NEW_IMAGE"

STREAM_ARN=$(aws dynamodb describe-table --table-name Employees --query Table.LatestStreamArn --output text)
echo $STREAM_ARN
```

**Windows (PowerShell)**

```powershell
aws dynamodb update-table --table-name Employees --stream-specification "StreamEnabled=true,StreamViewType=NEW_IMAGE"

$STREAM_ARN = aws dynamodb describe-table --table-name Employees --query Table.LatestStreamArn --output text
echo $STREAM_ARN
```

**You should see:** A stream ARN like `arn:aws:dynamodb:us-east-1:<account id>:table/Employees/stream/2026-11-05T…`. Items already in the table are **not** in the stream — only changes from now on.

---

## Step 2 · Create the SNS topic

The topic is the loudspeaker: one message in, a copy out to every subscriber.

**Console**

1. **SNS** → **Topics** → **Create topic**.
2. Type: **Standard**. Name: `new-employee` → **Create topic**.
3. Copy the topic **ARN** from the topic page — you need it in Step 6.

**Mac**

```bash
TOPIC_ARN=$(aws sns create-topic --name new-employee --query TopicArn --output text)
echo $TOPIC_ARN
```

**Windows (PowerShell)**

```powershell
$TOPIC_ARN = aws sns create-topic --name new-employee --query TopicArn --output text
echo $TOPIC_ARN
```

**You should see:** `arn:aws:sns:us-east-1:<account id>:new-employee`

---

## Step 3 · Subscribe your email to the topic

HR's inbox (yours, in the lab) becomes the first subscriber.

**Console**

1. Open the topic → **Create subscription**.
2. Protocol: **Email**. Endpoint: your email address → **Create subscription**.
3. Open your inbox: email **AWS Notification - Subscription Confirmation** → click **Confirm subscription**.
4. Back on the topic page, the subscription status changes from **Pending confirmation** to **Confirmed**.

**Mac**

```bash
aws sns subscribe --topic-arn $TOPIC_ARN --protocol email --notification-endpoint $EMAIL

# open the email and click "Confirm subscription", then:
aws sns list-subscriptions-by-topic --topic-arn $TOPIC_ARN --query "Subscriptions[].[Protocol,Endpoint,SubscriptionArn]" --output table
```

**Windows (PowerShell)**

```powershell
aws sns subscribe --topic-arn $TOPIC_ARN --protocol email --notification-endpoint $EMAIL

# open the email and click "Confirm subscription", then:
aws sns list-subscriptions-by-topic --topic-arn $TOPIC_ARN --query "Subscriptions[].[Protocol,Endpoint,SubscriptionArn]" --output table
```

**You should see:** One `email` subscription with a long subscription ARN. `PendingConfirmation` means you haven't clicked the link yet (check spam).

---

## Step 4 · Create the SQS queue and subscribe it to the topic

IT's to-do list. The queue also needs a policy that lets this topic put messages in it.

**Console**

1. **SQS** → **Create queue**. Type: **Standard**. Name: `it-onboarding`. Keep all defaults → **Create queue**.
2. On the queue page → **Subscribe to Amazon SNS topic** → pick `new-employee` → **Save**.
3. Open the queue's **Access policy** tab: the console added a statement that allows `sns.amazonaws.com` to `sqs:SendMessage`, only for your topic. Compare it with `policies/queue-policy.json`.

**Mac**

```bash
QUEUE_URL=$(aws sqs create-queue --queue-name it-onboarding --query QueueUrl --output text)
QUEUE_ARN=$(aws sqs get-queue-attributes --queue-url $QUEUE_URL --attribute-names QueueArn --query Attributes.QueueArn --output text)

sed "s/ACCOUNT_ID/$ACCOUNT/g" policies/queue-attributes.json > my-queue-attributes.json
aws sqs set-queue-attributes --queue-url $QUEUE_URL --attributes file://my-queue-attributes.json

aws sns subscribe --topic-arn $TOPIC_ARN --protocol sqs --notification-endpoint $QUEUE_ARN
```

**Windows (PowerShell)**

```powershell
$QUEUE_URL = aws sqs create-queue --queue-name it-onboarding --query QueueUrl --output text
$QUEUE_ARN = aws sqs get-queue-attributes --queue-url $QUEUE_URL --attribute-names QueueArn --query Attributes.QueueArn --output text

(Get-Content policies\queue-attributes.json) -replace "ACCOUNT_ID", $ACCOUNT | Set-Content -Encoding ascii my-queue-attributes.json
aws sqs set-queue-attributes --queue-url $QUEUE_URL --attributes file://my-queue-attributes.json

aws sns subscribe --topic-arn $TOPIC_ARN --protocol sqs --notification-endpoint $QUEUE_ARN
```

**You should see:** The topic now has two subscriptions: your email and the queue. A queue subscription needs no confirmation.

> `queue-attributes.json` holds the same policy as `queue-policy.json`, written as one text value — that is the shape `set-queue-attributes` expects.

---

## Step 5 · Create the IAM policy and role for the publisher

The publisher Lambda must read the stream, publish to the topic and write logs — nothing more.

**Console**

1. Open `policies/publisher-policy.json` in a text editor; replace both `ACCOUNT_ID` with your account ID.
2. **IAM** → **Policies** → **Create policy** → **JSON** → paste → **Next** → name `new-employee-publisher-policy` → **Create policy**.
3. **IAM** → **Roles** → **Create role** → **AWS service** → **Lambda** → **Next** → tick `new-employee-publisher-policy` → **Next**.
4. Role name: `new-employee-publisher-role` → **Create role**.

**Mac**

```bash
sed "s/ACCOUNT_ID/$ACCOUNT/g" policies/publisher-policy.json > my-publisher-policy.json
PUB_POLICY_ARN=$(aws iam create-policy --policy-name new-employee-publisher-policy --policy-document file://my-publisher-policy.json --query Policy.Arn --output text)

PUB_ROLE_ARN=$(aws iam create-role --role-name new-employee-publisher-role --assume-role-policy-document file://policies/trust-policy.json --query Role.Arn --output text)
aws iam attach-role-policy --role-name new-employee-publisher-role --policy-arn $PUB_POLICY_ARN
echo $PUB_ROLE_ARN
```

**Windows (PowerShell)**

```powershell
(Get-Content policies\publisher-policy.json) -replace "ACCOUNT_ID", $ACCOUNT | Set-Content -Encoding ascii my-publisher-policy.json
$PUB_POLICY_ARN = aws iam create-policy --policy-name new-employee-publisher-policy --policy-document file://my-publisher-policy.json --query Policy.Arn --output text

$PUB_ROLE_ARN = aws iam create-role --role-name new-employee-publisher-role --assume-role-policy-document file://policies/trust-policy.json --query Role.Arn --output text
aws iam attach-role-policy --role-name new-employee-publisher-role --policy-arn $PUB_POLICY_ARN
echo $PUB_ROLE_ARN
```

**You should see:** `arn:aws:iam::<account id>:role/new-employee-publisher-role`

---

## Step 6 · Create the publisher Lambda and connect it to the stream

The stream becomes the function's trigger: Lambda reads the stream and calls the function with new records.

**Console**

1. **Lambda** → **Create function** → **Author from scratch**. Name `new-employee-publisher`, Runtime **Python 3.14**.
2. **Change default execution role** → **Use an existing role** → `new-employee-publisher-role` → **Create function**.
3. **Code** tab: paste `publisher/lambda_function.py` → **Deploy**.
4. **Configuration** → **Environment variables** → **Edit** → add `TOPIC_ARN` = your topic ARN (Step 2) → **Save**.
5. **Add trigger** (top of the page) → source **DynamoDB** → table `Employees` → Batch size `10` → Starting position **Latest** → **Add**.
6. **Configuration** → **Triggers**: wait until the trigger state is **Enabled** (about a minute).

**Mac**

```bash
cd publisher
zip ../publisher.zip lambda_function.py
cd ..
sleep 10

aws lambda create-function --function-name new-employee-publisher --runtime python3.14 --handler lambda_function.lambda_handler --role $PUB_ROLE_ARN --zip-file fileb://publisher.zip --timeout 30 --environment "Variables={TOPIC_ARN=$TOPIC_ARN}"
aws lambda wait function-active-v2 --function-name new-employee-publisher

aws lambda create-event-source-mapping --function-name new-employee-publisher --event-source-arn $STREAM_ARN --starting-position LATEST --batch-size 10
aws lambda list-event-source-mappings --function-name new-employee-publisher --query "EventSourceMappings[].State" --output text
```

**Windows (PowerShell)**

```powershell
cd publisher
Compress-Archive -Path lambda_function.py -DestinationPath ..\publisher.zip -Force
cd ..
Start-Sleep -Seconds 10

aws lambda create-function --function-name new-employee-publisher --runtime python3.14 --handler lambda_function.lambda_handler --role $PUB_ROLE_ARN --zip-file fileb://publisher.zip --timeout 30 --environment "Variables={TOPIC_ARN=$TOPIC_ARN}"
aws lambda wait function-active-v2 --function-name new-employee-publisher

aws lambda create-event-source-mapping --function-name new-employee-publisher --event-source-arn $STREAM_ARN --starting-position LATEST --batch-size 10
aws lambda list-event-source-mappings --function-name new-employee-publisher --query "EventSourceMappings[].State" --output text
```

**You should see:** `Enabled`. If it says `Creating` or `Enabling`, wait a minute and run the last command again.

> Wait for **Enabled** before Step 7. **Latest** means "start reading from now" — changes made while the trigger is still being set up are not sent.

---

## Step 7 · Add new employees

Use the last lab's function to load week2-hires.json. You never call the publisher yourself.

**Console**

1. **S3** → your bucket → **Upload** `data/week2-hires.json` (from this lab's folder).
2. **Lambda** → `s3-to-dynamodb` → **Test** tab → change `"key"` to `"week2-hires.json"` → **Test**.

**Mac**

```bash
aws s3 cp data/week2-hires.json "s3://$BUCKET/week2-hires.json"

cat > test-event.json <<EOF
{ "bucket": "$BUCKET", "key": "week2-hires.json" }
EOF
aws lambda invoke --function-name s3-to-dynamodb --cli-binary-format raw-in-base64-out --payload file://test-event.json response.json
cat response.json
```

**Windows (PowerShell)**

```powershell
aws s3 cp data\week2-hires.json "s3://$BUCKET/week2-hires.json"

@"
{ "bucket": "$BUCKET", "key": "week2-hires.json" }
"@ | Set-Content -Encoding ascii test-event.json
aws lambda invoke --function-name s3-to-dynamodb --cli-binary-format raw-in-base64-out --payload file://test-event.json response.json
Get-Content response.json
```

**You should see:** `{"file": "week2-hires.json", "items_written": 2}` — E1006 Arjun and E1007 Divya are new, so the stream gets two INSERT records.

---

## Step 8 · See the chain work

Within a few seconds: two emails, two messages waiting in the queue, and the publisher's log.

**Console**

1. **Your inbox**: two emails, **New employee: Arjun** and **New employee: Divya**.
2. **SQS** → `it-onboarding` → **Send and receive messages** → **Poll for messages**: 2 messages. Click one → **Body**: SNS's envelope, with your employee JSON inside `"Message"`.
3. Poll again after 30 seconds: the same 2 messages come back — nobody deleted them yet.
4. **Lambda** → `new-employee-publisher` → **Monitor** → **View CloudWatch logs**: `Published E1006 Arjun`, `Published E1007 Divya`.

**Mac**

```bash
aws logs tail /aws/lambda/new-employee-publisher --since 10m

aws sqs receive-message --queue-url $QUEUE_URL --max-number-of-messages 10 --wait-time-seconds 10 --query "Messages[].Body" --output text
```

**Windows (PowerShell)**

```powershell
aws logs tail /aws/lambda/new-employee-publisher --since 10m

aws sqs receive-message --queue-url $QUEUE_URL --max-number-of-messages 10 --wait-time-seconds 10 --query "Messages[].Body" --output text
```

**You should see:** Two emails, two queue messages, two `Published …` log lines.

> A received message is hidden for 30 seconds (the **visibility timeout**), then reappears, because nobody deleted it. That is how SQS makes sure no task is lost. The worker in Step 9 deletes them after doing the work.

---

## Step 9 · (Optional) A worker Lambda empties the queue

Instead of polling by hand, Lambda reads the queue, runs the worker, and deletes each message after success.

**Console**

1. Replace `ACCOUNT_ID` in `policies/worker-policy.json`. **IAM** → create policy `it-onboarding-worker-policy` from it.
2. **IAM** → create role `it-onboarding-worker-role` (AWS service → Lambda) with that policy.
3. **Lambda** → create `it-onboarding-worker`, Python 3.14, existing role `it-onboarding-worker-role`. Paste `worker/lambda_function.py` → **Deploy**.
4. **Add trigger** → **SQS** → queue `it-onboarding` → Batch size `10` → **Add**.
5. Within a minute: **Monitor** → logs show `IT task: prepare a laptop for Arjun …` and `… for Divya …`. In SQS, **Messages available** drops to 0.

**Mac**

```bash
sed "s/ACCOUNT_ID/$ACCOUNT/g" policies/worker-policy.json > my-worker-policy.json
WRK_POLICY_ARN=$(aws iam create-policy --policy-name it-onboarding-worker-policy --policy-document file://my-worker-policy.json --query Policy.Arn --output text)
WRK_ROLE_ARN=$(aws iam create-role --role-name it-onboarding-worker-role --assume-role-policy-document file://policies/trust-policy.json --query Role.Arn --output text)
aws iam attach-role-policy --role-name it-onboarding-worker-role --policy-arn $WRK_POLICY_ARN

cd worker
zip ../worker.zip lambda_function.py
cd ..
sleep 10

aws lambda create-function --function-name it-onboarding-worker --runtime python3.14 --handler lambda_function.lambda_handler --role $WRK_ROLE_ARN --zip-file fileb://worker.zip --timeout 30
aws lambda wait function-active-v2 --function-name it-onboarding-worker
aws lambda create-event-source-mapping --function-name it-onboarding-worker --event-source-arn $QUEUE_ARN --batch-size 10

sleep 60
aws logs tail /aws/lambda/it-onboarding-worker --since 10m
```

**Windows (PowerShell)**

```powershell
(Get-Content policies\worker-policy.json) -replace "ACCOUNT_ID", $ACCOUNT | Set-Content -Encoding ascii my-worker-policy.json
$WRK_POLICY_ARN = aws iam create-policy --policy-name it-onboarding-worker-policy --policy-document file://my-worker-policy.json --query Policy.Arn --output text
$WRK_ROLE_ARN = aws iam create-role --role-name it-onboarding-worker-role --assume-role-policy-document file://policies/trust-policy.json --query Role.Arn --output text
aws iam attach-role-policy --role-name it-onboarding-worker-role --policy-arn $WRK_POLICY_ARN

cd worker
Compress-Archive -Path lambda_function.py -DestinationPath ..\worker.zip -Force
cd ..
Start-Sleep -Seconds 10

aws lambda create-function --function-name it-onboarding-worker --runtime python3.14 --handler lambda_function.lambda_handler --role $WRK_ROLE_ARN --zip-file fileb://worker.zip --timeout 30
aws lambda wait function-active-v2 --function-name it-onboarding-worker
aws lambda create-event-source-mapping --function-name it-onboarding-worker --event-source-arn $QUEUE_ARN --batch-size 10

Start-Sleep -Seconds 60
aws logs tail /aws/lambda/it-onboarding-worker --since 10m
```

**You should see:** `IT task: prepare a laptop for Arjun (E1006, Finance, Kolkata)` and the same for Divya. The queue is empty.

---

## Step 10 · Clean up

Remove this lab's pieces. Skip the worker lines if you didn't do Step 9. New terminal? Run Step 0 again first.

**Console**

1. **Lambda** → each function (`new-employee-publisher`, `it-onboarding-worker`) → **Configuration** → **Triggers** → delete the trigger; then **Actions** → **Delete** the function.
2. **CloudWatch** → **Log groups** → delete `/aws/lambda/new-employee-publisher` and `/aws/lambda/it-onboarding-worker`.
3. **IAM** → delete both roles, then both policies (`new-employee-publisher-…`, `it-onboarding-worker-…`).
4. **SNS** → delete topic `new-employee` (its subscriptions go with it). **SQS** → delete queue `it-onboarding`.
5. **DynamoDB** → `Employees` → **Exports and streams** → **Turn off** the stream.
6. Finished with the series? Do the last lab's Step 9 (clean up) too.

**Mac**

```bash
UUID=$(aws lambda list-event-source-mappings --function-name new-employee-publisher --query "EventSourceMappings[0].UUID" --output text)
aws lambda delete-event-source-mapping --uuid $UUID
UUID=$(aws lambda list-event-source-mappings --function-name it-onboarding-worker --query "EventSourceMappings[0].UUID" --output text)
aws lambda delete-event-source-mapping --uuid $UUID

aws lambda delete-function --function-name new-employee-publisher
aws lambda delete-function --function-name it-onboarding-worker
aws logs delete-log-group --log-group-name /aws/lambda/new-employee-publisher
aws logs delete-log-group --log-group-name /aws/lambda/it-onboarding-worker

aws iam detach-role-policy --role-name new-employee-publisher-role --policy-arn "arn:aws:iam::${ACCOUNT}:policy/new-employee-publisher-policy"
aws iam delete-role --role-name new-employee-publisher-role
aws iam delete-policy --policy-arn "arn:aws:iam::${ACCOUNT}:policy/new-employee-publisher-policy"
aws iam detach-role-policy --role-name it-onboarding-worker-role --policy-arn "arn:aws:iam::${ACCOUNT}:policy/it-onboarding-worker-policy"
aws iam delete-role --role-name it-onboarding-worker-role
aws iam delete-policy --policy-arn "arn:aws:iam::${ACCOUNT}:policy/it-onboarding-worker-policy"

aws sns delete-topic --topic-arn "arn:aws:sns:us-east-1:${ACCOUNT}:new-employee"
aws sqs delete-queue --queue-url $(aws sqs get-queue-url --queue-name it-onboarding --query QueueUrl --output text)
aws dynamodb update-table --table-name Employees --stream-specification StreamEnabled=false
```

**Windows (PowerShell)**

```powershell
$UUID = aws lambda list-event-source-mappings --function-name new-employee-publisher --query "EventSourceMappings[0].UUID" --output text
aws lambda delete-event-source-mapping --uuid $UUID
$UUID = aws lambda list-event-source-mappings --function-name it-onboarding-worker --query "EventSourceMappings[0].UUID" --output text
aws lambda delete-event-source-mapping --uuid $UUID

aws lambda delete-function --function-name new-employee-publisher
aws lambda delete-function --function-name it-onboarding-worker
aws logs delete-log-group --log-group-name /aws/lambda/new-employee-publisher
aws logs delete-log-group --log-group-name /aws/lambda/it-onboarding-worker

aws iam detach-role-policy --role-name new-employee-publisher-role --policy-arn "arn:aws:iam::${ACCOUNT}:policy/new-employee-publisher-policy"
aws iam delete-role --role-name new-employee-publisher-role
aws iam delete-policy --policy-arn "arn:aws:iam::${ACCOUNT}:policy/new-employee-publisher-policy"
aws iam detach-role-policy --role-name it-onboarding-worker-role --policy-arn "arn:aws:iam::${ACCOUNT}:policy/it-onboarding-worker-policy"
aws iam delete-role --role-name it-onboarding-worker-role
aws iam delete-policy --policy-arn "arn:aws:iam::${ACCOUNT}:policy/it-onboarding-worker-policy"

aws sns delete-topic --topic-arn "arn:aws:sns:us-east-1:${ACCOUNT}:new-employee"
$QUEUE_URL = aws sqs get-queue-url --queue-name it-onboarding --query QueueUrl --output text
aws sqs delete-queue --queue-url $QUEUE_URL
aws dynamodb update-table --table-name Employees --stream-specification StreamEnabled=false
```

**You should see:** Only the last lab's table, bucket and function remain (delete them with that lab's Step 9 when you're done).
