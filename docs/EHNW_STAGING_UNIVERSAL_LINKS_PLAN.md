# stage.ehnw.ca Universal Links - Implementation Plan

**Date:** 2026-01-12
**Status:** PLANNING
**Goal:** Create completely separate staging environment for universal links

---

## Overview

Create a staging environment at **stage.ehnw.ca** that mirrors the production setup but is completely isolated. This will allow testing universal links changes without affecting production.

---

## Key Requirements

✅ **Completely separate from production**
- Separate S3 bucket
- Separate CloudFront distribution
- Separate CloudFront Function
- Separate DNS record
- No shared resources with prod

✅ **Subdomain: stage.ehnw.ca**

✅ **Mirrors production functionality**
- Same URL patterns (/p/, /e/, /g/, /u/)
- Same UUID decoding
- Same mobile detection
- Same fallback behavior

---

## Architecture

```
stage.ehnw.ca (DNS CNAME)
    ↓
CloudFront Distribution (NEW - staging)
    ↓
CloudFront Function (NEW - ehnw-staging-universal-links)
    ↓
S3 Bucket (NEW - stage.ehnw.ca)
    ↓
.well-known files + fallback page
```

---

## Resources to Create

### 1. SSL Certificate
**Option A: Add to existing certificate (RECOMMENDED)**
- Current cert: `arn:aws:acm:us-east-1:870314670072:certificate/31baf6a5-c39b-4e4c-a5f5-7dee5b7a4adb`
- Add `stage.ehnw.ca` as Subject Alternative Name (SAN)
- Requires certificate reissue and DNS validation
- **Cost:** $0 (included with existing cert)

**Option B: Create new certificate**
- New cert just for `stage.ehnw.ca`
- Requires DNS validation
- **Cost:** $0 (ACM is free)

**RECOMMENDATION:** Option A - add to existing cert

### 2. S3 Bucket
**Name:** `stage.ehnw.ca`
**Configuration:**
- Static website hosting enabled
- Index document: `index.html`
- Error document: `index.html` (same as prod)
- Public read access via bucket policy
- Region: us-east-1

**Files to upload:**
- `/index.html` - fallback page with staging app store URLs
- `/.well-known/apple-app-site-association` - staging app config
- `/.well-known/assetlinks.json` - staging app config

### 3. CloudFront Distribution
**Name/Comment:** `Universal links for EH app - STAGING`
**Configuration:**
- Origin: `stage.ehnw.ca.s3-website-us-east-1.amazonaws.com`
- Alternate domain: `stage.ehnw.ca`
- Certificate: (from step 1)
- Viewer protocol: Redirect HTTP to HTTPS
- Allowed methods: GET, HEAD
- Cache policy: CachingOptimized (or custom with no-cache for redirects)

**Estimated deployment time:** 10-15 minutes

### 4. CloudFront Function
**Name:** `ehnw-staging-universal-links`
**Runtime:** `cloudfront-js-1.0`
**Event type:** `viewer-request`

**Code:** Same as production but with staging-specific deep link scheme

**Key differences from prod:**
- Deep link scheme: `com.ehnow.eh.staging://` OR `com.ehnow.eh://` (decision needed)
- Function name includes "staging" for clarity

### 5. DNS Record
**Type:** CNAME
**Name:** `stage.ehnw.ca`
**Value:** `[staging-distribution-id].cloudfront.net`
**TTL:** 300 (5 minutes - lower for easier testing)
**Hosted Zone:** Z08230981PLMAO1820UME (ehnw.ca)

**Note:** Using CNAME (not ALIAS) since this is a subdomain

---

## Configuration Decisions Needed

### Decision 1: Deep Link Scheme
**Question:** Should staging use a different deep link scheme?

**Option A: Separate staging scheme (RECOMMENDED for testing)**
- Production: `com.ehnow.eh://post/123`
- Staging: `com.ehnow.eh.staging://post/123`
- **Pros:** Can test without affecting prod app
- **Cons:** Requires separate staging app build

**Option B: Same scheme as production**
- Both use: `com.ehnow.eh://post/123`
- **Pros:** Tests exact production behavior
- **Cons:** Staging links might open prod app

**RECOMMENDATION:** Option A if staging app exists, Option B otherwise

### Decision 2: App Store URLs
**Question:** Where should fallback page redirect on staging?

**Option A: TestFlight (if staging uses TestFlight)**
- iOS: `https://testflight.apple.com/join/[CODE]`
- Android: Still Play Store or separate staging APK?

**Option B: Same as production**
- iOS: `https://apps.apple.com/ca/app/eh-canadas-social-network/id6747136970`
- Android: `https://play.google.com/store/apps/details?id=com.ehnow.eh`

**RECOMMENDATION:** Option A if TestFlight available, Option B otherwise

### Decision 3: App IDs in .well-known files
**Question:** Do staging iOS/Android apps have different IDs?

**For apple-app-site-association:**
- Production uses: `6CL22HCV8F.com.ehnow.ca`
- Staging uses: `6CL22HCV8F.com.ehnow.ca.staging` OR same?

**For assetlinks.json:**
- Production uses: `com.ehnow.eh` with specific SHA256
- Staging uses: `com.ehnow.eh.staging` OR same with different SHA256?

**RECOMMENDATION:** Use same IDs unless separate staging apps exist

---

## Implementation Steps

### Prerequisites Check
```python
# 1. Check current certificate
aws.describe_certificate('arn:aws:acm:us-east-1:870314670072:certificate/31baf6a5-c39b-4e4c-a5f5-7dee5b7a4adb')

# 2. Verify DNS hosted zone
aws.list_hosted_zones() # Confirm Z08230981PLMAO1820UME exists
```

### Step 1: Update SSL Certificate (~10 minutes)
```python
# Add stage.ehnw.ca to existing certificate
# This requires certificate reissue
aws.request_certificate_validation(
    domain='stage.ehnw.ca',
    certificate_arn='arn:aws:acm:us-east-1:870314670072:certificate/31baf6a5-c39b-4e4c-a5f5-7dee5b7a4adb'
)

# Add DNS validation record when prompted
# Wait for validation
```

**Alternative if adding to cert not supported:**
```python
# Request new certificate for stage.ehnw.ca
aws.request_certificate(
    domain='stage.ehnw.ca',
    validation_method='DNS'
)
```

### Step 2: Create S3 Bucket (~2 minutes)
```python
aws.create_s3_bucket(
    bucket='stage.ehnw.ca',
    region='us-east-1'
)

aws.configure_s3_website(
    bucket='stage.ehnw.ca',
    index_document='index.html',
    error_document='index.html'
)
```

### Step 3: Upload Staging Files (~2 minutes)

**File 1: index.html**
```python
# Create fallback page with staging app URLs
aws.upload_to_s3(
    file_path='/tmp/stage_index.html',
    bucket='stage.ehnw.ca',
    key='index.html'
)
```

**File 2: apple-app-site-association**
```python
aws.upload_with_content_type(
    bucket='stage.ehnw.ca',
    key='.well-known/apple-app-site-association',
    content=staging_apple_config,
    content_type='application/json'
)
```

**File 3: assetlinks.json**
```python
aws.upload_with_content_type(
    bucket='stage.ehnw.ca',
    key='.well-known/assetlinks.json',
    content=staging_android_config,
    content_type='application/json'
)
```

### Step 4: Create CloudFront Distribution (~15 minutes)
```python
staging_dist = aws.create_cloudfront_distribution(
    origin_domain='stage.ehnw.ca.s3-website-us-east-1.amazonaws.com',
    aliases=['stage.ehnw.ca'],
    certificate_arn='[cert-arn-from-step-1]',
    comment='Universal links for EH app - STAGING'
)

# Wait for deployment (InProgress → Deployed)
```

### Step 5: Create CloudFront Function (~5 minutes)
```python
# Create staging function with staging deep link scheme
cloudfront.create_function(
    Name='ehnw-staging-universal-links',
    FunctionConfig={
        'Comment': 'Universal links redirect for EH app - STAGING',
        'Runtime': 'cloudfront-js-1.0'
    },
    FunctionCode=staging_function_code
)

# Publish function
cloudfront.publish_function(
    Name='ehnw-staging-universal-links'
)
```

### Step 6: Associate Function with Distribution (~5 minutes)
```python
# Add function to staging distribution
aws.update_distribution_function_association(
    distribution_id=staging_dist['id'],
    function_arn='arn:aws:cloudfront::870314670072:function/ehnw-staging-universal-links',
    event_type='viewer-request'
)

# Wait for deployment
```

### Step 7: Create DNS CNAME Record (~2 minutes)
```python
aws.create_cname_record(
    hosted_zone_id='Z08230981PLMAO1820UME',
    name='stage.ehnw.ca',
    value=staging_dist['domain'],  # e.g., 'd123abc.cloudfront.net'
    ttl=300
)

# Wait for DNS propagation (5-10 minutes)
```

### Step 8: Validation (~5 minutes)
```bash
# Test .well-known files
curl -I https://stage.ehnw.ca/.well-known/apple-app-site-association

# Test redirects (mobile)
curl -A "iPhone" -I https://stage.ehnw.ca/p/Y9R9a-ahR1O3Ew1EkKuCkg

# Test fallback (desktop)
curl https://stage.ehnw.ca/p/Y9R9a-ahR1O3Ew1EkKuCkg

# Test root
curl https://stage.ehnw.ca/
```

---

## Resource Summary

### New AWS Resources
| Resource | Name/ID | Purpose |
|----------|---------|---------|
| S3 Bucket | stage.ehnw.ca | Static website hosting |
| CloudFront Distribution | [TBD] | CDN + function execution |
| CloudFront Function | ehnw-staging-universal-links | URL transformation |
| Route53 CNAME | stage.ehnw.ca | DNS routing |
| ACM Certificate | Updated or new | SSL/TLS |

### Isolation from Production
✅ Separate S3 bucket (stage.ehnw.ca vs ehnw.ca)
✅ Separate CloudFront distribution
✅ Separate CloudFront Function
✅ Separate DNS record
✅ No shared origin or cache
✅ Changes to staging never affect prod

---

## Testing Strategy

### Staging Testing Workflow
1. Make changes to staging function code
2. Update `ehnw-staging-universal-links` function
3. Invalidate staging CloudFront cache
4. Test on stage.ehnw.ca
5. If good, replicate changes to prod

### Test Cases
- [ ] Desktop browser → App Store fallback
- [ ] Mobile browser → Deep link redirect
- [ ] All path types (/p/, /e/, /g/, /u/)
- [ ] Query string pass-through
- [ ] Case insensitivity
- [ ] Invalid UUIDs → fallback
- [ ] .well-known files accessible
- [ ] SSL certificate valid

---

## Cost Estimate

### One-Time Setup
- ACM Certificate: $0 (free)
- S3 Bucket creation: $0
- Route53 hosted zone: Already exists ($0)

### Monthly Ongoing Costs
- **S3 Storage:** < $0.01/month (few KB of files)
- **S3 Requests:** ~$0.01/month (minimal staging traffic)
- **CloudFront Data Transfer:** ~$0.085 per GB (depends on testing volume)
- **CloudFront Requests:** ~$0.01 per 10,000 requests
- **CloudFront Function:** $0.10 per 1M invocations

**Estimated monthly cost for staging:** < $1 (assuming light testing traffic)

---

## Rollback Plan

If staging environment causes issues:

### Quick Disable
```python
# Disassociate function from staging distribution
# (Staging continues to work, just without URL transformations)
```

### Full Teardown
```python
# 1. Delete DNS CNAME record
aws.delete_dns_record('stage.ehnw.ca')

# 2. Delete CloudFront distribution (requires disabling first)
aws.disable_distribution(staging_dist_id)
aws.delete_distribution(staging_dist_id)

# 3. Delete CloudFront Function
cloudfront.delete_function('ehnw-staging-universal-links')

# 4. Delete S3 bucket contents and bucket
aws.empty_s3_bucket('stage.ehnw.ca')
aws.delete_s3_bucket('stage.ehnw.ca')

# 5. Remove stage.ehnw.ca from certificate (optional)
```

**Time to teardown:** ~20 minutes (mostly CloudFront disable wait time)

---

## Timeline Estimate

| Step | Task | Time |
|------|------|------|
| 1 | Update/request SSL certificate | 10 min |
| 2 | Create S3 bucket | 2 min |
| 3 | Upload staging files | 2 min |
| 4 | Create CloudFront distribution | 15 min |
| 5 | Create CloudFront Function | 5 min |
| 6 | Associate function | 5 min |
| 7 | Create DNS CNAME | 2 min |
| 8 | DNS propagation wait | 5-10 min |
| 9 | Validation testing | 5 min |

**Total estimated time:** ~50-55 minutes

---

## Open Questions

Before implementing, we need answers to:

1. **Deep link scheme for staging:**
   - [ ] Use `com.ehnow.eh.staging://` (requires staging app)
   - [ ] Use `com.ehnow.eh://` (same as prod)

2. **App Store URLs for fallback:**
   - [ ] TestFlight URLs (provide links if available)
   - [ ] Same production App Store URLs

3. **App IDs in .well-known files:**
   - [ ] Different app IDs for staging? (provide if different)
   - [ ] Same as production

4. **Certificate approach:**
   - [ ] Add stage.ehnw.ca to existing cert (preferred)
   - [ ] Create new certificate for stage.ehnw.ca

5. **Android SHA256 fingerprint:**
   - [ ] Different for staging app? (provide if different)
   - [ ] Same as production

---

## Next Steps

1. **User provides answers to open questions above**
2. Create staging configuration files based on answers
3. Execute implementation steps 1-9
4. Validate staging environment
5. Document staging-specific differences
6. Create testing workflow documentation

---

## Benefits of Staging Environment

✅ **Safe testing** - Changes won't affect production users
✅ **Fast iteration** - Test changes quickly without risk
✅ **Validation** - Verify function changes before prod deployment
✅ **Debugging** - Easier to debug with verbose logging in staging
✅ **Team testing** - Share stage.ehnw.ca links with team for QA
✅ **Complete isolation** - Zero risk of staging affecting prod

---

## Ready to Proceed

Once you answer the open questions above, I can execute the implementation in ~50 minutes with full validation.
