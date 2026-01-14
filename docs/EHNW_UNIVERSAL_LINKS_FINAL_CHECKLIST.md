# ehnw.ca Universal Links - Final Implementation Checklist

**Date:** 2026-01-12
**Status:** READY TO IMPLEMENT
**All validations passed:** ✅

---

## Validated Prerequisites ✅

- ✅ IAM authenticated: mega-agent user (870314670072)
- ✅ ACM certificate ISSUED: Valid for 392 days
- ✅ S3 bucket exists: ehnw.ca (with website hosting)
- ✅ Route53 hosted zone exists: Z08230981PLMAO1820UME
- ✅ All AWS permissions confirmed
- ✅ AWSClient methods available

---

## Confirmed Configuration

### URL Behavior
- **Path types:** `/p/`, `/e/`, `/g/`, `/u/` (case-insensitive)
- **User paths:** Take ALL segments (`/u/john/profile` → `com.ehnow.eh://user/john/profile`)
- **Query parameters:** Pass through to deep link
- **Error handling:** Pass through to S3 origin (fallback page)
- **Caching:** Don't cache redirects (always run function)

### Examples
```
https://ehnw.ca/p/Y9R9a-ahR1O3Ew1EkKuCkg?source=email
→ com.ehnow.eh://post/63d47d6b-e6a1-4753-b713-0d4490ab8292?source=email

https://ehnw.ca/P/Y9R9a-ahR1O3Ew1EkKuCkg
→ com.ehnow.eh://post/63d47d6b-e6a1-4753-b713-0d4490ab8292
(case insensitive works)

https://ehnw.ca/u/john/profile
→ com.ehnow.eh://user/john/profile
(all segments preserved)

https://ehnw.ca/e/Y9R9a-ahR1O3Ew1EkKuCkg
→ com.ehnow.eh://event/63d47d6b-e6a1-4753-b713-0d4490ab8292

https://ehnw.ca/g/Y9R9a-ahR1O3Ew1EkKuCkg
→ com.ehnow.eh://group/63d47d6b-e6a1-4753-b713-0d4490ab8292
```

---

## Implementation Steps

### Step 1: Update Fallback Page (2 min)
**File:** `s3://ehnw.ca/index.html`

**Content:** iOS/Android detection with automatic redirect
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EH - Canada's Social Network</title>
    <script>
        var userAgent = navigator.userAgent || navigator.vendor || window.opera;
        if (/iPad|iPhone|iPod/.test(userAgent) && !window.MSStream) {
            window.location.href = 'https://apps.apple.com/ca/app/eh-canadas-social-network/id6747136970';
        } else if (/android/i.test(userAgent)) {
            window.location.href = 'https://play.google.com/store/apps/details?id=com.ehnow.eh';
        } else {
            window.location.href = 'https://apps.apple.com/ca/app/eh-canadas-social-network/id6747136970';
        }
    </script>
</head>
<body>
    <p>Redirecting to app store...</p>
</body>
</html>
```

**Action:** Upload with `Content-Type: text/html`

---

### Step 2: Upload .well-known Files (2 min)

#### File 1: apple-app-site-association
**Path:** `s3://ehnw.ca/.well-known/apple-app-site-association`
**Content-Type:** `application/json` ⚠️ CRITICAL

```json
{
  "applinks": {
    "apps": [],
    "details": [
      {
        "appID": "6CL22HCV8F.com.ehnow.ca",
        "paths": [
          "*"
        ]
      }
    ]
  }
}
```

#### File 2: assetlinks.json
**Path:** `s3://ehnw.ca/.well-known/assetlinks.json`
**Content-Type:** `application/json` ⚠️ CRITICAL

```json
[
  {
    "relation": [
      "delegate_permission/common.handle_all_urls"
    ],
    "target": {
      "namespace": "android_app",
      "package_name": "com.ehnow.eh",
      "sha256_cert_fingerprints": [
        "D8:EC:09:FF:37:41:DC:43:34:22:72:4E:CA:1F:C3:A9:09:34:A3:04:76:83:F1:8D:01:4C:63:70:97:94:BE:1D"
      ]
    }
  }
]
```

**Test after upload:**
```bash
curl -I https://ehnw.ca.s3-website-us-east-1.amazonaws.com/.well-known/apple-app-site-association
curl -I https://ehnw.ca.s3-website-us-east-1.amazonaws.com/.well-known/assetlinks.json
```

---

### Step 3: Create CloudFront Distribution (15 min deployment)

**Configuration:**
```python
aws.create_cloudfront_distribution(
    origin_domain='ehnw.ca.s3-website-us-east-1.amazonaws.com',
    aliases=['ehnw.ca'],
    certificate_arn='arn:aws:acm:us-east-1:870314670072:certificate/31baf6a5-c39b-4e4c-a5f5-7dee5b7a4adb',
    comment='Universal links for EH app'
)
```

**Wait for deployment:** Status changes from InProgress → Deployed (~10-15 min)

**Save:** Distribution ID and CloudFront domain

---

### Step 4: Create CloudFront Function (5 min)

**Name:** `ehnw-universal-links`
**Runtime:** `cloudfront-js-1.0`

**Code:**
```javascript
function handler(event) {
    var request = event.request;
    var uri = request.uri;

    // Handle .well-known paths - pass through to S3
    if (uri.startsWith('/.well-known/')) {
        return request;
    }

    // Handle root and static files - pass through to S3
    if (uri === '/' || uri === '/index.html' || uri === '/error.html') {
        return request;
    }

    // Strip trailing slashes
    uri = uri.replace(/\/+$/, '');

    // Parse path segments
    var segments = uri.split('/').filter(function(s) { return s.length > 0; });

    // Need at least 2 segments: /type/id
    if (segments.length < 2 || !segments[1]) {
        return request;
    }

    var type = segments[0].toLowerCase(); // Case insensitive
    var pathRemainder = segments.slice(1); // All remaining segments

    // Map path types to deep link types (case insensitive)
    var typeMap = {
        'p': 'post',
        'e': 'event',
        'g': 'group',
        'u': 'user'
    };

    var deepLinkType = typeMap[type];

    // Unknown type - pass through
    if (!deepLinkType) {
        return request;
    }

    var deepLinkPath;

    // Decode UUID for post, event, group (not for user)
    if (type === 'p' || type === 'e' || type === 'g') {
        try {
            var uuid = decodeBase64UrlToUUID(pathRemainder[0]);
            deepLinkPath = uuid;

            // If there are additional segments, append them
            if (pathRemainder.length > 1) {
                deepLinkPath = uuid + '/' + pathRemainder.slice(1).join('/');
            }
        } catch (e) {
            // Invalid base64 - pass through to origin
            return request;
        }
    } else {
        // For user paths, take all segments
        deepLinkPath = pathRemainder.join('/');
    }

    // Build deep link with query string
    var deepLink = 'com.ehnow.eh://' + deepLinkType + '/' + deepLinkPath;

    // Append query string if present
    if (request.querystring) {
        deepLink += '?' + request.querystring;
    }

    // Return redirect with no-cache
    var response = {
        statusCode: 302,
        statusDescription: 'Found',
        headers: {
            'location': { value: deepLink },
            'cache-control': { value: 'no-cache, no-store, must-revalidate' }
        }
    };

    return response;
}

function decodeBase64UrlToUUID(base64url) {
    // Validate length (16 bytes = 22 base64url chars without padding)
    if (base64url.length !== 22) {
        throw new Error('Invalid base64url length');
    }

    // Convert base64url to standard base64
    var base64 = base64url.replace(/-/g, '+').replace(/_/g, '/');

    // Add padding
    while (base64.length % 4 !== 0) {
        base64 += '=';
    }

    // Decode base64 to binary string
    var binary = atob(base64);

    // Convert binary string to hex
    var hex = '';
    for (var i = 0; i < binary.length; i++) {
        var byte = binary.charCodeAt(i).toString(16);
        hex += byte.length === 1 ? '0' + byte : byte;
    }

    // Insert dashes at UUID positions: 8-4-4-4-12
    var uuid = hex.substr(0, 8) + '-' +
               hex.substr(8, 4) + '-' +
               hex.substr(12, 4) + '-' +
               hex.substr(16, 4) + '-' +
               hex.substr(20, 12);

    return uuid;
}
```

**Test in CloudFront console:**
- Test URI: `/p/Y9R9a-ahR1O3Ew1EkKuCkg`
- Expected: 302 redirect to `com.ehnow.eh://post/63d47d6b-e6a1-4753-b713-0d4490ab8292`

**Publish function**

---

### Step 5: Associate Function with Distribution (5 min)

**Configuration:**
- Event type: `viewer-request`
- Function: `ehnw-universal-links`

**Wait for deployment:** ~5 minutes

---

### Step 6: Create DNS ALIAS Record (2 min)

**Configuration:**
```python
aws.upsert_cloudfront_alias(
    hosted_zone_id='Z08230981PLMAO1820UME',
    name='ehnw.ca',
    cloudfront_domain='d1234567890abc.cloudfront.net',  # From Step 3
    cloudfront_hosted_zone_id='Z2FDTNDATAQYW2'  # CloudFront constant
)
```

**Wait for DNS propagation:** 5-10 minutes

---

### Step 7: Validation Tests

#### Test 1: .well-known files
```bash
curl -I https://ehnw.ca/.well-known/apple-app-site-association
# Should return: 200 OK, Content-Type: application/json

curl https://ehnw.ca/.well-known/apple-app-site-association
# Should return: JSON with appID 6CL22HCV8F.com.ehnow.ca

curl -I https://ehnw.ca/.well-known/assetlinks.json
# Should return: 200 OK, Content-Type: application/json

curl https://ehnw.ca/.well-known/assetlinks.json
# Should return: JSON array with package_name com.ehnow.eh
```

#### Test 2: URL redirects (curl)
```bash
# Post with UUID decode
curl -I https://ehnw.ca/p/Y9R9a-ahR1O3Ew1EkKuCkg
# Expected: 302 Location: com.ehnow.eh://post/63d47d6b-e6a1-4753-b713-0d4490ab8292

# Post with query string
curl -I 'https://ehnw.ca/p/Y9R9a-ahR1O3Ew1EkKuCkg?source=email'
# Expected: 302 Location: com.ehnow.eh://post/63d47d6b-e6a1-4753-b713-0d4490ab8292?source=email

# Case insensitive
curl -I https://ehnw.ca/P/Y9R9a-ahR1O3Ew1EkKuCkg
# Expected: 302 Location: com.ehnow.eh://post/63d47d6b-e6a1-4753-b713-0d4490ab8292

# Event
curl -I https://ehnw.ca/e/Y9R9a-ahR1O3Ew1EkKuCkg
# Expected: 302 Location: com.ehnow.eh://event/63d47d6b-e6a1-4753-b713-0d4490ab8292

# Group
curl -I https://ehnw.ca/g/Y9R9a-ahR1O3Ew1EkKuCkg
# Expected: 302 Location: com.ehnow.eh://group/63d47d6b-e6a1-4753-b713-0d4490ab8292

# User (no decode, multiple segments)
curl -I https://ehnw.ca/u/johndoe/profile
# Expected: 302 Location: com.ehnow.eh://user/johndoe/profile

# Root (fallback page)
curl -I https://ehnw.ca/
# Expected: 200 OK, shows HTML redirect page

# Invalid base64 (pass through to origin)
curl -I https://ehnw.ca/p/INVALID
# Expected: 404 or shows fallback page
```

#### Test 3: UUID encoding/decoding validation
```bash
cd /home/ec2-user/mega-agent2/tests
node uuid_encoding_test.js
# Should show: All tests passed
```

---

## Success Criteria

**Phase 1: Infrastructure (Ready to test on devices)**
- ✅ .well-known files accessible via HTTPS
- ✅ apple-app-site-association returns correct JSON
- ✅ assetlinks.json returns correct JSON
- ✅ CloudFront distribution deployed
- ✅ CloudFront function created and associated
- ✅ DNS ALIAS record pointing to CloudFront
- ✅ All curl tests return expected redirects
- ✅ UUID encoding/decoding tests pass

**Phase 2: Device Testing (After app configured)**
- ⏳ iOS: Safari opens links in EH app
- ⏳ Android: Chrome prompts to open in EH app
- ⏳ Deep links navigate to correct content in app

**Phase 3: Production (After successful testing)**
- ⏳ Monitoring enabled
- ⏳ CloudFront logs configured
- ⏳ Documentation complete

---

## Rollback Plan

If issues arise during testing:

### Quick Disable
```python
# Disassociate function from distribution
# Takes 5 minutes, no downtime
```

### Full Rollback
```python
# 1. Remove DNS record
aws.delete_dns_record(zone_id, 'ehnw.ca', 'A')

# 2. Wait 5 min for DNS propagation
# 3. Users fall back to S3 directly
```

---

## Post-Implementation Notes

### App Configuration Required (Before Testing)
The EH app needs these changes before universal links work:

**iOS (Info.plist + Entitlements):**
```xml
<key>com.apple.developer.associated-domains</key>
<array>
    <string>applinks:ehnw.ca</string>
</array>
```

**Android (AndroidManifest.xml):**
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

**Note:** Universal links won't work until apps are updated and published to stores.

---

## Estimated Timeline

**Implementation:** ~30-40 minutes
- Upload files: 5 min
- Create distribution: 15 min (AWS deployment)
- Create function: 5 min
- Associate function: 5 min
- Create DNS: 2 min
- DNS propagation: 5-10 min

**Testing:** ~15 minutes
- curl tests: 5 min
- Validation tests: 5 min
- Documentation: 5 min

**Total:** ~50 minutes from start to "ready for device testing"

---

## Ready to Proceed

All prerequisites validated ✅
All questions answered ✅
Implementation plan finalized ✅

**Waiting for explicit permission to start implementation.**

When you say "go" or "proceed" or "implement", I will execute all 7 steps above.
