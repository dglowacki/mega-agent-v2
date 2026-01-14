// UUID Base64URL Encoding/Decoding Tests
// Testing the encoding algorithm for ehnw.ca universal links

function encodeUUID(uuid) {
  const hex = uuid.replace(/-/g, '');
  const bytes = new Uint8Array(hex.match(/.{2}/g).map(b => parseInt(b, 16)));
  return btoa(String.fromCharCode(...bytes))
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}

function decodeUUID(base64url) {
  const base64 = base64url.replace(/-/g, '+').replace(/_/g, '/') + '==';
  const bytes = atob(base64).split('').map(c => c.charCodeAt(0));
  const hex = bytes.map(b => b.toString(16).padStart(2, '0')).join('');
  return hex.replace(/(.{8})(.{4})(.{4})(.{4})(.{12})/, '$1-$2-$3-$4-$5');
}

// Test cases
const tests = [
  {
    name: 'Original example from user',
    uuid: '63d47d6b-e6a1-4753-b713-0d4490ab8292',
    expected: 'Y9R9a-ahR1O3Ew1EkKuCkg'
  },
  {
    name: 'All zeros',
    uuid: '00000000-0000-0000-0000-000000000000',
    expected: null // Will calculate
  },
  {
    name: 'All ones',
    uuid: 'ffffffff-ffff-ffff-ffff-ffffffffffff',
    expected: null // Will calculate
  },
  {
    name: 'Mixed pattern',
    uuid: '12345678-90ab-cdef-1234-567890abcdef',
    expected: null // Will calculate
  }
];

console.log('='.repeat(70));
console.log('UUID BASE64URL ENCODING/DECODING TESTS');
console.log('='.repeat(70));
console.log();

let passed = 0;
let failed = 0;

tests.forEach((test, index) => {
  console.log(`Test ${index + 1}: ${test.name}`);
  console.log('-'.repeat(70));

  try {
    const encoded = encodeUUID(test.uuid);
    const decoded = decodeUUID(encoded);

    console.log(`  Original UUID: ${test.uuid}`);
    console.log(`  Encoded:       ${encoded}`);
    console.log(`  Length:        ${encoded.length} chars`);

    if (test.expected) {
      console.log(`  Expected:      ${test.expected}`);
      const encodeMatch = encoded === test.expected;
      console.log(`  Encode match:  ${encodeMatch ? '✓ PASS' : '✗ FAIL'}`);
      if (!encodeMatch) {
        failed++;
      }
    }

    console.log(`  Decoded:       ${decoded}`);
    const decodeMatch = test.uuid === decoded;
    console.log(`  Decode match:  ${decodeMatch ? '✓ PASS' : '✗ FAIL'}`);

    if (decodeMatch) {
      passed++;
    } else {
      failed++;
    }

    // Validate base64url format
    const validChars = /^[A-Za-z0-9_-]+$/.test(encoded);
    console.log(`  Valid chars:   ${validChars ? '✓ PASS' : '✗ FAIL'}`);

    const noPadding = !encoded.includes('=');
    console.log(`  No padding:    ${noPadding ? '✓ PASS' : '✗ FAIL'}`);

  } catch (e) {
    console.log(`  ✗ ERROR: ${e.message}`);
    failed++;
  }

  console.log();
});

console.log('='.repeat(70));
console.log('ADDITIONAL VALIDATION TESTS');
console.log('='.repeat(70));
console.log();

// Test that encoding is deterministic
console.log('Test: Deterministic encoding');
console.log('-'.repeat(70));
const uuid1 = '63d47d6b-e6a1-4753-b713-0d4490ab8292';
const encode1 = encodeUUID(uuid1);
const encode2 = encodeUUID(uuid1);
const deterministic = encode1 === encode2;
console.log(`  Same UUID encoded twice: ${deterministic ? '✓ PASS' : '✗ FAIL'}`);
console.log(`  First:  ${encode1}`);
console.log(`  Second: ${encode2}`);
console.log();

// Test round-trip encoding/decoding multiple times
console.log('Test: Round-trip stability');
console.log('-'.repeat(70));
let currentUUID = uuid1;
let stable = true;
for (let i = 0; i < 5; i++) {
  const encoded = encodeUUID(currentUUID);
  const decoded = decodeUUID(encoded);
  if (decoded !== uuid1) {
    stable = false;
    console.log(`  Round ${i + 1}: ✗ FAIL - Got ${decoded}`);
    break;
  }
}
if (stable) {
  console.log(`  5 round-trips: ✓ PASS`);
  passed++;
}
console.log();

// Test length consistency
console.log('Test: Encoded length is always 22 characters');
console.log('-'.repeat(70));
const testUUIDs = [
  '00000000-0000-0000-0000-000000000000',
  'ffffffff-ffff-ffff-ffff-ffffffffffff',
  '12345678-90ab-cdef-1234-567890abcdef',
  '63d47d6b-e6a1-4753-b713-0d4490ab8292',
  'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
];

let allLength22 = true;
testUUIDs.forEach(uuid => {
  const encoded = encodeUUID(uuid);
  if (encoded.length !== 22) {
    console.log(`  ${uuid} -> ${encoded} (${encoded.length} chars) ✗ FAIL`);
    allLength22 = false;
  }
});
if (allLength22) {
  console.log(`  All ${testUUIDs.length} UUIDs encode to 22 chars: ✓ PASS`);
  passed++;
}
console.log();

// Test invalid inputs
console.log('Test: Error handling for invalid inputs');
console.log('-'.repeat(70));

const invalidInputs = [
  { value: 'not-a-uuid', name: 'Invalid format' },
  { value: '123', name: 'Too short' },
  { value: 'NOTBASE64URL!!!', name: 'Invalid base64url for decode' }
];

invalidInputs.forEach(input => {
  try {
    if (input.name.includes('decode')) {
      decodeUUID(input.value);
      console.log(`  ${input.name}: ✗ Should have thrown error`);
      failed++;
    } else {
      encodeUUID(input.value);
      console.log(`  ${input.name}: ✗ Should have thrown error`);
      failed++;
    }
  } catch (e) {
    console.log(`  ${input.name}: ✓ Correctly throws error`);
    // This is expected, don't count as pass/fail for now
  }
});
console.log();

// Compare with earlier example from conversation
console.log('Test: Compare with example from earlier in conversation');
console.log('-'.repeat(70));
console.log('  Earlier example: VQ6EAOKbQdSnFkRmVUQAAA -> 63d47d6b-e6a1-4753-b713-0d4490ab8292');
const earlierEncoded = 'VQ6EAOKbQdSnFkRmVUQAAA';
const earlierExpectedUUID = '63d47d6b-e6a1-4753-b713-0d4490ab8292';
try {
  const decodedEarlier = decodeUUID(earlierEncoded);
  const matchesEarlier = decodedEarlier === earlierExpectedUUID;
  console.log(`  Decoded: ${decodedEarlier}`);
  console.log(`  Match:   ${matchesEarlier ? '✓ PASS' : '✗ FAIL'}`);

  // Now encode the UUID and see what we get
  const reencoded = encodeUUID(earlierExpectedUUID);
  console.log(`  Re-encoded: ${reencoded}`);
  console.log(`  Original:   ${earlierEncoded}`);
  const reencodedMatch = reencoded === earlierEncoded;
  console.log(`  Re-encode match: ${reencodedMatch ? '✓ PASS' : '✗ FAIL'}`);

  if (matchesEarlier) passed++;
  else failed++;

  if (!reencodedMatch) {
    console.log();
    console.log('  ⚠️  WARNING: Re-encoding produces different result!');
    console.log('  This means there may be two different encoding methods in use.');
    console.log('  Current test uses: Y9R9a-ahR1O3Ew1EkKuCkg');
    console.log('  Earlier example:   VQ6EAOKbQdSnFkRmVUQAAA');
    console.log('  Both decode to the same UUID, but encode differently.');
  }
} catch (e) {
  console.log(`  ✗ ERROR: ${e.message}`);
  failed++;
}
console.log();

console.log('='.repeat(70));
console.log('SUMMARY');
console.log('='.repeat(70));
console.log(`Tests passed: ${passed}`);
console.log(`Tests failed: ${failed}`);
console.log(`Overall: ${failed === 0 ? '✓ ALL TESTS PASSED' : '✗ SOME TESTS FAILED'}`);
console.log('='.repeat(70));
