# Lab: Lambda — load a file from S3 into DynamoDB

**VidyaSankalp · AWS Series** · Tutor: Prudhvi Akella · Region: `us-east-1`

```
 1 you place employees.json        2 you run the Lambda (Test)        3 Lambda wears its IAM role
   in the S3 bucket                  event: bucket + file name          s3-to-dynamodb-role
        │                                    │                                  │
        └────────────── Lambda s3-to-dynamodb: read file → JSON → save each employee ──> DynamoDB Employees
```

Read the IAM document first: this lab uses a **policy**, a **role**, and attaches the role to the **Lambda**.

## Files

```
lab_lambda_s3_dynamodb/
├── lambda_function.py            the function (the comment at the top explains the 4 steps)
├── data/
│   ├── employees.json            3 employees  (Steps 2 and 6)
│   └── new-hires.json            2 more       (Step 8)
└── policies/
    ├── permissions-policy.json   what the Lambda may do  (Step 3 — replace BUCKET_NAME and ACCOUNT_ID)
    └── trust-policy.json         who may use the role: the Lambda service (Step 4)
```

## Names used

| Thing | Name |
|---|---|
| DynamoDB table | `Employees` — key `emp_id` (String) |
| S3 bucket | `vs-lab-employees-<your account id>` |
| IAM policy | `s3-to-dynamodb-policy` |
| IAM role | `s3-to-dynamodb-role` |
| Lambda function | `s3-to-dynamodb` (Python 3.14) |

## Before you start

- An AWS account. For the command-line steps: **AWS CLI v2**, set up with `aws configure`.
- Do each step **either** in the console **or** with the commands — not both.
- Commands: open the **PyCharm Terminal** (Mac: zsh, Windows: PowerShell) and keep the **same window** open for all steps — later steps use the variables from earlier ones.

---

## Step 0 · Open the lab folder and set two variables

Every later command uses your account ID and bucket name. We store them once.

**Console**

1. Sign in to the AWS console.
2. Top right, set the Region to **US East (N. Virginia) us-east-1**.
3. Click your account name (top right) and copy the 12-digit **Account ID** — you need it for the bucket name and the policy.

**Mac**

```bash
cd ~/Downloads/lab_lambda_s3_dynamodb
aws configure set region us-east-1

ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
BUCKET="vs-lab-employees-$ACCOUNT"
echo $ACCOUNT $BUCKET
```

**Windows (PowerShell)**

```powershell
cd ~\Downloads\lab_lambda_s3_dynamodb
aws configure set region us-east-1

$ACCOUNT = aws sts get-caller-identity --query Account --output text
$BUCKET = "vs-lab-employees-$ACCOUNT"
echo $ACCOUNT $BUCKET
```

**You should see:** Two values printed, e.g. `123456789012 vs-lab-employees-123456789012`.

---

## Step 1 · Create the DynamoDB table

This is where the employees will be saved.

**Console**

1. Open **DynamoDB** → **Tables** → **Create table**.
2. Table name: `Employees`. Partition key: `emp_id`, type **String**.
3. Leave **Default settings** → **Create table**. Wait until the status is **Active**.

**Mac**

```bash
aws dynamodb create-table --table-name Employees --attribute-definitions "AttributeName=emp_id,AttributeType=S" --key-schema "AttributeName=emp_id,KeyType=HASH" --billing-mode PAY_PER_REQUEST
aws dynamodb wait table-exists --table-name Employees
```

**Windows (PowerShell)**

```powershell
aws dynamodb create-table --table-name Employees --attribute-definitions "AttributeName=emp_id,AttributeType=S" --key-schema "AttributeName=emp_id,KeyType=HASH" --billing-mode PAY_PER_REQUEST
aws dynamodb wait table-exists --table-name Employees
```

**You should see:** Table `Employees` is **Active** and has 0 items.

---

## Step 2 · Create the S3 bucket and place the file

The Lambda will read `employees.json` from this bucket.

**Console**

1. Open **S3** → **Create bucket**.
2. Bucket name: `vs-lab-employees-<your account id>` (names must be unique in the whole world). Keep all other defaults → **Create bucket**.
3. Open the bucket → **Upload** → **Add files** → pick `data/employees.json` from the lab folder → **Upload**.

**Mac**

```bash
aws s3 mb "s3://$BUCKET"
aws s3 cp data/employees.json "s3://$BUCKET/employees.json"
aws s3 ls "s3://$BUCKET/"
```

**Windows (PowerShell)**

```powershell
aws s3 mb "s3://$BUCKET"
aws s3 cp data\employees.json "s3://$BUCKET/employees.json"
aws s3 ls "s3://$BUCKET/"
```

**You should see:** The bucket lists one file: `employees.json`.

---

## Step 3 · Create the IAM policy (what the Lambda may do)

A policy lists exactly three permissions: read files in this bucket, write to this table, write logs.

**Console**

1. Open `policies/permissions-policy.json` from the lab folder in a text editor. Replace `BUCKET_NAME` with your bucket name and `ACCOUNT_ID` with your account ID.
2. Open **IAM** → **Policies** → **Create policy** → switch to the **JSON** tab → delete what is there and paste your edited policy → **Next**.
3. Policy name: `s3-to-dynamodb-policy` → **Create policy**.

**Mac**

```bash
sed -e "s/BUCKET_NAME/$BUCKET/" -e "s/ACCOUNT_ID/$ACCOUNT/" policies/permissions-policy.json > my-policy.json
cat my-policy.json

POLICY_ARN=$(aws iam create-policy --policy-name s3-to-dynamodb-policy --policy-document file://my-policy.json --query Policy.Arn --output text)
echo $POLICY_ARN
```

**Windows (PowerShell)**

```powershell
(Get-Content policies\permissions-policy.json) -replace "BUCKET_NAME", $BUCKET -replace "ACCOUNT_ID", $ACCOUNT | Set-Content -Encoding ascii my-policy.json
Get-Content my-policy.json

$POLICY_ARN = aws iam create-policy --policy-name s3-to-dynamodb-policy --policy-document file://my-policy.json --query Policy.Arn --output text
echo $POLICY_ARN
```

**You should see:** `arn:aws:iam::<account id>:policy/s3-to-dynamodb-policy` — the policy exists but nobody uses it yet.

---

## Step 4 · Create the IAM role and attach the policy

A role is what the Lambda "wears" when it runs. The policy gives the role its permissions.

**Console**

1. **IAM** → **Roles** → **Create role**.
2. Trusted entity type: **AWS service**. Use case: **Lambda** → **Next**. (This writes the trust policy for you: "the Lambda service may use this role".)
3. In the search box type `s3-to-dynamodb-policy`, tick it → **Next**.
4. Role name: `s3-to-dynamodb-role` → **Create role**.
5. Open the role and check: **Permissions** tab shows your policy; **Trust relationships** tab shows `lambda.amazonaws.com`.

**Mac**

```bash
ROLE_ARN=$(aws iam create-role --role-name s3-to-dynamodb-role --assume-role-policy-document file://policies/trust-policy.json --query Role.Arn --output text)
aws iam attach-role-policy --role-name s3-to-dynamodb-role --policy-arn $POLICY_ARN

aws iam list-attached-role-policies --role-name s3-to-dynamodb-role
echo $ROLE_ARN
```

**Windows (PowerShell)**

```powershell
$ROLE_ARN = aws iam create-role --role-name s3-to-dynamodb-role --assume-role-policy-document file://policies/trust-policy.json --query Role.Arn --output text
aws iam attach-role-policy --role-name s3-to-dynamodb-role --policy-arn $POLICY_ARN

aws iam list-attached-role-policies --role-name s3-to-dynamodb-role
echo $ROLE_ARN
```

**You should see:** The role lists one attached policy, `s3-to-dynamodb-policy`.

---

## Step 5 · Create the Lambda function with the role

Create the function, give it the role from Step 4, put the code in, and tell it the table name.

**Console**

1. Open **Lambda** → **Create function** → **Author from scratch**.
2. Function name: `s3-to-dynamodb`. Runtime: **Python 3.14**.
3. Expand **Change default execution role** → **Use an existing role** → pick `s3-to-dynamodb-role` → **Create function**.
4. **Code** tab: open `lambda_function.py`, delete the sample code, paste the code from the lab folder → **Deploy**.
5. **Configuration** → **Environment variables** → **Edit** → **Add environment variable**: key `TABLE_NAME`, value `Employees` → **Save**.
6. **Configuration** → **General configuration** → **Edit** → Timeout `30` sec → **Save**.

**Mac**

```bash
zip function.zip lambda_function.py
sleep 10

aws lambda create-function --function-name s3-to-dynamodb --runtime python3.14 --handler lambda_function.lambda_handler --role $ROLE_ARN --zip-file fileb://function.zip --timeout 30 --environment "Variables={TABLE_NAME=Employees}"
aws lambda wait function-active-v2 --function-name s3-to-dynamodb
```

**Windows (PowerShell)**

```powershell
Compress-Archive -Path lambda_function.py -DestinationPath function.zip -Force
Start-Sleep -Seconds 10

aws lambda create-function --function-name s3-to-dynamodb --runtime python3.14 --handler lambda_function.lambda_handler --role $ROLE_ARN --zip-file fileb://function.zip --timeout 30 --environment "Variables={TABLE_NAME=Employees}"
aws lambda wait function-active-v2 --function-name s3-to-dynamodb
```

**You should see:** The function exists. **Configuration** → **Permissions** shows the role `s3-to-dynamodb-role`.

> `sleep 10` waits for the new role to reach every AWS server. Without it you may see "The role defined for the function cannot be assumed by Lambda" — just run the command again.

---

## Step 6 · Run the Lambda

The test event tells the function which file to load.

**Console**

1. In the function, open the **Test** tab → **Create new event**. Event name: `load-employees`.
2. Replace the event JSON with the block below (use **your** bucket name) → **Save** → **Test**.
3. Open **Details** under the green result box: you see the return value and the log lines.

```json
{
  "bucket": "vs-lab-employees-123456789012",
  "key": "employees.json"
}
```

**Mac**

```bash
cat > test-event.json <<EOF
{ "bucket": "$BUCKET", "key": "employees.json" }
EOF

aws lambda invoke --function-name s3-to-dynamodb --cli-binary-format raw-in-base64-out --payload file://test-event.json response.json
cat response.json
```

**Windows (PowerShell)**

```powershell
@"
{ "bucket": "$BUCKET", "key": "employees.json" }
"@ | Set-Content -Encoding ascii test-event.json

aws lambda invoke --function-name s3-to-dynamodb --cli-binary-format raw-in-base64-out --payload file://test-event.json response.json
Get-Content response.json
```

**You should see:** `{"file": "employees.json", "items_written": 3}`

---

## Step 7 · Check DynamoDB and the logs

See the saved items, and the lines the function printed.

**Console**

1. **DynamoDB** → **Tables** → `Employees` → **Explore table items**: 3 items, E1001–E1003.
2. **Lambda** → your function → **Monitor** → **View CloudWatch logs** → open the newest log stream.

**Mac**

```bash
aws dynamodb scan --table-name Employees --query "Items[].[emp_id.S, name.S, department.S]" --output table
aws logs tail /aws/lambda/s3-to-dynamodb --since 10m
```

**Windows (PowerShell)**

```powershell
aws dynamodb scan --table-name Employees --query "Items[].[emp_id.S, name.S, department.S]" --output table
aws logs tail /aws/lambda/s3-to-dynamodb --since 10m
```

**You should see:** 3 rows (E1001 Anita HR, E1002 Ravi Finance, E1003 Sana IT) and the log lines `Saved E1001 Anita` …

---

## Step 8 · Place a second file and run again

Same function, a different file: only the event changes.

**Console**

1. **S3** → your bucket → **Upload** `data/new-hires.json`.
2. **Lambda** → **Test** tab → change `"key"` to `"new-hires.json"` → **Test**.
3. **DynamoDB** → **Explore table items** → **Run**: now 5 items.

**Mac**

```bash
aws s3 cp data/new-hires.json "s3://$BUCKET/new-hires.json"

cat > test-event.json <<EOF
{ "bucket": "$BUCKET", "key": "new-hires.json" }
EOF
aws lambda invoke --function-name s3-to-dynamodb --cli-binary-format raw-in-base64-out --payload file://test-event.json response.json
cat response.json

aws dynamodb scan --table-name Employees --select COUNT
```

**Windows (PowerShell)**

```powershell
aws s3 cp data\new-hires.json "s3://$BUCKET/new-hires.json"

@"
{ "bucket": "$BUCKET", "key": "new-hires.json" }
"@ | Set-Content -Encoding ascii test-event.json
aws lambda invoke --function-name s3-to-dynamodb --cli-binary-format raw-in-base64-out --payload file://test-event.json response.json
Get-Content response.json

aws dynamodb scan --table-name Employees --select COUNT
```

**You should see:** `{"file": "new-hires.json", "items_written": 2}` and `"Count": 5`.

---

## Step 9 · Clean up

Delete everything so nothing is left running. Opened a new terminal? Run Step 0 again first.

**Console**

1. **Lambda** → select `s3-to-dynamodb` → **Actions** → **Delete**.
2. **CloudWatch** → **Log groups** → `/aws/lambda/s3-to-dynamodb` → **Delete**.
3. **IAM** → **Roles** → `s3-to-dynamodb-role` → **Delete**. Then **Policies** → `s3-to-dynamodb-policy` → **Delete**.
4. **S3** → your bucket → **Empty**, then **Delete**.
5. **DynamoDB** → `Employees` → **Delete**.

**Mac**

```bash
aws lambda delete-function --function-name s3-to-dynamodb
aws logs delete-log-group --log-group-name /aws/lambda/s3-to-dynamodb

aws iam detach-role-policy --role-name s3-to-dynamodb-role --policy-arn "arn:aws:iam::${ACCOUNT}:policy/s3-to-dynamodb-policy"
aws iam delete-role --role-name s3-to-dynamodb-role
aws iam delete-policy --policy-arn "arn:aws:iam::${ACCOUNT}:policy/s3-to-dynamodb-policy"

aws s3 rb "s3://$BUCKET" --force
aws dynamodb delete-table --table-name Employees
```

**Windows (PowerShell)**

```powershell
aws lambda delete-function --function-name s3-to-dynamodb
aws logs delete-log-group --log-group-name /aws/lambda/s3-to-dynamodb

aws iam detach-role-policy --role-name s3-to-dynamodb-role --policy-arn "arn:aws:iam::${ACCOUNT}:policy/s3-to-dynamodb-policy"
aws iam delete-role --role-name s3-to-dynamodb-role
aws iam delete-policy --policy-arn "arn:aws:iam::${ACCOUNT}:policy/s3-to-dynamodb-policy"

aws s3 rb "s3://$BUCKET" --force
aws dynamodb delete-table --table-name Employees
```

**You should see:** Nothing from this lab is left in your account.
