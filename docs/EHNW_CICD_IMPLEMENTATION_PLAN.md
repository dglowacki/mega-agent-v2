# EH Universal Links - CI/CD Implementation Plan

**Date:** 2026-01-12
**Repository:** TrailMixTech/eh-shortlink
**Deployment Method:** AWS CodePipeline + Lambda (Serverless)

---

## Overview

Implement fully serverless CI/CD pipeline where AWS pulls from GitHub and auto-deploys CloudFront Functions and static files.

**Branches:**
- `stage` → Deploys to stage.ehnw.ca (auto)
- `main` → Deploys to ehnw.ca (auto, no approval)

---

## Architecture

```
GitHub (eh-shortlink repo)
  ├── stage branch
  │   ↓ (CodePipeline pulls on commit)
  │   CodePipeline (staging)
  │   ↓
  │   Lambda Deployer
  │   ↓
  │   stage.ehnw.ca (E12SFO751YQTOX)
  │
  └── main branch
      ↓ (CodePipeline pulls on commit)
      CodePipeline (production)
      ↓
      Lambda Deployer
      ↓
      ehnw.ca (E28JUE6Q00L6TK)
```

**Notification:** Slack #engineering (C08R87AAKT5)

---

## Repository Structure

```
eh-shortlink/
├── functions/
│   └── universal-links.js          # CloudFront Function code
├── config/
│   ├── prod.json                   # Production environment config
│   └── stage.json                  # Staging environment config
├── deploy/
│   ├── lambda_deployer.py          # Lambda function code
│   ├── requirements.txt            # Python dependencies (boto3)
│   └── deploy_lambda.py            # Script to create Lambda from mega-agent
├── .well-known/
│   ├── apple-app-site-association  # iOS universal links config
│   └── assetlinks.json             # Android app links config
├── static/
│   └── index.html                  # Fallback page
├── .gitignore
└── README.md
```

---

## Environment Parameters

### Production (config/prod.json)
```json
{
  "environment": "production",
  "domain": "ehnw.ca",
  "distribution_id": "E28JUE6Q00L6TK",
  "function_name": "ehnw-universal-links",
  "s3_bucket": "ehnw.ca",
  "certificate_arn": "arn:aws:acm:us-east-1:870314670072:certificate/31baf6a5-c39b-4e4c-a5f5-7dee5b7a4adb",
  "deep_link_scheme": "com.ehnow.eh",
  "ios_app_store_url": "https://apps.apple.com/ca/app/eh-canadas-social-network/id6747136970",
  "android_play_store_url": "https://play.google.com/store/apps/details?id=com.ehnow.eh",
  "ios_app_id": "6CL22HCV8F.com.ehnow.ca",
  "android_package_name": "com.ehnow.eh",
  "android_sha256": "D8:EC:09:FF:37:41:DC:43:34:22:72:4E:CA:1F:C3:A9:09:34:A3:04:76:83:F1:8D:01:4C:63:70:97:94:BE:1D"
}
```

### Staging (config/stage.json)
```json
{
  "environment": "staging",
  "domain": "stage.ehnw.ca",
  "distribution_id": "E12SFO751YQTOX",
  "function_name": "ehnw-staging-universal-links",
  "s3_bucket": "stage.ehnw.ca",
  "certificate_arn": "arn:aws:acm:us-east-1:870314670072:certificate/be463d69-77de-48ec-a0c4-c30f547df07c",
  "deep_link_scheme": "com.ehnow.eh",
  "ios_app_store_url": "https://apps.apple.com/ca/app/eh-canadas-social-network/id6747136970",
  "android_play_store_url": "https://play.google.com/store/apps/details?id=com.ehnow.eh",
  "ios_app_id": "6CL22HCV8F.com.ehnow.ca",
  "android_package_name": "com.ehnow.eh",
  "android_sha256": "D8:EC:09:FF:37:41:DC:43:34:22:72:4E:CA:1F:C3:A9:09:34:A3:04:76:83:F1:8D:01:4C:63:70:97:94:BE:1D"
}
```

**Note:** Both use same app IDs and URLs (testing production behavior in staging)

---

## Implementation Steps

### Phase 1: Prepare Repository (15 minutes)

**Step 1.1: Create repository structure**
- Create all directories (functions/, config/, deploy/, .well-known/, static/)
- Copy CloudFront Function code to functions/universal-links.js
- Create config files (prod.json, stage.json)
- Copy .well-known files
- Copy fallback page (index.html)
- Create .gitignore
- Create README.md

**Step 1.2: Create Lambda deployer code**
File: `deploy/lambda_deployer.py`
```python
import boto3
import json
import os
import zipfile
from io import BytesIO

def lambda_handler(event, context):
    """
    Lambda function to deploy CloudFront Function and S3 files.
    Triggered by CodePipeline.
    """

    # Get environment from CodePipeline
    job_id = event['CodePipeline.job']['id']

    # Determine environment from pipeline name
    pipeline_name = event['CodePipeline.job']['data']['pipelineContext']['pipelineName']
    environment = 'stage' if 'staging' in pipeline_name.lower() else 'prod'

    try:
        # Download artifact from CodePipeline
        artifact_location = event['CodePipeline.job']['data']['inputArtifacts'][0]['location']['s3Location']
        s3 = boto3.client('s3')

        # Download and extract artifact
        artifact_bucket = artifact_location['bucketName']
        artifact_key = artifact_location['objectKey']

        artifact_obj = s3.get_object(Bucket=artifact_bucket, Key=artifact_key)
        artifact_zip = zipfile.ZipFile(BytesIO(artifact_obj['Body'].read()))

        # Read config
        config_data = artifact_zip.read(f'config/{environment}.json')
        config = json.loads(config_data)

        # Read CloudFront Function code
        function_code = artifact_zip.read('functions/universal-links.js').decode('utf-8')

        # Update CloudFront Function
        cloudfront = boto3.client('cloudfront')

        # Get current function
        func_response = cloudfront.describe_function(
            Name=config['function_name'],
            Stage='LIVE'
        )

        # Update function
        update_response = cloudfront.update_function(
            Name=config['function_name'],
            IfMatch=func_response['ETag'],
            FunctionConfig={
                'Comment': f'Universal links for EH app - {config["environment"]}',
                'Runtime': 'cloudfront-js-1.0'
            },
            FunctionCode=function_code.encode('utf-8')
        )

        # Publish function
        publish_response = cloudfront.publish_function(
            Name=config['function_name'],
            IfMatch=update_response['ETag']
        )

        # Upload S3 files
        # 1. index.html
        index_html = artifact_zip.read('static/index.html')
        s3.put_object(
            Bucket=config['s3_bucket'],
            Key='index.html',
            Body=index_html,
            ContentType='text/html'
        )

        # 2. apple-app-site-association
        apple_config = artifact_zip.read('.well-known/apple-app-site-association')
        s3.put_object(
            Bucket=config['s3_bucket'],
            Key='.well-known/apple-app-site-association',
            Body=apple_config,
            ContentType='application/json'
        )

        # 3. assetlinks.json
        android_config = artifact_zip.read('.well-known/assetlinks.json')
        s3.put_object(
            Bucket=config['s3_bucket'],
            Key='.well-known/assetlinks.json',
            Body=android_config,
            ContentType='application/json'
        )

        # Invalidate CloudFront cache
        import time
        invalidation = cloudfront.create_invalidation(
            DistributionId=config['distribution_id'],
            InvalidationBatch={
                'Paths': {
                    'Quantity': 1,
                    'Items': ['/*']
                },
                'CallerReference': f'deploy-{int(time.time())}'
            }
        )

        # Send success to Slack
        send_slack_notification(
            environment=config['environment'],
            domain=config['domain'],
            status='SUCCESS',
            message=f"Deployed to {config['domain']}",
            pipeline_name=pipeline_name
        )

        # Notify CodePipeline of success
        codepipeline = boto3.client('codepipeline')
        codepipeline.put_job_success_result(jobId=job_id)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Deployment successful',
                'environment': environment,
                'domain': config['domain']
            })
        }

    except Exception as e:
        # Send failure to Slack
        send_slack_notification(
            environment=environment if 'environment' in locals() else 'unknown',
            domain='unknown',
            status='FAILED',
            message=str(e),
            pipeline_name=pipeline_name if 'pipeline_name' in locals() else 'unknown'
        )

        # Notify CodePipeline of failure
        codepipeline = boto3.client('codepipeline')
        codepipeline.put_job_failure_result(
            jobId=job_id,
            failureDetails={
                'message': str(e),
                'type': 'JobFailed'
            }
        )

        raise

def send_slack_notification(environment, domain, status, message, pipeline_name):
    """Send deployment notification to Slack."""
    import urllib3
    http = urllib3.PoolManager()

    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    if not webhook_url:
        print("No Slack webhook URL configured")
        return

    emoji = '✅' if status == 'SUCCESS' else '❌'
    color = 'good' if status == 'SUCCESS' else 'danger'

    payload = {
        "channel": "#engineering",
        "username": "EH Deployment Bot",
        "icon_emoji": ":rocket:",
        "attachments": [{
            "color": color,
            "title": f"{emoji} Universal Links Deployment {status}",
            "fields": [
                {
                    "title": "Environment",
                    "value": environment.upper(),
                    "short": True
                },
                {
                    "title": "Domain",
                    "value": f"https://{domain}",
                    "short": True
                },
                {
                    "title": "Pipeline",
                    "value": pipeline_name,
                    "short": False
                },
                {
                    "title": "Message",
                    "value": message,
                    "short": False
                }
            ],
            "footer": "AWS CodePipeline",
            "ts": int(time.time())
        }]
    }

    http.request(
        'POST',
        webhook_url,
        body=json.dumps(payload),
        headers={'Content-Type': 'application/json'}
    )
```

**Step 1.3: Create helper scripts**
File: `deploy/deploy_lambda.py` - Script to create Lambda from mega-agent
File: `deploy/requirements.txt` - `boto3>=1.26.0`

**Step 1.4: Commit to stage branch**
- Create initial commit
- Push to origin/stage

**Step 1.5: Create main branch from stage**
- Checkout main from stage
- Push to origin/main

---

### Phase 2: Create Lambda Function (10 minutes)

**Step 2.1: Package Lambda function**
```bash
cd /home/ec2-user/mega-agent/repos/eh-shortlink/deploy
pip install -r requirements.txt -t package/
cp lambda_deployer.py package/
cd package
zip -r ../lambda_deployer.zip .
```

**Step 2.2: Create Lambda function**
```python
import boto3

lambda_client = boto3.client('lambda')

# Read zip file
with open('lambda_deployer.zip', 'rb') as f:
    zip_content = f.read()

# Create Lambda function
response = lambda_client.create_function(
    FunctionName='eh-universal-links-deployer',
    Runtime='python3.11',
    Role='arn:aws:iam::870314670072:role/eh-lambda-deployer-role',  # Need to create
    Handler='lambda_deployer.lambda_handler',
    Code={'ZipFile': zip_content},
    Timeout=300,
    MemorySize=512,
    Environment={
        'Variables': {
            'SLACK_WEBHOOK_URL': 'https://hooks.slack.com/services/...'  # Need webhook
        }
    }
)
```

**Step 2.3: Create IAM role for Lambda**
Permissions needed:
- CloudFront: UpdateFunction, PublishFunction, DescribeFunction, CreateInvalidation
- S3: PutObject (for ehnw.ca and stage.ehnw.ca buckets)
- S3: GetObject (for CodePipeline artifact bucket)
- CodePipeline: PutJobSuccessResult, PutJobFailureResult
- Logs: CreateLogGroup, CreateLogStream, PutLogEvents

---

### Phase 3: Create Staging Pipeline (20 minutes)

**Step 3.1: Create CodePipeline (Staging)**
```python
pipeline = {
    'name': 'eh-universal-links-staging',
    'roleArn': 'arn:aws:iam::870314670072:role/eh-codepipeline-role',  # Need to create
    'stages': [
        {
            'name': 'Source',
            'actions': [{
                'name': 'GitHub',
                'actionTypeId': {
                    'category': 'Source',
                    'owner': 'AWS',
                    'provider': 'CodeStarSourceConnection',
                    'version': '1'
                },
                'configuration': {
                    'ConnectionArn': 'arn:aws:codestar-connections:...',  # GitHub connection
                    'FullRepositoryId': 'TrailMixTech/eh-shortlink',
                    'BranchName': 'stage',
                    'OutputArtifactFormat': 'CODE_ZIP'
                },
                'outputArtifacts': [{'name': 'SourceOutput'}]
            }]
        },
        {
            'name': 'Deploy',
            'actions': [{
                'name': 'DeployToStaging',
                'actionTypeId': {
                    'category': 'Invoke',
                    'owner': 'AWS',
                    'provider': 'Lambda',
                    'version': '1'
                },
                'configuration': {
                    'FunctionName': 'eh-universal-links-deployer'
                },
                'inputArtifacts': [{'name': 'SourceOutput'}]
            }]
        }
    ],
    'artifactStore': {
        'type': 'S3',
        'location': 'eh-codepipeline-artifacts'  # Need to create bucket
    }
}
```

**Step 3.2: Create GitHub connection**
- Create CodeStar Connections to GitHub
- Authorize TrailMixTech organization
- Get connection ARN

**Step 3.3: Create S3 bucket for artifacts**
- Bucket: `eh-codepipeline-artifacts`
- Region: us-east-1
- Encryption: AES256

---

### Phase 4: Test Staging Pipeline (10 minutes)

**Step 4.1: Make test commit to stage branch**
- Add comment to functions/universal-links.js
- Commit and push

**Step 4.2: Monitor pipeline**
- Watch CodePipeline console
- Check Lambda logs in CloudWatch
- Verify Slack notification

**Step 4.3: Validate deployment**
```bash
# Test staging deployment
curl -I https://stage.ehnw.ca/p/Y9R9a-ahR1O3Ew1EkKuCkg
# Should see 302 redirect

# Check function was updated
# Look at comment in CloudFront function
```

---

### Phase 5: Create Production Pipeline (20 minutes)

**Step 5.1: Create CodePipeline (Production)**
Same as staging, but:
- Name: `eh-universal-links-production`
- Branch: `main`
- No approval stage (per your requirement)

**Step 5.2: Test production pipeline**
- Merge stage to main
- Push to main
- Watch deployment
- Verify production works

---

### Phase 6: Documentation & Cleanup (10 minutes)

**Step 6.1: Update README.md**
- Deployment instructions
- How to rollback
- Troubleshooting

**Step 6.2: Test full workflow**
1. Make change to functions/universal-links.js
2. Commit to stage
3. Verify staging deployment
4. Merge to main
5. Verify production deployment
6. Check Slack notifications

---

## Resource Summary

### AWS Resources to Create

| Resource | Name/ID | Purpose |
|----------|---------|---------|
| Lambda Function | eh-universal-links-deployer | Deploys updates |
| IAM Role (Lambda) | eh-lambda-deployer-role | Lambda permissions |
| IAM Role (Pipeline) | eh-codepipeline-role | Pipeline permissions |
| S3 Bucket | eh-codepipeline-artifacts | Store pipeline artifacts |
| CodePipeline | eh-universal-links-staging | Staging deployments |
| CodePipeline | eh-universal-links-production | Production deployments |
| CodeStar Connection | GitHub-TrailMixTech | GitHub integration |
| Slack Webhook | (get from Slack) | Deployment notifications |

### Permissions Required

**Lambda Role:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudfront:UpdateFunction",
        "cloudfront:PublishFunction",
        "cloudfront:DescribeFunction",
        "cloudfront:CreateInvalidation"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::ehnw.ca/*",
        "arn:aws:s3:::stage.ehnw.ca/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::eh-codepipeline-artifacts/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "codepipeline:PutJobSuccessResult",
        "codepipeline:PutJobFailureResult"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

**CodePipeline Role:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::eh-codepipeline-artifacts/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "codestar-connections:UseConnection"
      ],
      "Resource": "arn:aws:codestar-connections:*:*:connection/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": "arn:aws:lambda:us-east-1:870314670072:function:eh-universal-links-deployer"
    }
  ]
}
```

---

## Deployment Workflow

### Making Changes

**Option 1: Deploy to staging only**
```bash
git checkout stage
# Make changes
git add .
git commit -m "Update CloudFront function"
git push origin stage
# AWS automatically deploys to stage.ehnw.ca
```

**Option 2: Deploy to staging, then production**
```bash
git checkout stage
# Make changes
git add .
git commit -m "Update CloudFront function"
git push origin stage
# Wait for staging deployment, test

git checkout main
git merge stage
git push origin main
# AWS automatically deploys to ehnw.ca
```

**Option 3: Hotfix to production**
```bash
git checkout main
# Make urgent fix
git add .
git commit -m "Hotfix: urgent bug"
git push origin main
# AWS automatically deploys to ehnw.ca

# Then sync back to stage
git checkout stage
git merge main
git push origin stage
```

---

## Rollback Strategy

### Automatic Rollback
CodePipeline will fail deployment if Lambda returns error. Previous version stays active.

### Manual Rollback

**Option 1: Revert commit and redeploy**
```bash
git revert HEAD
git push origin main
# AWS will deploy previous version
```

**Option 2: Roll back CloudFront Function manually**
```python
# From mega-agent
cloudfront = boto3.client('cloudfront')

# Get previous function version
# Update function back to previous code
# Publish function
```

**Option 3: Emergency disable function**
```python
# Disassociate function from distribution
# Falls back to S3 origin (shows fallback page for all requests)
```

---

## Testing Strategy

### Pre-Deployment Testing (Local)
1. Review changes in PR
2. Validate JSON config files
3. Check function code syntax

### Staging Testing (Automated)
1. Push to stage branch
2. AWS auto-deploys
3. Run automated tests:
   - `curl` tests for redirects
   - Verify .well-known files
   - Check Slack notification

### Production Validation (Manual)
1. Push to main branch
2. AWS auto-deploys
3. Manual verification:
   - Test production links
   - Monitor for errors
   - Check Slack notification

---

## Cost Estimate

### One-Time Setup
- Lambda function: $0
- IAM roles: $0
- CodePipeline: $1/pipeline/month
- S3 bucket: $0.23/month (storage)

### Per Deployment
- Lambda execution: ~$0.0001 per invocation (~5 seconds)
- CloudFront invalidation: First 1000/month free
- S3 PUT requests: $0.005 per 1000 requests
- CodePipeline: Included in monthly fee

**Monthly cost:** ~$2-3 for both pipelines with light deployments

---

## Timeline

| Phase | Time | Description |
|-------|------|-------------|
| Phase 1 | 15 min | Prepare repository structure |
| Phase 2 | 10 min | Create Lambda function |
| Phase 3 | 20 min | Create staging pipeline |
| Phase 4 | 10 min | Test staging pipeline |
| Phase 5 | 20 min | Create production pipeline |
| Phase 6 | 10 min | Documentation & cleanup |
| **Total** | **~85 minutes** | End-to-end implementation |

---

## Success Criteria

### Staging Pipeline ✓
- [ ] Push to `stage` branch triggers deployment
- [ ] Lambda updates CloudFront Function
- [ ] S3 files updated
- [ ] Cache invalidated
- [ ] Slack notification sent
- [ ] Deployment succeeds within 2 minutes
- [ ] stage.ehnw.ca serves updated code

### Production Pipeline ✓
- [ ] Push to `main` branch triggers deployment
- [ ] Lambda updates CloudFront Function
- [ ] S3 files updated
- [ ] Cache invalidated
- [ ] Slack notification sent
- [ ] Deployment succeeds within 2 minutes
- [ ] ehnw.ca serves updated code

### Rollback ✓
- [ ] Failed deployment doesn't break site
- [ ] Can revert to previous version
- [ ] Rollback completes within 5 minutes

---

## Next Steps

Ready to proceed with implementation. Confirm:

1. ✅ Repository structure approved
2. ✅ Environment parameters complete
3. ✅ No approval gate for production
4. ✅ Slack notifications to #engineering
5. ✅ Deploy staging first, test, then production

**Ready to start Phase 1?**
