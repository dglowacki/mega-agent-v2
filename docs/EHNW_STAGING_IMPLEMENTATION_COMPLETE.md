# stage.ehnw.ca Universal Links - Implementation Complete ✅

**Date:** 2026-01-12
**Status:** LIVE AND VALIDATED
**Implementation Time:** ~15 minutes (faster than estimated!)

---

## Summary

Staging environment for universal links at **stage.ehnw.ca** is now live and fully operational. All validation tests pass successfully.

---

## Infrastructure Deployed

### 1. SSL Certificate
- **ARN:** arn:aws:acm:us-east-1:870314670072:certificate/be463d69-77de-48ec-a0c4-c30f547df07c
- **Domain:** stage.ehnw.ca
- **Status:** ISSUED ✅
- **Validation:** DNS (completed in 30 seconds)

### 2. S3 Bucket (stage.ehnw.ca)
- **Bucket:** stage.ehnw.ca
- **Website hosting:** Enabled
- **Endpoint:** stage.ehnw.ca.s3-website-us-east-1.amazonaws.com
- **Files uploaded:**
  - index.html (fallback page)
  - .well-known/apple-app-site-association
  - .well-known/assetlinks.json

### 3. CloudFront Distribution
- **Distribution ID:** E12SFO751YQTOX
- **Domain:** d122g7lyv88tn3.cloudfront.net
- **Status:** Deployed ✅
- **Origin:** stage.ehnw.ca.s3-website-us-east-1.amazonaws.com
- **Certificate:** arn:aws:acm:us-east-1:870314670072:certificate/be463d69-77de-48ec-a0c4-c30f547df07c
- **Comment:** Universal links for EH app - STAGING

### 4. CloudFront Function
- **Name:** ehnw-staging-universal-links
- **ARN:** arn:aws:cloudfront::870314670072:function/ehnw-staging-universal-links
- **Runtime:** cloudfront-js-1.0
- **Event:** viewer-request
- **Status:** LIVE ✅
- **Code:** Same as production (mobile detection, UUID decoding, query string pass-through)

### 5. DNS Record
- **Type:** CNAME
- **Name:** stage.ehnw.ca
- **Target:** d122g7lyv88tn3.cloudfront.net
- **TTL:** 300 seconds (5 minutes)
- **Status:** Propagated ✅

---

## Configuration

Staging uses **identical configuration to production:**
- ✅ Same deep link scheme: `com.ehnow.eh://`
- ✅ Same App Store URLs (iOS & Android)
- ✅ Same app IDs in .well-known files
- ✅ Same Android SHA256 fingerprint
- ✅ Same CloudFront Function code

This ensures staging accurately tests production behavior.

---

## Validation Results (All Passing ✅)

### Test 1: DNS Resolution ✅
- stage.ehnw.ca resolves to d122g7lyv88tn3.cloudfront.net
- CNAME record working correctly

### Test 2: Apple Universal Links ✅
- URL: https://stage.ehnw.ca/.well-known/apple-app-site-association
- Status: 200 OK
- Content-Type: application/json
- AppID: 6CL22HCV8F.com.ehnow.ca

### Test 3: Android App Links ✅
- URL: https://stage.ehnw.ca/.well-known/assetlinks.json
- Status: 200 OK
- Content-Type: application/json
- Package: com.ehnow.eh

### Test 4: Desktop Fallback ✅
- Desktop browsers receive HTML page
- JavaScript redirects to App Store

### Test 5: Mobile Redirect ✅
- Input: https://stage.ehnw.ca/p/Y9R9a-ahR1O3Ew1EkKuCkg
- Output: com.ehnow.eh://post/63d47d6b-e6a1-4753-b713-0d4490ab8292
- Status: 302 redirect

### Test 6: Query String Pass-Through ✅
- Input: https://stage.ehnw.ca/p/Y9R9a-ahR1O3Ew1EkKuCkg?source=email
- Query params preserved correctly

### Test 7: Case Insensitivity ✅
- /P/ and /p/ both work correctly

### Test 8: User Path (Multi-Segment) ✅
- Input: https://stage.ehnw.ca/u/john/profile
- Output: com.ehnow.eh://user/john/profile
- All segments preserved

---

## Resource Isolation

**Staging is completely isolated from production:**

| Resource | Production | Staging |
|----------|-----------|---------|
| Domain | ehnw.ca | stage.ehnw.ca |
| S3 Bucket | ehnw.ca | stage.ehnw.ca |
| CloudFront Dist | E28JUE6Q00L6TK | E12SFO751YQTOX |
| CloudFront Func | ehnw-universal-links | ehnw-staging-universal-links |
| Certificate | 31baf6a5-... | be463d69-... |
| DNS Record | A ALIAS | CNAME |

**Zero shared resources** - changes to staging never affect production.

---

## Testing Workflow

### Making Changes to Staging

1. **Update staging function code**
   ```python
   # Edit /tmp/ehnw-universal-links-function-staging.js
   # Then update function
   cloudfront.update_function(
       Name='ehnw-staging-universal-links',
       FunctionCode=new_code
   )
   cloudfront.publish_function(Name='ehnw-staging-universal-links')
   ```

2. **Invalidate staging cache**
   ```python
   cloudfront.create_invalidation(
       DistributionId='E12SFO751YQTOX',
       InvalidationBatch={'Paths': {'Quantity': 1, 'Items': ['/*']}}
   )
   ```

3. **Test on staging**
   ```bash
   curl -A "iPhone" -I https://stage.ehnw.ca/p/Y9R9a-ahR1O3Ew1EkKuCkg
   ```

4. **If good, replicate to production**
   ```python
   # Update production function with same code
   cloudfront.update_function(
       Name='ehnw-universal-links',
       FunctionCode=new_code
   )
   ```

### Test Links

**Staging URLs to test:**
- Post: https://stage.ehnw.ca/p/Y9R9a-ahR1O3Ew1EkKuCkg
- Event: https://stage.ehnw.ca/e/Y9R9a-ahR1O3Ew1EkKuCkg
- Group: https://stage.ehnw.ca/g/Y9R9a-ahR1O3Ew1EkKuCkg
- User: https://stage.ehnw.ca/u/john/profile
- Root: https://stage.ehnw.ca/

**Production URLs (for comparison):**
- Post: https://ehnw.ca/p/Y9R9a-ahR1O3Ew1EkKuCkg

---

## Common Operations

### Check Staging Distribution Status
```python
from integrations.aws_client import AWSClient
aws = AWSClient()
cloudfront = aws.get_client('cloudfront')

dist = cloudfront.get_distribution(Id='E12SFO751YQTOX')
print(f"Status: {dist['Distribution']['Status']}")
print(f"Domain: {dist['Distribution']['DomainName']}")
```

### Update Staging Function
```python
# Read new code
with open('/tmp/new_function.js', 'r') as f:
    code = f.read()

# Get current function
func = cloudfront.describe_function(
    Name='ehnw-staging-universal-links',
    Stage='LIVE'
)

# Update
cloudfront.update_function(
    Name='ehnw-staging-universal-links',
    IfMatch=func['ETag'],
    FunctionConfig={
        'Comment': 'Updated staging function',
        'Runtime': 'cloudfront-js-1.0'
    },
    FunctionCode=code.encode('utf-8')
)

# Publish
cloudfront.publish_function(
    Name='ehnw-staging-universal-links',
    IfMatch=new_etag
)
```

### Invalidate Staging Cache
```python
import time

cloudfront.create_invalidation(
    DistributionId='E12SFO751YQTOX',
    InvalidationBatch={
        'Paths': {
            'Quantity': 1,
            'Items': ['/*']
        },
        'CallerReference': f'staging-{int(time.time())}'
    }
)
```

### Compare Staging vs Production
```bash
# Test same URL on both
echo "Production:"
curl -A "iPhone" -I https://ehnw.ca/p/Y9R9a-ahR1O3Ew1EkKuCkg | grep -i location

echo "Staging:"
curl -A "iPhone" -I https://stage.ehnw.ca/p/Y9R9a-ahR1O3Ew1EkKuCkg | grep -i location
```

---

## Cost Estimate

### Monthly Costs (Staging)
- **SSL Certificate:** $0 (ACM is free)
- **S3 Storage:** < $0.01/month (few KB)
- **S3 Requests:** < $0.01/month
- **CloudFront Data Transfer:** ~$0.085 per GB
- **CloudFront Requests:** ~$0.01 per 10,000 requests
- **CloudFront Function:** $0.10 per 1M invocations
- **Route53:** $0 (CNAME record, no additional cost)

**Estimated total for staging:** < $1/month (assuming light testing traffic)

---

## Rollback / Teardown

If you need to remove staging:

### Quick Disable (keep resources, disable function)
```python
# Disassociate function from distribution
# Staging will continue serving static content without URL transformation
```

### Full Teardown
```python
from integrations.aws_client import AWSClient
aws = AWSClient()

# 1. Delete DNS CNAME
route53 = aws.get_client('route53')
route53.change_resource_record_sets(
    HostedZoneId='Z08230981PLMAO1820UME',
    ChangeBatch={
        'Changes': [{
            'Action': 'DELETE',
            'ResourceRecordSet': {
                'Name': 'stage.ehnw.ca',
                'Type': 'CNAME',
                'TTL': 300,
                'ResourceRecords': [{'Value': 'd122g7lyv88tn3.cloudfront.net'}]
            }
        }]
    }
)

# 2. Disable CloudFront distribution
# (must disable before deleting)

# 3. Delete CloudFront function
cloudfront = aws.get_client('cloudfront')
cloudfront.delete_function(Name='ehnw-staging-universal-links')

# 4. Empty and delete S3 bucket
s3 = aws.get_client('s3')
# ... empty bucket first ...
s3.delete_bucket(Bucket='stage.ehnw.ca')

# 5. Delete certificate (optional)
acm = aws.get_client('acm')
acm.delete_certificate(
    CertificateArn='arn:aws:acm:us-east-1:870314670072:certificate/be463d69-77de-48ec-a0c4-c30f547df07c'
)
```

---

## Implementation Timeline

| Step | Time |
|------|------|
| SSL Certificate request & validation | 1 min |
| S3 bucket creation & config | 1 min |
| Upload staging files | 1 min |
| CloudFront distribution creation | 4 min |
| CloudFront Function creation | 1 min |
| Function association & deployment | 3 min |
| DNS CNAME creation | 1 min |
| DNS propagation | 1 min |
| Validation testing | 2 min |
| **Total** | **~15 minutes** |

Much faster than the estimated 50-55 minutes!

---

## Key Achievements

✅ **Complete isolation** - Zero risk to production
✅ **Fast implementation** - Done in 15 minutes
✅ **Identical configuration** - Accurate production testing
✅ **All tests passing** - Fully functional staging environment
✅ **Low cost** - < $1/month for testing
✅ **Easy workflow** - Simple to test changes before prod
✅ **Full documentation** - Complete operational guide

---

## Next Steps

Staging is ready for use! You can now:

1. **Test changes safely** - Make function updates on staging first
2. **Share with team** - Give QA team stage.ehnw.ca links to test
3. **Debug issues** - Use staging for troubleshooting without affecting users
4. **Validate updates** - Confirm changes work before pushing to prod
5. **Experiment freely** - Try new features without risk

---

## Files Created

### AWS Resources
- ACM Certificate: be463d69-77de-48ec-a0c4-c30f547df07c
- S3 Bucket: stage.ehnw.ca
- CloudFront Distribution: E12SFO751YQTOX
- CloudFront Function: ehnw-staging-universal-links
- Route53 CNAME: stage.ehnw.ca

### Documentation
- /home/ec2-user/mega-agent2/docs/EHNW_STAGING_UNIVERSAL_LINKS_PLAN.md
- /home/ec2-user/mega-agent2/docs/EHNW_STAGING_IMPLEMENTATION_COMPLETE.md (this file)
- /tmp/validation_tests_staging.sh

---

## Support

**Staging URL:** https://stage.ehnw.ca/

**Production URL (for reference):** https://ehnw.ca/

**CloudWatch Logs:** Check CloudFront function logs for debugging

**Questions or issues?** All resources are tagged with "STAGING" for easy identification.

---

## Implementation Complete! 🎉

Staging environment is live and ready for testing. All infrastructure deployed, validated, and documented.
