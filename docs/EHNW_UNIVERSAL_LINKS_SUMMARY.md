# ehnw.ca Universal Links - Complete Summary

**Date:** 2026-01-12
**Status:** Production & Staging Both LIVE ✅

---

## Environments

### Production: ehnw.ca
- **CloudFront Distribution:** E28JUE6Q00L6TK
- **CloudFront Function:** ehnw-universal-links
- **Certificate:** arn:aws:acm:us-east-1:870314670072:certificate/31baf6a5-c39b-4e4c-a5f5-7dee5b7a4adb
- **S3 Bucket:** ehnw.ca
- **Status:** ✅ LIVE

### Staging: stage.ehnw.ca
- **CloudFront Distribution:** E12SFO751YQTOX
- **CloudFront Function:** ehnw-staging-universal-links
- **Certificate:** arn:aws:acm:us-east-1:870314670072:certificate/be463d69-77de-48ec-a0c4-c30f547df07c
- **S3 Bucket:** stage.ehnw.ca
- **Status:** ✅ LIVE

**Configuration:** Staging uses identical settings to production (same deep link scheme, app IDs, App Store URLs)

**Isolation:** Zero shared resources - staging changes never affect production

---

## Test Links

### Production (ehnw.ca)

#### Mobile Deep Links (iOS/Android)
```
Post:   https://ehnw.ca/p/Y9R9a-ahR1O3Ew1EkKuCkg
Event:  https://ehnw.ca/e/Y9R9a-ahR1O3Ew1EkKuCkg
Group:  https://ehnw.ca/g/Y9R9a-ahR1O3Ew1EkKuCkg
User:   https://ehnw.ca/u/john/profile
```

#### Query String Test
```
https://ehnw.ca/p/Y9R9a-ahR1O3Ew1EkKuCkg?source=email&campaign=test
```

#### Case Insensitive Test
```
https://ehnw.ca/P/Y9R9a-ahR1O3Ew1EkKuCkg
```

#### Desktop Fallback
```
https://ehnw.ca/
https://ehnw.ca/p/Y9R9a-ahR1O3Ew1EkKuCkg (on desktop browser)
```

#### Universal Links Files
```
https://ehnw.ca/.well-known/apple-app-site-association
https://ehnw.ca/.well-known/assetlinks.json
```

### Staging (stage.ehnw.ca)

#### Mobile Deep Links (iOS/Android)
```
Post:   https://stage.ehnw.ca/p/Y9R9a-ahR1O3Ew1EkKuCkg
Event:  https://stage.ehnw.ca/e/Y9R9a-ahR1O3Ew1EkKuCkg
Group:  https://stage.ehnw.ca/g/Y9R9a-ahR1O3Ew1EkKuCkg
User:   https://stage.ehnw.ca/u/john/profile
```

#### Query String Test
```
https://stage.ehnw.ca/p/Y9R9a-ahR1O3Ew1EkKuCkg?source=email&campaign=test
```

#### Case Insensitive Test
```
https://stage.ehnw.ca/P/Y9R9a-ahR1O3Ew1EkKuCkg
```

#### Desktop Fallback
```
https://stage.ehnw.ca/
https://stage.ehnw.ca/p/Y9R9a-ahR1O3Ew1EkKuCkg (on desktop browser)
```

#### Universal Links Files
```
https://stage.ehnw.ca/.well-known/apple-app-site-association
https://stage.ehnw.ca/.well-known/assetlinks.json
```

---

## How It Works

### URL Patterns

| Path Pattern | Example | Converts To |
|-------------|---------|-------------|
| `/p/{base64uuid}` | `/p/Y9R9a-ahR1O3Ew1EkKuCkg` | `com.ehnow.eh://post/63d47d6b-e6a1-4753-b713-0d4490ab8292` |
| `/e/{base64uuid}` | `/e/Y9R9a-ahR1O3Ew1EkKuCkg` | `com.ehnow.eh://event/63d47d6b-e6a1-4753-b713-0d4490ab8292` |
| `/g/{base64uuid}` | `/g/Y9R9a-ahR1O3Ew1EkKuCkg` | `com.ehnow.eh://group/63d47d6b-e6a1-4753-b713-0d4490ab8292` |
| `/u/{path}` | `/u/john/profile` | `com.ehnow.eh://user/john/profile` |

### Behavior

**Mobile Browsers (iPhone/iPad/Android):**
- Receive 302 redirect to deep link (`com.ehnow.eh://...`)
- Deep link opens in EH app (once app is configured)

**Desktop Browsers (Mac/Windows/Linux):**
- Receive HTML page with JavaScript redirect
- Automatically redirected to App Store (iOS) or Play Store (Android)

**Features:**
- ✅ Case-insensitive paths (`/p/` = `/P/`)
- ✅ Query parameters preserved
- ✅ Multi-segment user paths
- ✅ UUID base64url decoding
- ✅ Invalid UUIDs fall back to App Store
- ✅ Redirects never cached

---

## Testing Instructions

### Test on Mobile Device (iOS)

1. Open Safari on iPhone
2. Visit: `https://stage.ehnw.ca/p/Y9R9a-ahR1O3Ew1EkKuCkg`
3. **Expected:** Link should try to open in EH app
4. **Note:** App must be configured first (see App Configuration section below)

### Test on Mobile Device (Android)

1. Open Chrome on Android
2. Visit: `https://stage.ehnw.ca/p/Y9R9a-ahR1O3Ew1EkKuCkg`
3. **Expected:** Browser prompts to open in EH app
4. **Note:** App must be configured first

### Test on Desktop Browser

1. Open Chrome/Safari/Firefox on desktop
2. Visit: `https://stage.ehnw.ca/p/Y9R9a-ahR1O3Ew1EkKuCkg`
3. **Expected:** Page redirects to App Store

### Test with curl

```bash
# Test mobile redirect
curl -A "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)" \
  -I https://stage.ehnw.ca/p/Y9R9a-ahR1O3Ew1EkKuCkg

# Expected: 302 redirect with Location: com.ehnow.eh://post/...

# Test desktop fallback
curl -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)" \
  https://stage.ehnw.ca/p/Y9R9a-ahR1O3Ew1EkKuCkg

# Expected: HTML page with "Redirecting to app store..."

# Test .well-known files
curl -I https://stage.ehnw.ca/.well-known/apple-app-site-association
# Expected: 200 OK, Content-Type: application/json

curl https://stage.ehnw.ca/.well-known/apple-app-site-association
# Expected: JSON with appID 6CL22HCV8F.com.ehnow.ca
```

---

## App Configuration Required

Universal links infrastructure is complete, but **apps need configuration** before links work on devices.

### iOS (Info.plist + Entitlements)

```xml
<key>com.apple.developer.associated-domains</key>
<array>
    <string>applinks:ehnw.ca</string>
    <string>applinks:stage.ehnw.ca</string>
</array>
```

### Android (AndroidManifest.xml)

```xml
<!-- Production -->
<intent-filter android:autoVerify="true">
    <action android:name="android.intent.action.VIEW" />
    <category android:name="android.intent.category.DEFAULT" />
    <category android:name="android.intent.category.BROWSABLE" />
    <data android:scheme="https" android:host="ehnw.ca" />
</intent-filter>

<!-- Staging -->
<intent-filter android:autoVerify="true">
    <action android:name="android.intent.action.VIEW" />
    <category android:name="android.intent.category.DEFAULT" />
    <category android:name="android.intent.category.BROWSABLE" />
    <data android:scheme="https" android:host="stage.ehnw.ca" />
</intent-filter>

<!-- Deep link scheme -->
<intent-filter>
    <action android:name="android.intent.action.VIEW" />
    <category android:name="android.intent.category.DEFAULT" />
    <category android:name="android.intent.category.BROWSABLE" />
    <data android:scheme="com.ehnow.eh" />
</intent-filter>
```

---

## Common Operations

### Update Staging Function

```python
from integrations.aws_client import AWSClient
aws = AWSClient()
cloudfront = aws.get_client('cloudfront')

# Read new function code
with open('/tmp/new_function.js', 'r') as f:
    code = f.read()

# Get current function
func = cloudfront.describe_function(
    Name='ehnw-staging-universal-links',
    Stage='LIVE'
)

# Update function
update = cloudfront.update_function(
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
    IfMatch=update['ETag']
)
```

### Invalidate Cache (Staging)

```python
import time

cloudfront.create_invalidation(
    DistributionId='E12SFO751YQTOX',
    InvalidationBatch={
        'Paths': {'Quantity': 1, 'Items': ['/*']},
        'CallerReference': f'staging-{int(time.time())}'
    }
)
```

### Invalidate Cache (Production)

```python
import time

cloudfront.create_invalidation(
    DistributionId='E28JUE6Q00L6TK',
    InvalidationBatch={
        'Paths': {'Quantity': 1, 'Items': ['/*']},
        'CallerReference': f'prod-{int(time.time())}'
    }
)
```

### Promote Staging to Production

```python
# 1. Test thoroughly on staging first!

# 2. Get staging function code
staging_func = cloudfront.describe_function(
    Name='ehnw-staging-universal-links',
    Stage='LIVE'
)
staging_code = cloudfront.get_function(
    Name='ehnw-staging-universal-links',
    Stage='LIVE'
)['FunctionCode'].read()

# 3. Update production function
prod_func = cloudfront.describe_function(
    Name='ehnw-universal-links',
    Stage='LIVE'
)

update = cloudfront.update_function(
    Name='ehnw-universal-links',
    IfMatch=prod_func['ETag'],
    FunctionConfig={
        'Comment': 'Promoted from staging',
        'Runtime': 'cloudfront-js-1.0'
    },
    FunctionCode=staging_code
)

# 4. Publish production
cloudfront.publish_function(
    Name='ehnw-universal-links',
    IfMatch=update['ETag']
)

# 5. Invalidate production cache
cloudfront.create_invalidation(
    DistributionId='E28JUE6Q00L6TK',
    InvalidationBatch={
        'Paths': {'Quantity': 1, 'Items': ['/*']},
        'CallerReference': f'prod-promote-{int(time.time())}'
    }
)
```

### Check Distribution Status

```python
# Staging
dist = cloudfront.get_distribution(Id='E12SFO751YQTOX')
print(f"Staging Status: {dist['Distribution']['Status']}")

# Production
dist = cloudfront.get_distribution(Id='E28JUE6Q00L6TK')
print(f"Production Status: {dist['Distribution']['Status']}")
```

---

## Troubleshooting

### Links don't open in app

**Check:**
1. App has associated domains configured (see App Configuration above)
2. App is installed on device
3. Using HTTPS (not HTTP)
4. Testing on device (not simulator - simulators don't support universal links well)
5. .well-known files are accessible and return 200 OK

**iOS Specific:**
- Delete app and reinstall to re-fetch .well-known file
- Check Settings → [App Name] → "Open links" is enabled

**Android Specific:**
- Check Settings → Apps → [App Name] → "Open by default"
- Verify SHA256 fingerprint in assetlinks.json matches app signing cert

### Desktop shows "Cannot open this address"

This was the original issue - now fixed! Desktop browsers now receive HTML fallback page that redirects to App Store.

**If you still see this:**
1. Clear browser cache
2. Try: https://stage.ehnw.ca/p/Y9R9a-ahR1O3Ew1EkKuCkg
3. Should see "Redirecting to app store..." then redirect

### Changes not taking effect

**Solution:** Invalidate CloudFront cache

```bash
# Via AWS CLI (if available)
aws cloudfront create-invalidation \
  --distribution-id E12SFO751YQTOX \
  --paths "/*"
```

Or use Python code above.

### Deep links redirect but app doesn't open

**Likely cause:** App not configured or not installed

**Test the deep link directly:**
```bash
# On Mac with iPhone connected
xcrun simctl openurl booted "com.ehnow.eh://post/63d47d6b-e6a1-4753-b713-0d4490ab8292"

# On Android with device connected
adb shell am start -a android.intent.action.VIEW -d "com.ehnow.eh://post/63d47d6b-e6a1-4753-b713-0d4490ab8292"
```

---

## Key Facts

### URL Encoding
- **Base64URL format:** URL-safe base64 (no padding)
- **UUID:** 16 bytes → 22 characters
- **Example:** `Y9R9a-ahR1O3Ew1EkKuCkg` → `63d47d6b-e6a1-4753-b713-0d4490ab8292`

### Deep Link Scheme
- **Production & Staging:** `com.ehnow.eh://`
- **Types:** post, event, group, user

### App Store URLs
- **iOS:** https://apps.apple.com/ca/app/eh-canadas-social-network/id6747136970
- **Android:** https://play.google.com/store/apps/details?id=com.ehnow.eh

### App IDs
- **iOS:** 6CL22HCV8F.com.ehnow.ca
- **Android:** com.ehnow.eh
- **SHA256:** D8:EC:09:FF:37:41:DC:43:34:22:72:4E:CA:1F:C3:A9:09:34:A3:04:76:83:F1:8D:01:4C:63:70:97:94:BE:1D

---

## Quick Reference

### Resource IDs

| Resource | Production | Staging |
|----------|-----------|---------|
| Domain | ehnw.ca | stage.ehnw.ca |
| CloudFront Dist | E28JUE6Q00L6TK | E12SFO751YQTOX |
| CloudFront Func | ehnw-universal-links | ehnw-staging-universal-links |
| S3 Bucket | ehnw.ca | stage.ehnw.ca |
| Certificate | 31baf6a5-c39b-4e4c-a5f5-7dee5b7a4adb | be463d69-77de-48ec-a0c4-c30f547df07c |

### Documentation Files
- `/home/ec2-user/mega-agent2/docs/EHNW_UNIVERSAL_LINKS_IMPLEMENTATION_COMPLETE.md` - Production details
- `/home/ec2-user/mega-agent2/docs/EHNW_STAGING_IMPLEMENTATION_COMPLETE.md` - Staging details
- `/home/ec2-user/mega-agent2/docs/EHNW_UNIVERSAL_LINKS_SUMMARY.md` - This file

### Cost
- **Production:** < $1/month (scales with traffic)
- **Staging:** < $1/month (light testing only)
- **Total:** < $2/month

---

## Status Summary

✅ **Production (ehnw.ca):** LIVE and validated
✅ **Staging (stage.ehnw.ca):** LIVE and validated
✅ **All infrastructure deployed**
✅ **All tests passing**
✅ **Complete isolation between environments**
✅ **Mobile detection working**
✅ **Desktop fallback working**
✅ **Universal links files served correctly**
✅ **Ready for app configuration**

---

## Next Steps

1. **Configure apps** - Add associated domains to iOS & Android apps
2. **Test on devices** - Install configured app and test links
3. **Monitor** - Watch CloudWatch logs for function execution
4. **Iterate** - Use staging to test changes before production

---

**Questions?** All infrastructure is documented and operational. Test links above, or check detailed docs in `/home/ec2-user/mega-agent2/docs/`
