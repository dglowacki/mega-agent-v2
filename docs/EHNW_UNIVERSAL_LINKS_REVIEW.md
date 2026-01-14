# ehnw.ca Universal Links Implementation - Review & Questions

**Date:** 2026-01-12
**Reviewer:** Claude
**Plan Location:** `/home/ec2-user/mega-agent2/docs/EHNW_UNIVERSAL_LINKS_PLAN.md`

---

## Critical Prerequisites (Must Resolve Before Implementation)

### 1. CloudFront Distribution Status ⚠️
**Issue:** We don't know if ehnw.ca CloudFront distribution exists or is created.

**Last Known State:**
- Certificate ARN: `arn:aws:acm:us-east-1:870314670072:certificate/31baf6a5-c39b-4e4c-a5f5-7dee5b7a4adb`
- Last checked: Certificate was PENDING_VALIDATION
- Nameservers were updated ~2 hours ago
- DNS propagation in progress

**Questions:**
1. Has the ACM certificate validated yet? (Check status: ISSUED vs PENDING_VALIDATION)
2. Was the CloudFront distribution created earlier, or do we need to create it?
3. If it exists, what's the distribution ID?
4. If it exists, is it already deployed and operational?

**Required Action:**
```bash
# Check certificate status
aws acm describe-certificate --certificate-arn arn:aws:acm:us-east-1:870314670072:certificate/31baf6a5-c39b-4e4c-a5f5-7dee5b7a4adb --region us-east-1

# Check if distribution exists
aws cloudfront list-distributions --query 'DistributionList.Items[?Aliases.Items[?contains(@, `ehnw.ca`)]]'
```

**Blocker:** ❌ Cannot proceed with CloudFront Function until distribution exists

---

### 2. DNS ALIAS Record Status ⚠️
**Issue:** Unclear if DNS ALIAS record for ehnw.ca → CloudFront is configured.

**Questions:**
1. Is there currently an A ALIAS record pointing ehnw.ca to CloudFront?
2. Or is ehnw.ca pointing directly to S3?
3. Do we need to create/update this record?

**Required Action:**
```bash
# Check current DNS configuration
dig ehnw.ca A
dig ehnw.ca CNAME

# Check Route53 hosted zone
aws route53 list-resource-record-sets --hosted-zone-id Z08230981PLMAO1820UME
```

---

### 3. S3 Bucket Current State ⚠️
**Issue:** Need to verify S3 bucket state before uploading files.

**Questions:**
1. Does ehnw.ca S3 bucket exist? (We created it earlier)
2. What's currently in the bucket?
3. Is static website hosting enabled? (We configured this earlier)
4. Is the bucket policy allowing public reads?

**Required Action:**
```bash
# Check bucket exists and list contents
aws s3 ls s3://ehnw.ca/

# Check website configuration
aws s3api get-bucket-website --bucket ehnw.ca

# Check bucket policy
aws s3api get-bucket-policy --bucket ehnw.ca
```

**Current Known State:**
- ✅ Bucket created: ehnw.ca
- ✅ Static hosting enabled: ehnw.ca.s3-website-us-east-1.amazonaws.com
- ✅ Placeholder index.html uploaded
- ❓ .well-known files not yet uploaded

---

## Technical Ambiguities

### 4. URL Path Handling

#### 4a. Trailing Slashes
**Issue:** Behavior undefined for URLs with trailing slashes.

**Examples:**
- `/p/Y9R9a-ahR1O3Ew1EkKuCkg` ✅ Defined
- `/p/Y9R9a-ahR1O3Ew1EkKuCkg/` ❓ Trailing slash
- `/p/Y9R9a-ahR1O3Ew1EkKuCkg//` ❓ Multiple trailing slashes

**Question:** Should we:
- Strip trailing slashes before processing?
- Treat them as different URLs?
- Return error?

**Recommendation:** Strip trailing slashes in CloudFront function:
```javascript
var uri = request.uri.replace(/\/+$/, ''); // Remove trailing slashes
```

---

#### 4b. Query Parameters
**Issue:** Behavior undefined for query parameters.

**Examples:**
- `/p/Y9R9a-ahR1O3Ew1EkKuCkg?source=email`
- `/p/Y9R9a-ahR1O3Ew1EkKuCkg?utm_campaign=spring2024`

**Questions:**
1. Should query parameters be preserved in the deep link?
2. Should they be stripped?
3. Does the app expect/handle query parameters?

**Current Behavior:** CloudFront function ignores query string (only looks at URI path)

**Possible Options:**
- **Option A:** Ignore query params (current)
- **Option B:** Pass through to deep link: `com.ehnow.eh://post/{uuid}?source=email`
- **Option C:** Strip specific params (utm_*) but preserve others

**Need Answer:** How should query parameters be handled?

---

#### 4c. Fragment Identifiers
**Issue:** Behavior undefined for URL fragments (#anchors).

**Examples:**
- `/p/Y9R9a-ahR1O3Ew1EkKuCkg#comments`
- `/p/Y9R9a-ahR1O3Ew1EkKuCkg#reply-123`

**Note:** Fragments are not sent to the server, so CloudFront function won't see them. They're client-side only.

**Current Behavior:** Fragments automatically lost in 302 redirect

**Question:** Does this matter for the app?

---

#### 4d. Case Sensitivity
**Issue:** Are path prefixes case-sensitive?

**Examples:**
- `/p/...` ✅ Defined (lowercase)
- `/P/...` ❓ Uppercase
- `/Post/...` ❓ Mixed case

**Recommendation:** Normalize to lowercase:
```javascript
var type = segments[0].toLowerCase();
```

**Question:** Should we support case-insensitive paths?

---

#### 4e. User Path Validation
**Issue:** /u/ paths pass through without validation.

**Examples:**
- `/u/johndoe` ✅ Simple username
- `/u/john.doe` ❓ Period in username
- `/u/john@doe` ❓ @ symbol
- `/u/john%20doe` ❓ URL-encoded space
- `/u/john/profile` ❓ Multiple segments

**Questions:**
1. What characters are valid in usernames?
2. Should we validate or just pass through?
3. Should we URL-encode before creating deep link?
4. What about usernames with multiple path segments?

**Current Behavior:** Takes everything after /u/ as username, no validation

**Potential Issue:** If username is `john/profile`, becomes `/u/john/profile` which splits into 3 segments, not 2.

**Recommendation:** Either:
- Validate username format (alphanumeric + _ - .)
- Or take ALL remaining path segments: `segments.slice(1).join('/')`

---

### 5. Error Handling & Edge Cases

#### 5a. Invalid Base64 URL Input
**Issue:** What happens with malformed base64url?

**Examples:**
- `/p/TOOSHORT` (only 8 chars, not 22)
- `/p/TOOLONGGGGGGGGGGGGGGGGG` (more than 22 chars)
- `/p/Invalid+Chars=` (+ and = not allowed in base64url)
- `/p/Y9R9a-ahR1O3Ew1E` (valid base64url but wrong length)

**Current Behavior:** Plan says "pass through to origin"

**Questions:**
1. Should we return 404 Not Found instead?
2. Should we redirect to / (store redirect page)?
3. Should we log these errors for monitoring?

**Recommendation:**
```javascript
try {
    deepLinkId = decodeBase64UrlToUUID(id);
} catch (e) {
    // Option 1: Pass through to origin (shows fallback page or 404)
    return request;

    // Option 2: Redirect to root (store redirect page)
    // return { statusCode: 302, headers: { location: { value: '/' } } };

    // Option 3: Return 404
    // return { statusCode: 404, body: 'Invalid link' };
}
```

**Need Answer:** Which option do you prefer?

---

#### 5b. Unknown Path Types
**Issue:** What happens with undefined paths?

**Examples:**
- `/unknown/Y9R9a-ahR1O3Ew1EkKuCkg`
- `/post/Y9R9a-ahR1O3Ew1EkKuCkg` (full word instead of /p/)
- `/profile/johndoe`

**Current Behavior:** Pass through to origin

**Question:** Is this correct, or should we return 404?

---

#### 5c. Empty Segments
**Issue:** What about edge case URLs?

**Examples:**
- `/p/` (missing ID)
- `/p` (no trailing slash, no ID)
- `//p/Y9R9a...` (double slash at start)

**Current Behavior:** Path parsing might fail

**Recommendation:** Add validation:
```javascript
if (segments.length < 2 || !segments[1]) {
    return request; // Pass through to origin
}
```

---

### 6. Content-Type Headers for .well-known Files

**Issue:** S3 default Content-Type is application/octet-stream, but we need application/json.

**Critical:** iOS and Android require `Content-Type: application/json` for .well-known files.

**Solution:** Must explicitly set metadata when uploading to S3:
```python
s3.put_object(
    Bucket='ehnw.ca',
    Key='.well-known/apple-app-site-association',
    Body=json.dumps(aasa_content),
    ContentType='application/json',  # ← CRITICAL
    CacheControl='max-age=300'
)
```

**Question:** Confirmed this is in the implementation plan?

**Verification Test:**
```bash
curl -I https://ehnw.ca/.well-known/apple-app-site-association
# Should show: Content-Type: application/json
```

---

### 7. CloudFront Caching Behavior

**Issue:** Should redirects be cached?

**Scenarios:**
1. **Cache redirects:** Faster, cheaper, but can't update links without invalidation
2. **Don't cache redirects:** Slower, more expensive, but more flexible

**Current Plan:** Not specified

**Recommendation:**
- Cache .well-known files: `Cache-Control: max-age=3600` (1 hour)
- DON'T cache redirects: `Cache-Control: no-cache` (always run function)

**Implementation:** Set in CloudFront function response:
```javascript
return {
    statusCode: 302,
    headers: {
        'location': { value: deepLink },
        'cache-control': { value: 'no-cache, no-store, must-revalidate' }
    }
};
```

**Question:** Do you want redirects cached or not?

---

### 8. S3 Directory Structure

**Issue:** Exact S3 file structure not specified.

**Required Structure:**
```
s3://ehnw.ca/
├── .well-known/
│   ├── apple-app-site-association (NO .json extension)
│   └── assetlinks.json (YES .json extension)
├── index.html
└── error.html (optional)
```

**Critical Details:**
1. `.well-known/apple-app-site-association` has NO file extension
2. `.well-known/assetlinks.json` DOES have .json extension
3. Both files must have Content-Type: application/json

**Question:** Do we need error.html, or is index.html sufficient?

---

### 9. CloudFront Function Limits

**Issue:** Need to verify function stays within limits.

**CloudFront Function Limits:**
- Max size: 10 KB
- Max execution time: 1 ms
- Max memory: 2 MB
- No external network calls
- Limited JavaScript runtime

**Current Function Size:** ~2-3 KB (within limits ✅)

**Potential Issue:** `atob()` and string manipulation could be slow for malformed input.

**Recommendation:** Add timeout protection:
```javascript
// Validate length BEFORE attempting decode
if (base64url.length !== 22) {
    return request; // Fast fail
}
```

---

### 10. Testing Prerequisites

**Issue:** Testing requires specific conditions.

**iOS Testing Requires:**
1. Physical iOS device (simulator might not support universal links)
2. EH app installed from App Store (not TestFlight)
3. Device iOS version (14+ recommended for best universal links support)
4. Safari browser (Chrome/Firefox don't support universal links)
5. Not on cellular data (some carriers block universal links)
6. Device not in Low Power Mode

**Android Testing Requires:**
1. Physical Android device (emulator might not work)
2. EH app installed from Play Store (not debug build)
3. Android 6.0+ (API 23+)
4. Google Chrome browser
5. App Links verification passed (can check with adb)

**Questions:**
1. Do you have both iOS and Android devices ready?
2. Is the app published on both stores?
3. Do you have developer access to check app configuration?
4. When do you plan to test? (Timing affects when we deploy)

---

### 11. App Configuration Requirements

**Issue:** The app must be configured correctly on both platforms.

**iOS Requirements:**
- Associated Domains capability enabled
- `applinks:ehnw.ca` in Associated Domains
- URL scheme `com.ehnow.eh` registered
- Deep link handling implemented

**Android Requirements:**
- Intent filter with `android:autoVerify="true"`
- Host `ehnw.ca` in intent filter
- URL scheme `com.ehnow.eh` handled
- Deep link handling implemented

**Questions:**
1. Is the app already configured for ehnw.ca?
2. Or is this the first time adding this domain?
3. If first time, will you need to submit new app versions?

**Critical:** If app doesn't have ehnw.ca in Associated Domains, universal links won't work until app is updated.

---

### 12. Monitoring & Alerts

**Issue:** No monitoring plan specified.

**Questions:**
1. Should we enable CloudFront logging?
   - Standard logs (free, delayed)
   - Real-time logs (paid, immediate)
   - No logs

2. What CloudWatch alarms do you want?
   - High error rate (4xx/5xx)
   - Unusual traffic spike
   - Function execution errors

3. Should we set up billing alerts?
   - Alert at $10/month
   - Alert at $50/month
   - No alerts

**Recommendation:** Start with standard logging to S3, no alerts initially.

---

### 13. Rollback & Disaster Recovery

**Issue:** Rollback procedure exists but missing details.

**Scenarios:**
1. **Function breaks all links** → Disassociate function (5 min)
2. **.well-known files broken** → Fix files in S3 (2 min)
3. **CloudFront distribution broken** → Rollback to previous config (10 min)
4. **Complete disaster** → Point DNS to old infrastructure

**Questions:**
1. Do you have a backup plan if everything breaks?
2. Should we create a staging environment first?
3. What's the acceptable downtime window?

---

### 14. Deployment Timing & Strategy

**Issue:** No deployment timing specified.

**Options:**

**Option A: Deploy Now (Risky)**
- Deploy directly to production
- Test with real users
- Quick feedback
- Risk: Breaks existing links

**Option B: Staged Deployment (Safer)**
- Create staging distribution first (staging.ehnw.ca)
- Test thoroughly
- Then deploy to production
- Lower risk but more work

**Option C: Blue/Green Deployment (Safest)**
- Keep existing setup running
- Create new distribution
- Test new distribution with test subdomain
- Switch DNS when verified
- Can rollback instantly

**Questions:**
1. Which deployment strategy do you prefer?
2. When do you want to deploy? (Now, tonight, tomorrow, next week?)
3. Is there a maintenance window we should use?
4. Can we accept brief downtime (1-2 minutes) during deployment?

---

### 15. Multiple Examples Throughout Plan

**Issue:** Plan uses inconsistent examples.

**Examples Used:**
1. `VQ6EAOKbQdSnFkRmVUQAAA` (incorrect, from early conversation)
2. `Y9R9a-ahR1O3Ew1EkKuCkg` (correct, from your test)

**Impact:** Could confuse during implementation/testing.

**Action Required:** Update all examples in plan to use `Y9R9a-ahR1O3Ew1EkKuCkg`

---

### 16. CloudFront Origin Configuration

**Issue:** Need to confirm origin protocol policy.

**S3 Website Endpoints:**
- Use HTTP only (not HTTPS)
- CloudFront must use `http-only` origin protocol
- CloudFront handles HTTPS to users, HTTP to S3

**Configuration:**
```javascript
'OriginProtocolPolicy': 'http-only',  // Must be http-only for S3 website
```

**Question:** Is this correctly documented in the plan?

---

### 17. Security Headers

**Issue:** Plan doesn't mention security headers.

**Should we add security headers via CloudFront?**
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000`

**Question:** Do you want these headers added?

**Consideration:** For redirects, headers don't matter much. But for .well-known files served from S3, they might be useful.

---

### 18. Version Control & CI/CD

**Issue:** No mention of version control for CloudFront function.

**Questions:**
1. Should we commit the function code to git?
2. Which repo? (eh-client, separate repo, or mega-agent2?)
3. Should we set up automated deployment?
4. How do we track function versions?

**Recommendation:**
- Store function code in `eh-client/infrastructure/cloudfront-functions/`
- Include tests in repo
- Manual deployment for now
- Add CI/CD later if needed

---

### 19. Cost Tracking

**Issue:** Estimate provided but no tracking plan.

**Estimated Costs:**
- CloudFront: ~$1.60/month
- S3: ~$0.10/month
- Total: <$5/month

**Questions:**
1. Should we tag resources for cost tracking?
2. Set up AWS Cost Explorer reports?
3. Set up billing alerts?

---

### 20. Documentation & Knowledge Transfer

**Issue:** After implementation, how is this documented?

**Questions:**
1. Where should final documentation live?
   - eh-client repo README?
   - Separate infrastructure docs?
   - Company wiki?

2. Who needs to know how this works?
   - Mobile team?
   - Backend team?
   - DevOps?
   - Marketing (for link creation)?

3. Should we create a "How to create universal links" guide for the team?

---

## Summary of Required Decisions

### Critical (Block Implementation)

1. ❓ **Is ACM certificate validated?** (Check status now)
2. ❓ **Does CloudFront distribution exist?** (Check now)
3. ❓ **Is DNS ALIAS configured?** (Check now)

### High Priority (Affect Implementation)

4. ❓ **Query parameter handling** (Ignore, pass through, or strip?)
5. ❓ **Error handling for invalid base64** (Pass through, 404, or redirect to /?)
6. ❓ **CloudFront caching** (Cache redirects or not?)
7. ❓ **Deployment strategy** (Deploy now, staged, or blue/green?)
8. ❓ **Testing timeline** (When will you test on devices?)

### Medium Priority (Best Practices)

9. ❓ **Trailing slash handling** (Strip or preserve?)
10. ❓ **Case sensitivity** (Normalize to lowercase?)
11. ❓ **Security headers** (Add or not?)
12. ❓ **Monitoring** (Enable logging, alerts?)
13. ❓ **User path validation** (Validate usernames or pass through?)

### Low Priority (Nice to Have)

14. ❓ **Version control** (Where to store function code?)
15. ❓ **Cost tracking** (Tags, reports, alerts?)
16. ❓ **Documentation location** (Where should docs live?)
17. ❓ **Error document** (Need error.html or just index.html?)

---

## Recommended Next Steps

### Step 1: Verify Prerequisites
```bash
# 1. Check certificate status
aws acm describe-certificate \
  --certificate-arn arn:aws:acm:us-east-1:870314670072:certificate/31baf6a5-c39b-4e4c-a5f5-7dee5b7a4adb \
  --region us-east-1 \
  --query 'Certificate.Status'

# 2. Check CloudFront distribution
aws cloudfront list-distributions \
  --query 'DistributionList.Items[?Aliases.Items[?contains(@, `ehnw.ca`)]]'

# 3. Check DNS configuration
dig ehnw.ca A
aws route53 list-resource-record-sets \
  --hosted-zone-id Z08230981PLMAO1820UME \
  --query 'ResourceRecordSets[?Name==`ehnw.ca.`]'

# 4. Check S3 bucket
aws s3 ls s3://ehnw.ca/
aws s3api get-bucket-website --bucket ehnw.ca
```

### Step 2: Answer Critical Questions

Please provide answers to the Critical and High Priority questions above.

### Step 3: Update Plan

Based on your answers, I'll update the plan to resolve all ambiguities.

### Step 4: Final Review

Review updated plan together before implementation.

### Step 5: Implementation

Only proceed after all questions answered and plan finalized.

---

## Questions for You

**Please answer these questions so we can proceed:**

1. **Prerequisites:**
   - Should I check the certificate and CloudFront status now?
   - Or do you want to check yourself?

2. **Query Parameters:**
   - Ignore them? ← Recommended for simplicity
   - Pass through to deep link?
   - Strip specific ones?

3. **Error Handling:**
   - Pass through to origin (shows fallback page)? ← Recommended
   - Return 404?
   - Redirect to /?

4. **Caching:**
   - Don't cache redirects (always run function)? ← Recommended
   - Cache for X seconds?

5. **Deployment:**
   - Deploy directly to production?
   - Create staging first? ← Recommended
   - When do you want to deploy?

6. **Testing:**
   - Do you have iOS and Android devices ready?
   - When will you test?
   - Is the app already configured for ehnw.ca?

**Once you answer these, I can finalize the plan and we'll be ready to implement!**
