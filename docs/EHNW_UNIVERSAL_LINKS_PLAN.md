# ehnw.ca Universal Links Implementation Plan

**Date:** 2026-01-12
**Domain:** ehnw.ca
**CloudFront Distribution:** (Pending - need to check if created)
**App:** EH - Canada's Social Network

---

## Overview

Implement universal links for the EH app using CloudFront Functions to:
1. Decode base64url-encoded UUIDs in short URLs
2. Redirect to deep links in the native app
3. Fall back to App Store/Play Store if app not installed

---

## URL Mapping Examples

### Posts (with UUID decode)
```
https://ehnw.ca/p/VQ6EAOKbQdSnFkRmVUQAAA
  ↓
com.ehnow.eh://post/63d47d6b-e6a1-4753-b713-0d4490ab8292
```

### Events (with UUID decode)
```
https://ehnw.ca/e/VQ6EAOKbQdSnFkRmVUQAAA
  ↓
com.ehnow.eh://event/63d47d6b-e6a1-4753-b713-0d4490ab8292
```

### Groups (with UUID decode)
```
https://ehnw.ca/g/VQ6EAOKbQdSnFkRmVUQAAA
  ↓
com.ehnow.eh://group/63d47d6b-e6a1-4753-b713-0d4490ab8292
```

### Users (NO decode - pass through as-is)
```
https://ehnw.ca/u/username
  ↓
com.ehnow.eh://user/username
```

---

## UUID Encoding/Decoding Algorithm

### Encoding (for reference - done by backend)
```
UUID: 63d47d6b-e6a1-4753-b713-0d4490ab8292
  ↓
Remove dashes: 63d47d6be6a14753b7130d4490ab8292
  ↓
Parse as hex bytes: [0x63, 0xd4, 0x7d, 0x6b, ...]
  ↓
Base64url encode: VQ6EAOKbQdSnFkRmVUQAAA
  ↓
Final URL: https://ehnw.ca/p/VQ6EAOKbQdSnFkRmVUQAAA
```

### Decoding (CloudFront Function)
```javascript
Input: VQ6EAOKbQdSnFkRmVUQAAA
  ↓
Base64url decode to bytes: [0x55, 0x0e, 0x84, 0x00, ...]
  ↓
Convert bytes to hex: 550e840e2...
  ↓
Insert dashes at positions 8,12,16,20:
  63d47d6b-e6a1-4753-b713-0d4490ab8292
  ↓
Return: com.ehnow.eh://post/63d47d6b-e6a1-4753-b713-0d4490ab8292
```

**Key Details:**
- Base64url uses `-` and `_` instead of `+` and `/`
- No padding `=` characters
- UUIDs are 16 bytes = 22 base64url characters
- UUID v4 format with dashes in output

---

## CloudFront Function Logic

### Function Flow

```
Request: GET /p/VQ6EAOKbQdSnFkRmVUQAAA

1. Parse path: /p/VQ6EAOKbQdSnFkRmVUQAAA
2. Extract segments: ["p", "VQ6EAOKbQdSnFkRmVUQAAA"]
3. Check if path needs decoding (/p, /e, /g = YES, /u = NO)
4. If YES:
   - Decode base64url to UUID
   - Build deep link: com.ehnow.eh://post/{uuid}
5. If NO (/u):
   - Pass through as-is
   - Build deep link: com.ehnow.eh://user/{username}
6. Return 302 redirect

Fallback: If invalid base64 or other error → serve from S3 origin
```

### Error Handling

**Invalid base64:**
- Length != 22 characters
- Invalid base64url characters
- Decode fails
→ Pass through to origin (S3)

**Unknown path:**
- Not /p, /e, /g, /u
→ Pass through to origin (S3)

**Root path:**
- / or /index.html
→ Pass through to origin (S3)

---

## CloudFront Function Code

```javascript
function handler(event) {
    var request = event.request;
    var uri = request.uri;

    // Handle .well-known paths - pass through to S3
    if (uri.startsWith('/.well-known/')) {
        return request;
    }

    // Handle root and static files - pass through to S3
    if (uri === '/' || uri === '/index.html' || uri.endsWith('.html') ||
        uri.endsWith('.css') || uri.endsWith('.js') || uri.endsWith('.png')) {
        return request;
    }

    // Parse path segments
    var segments = uri.split('/').filter(function(s) { return s.length > 0; });

    // Need at least 2 segments: /type/id
    if (segments.length < 2) {
        return request;
    }

    var type = segments[0];
    var id = segments[1];

    // Map path types to deep link types
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

    var deepLinkId = id;

    // Decode UUID for post, event, group (not for user)
    if (type === 'p' || type === 'e' || type === 'g') {
        try {
            deepLinkId = decodeBase64UrlToUUID(id);
        } catch (e) {
            // Invalid base64 - pass through to origin
            return request;
        }
    }

    // Build deep link
    var deepLink = 'com.ehnow.eh://' + deepLinkType + '/' + deepLinkId;

    // Return redirect
    var response = {
        statusCode: 302,
        statusDescription: 'Found',
        headers: {
            'location': { value: deepLink }
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

---

## .well-known Files

### iOS: apple-app-site-association

**Path:** `/.well-known/apple-app-site-association`

**Content:**
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

**Important:**
- Must be served with `Content-Type: application/json`
- Must be accessible via HTTPS
- No `.json` extension in filename
- Must return 200 status code

### Android: assetlinks.json

**Path:** `/.well-known/assetlinks.json`

**Content:**
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

**Important:**
- Must be served with `Content-Type: application/json`
- Must be accessible via HTTPS
- Includes `.json` extension
- Must return 200 status code

---

## Fallback HTML Page

For browsers or when app isn't installed, redirect to appropriate app store based on user agent.

**File:** `/index.html` at S3 origin

**Content:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EH - Canada's Social Network</title>
    <script>
        // Detect platform and redirect to appropriate store
        var userAgent = navigator.userAgent || navigator.vendor || window.opera;

        // iOS detection
        if (/iPad|iPhone|iPod/.test(userAgent) && !window.MSStream) {
            window.location.href = 'https://apps.apple.com/ca/app/eh-canadas-social-network/id6747136970';
        }
        // Android detection
        else if (/android/i.test(userAgent)) {
            window.location.href = 'https://play.google.com/store/apps/details?id=com.ehnow.eh';
        }
        // Desktop or unknown - redirect to iOS store as default
        else {
            window.location.href = 'https://apps.apple.com/ca/app/eh-canadas-social-network/id6747136970';
        }
    </script>
</head>
<body>
    <p>Redirecting to app store...</p>
</body>
</html>
```

**Behavior:**
- iOS devices → App Store
- Android devices → Play Store
- Desktop/Other → App Store (default)
- Redirect happens immediately via JavaScript

---

## Implementation Steps

### Phase 1: Verify CloudFront Setup (5 min)

1. **Check if ehnw.ca CloudFront distribution exists**
   ```python
   distributions = aws.list_cloudfront_distributions()
   # Find ehnw.ca distribution
   ```

2. **If not created, create it:**
   - Origin: ehnw.ca.s3-website-us-east-1.amazonaws.com
   - Aliases: ehnw.ca
   - Certificate: arn:aws:acm:us-east-1:870314670072:certificate/31baf6a5-c39b-4e4c-a5f5-7dee5b7a4adb
   - Default root object: index.html

3. **Check certificate is ISSUED**
   - Should be validated by now

---

### Phase 2: Upload .well-known Files (5 min)

1. **Create directory structure in S3:**
   ```
   ehnw.ca/
   ├── .well-known/
   │   ├── apple-app-site-association
   │   └── assetlinks.json
   └── index.html
   ```

2. **Upload files with correct Content-Type:**
   - `apple-app-site-association` → `Content-Type: application/json`
   - `assetlinks.json` → `Content-Type: application/json`
   - `index.html` → `Content-Type: text/html`

3. **Test accessibility:**
   ```bash
   curl -I https://ehnw.ca/.well-known/apple-app-site-association
   curl -I https://ehnw.ca/.well-known/assetlinks.json
   ```

---

### Phase 3: Create CloudFront Function (10 min)

1. **Create function in CloudFront:**
   - Name: `ehnw-universal-links`
   - Runtime: cloudfront-js-1.0
   - Code: (see CloudFront Function Code above)

2. **Test function with CloudFront console test tool:**
   - Test case 1: `/p/VQ6EAOKbQdSnFkRmVUQAAA`
     - Expected: 302 to `com.ehnow.eh://post/63d47d6b-e6a1-4753-b713-0d4490ab8292`

   - Test case 2: `/u/johndoe`
     - Expected: 302 to `com.ehnow.eh://user/johndoe`

   - Test case 3: `/.well-known/apple-app-site-association`
     - Expected: Request passed through to origin

   - Test case 4: `/`
     - Expected: Request passed through to origin

3. **Publish function**

---

### Phase 4: Associate Function with Distribution (5 min)

1. **Get distribution config**

2. **Associate function with viewer-request:**
   - Event type: `viewer-request`
   - Function ARN: (from Phase 3)

3. **Update distribution**

4. **Wait for deployment** (5-10 minutes)

---

### Phase 5: Configure DNS (2 min)

**If not already done:**

1. **Create A ALIAS record:**
   - Name: ehnw.ca
   - Type: A
   - Alias: Yes
   - Target: CloudFront distribution domain
   - Hosted Zone ID: Z2FDTNDATAQYW2 (CloudFront)

---

### Phase 6: Testing (15-30 min)

#### Test 1: .well-known Files
```bash
# iOS
curl https://ehnw.ca/.well-known/apple-app-site-association
# Should return JSON with appID 6CL22HCV8F.com.ehnow.ca

# Android
curl https://ehnw.ca/.well-known/assetlinks.json
# Should return JSON array with package_name com.ehnow.eh
```

#### Test 2: URL Redirects (via curl)
```bash
# Post
curl -I https://ehnw.ca/p/VQ6EAOKbQdSnFkRmVUQAAA
# Should: 302 Location: com.ehnow.eh://post/63d47d6b-e6a1-4753-b713-0d4490ab8292

# Event
curl -I https://ehnw.ca/e/VQ6EAOKbQdSnFkRmVUQAAA
# Should: 302 Location: com.ehnow.eh://event/63d47d6b-e6a1-4753-b713-0d4490ab8292

# Group
curl -I https://ehnw.ca/g/VQ6EAOKbQdSnFkRmVUQAAA
# Should: 302 Location: com.ehnow.eh://group/63d47d6b-e6a1-4753-b713-0d4490ab8292

# User (no decode)
curl -I https://ehnw.ca/u/johndoe
# Should: 302 Location: com.ehnow.eh://user/johndoe
```

#### Test 3: iOS Device Testing

**Requirements:**
- Physical iOS device with EH app installed
- Device connected to WiFi (not cellular - carrier might block)

**Steps:**
1. Open Safari on iOS device
2. Navigate to: `https://ehnw.ca/p/VQ6EAOKbQdSnFkRmVUQAAA`
3. Should automatically open EH app to post
4. If not working:
   - Check universal links are enabled in app
   - Check Associated Domains capability
   - Check ehnw.ca is in Associated Domains list
   - Verify apple-app-site-association is accessible

**iOS Universal Links Debug:**
```bash
# On Mac with device connected:
xcrun simctl openurl booted https://ehnw.ca/p/VQ6EAOKbQdSnFkRmVUQAAA

# Check if iOS downloaded the apple-app-site-association:
# Settings → Safari → Advanced → Website Data → Search for "ehnw"
```

#### Test 4: Android Device Testing

**Requirements:**
- Physical Android device with EH app installed
- Device connected to WiFi

**Steps:**
1. Open Chrome on Android device
2. Navigate to: `https://ehnw.ca/p/VQ6EAOKbQdSnFkRmVUQAAA`
3. Should show dialog to open in EH app
4. If not working:
   - Check intent filters in AndroidManifest.xml
   - Check assetlinks.json is accessible
   - Verify SHA256 fingerprint matches

**Android App Links Debug:**
```bash
# Check if assetlinks.json is valid:
adb shell pm get-app-links com.ehnow.eh

# Verify specific domain:
adb shell pm verify-app-links --re-verify com.ehnow.eh
```

#### Test 5: Fallback Behavior

**Test when app NOT installed:**
1. Use device without EH app
2. Navigate to: `https://ehnw.ca/p/VQ6EAOKbQdSnFkRmVUQAAA`
3. CloudFront returns 302 to `com.ehnow.eh://post/...`
4. Browser attempts to open custom scheme
5. If app not installed:
   - iOS: May show "Cannot Open Page" or silently fail
   - Android: May show "No app found" dialog
6. User can then navigate to `/` which redirects to appropriate app store

**Note:** The 302 redirect to custom scheme doesn't automatically fallback. If app isn't installed, the redirect fails. This is standard behavior for deep links. The fallback page at `/` provides the store redirect as a secondary option.

---

## CloudFront Function Limitations

**What CloudFront Functions CAN'T do:**
- ❌ Make external HTTP requests
- ❌ Access databases
- ❌ Read/write to S3 directly
- ❌ Use Node.js modules
- ❌ Run for more than 1ms
- ❌ Use more than 2MB memory

**What CloudFront Functions CAN do:**
- ✅ URL parsing and manipulation
- ✅ Header manipulation
- ✅ Query string parsing
- ✅ Base64 encode/decode
- ✅ Redirects (301/302)
- ✅ Pure JavaScript transformations

**For our use case:**
- ✅ Base64url decode: YES (pure JavaScript)
- ✅ UUID formatting: YES (string manipulation)
- ✅ 302 redirect: YES (supported)
- ✅ Pattern matching: YES (if/else logic)

**Perfect fit for CloudFront Functions!**

---

## Monitoring and Debugging

### CloudFront Logs

**Enable logging on distribution:**
- Store logs in S3 bucket
- Monitor for errors in function execution
- Track redirect patterns

### CloudWatch Metrics

**Monitor:**
- Request count
- Error rate
- Function execution time
- Cache hit ratio

### Testing Tools

**Online validators:**
- iOS: https://search.developer.apple.com/appsearch-validation-tool/
- Android: https://developers.google.com/digital-asset-links/tools/generator

**Command line:**
```bash
# iOS validation
curl -I https://ehnw.ca/.well-known/apple-app-site-association

# Android validation
curl https://ehnw.ca/.well-known/assetlinks.json | jq
```

---

## Troubleshooting Guide

### Issue: Universal links not working on iOS

**Checklist:**
1. ✅ App has Associated Domains capability
2. ✅ ehnw.ca is in Associated Domains list
3. ✅ apple-app-site-association is accessible via HTTPS
4. ✅ apple-app-site-association returns 200 status
5. ✅ Content-Type is application/json
6. ✅ appID matches: TeamID.BundleID
7. ✅ Paths include "*" or specific paths
8. ✅ Device has downloaded the file (check Safari website data)

**Common issues:**
- **Redirects:** Apple won't follow redirects for apple-app-site-association
- **CDN caching:** Make sure file is always fresh
- **HTTPS required:** Must be served over HTTPS with valid cert
- **First install:** User must visit domain AFTER installing app
- **Safari only:** Universal links only work from Safari, not Chrome/Firefox

### Issue: App Links not working on Android

**Checklist:**
1. ✅ App has intent-filter with android:autoVerify="true"
2. ✅ assetlinks.json is accessible via HTTPS
3. ✅ assetlinks.json returns 200 status
4. ✅ Content-Type is application/json
5. ✅ package_name matches exactly
6. ✅ SHA256 fingerprint is correct (release cert, not debug)
7. ✅ Verified with: adb shell pm get-app-links

**Common issues:**
- **Wrong fingerprint:** Debug vs Release certificate
- **Not verified:** Run pm verify-app-links
- **Play Store:** Links may not work until app published
- **Subdomain:** Make sure assetlinks.json on correct domain

### Issue: CloudFront function not executing

**Check:**
1. Function is published (not in draft)
2. Function is associated with distribution
3. Event type is viewer-request
4. Distribution is deployed (not in-progress)
5. DNS points to CloudFront (not directly to S3)

### Issue: Base64 decode errors

**Common causes:**
- Invalid length (not 22 characters)
- Invalid characters (not base64url alphabet)
- Padding included (shouldn't have =)
- Wrong encoding (base64 instead of base64url)

**Test:**
```javascript
// Valid: VQ6EAOKbQdSnFkRmVUQAAA
// Invalid: VQ6EAOKbQdSnFkRmVUQAAA= (has padding)
// Invalid: VQ6EAOKbQdSn (too short)
// Invalid: VQ6EAOKbQdSnFkRmVUQAAA+ (invalid char +)
```

---

## Security Considerations

### HTTPS Only
- ✅ CloudFront enforces HTTPS
- ✅ Certificate validated
- ✅ TLS 1.2+

### No Sensitive Data in URLs
- ✅ Only public UUIDs in paths
- ✅ No auth tokens
- ✅ No personal information

### Rate Limiting
- CloudFront provides DDoS protection
- Consider adding AWS WAF if needed

### Input Validation
- CloudFront function validates base64url format
- Rejects invalid input
- No code injection risk (pure decoding)

---

## Cost Estimate

### CloudFront
- **Requests:** $0.0075 per 10,000 requests (viewer-request function)
- **Data transfer:** ~$0.085/GB (first 10TB)
- **Function executions:** Included in request pricing

### Example:
- 1M requests/month: ~$0.75
- 10GB data transfer: ~$0.85
- **Total: ~$1.60/month**

### S3
- **Storage:** Negligible (few KB for .well-known files)
- **Requests:** Most traffic served by CloudFront (cached)

**Estimated total: <$5/month**

---

## Future Enhancements

### 1. Analytics
Track:
- Which links are most clicked
- iOS vs Android traffic
- Conversion rate (web → app)
- Geographic distribution

**Implementation:** CloudFront logs + Athena queries

### 2. Short URL Management
- Admin interface to create short links
- Track click counts
- A/B testing different deep link formats

### 3. QR Codes
Generate QR codes for universal links:
```
https://ehnw.ca/p/VQ6EAOKbQdSnFkRmVUQAAA
```

Scan → Opens in app

---

## Rollback Plan

If issues arise:

### Option 1: Disable Function
1. Disassociate function from distribution
2. Traffic flows directly to S3 origin
3. Users see fallback HTML

### Option 2: Revert to Previous Version
1. CloudFront functions are versioned
2. Can associate previous version
3. No code redeployment needed

### Option 3: Full Rollback
1. Remove function association
2. Delete function
3. Update distribution to default behavior

**Rollback time: <5 minutes**
**No downtime** (gradual deployment)

---

## Success Criteria

**Phase 1 (MVP):**
- ✅ .well-known files accessible
- ✅ CloudFront function deployed
- ✅ URL decoding works correctly
- ✅ Redirects to correct deep links
- ✅ iOS universal links work
- ✅ Android app links work

**Phase 2 (Production Ready):**
- ✅ Tested on multiple devices
- ✅ Monitoring in place
- ✅ Error handling validated
- ✅ Performance acceptable (<100ms)
- ✅ Documentation complete

**Phase 3 (Optimized):**
- ✅ Analytics tracking
- ✅ Smart fallback implemented
- ✅ Load tested
- ✅ CDN cache optimized

---

## Questions Before Implementation

1. **CloudFront Distribution Status**
   - Is the ehnw.ca CloudFront distribution already created?
   - If not, should I create it now?

2. **Certificate Validation**
   - Has the ACM certificate validated yet?
   - Can I proceed with CloudFront setup?

3. **Testing Timeline**
   - When do you want to test on devices?
   - Do you have iOS/Android devices ready?

4. **Deployment Timing**
   - Deploy to production immediately?
   - Or create in staging first?

---

**Ready to implement when you give the go-ahead!**
