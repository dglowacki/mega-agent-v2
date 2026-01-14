# ehnw.ca Universal Links - Implementation Complete ✅

**Date:** 2026-01-12
**Status:** LIVE AND VALIDATED
**Implementation Time:** ~40 minutes

---

## Summary

Universal links for ehnw.ca are now live and fully operational. All validation tests pass successfully.

---

## Infrastructure Deployed

### 1. S3 Bucket (ehnw.ca)
- **Fallback page:** index.html with iOS/Android detection → App Store redirect
- **Apple Universal Links:** `.well-known/apple-app-site-association` ✅
- **Android App Links:** `.well-known/assetlinks.json` ✅
- **Content-Type:** application/json (verified)

### 2. CloudFront Distribution
- **Distribution ID:** E28JUE6Q00L6TK
- **Domain:** dzqlxq2oisjlq.cloudfront.net
- **Status:** Deployed ✅
- **Origin:** ehnw.ca.s3-website-us-east-1.amazonaws.com
- **Certificate:** arn:aws:acm:us-east-1:870314670072:certificate/31baf6a5-c39b-4e4c-a5f5-7dee5b7a4adb
- **SSL:** Valid (expires Feb 8, 2027)

### 3. CloudFront Function
- **Name:** ehnw-universal-links
- **Runtime:** cloudfront-js-1.0
- **Event:** viewer-request
- **Status:** LIVE ✅
- **Features:**
  - UUID base64url decoding for /p/, /e/, /g/ paths
  - Case-insensitive path matching
  - Query string pass-through
  - Multi-segment user paths (/u/...)

### 4. DNS
- **Record Type:** A ALIAS
- **Domain:** ehnw.ca
- **Target:** dzqlxq2oisjlq.cloudfront.net
- **Status:** Propagated ✅

---

## Validation Results (All Passing ✅)

### Test 1: DNS Resolution ✅
- ehnw.ca resolves correctly
- Points to CloudFront distribution

### Test 2: Apple Universal Links ✅
- URL: https://ehnw.ca/.well-known/apple-app-site-association
- Status: 200 OK
- Content-Type: application/json
- AppID: 6CL22HCV8F.com.ehnow.ca

### Test 3: Android App Links ✅
- URL: https://ehnw.ca/.well-known/assetlinks.json
- Status: 200 OK
- Content-Type: application/json
- Package: com.ehnow.eh

### Test 4: Post URL with UUID Decode ✅
- Input: https://ehnw.ca/p/Y9R9a-ahR1O3Ew1EkKuCkg
- Output: com.ehnow.eh://post/63d47d6b-e6a1-4753-b713-0d4490ab8292
- Status: 302 redirect

### Test 5: Query String Pass-Through ✅
- Input: https://ehnw.ca/p/Y9R9a-ahR1O3Ew1EkKuCkg?source=email
- Output: com.ehnow.eh://post/63d47d6b-e6a1-4753-b713-0d4490ab8292?source=email
- Query params preserved

### Test 6: Case Insensitivity ✅
- Input: https://ehnw.ca/P/Y9R9a-ahR1O3Ew1EkKuCkg (uppercase P)
- Output: com.ehnow.eh://post/63d47d6b-e6a1-4753-b713-0d4490ab8292
- Works correctly

### Test 7: Event URL ✅
- Input: https://ehnw.ca/e/Y9R9a-ahR1O3Ew1EkKuCkg
- Output: com.ehnow.eh://event/63d47d6b-e6a1-4753-b713-0d4490ab8292
- Status: 302 redirect

### Test 8: Group URL ✅
- Input: https://ehnw.ca/g/Y9R9a-ahR1O3Ew1EkKuCkg
- Output: com.ehnow.eh://group/63d47d6b-e6a1-4753-b713-0d4490ab8292
- Status: 302 redirect

### Test 9: User Path (Multi-Segment) ✅
- Input: https://ehnw.ca/u/john/profile
- Output: com.ehnow.eh://user/john/profile
- All segments preserved (no UUID decode)

### Test 10: Fallback Page ✅
- Input: https://ehnw.ca/
- Output: 200 OK with App Store redirect page
- Detects iOS/Android and redirects accordingly

---

## URL Behavior Reference

### Supported Path Types
| Path | Type | UUID Decode | Example |
|------|------|-------------|---------|
| `/p/` | post | Yes | `/p/Y9R9a-ahR1O3Ew1EkKuCkg` |
| `/e/` | event | Yes | `/e/Y9R9a-ahR1O3Ew1EkKuCkg` |
| `/g/` | group | Yes | `/g/Y9R9a-ahR1O3Ew1EkKuCkg` |
| `/u/` | user | No | `/u/john/profile` |

### Features
- ✅ Case-insensitive path matching (`/p/` = `/P/`)
- ✅ Query parameters preserved
- ✅ Multi-segment user paths supported
- ✅ Invalid base64url passes through to fallback (404 → App Store)
- ✅ Redirects never cached (no-cache headers)

---

## Technical Issues Resolved

### Issue 1: CloudFront Function Not Working Initially
**Problem:** Function wasn't intercepting requests, all paths returned 404

**Root Cause:** Original function used `atob()` which is not available in CloudFront JS runtime

**Solution:** Implemented manual base64 decode using lookup table

### Issue 2: Query String Not Passing Through
**Problem:** Query parameters were showing as "[object Object]"

**Root Cause:** CloudFront Functions represent querystring as an object, not a string

**Solution:** Iterate through querystring object and build query string manually:
```javascript
var queryParams = [];
for (var key in request.querystring) {
    if (request.querystring[key].value) {
        queryParams.push(key + '=' + request.querystring[key].value);
    }
}
```

### Issue 3: Cache Errors
**Problem:** Initial 404 errors were cached

**Solution:** Created cache invalidation for `/*` pattern

---

## Next Steps (App Configuration Required)

Universal links infrastructure is complete, but **the EH app needs to be configured** before universal links will work on devices.

### iOS Configuration (Info.plist + Entitlements)
```xml
<key>com.apple.developer.associated-domains</key>
<array>
    <string>applinks:ehnw.ca</string>
</array>
```

### Android Configuration (AndroidManifest.xml)
```xml
<intent-filter android:autoVerify="true">
    <action android:name="android.intent.action.VIEW" />
    <category android:name="android.intent.category.DEFAULT" />
    <category android:name="android.intent.category.BROWSABLE" />
    <data android:scheme="https"
          android:host="ehnw.ca" />
</intent-filter>

<intent-filter>
    <action android:name="android.intent.action.VIEW" />
    <category android:name="android.intent.category.DEFAULT" />
    <category android:name="android.intent.category.BROWSABLE" />
    <data android:scheme="com.ehnow.eh" />
</intent-filter>
```

### Device Testing Checklist
Once apps are configured and published:
- [ ] iOS: Tap link in Safari → opens in EH app
- [ ] iOS: Tap link in Messages → opens in EH app
- [ ] Android: Tap link in Chrome → prompts to open in EH app
- [ ] Android: Tap link in other apps → opens in EH app
- [ ] Verify deep link navigates to correct content
- [ ] Verify query parameters are received by app
- [ ] Test all path types (post, event, group, user)

---

## Monitoring and Maintenance

### CloudFront Logs
Enable logging if needed:
```python
aws.update_distribution_logging(
    distribution_id='E28JUE6Q00L6TK',
    bucket='ehnw-logs',
    prefix='cloudfront/'
)
```

### Metrics to Monitor
- Redirect success rate (should be ~100% for valid UUIDs)
- 404 rate on /p/, /e/, /g/, /u/ paths
- Cache hit ratio
- Function execution time

### Common Operations

**Update Function Code:**
```bash
cd /home/ec2-user/mega-agent2
# Edit function, then:
python3 -c "from integrations.aws_client import AWSClient; ..."
```

**Invalidate Cache:**
```python
aws.create_invalidation(
    distribution_id='E28JUE6Q00L6TK',
    paths=['/*']
)
```

**Check Distribution Status:**
```python
aws.get_distribution(distribution_id='E28JUE6Q00L6TK')
```

---

## Files Created/Modified

### New Files
- `/tmp/ehnw_index.html` - Fallback page
- `/tmp/.well-known/apple-app-site-association` - iOS universal links
- `/tmp/.well-known/assetlinks.json` - Android app links
- `/tmp/ehnw-universal-links-function-v2.js` - CloudFront Function code
- `/tmp/validation_tests.sh` - Validation test suite
- `/home/ec2-user/mega-agent2/docs/EHNW_UNIVERSAL_LINKS_IMPLEMENTATION_COMPLETE.md` - This file

### S3 Objects Created
- `s3://ehnw.ca/index.html`
- `s3://ehnw.ca/.well-known/apple-app-site-association`
- `s3://ehnw.ca/.well-known/assetlinks.json`

### AWS Resources Created
- CloudFront Distribution: E28JUE6Q00L6TK
- CloudFront Function: ehnw-universal-links
- Route53 A ALIAS record: ehnw.ca → dzqlxq2oisjlq.cloudfront.net

---

## Success Criteria Met ✅

**Phase 1: Infrastructure (Complete)** ✅
- ✅ .well-known files accessible via HTTPS
- ✅ apple-app-site-association returns correct JSON
- ✅ assetlinks.json returns correct JSON
- ✅ CloudFront distribution deployed
- ✅ CloudFront function created and associated
- ✅ DNS ALIAS record pointing to CloudFront
- ✅ All curl tests return expected redirects
- ✅ UUID encoding/decoding tests pass

**Phase 2: Device Testing (Pending App Configuration)** ⏳
- ⏳ iOS: Safari opens links in EH app
- ⏳ Android: Chrome prompts to open in EH app
- ⏳ Deep links navigate to correct content in app

**Phase 3: Production (Future)** ⏳
- ⏳ Monitoring enabled
- ⏳ CloudFront logs configured
- ⏳ Documentation complete

---

## Cost Estimate

### Ongoing Costs
- **CloudFront:** ~$0.085 per GB + $0.01 per 10,000 requests
- **CloudFront Function:** $0.10 per 1M invocations
- **Route53:** $0.50/month per hosted zone
- **S3:** Minimal (< $0.01/month for static files)

**Estimated monthly cost:** < $1 for low traffic, scales with usage

---

## Implementation Complete! 🎉

All infrastructure is deployed and validated. Universal links will work once the EH app is configured with the associated domains.

**Test the infrastructure now:** https://ehnw.ca/p/Y9R9a-ahR1O3Ew1EkKuCkg

**Questions or issues?** Check CloudWatch Logs for function execution errors.
