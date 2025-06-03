Here's how to attach an IAM role to an EC2 instance:

## Step 1: Create the IAM Role

### Using AWS Console

1. **Go to IAM Console** → **Roles** → **Create Role**

2. **Select trusted entity:**

   - Choose "AWS service"
   - Select "EC2"
   - Click "Next"

3. **Create/Attach Policy:**
   - Click "Create policy" (opens new tab)
   - Choose "JSON" tab
   - Paste your policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["ssm:GetParameter", "ssm:GetParameters"],
      "Resource": "arn:aws:ssm:us-east-1:123456789012:parameter/pianofi/production/*"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::pianofi-prod-bucket/*"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::pianofi-prod-bucket"
    }
  ]
}
```

4. **Name the policy:** `PianofiBackendPolicy`

5. **Back to role creation:**

   - Search for and select `PianofiBackendPolicy`
   - Click "Next"

6. **Name the role:** `PianofiBackendRole`

### Using AWS CLI

```bash
# Create the policy document
cat > pianofi-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter",
                "ssm:GetParameters"
            ],
            "Resource": "arn:aws:ssm:us-east-1:123456789012:parameter/pianofi/production/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": "arn:aws:s3:::pianofi-prod-bucket/*"
        }
    ]
}
EOF

# Create the trust policy for EC2
cat > trust-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

# Create the IAM policy
aws iam create-policy \
    --policy-name PianofiBackendPolicy \
    --policy-document file://pianofi-policy.json

# Create the IAM role
aws iam create-role \
    --role-name PianofiBackendRole \
    --assume-role-policy-document file://trust-policy.json

# Attach policy to role
aws iam attach-role-policy \
    --role-name PianofiBackendRole \
    --policy-arn arn:aws:iam::123456789012:policy/PianofiBackendPolicy

# Create instance profile
aws iam create-instance-profile \
    --instance-profile-name PianofiBackendInstanceProfile

# Add role to instance profile
aws iam add-role-to-instance-profile \
    --instance-profile-name PianofiBackendInstanceProfile \
    --role-name PianofiBackendRole
```

## Step 2: Attach Role to EC2 Instance

### Option A: During EC2 Launch (New Instance)

1. **Launch Instance** → **Configure Instance Details**
2. **IAM role:** Select `PianofiBackendRole`
3. Continue with launch

### Option B: Attach to Existing Instance

**Using AWS Console:**

1. **EC2 Console** → **Instances**
2. **Select your instance** → **Actions** → **Security** → **Modify IAM role**
3. **Choose role:** `PianofiBackendRole`
4. **Save**

**Using AWS CLI:**

```bash
# Get your instance ID
aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId,Tags[?Key==`Name`].Value|[0]]' --output table

# Attach the instance profile
aws ec2 associate-iam-instance-profile \
    --instance-id i-1234567890abcdef0 \
    --iam-instance-profile Name=PianofiBackendInstanceProfile
```

## Step 3: Verify the Setup

### On your EC2 instance:

```bash
# SSH into your EC2 instance
ssh -i your-key.pem ec2-user@your-ec2-ip

# Check if IAM role is attached
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/

# Should return: PianofiBackendRole

# Test AWS CLI access
aws sts get-caller-identity

# Should return something like:
# {
#     "UserId": "AROABC123DEFGHIJKLMN:i-1234567890abcdef0",
#     "Account": "123456789012",
#     "Arn": "arn:aws:sts::123456789012:assumed-role/PianofiBackendRole/i-1234567890abcdef0"
# }

# Test Parameter Store access
aws ssm get-parameter --name "/pianofi/production/database/url" --with-decryption
```

## Step 4: Set Environment Variables on EC2

```bash
# Set environment variables for your app
echo 'export ENVIRONMENT=production' >> ~/.bashrc
echo 'export AWS_REGION=us-east-1' >> ~/.bashrc
source ~/.bashrc

# Or set them in your application startup script
export ENVIRONMENT=production
export AWS_REGION=us-east-1

# Start your FastAPI app
cd /path/to/your/app
fastapi run app/main.py --host 0.0.0.0 --port 8000
```

## Important Notes

### ⚠️ Update ARNs in Policy

Replace these in your policy:

- `123456789012` → Your actual AWS account ID
- `pianofi-prod-bucket` → Your actual S3 bucket name

### ⚠️ S3 GeneratePresignedUrl

Note: `s3:GeneratePresignedUrl` isn't actually an IAM action. The presigned URL generation happens client-side. You need the underlying S3 permissions:

```json
{
  "Effect": "Allow",
  "Action": ["s3:GetObject", "s3:PutObject"],
  "Resource": "arn:aws:s3:::pianofi-prod-bucket/*"
}
```

### ✅ Test Your Setup

Your Python code should now work without any AWS credentials in files or environment variables:

```python
# This will automatically use the IAM role
ssm = boto3.client('ssm', region_name='us-east-1')
s3 = boto3.client('s3', region_name='us-east-1')
```

The IAM role provides temporary, automatically-rotating credentials that your application uses transparently!

Similar code found with 2 license types
