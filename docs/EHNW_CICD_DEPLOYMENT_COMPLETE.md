# EH Universal Links CI/CD Deployment - COMPLETE ✅

**Date:** 2026-01-12
**Status:** Infrastructure deployed, GitHub connection requires manual approval

---

## ✅ What's Been Deployed

### 1. GitHub Repository
- **Repository:** TrailMixTech/eh-shortlink
- **Branches:**
  - `stage` - Auto-deploys to stage.ehnw.ca
  - `main` - Auto-deploys to ehnw.ca
- **URL:** https://github.com/TrailMixTech/eh-shortlink

### 2. Lambda Function
- **Name:** `eh-universal-links-deployer`
- **Runtime:** Python 3.9
- **Timeout:** 300 seconds (5 minutes)
- **Memory:** 512 MB
- **Role:** `eh-universal-links-deployer-role`
- **ARN:** `arn:aws:lambda:us-east-1:870314670072:function:eh-universal-links-deployer`
- **Environment Variables:**
  - `SLACK_WEBHOOK_URL`: [REDACTED - stored in GitHub secrets]

**What it does:**
1. Downloads code from CodePipeline artifact
2. Updates CloudFront Function code
3. Publishes CloudFront Function
4. Uploads S3 files (.well-known, index.html)
5. Creates CloudFront cache invalidation
6. Sends Slack notification to #devops
7. Reports success/failure to CodePipeline

### 3. IAM Roles

**Lambda Role:** `eh-universal-links-deployer-role`
- CloudFront Function management (describe, update, publish)
- CloudFront cache invalidation
- S3 bucket access (ehnw.ca, stage.ehnw.ca)
- CodePipeline artifact access
- CodePipeline job status reporting
- CloudWatch Logs

**CodePipeline Role:** `eh-codepipeline-role`
- S3 artifact bucket access
- GitHub connection via CodeStar
- Lambda function invocation

### 4. S3 Bucket
- **Name:** `eh-codepipeline-artifacts`
- **Purpose:** Stores pipeline artifacts
- **Region:** us-east-1

### 5. GitHub Connection
- **Name:** `eh-shortlink-github`
- **ARN:** `arn:aws:codestar-connections:us-east-1:870314670072:connection/aad319c1-6c6f-4745-b989-b82c15e90de3`
- **Status:** ⚠️ **PENDING - REQUIRES MANUAL APPROVAL**

### 6. CodePipelines

**Staging Pipeline:** `eh-universal-links-staging`
- **Branch:** `stage`
- **Deploys to:** stage.ehnw.ca
- **Distribution:** E12SFO751YQTOX
- **Function:** ehnw-staging-universal-links

**Production Pipeline:** `eh-universal-links-production`
- **Branch:** `main`
- **Deploys to:** ehnw.ca
- **Distribution:** E28JUE6Q00L6TK
- **Function:** ehnw-universal-links

---

## 🔧 REQUIRED MANUAL STEP

**You must complete the GitHub connection before the pipelines will work.**

### Complete GitHub Connection

1. **Go to AWS Console:**
   ```
   https://us-east-1.console.aws.amazon.com/codesuite/settings/connections
   ```

2. **Find connection:**
   - Name: `eh-shortlink-github`
   - Status: "Pending"

3. **Click "Update pending connection"**

4. **Authorize with GitHub:**
   - Click "Connect to GitHub"
   - Authenticate with your GitHub account
   - Select "TrailMixTech" organization
   - Grant access to "eh-shortlink" repository
   - Click "Connect"

5. **Verify:**
   - Status should change to "Available"
   - Connection ARN: `arn:aws:codestar-connections:us-east-1:870314670072:connection/aad319c1-6c6f-4745-b989-b82c15e90de3`

---

## 🧪 Testing the Pipelines

### Test Staging Pipeline

Once the GitHub connection is approved:

1. **Make a test change:**
   ```bash
   cd /home/ec2-user/mega-agent/repos/eh-shortlink
   git checkout stage

   # Add a comment to the CloudFront Function
   echo "// Test deployment $(date)" >> functions/universal-links.js

   git add functions/universal-links.js
   git commit -m "Test: Trigger staging deployment"
   git push origin stage
   ```

2. **Watch the pipeline:**
   - Go to: https://console.aws.amazon.com/codesuite/codepipeline/pipelines/eh-universal-links-staging/view
   - Should see execution start within seconds
   - Source stage pulls from GitHub
   - Deploy stage invokes Lambda
   - Takes 2-3 minutes total

3. **Check Slack:**
   - Notification should appear in #devops
   - Shows deployment status (SUCCESS or FAILED)
   - Includes environment, domain, distribution ID

4. **Verify deployment:**
   ```bash
   # Check CloudFront Function was updated
   curl -I https://stage.ehnw.ca/p/test

   # Should return deep link redirect for mobile
   # Should return HTML fallback for desktop
   ```

### Test Production Pipeline

After staging works:

1. **Merge to main:**
   ```bash
   cd /home/ec2-user/mega-agent/repos/eh-shortlink
   git checkout main
   git merge stage
   git push origin main
   ```

2. **Watch pipeline:**
   - Go to: https://console.aws.amazon.com/codesuite/codepipeline/pipelines/eh-universal-links-production/view

3. **Check Slack + verify:**
   - Same as staging, but for ehnw.ca

---

## 📊 Monitoring

### CloudWatch Logs
- **Lambda Logs:** `/aws/lambda/eh-universal-links-deployer`
- View at: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups/log-group/$252Faws$252Flambda$252Feh-universal-links-deployer

### CodePipeline Console
- **Staging:** https://console.aws.amazon.com/codesuite/codepipeline/pipelines/eh-universal-links-staging/view
- **Production:** https://console.aws.amazon.com/codesuite/codepipeline/pipelines/eh-universal-links-production/view

### Slack Notifications
- **Channel:** #devops
- **On every deployment:**
  - Environment (STAGING or PRODUCTION)
  - Domain (stage.ehnw.ca or ehnw.ca)
  - Status (SUCCESS or FAILED)
  - Distribution ID
  - Pipeline name
  - Error message (if failed)

---

## 🔄 Deployment Workflow

### Normal Development Flow

1. **Make changes:**
   ```bash
   cd /home/ec2-user/mega-agent/repos/eh-shortlink
   git checkout stage

   # Edit files
   vim functions/universal-links.js

   git add .
   git commit -m "Description of changes"
   git push origin stage
   ```

2. **AWS automatically:**
   - Detects push to `stage` branch
   - Triggers `eh-universal-links-staging` pipeline
   - Downloads code
   - Invokes Lambda deployer
   - Updates CloudFront Function
   - Uploads S3 files
   - Invalidates CloudFront cache
   - Sends Slack notification

3. **Test on staging:**
   ```bash
   curl -A "Mozilla/5.0 (iPhone)" -I https://stage.ehnw.ca/p/test
   ```

4. **Promote to production:**
   ```bash
   git checkout main
   git merge stage
   git push origin main
   # AWS auto-deploys to ehnw.ca
   ```

### Hotfix Flow

1. **Direct to main:**
   ```bash
   git checkout main
   # Make urgent fix
   git add .
   git commit -m "Hotfix: description"
   git push origin main
   ```

2. **Sync back to stage:**
   ```bash
   git checkout stage
   git merge main
   git push origin stage
   ```

---

## 🛠️ Troubleshooting

### Pipeline Not Triggering

**Problem:** Push to GitHub but pipeline doesn't start

**Solution:**
1. Check GitHub connection status in AWS Console
2. Verify connection ARN in pipeline configuration
3. Check CodePipeline execution history for errors

### Lambda Deployment Fails

**Problem:** Pipeline starts but Lambda fails

**Solution:**
1. Check CloudWatch Logs: `/aws/lambda/eh-universal-links-deployer`
2. Common issues:
   - IAM permissions missing
   - CloudFront Function code syntax error
   - S3 bucket permissions
   - Invalid config in `config/prod.json` or `config/stage.json`

### Links Don't Work After Deployment

**Problem:** Deployment succeeds but links broken

**Solution:**
1. Wait 2-3 minutes for CloudFront cache invalidation
2. Test with curl to bypass browser cache
3. Check CloudFront Function code was actually updated:
   ```bash
   AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... AWS_DEFAULT_REGION=us-east-1 \
     aws cloudfront describe-function \
     --name ehnw-staging-universal-links \
     --stage LIVE
   ```

### No Slack Notification

**Problem:** Deployment completes but no Slack message

**Solution:**
1. Check Lambda environment variable `SLACK_WEBHOOK_URL`
2. Verify webhook URL is valid
3. Check Lambda logs for Slack errors
4. Deployment will still succeed even if Slack fails

---

## 📝 What's in the Repository

### Directory Structure
```
eh-shortlink/
├── functions/
│   └── universal-links.js          # CloudFront Function (URL → deep link)
├── config/
│   ├── prod.json                   # Production configuration
│   └── stage.json                  # Staging configuration
├── deploy/
│   ├── lambda_deployer.py          # Lambda deployment function
│   └── requirements.txt            # Python dependencies
├── .well-known/
│   ├── apple-app-site-association  # iOS universal links config
│   └── assetlinks.json             # Android app links config
├── static/
│   └── index.html                  # Fallback page (→ App Store)
├── .gitignore
└── README.md
```

### Key Files

**functions/universal-links.js**
- CloudFront Function that runs at edge
- Transforms URLs to deep links
- Detects mobile vs desktop
- Decodes Base64URL UUIDs
- Preserves query strings

**deploy/lambda_deployer.py**
- Invoked by CodePipeline
- Reads config based on pipeline name (staging/production)
- Updates CloudFront Function
- Uploads S3 files
- Creates cache invalidation
- Sends Slack notifications
- Reports status to CodePipeline

**config/prod.json & stage.json**
- Environment-specific settings
- CloudFront distribution ID
- CloudFront function name
- S3 bucket name
- Deep link scheme
- App Store URLs
- App IDs

---

## 💰 Cost Estimate

**Monthly costs:**
- CodePipeline: $1/pipeline × 2 = **$2.00**
- Lambda: ~100 executions/month × $0.002 = **$0.20**
- S3 (artifacts): Storage + requests = **$0.50**
- CloudFront Function: Included in existing distribution
- CloudWatch Logs: ~1 GB/month = **$0.50**

**Total:** ~**$3.20/month**

---

## 🎯 Success Criteria

- [x] Repository created and pushed to GitHub
- [x] Lambda function deployed and configured
- [x] IAM roles created with proper permissions
- [x] S3 artifact bucket created
- [x] GitHub connection created (pending approval)
- [x] Staging pipeline created
- [x] Production pipeline created
- [ ] GitHub connection approved ⚠️ **MANUAL STEP REQUIRED**
- [ ] Staging pipeline tested
- [ ] Production pipeline tested
- [ ] Slack notifications verified

---

## 📚 Related Documentation

- [Repository README](/home/ec2-user/mega-agent/repos/eh-shortlink/README.md)
- [CI/CD Implementation Plan](/home/ec2-user/mega-agent2/docs/EHNW_CICD_IMPLEMENTATION_PLAN.md)
- [Universal Links Summary](/home/ec2-user/mega-agent2/docs/EHNW_UNIVERSAL_LINKS_SUMMARY.md)
- [Staging Implementation](/home/ec2-user/mega-agent2/docs/EHNW_STAGING_IMPLEMENTATION_COMPLETE.md)

---

**🎉 Infrastructure is ready! Complete the GitHub connection to start deploying.**
