// Run: node tests/qrbill.test.mjs — Swiss QR-bill (IG QR-bill v2.4, SIX).
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const QRCode = require('../js/qrcode.js');
const Q = require('../js/qrbill.js');
let jsQR = null;
try { jsQR = require('jsqr'); } catch (e) { /* optional: decode test skipped */ }

let pass = 0;
let fail = 0;
function eq(name, actual, expected) {
  const ok = JSON.stringify(actual) === JSON.stringify(expected);
  if (ok) { pass++; console.log(`ok   ${name}`); }
  else { fail++; console.log(`FAIL ${name}\n     expected ${JSON.stringify(expected)}\n     got      ${JSON.stringify(actual)}`); }
}

const creditor = { name: 'Muster Malerei GmbH', street: 'Bahnhofstrasse', buildingNo: '12', postalCode: '8001', town: 'Zürich', country: 'CH' };
const debtor = { name: 'Anna Beispiel', street: 'Rue du Lac', buildingNo: '5', postalCode: '1003', town: 'Lausanne', country: 'CH' };
const QRIBAN = 'CH44 3199 9123 0008 8901 2';
const IBAN = 'CH93 0076 2011 6238 5295 7';

// IBAN
eq('QR-IBAN recognised', Q.validateIban(QRIBAN).qr, true);
eq('normal IBAN valid, not QR', [Q.validateIban(IBAN).valid, Q.validateIban(IBAN).qr], [true, false]);
eq('wrong check digit', Q.validateIban('CH93 0076 2011 6238 5295 8').error, 'checksum');
eq('foreign IBAN refused', Q.validateIban('DE89 3704 0044 0532 0130 00').error, 'country');

// References
const qrr = Q.makeQrReference('2026117');
eq('QR reference 27 digits, valid', [qrr.length, Q.isValidQrReference(qrr)], [27, true]);
eq('QR reference of example', Q.formatReference('QRR', qrr), '00 00000 00000 00000 00202 61178');
eq('IG example QR reference valid', Q.isValidQrReference('21 00000 00003 13947 14300 09017'), true);
eq('IG example creditor reference valid', Q.isValidCreditorReference('RF18 5390 0754 7034'), true);
eq('RF reference built and valid', Q.isValidCreditorReference(Q.makeCreditorReference('2026117')), true);

// Validation
const ok = { account: QRIBAN, creditor, amount: 1250.5, currency: 'CHF', debtor, referenceType: 'QRR', reference: qrr, message: 'Rechnung 2026117' };
eq('complete QR bill: no error', Q.validateBill(ok), []);
eq('QR-IBAN without QR reference', Q.validateBill({ ...ok, referenceType: 'NON', reference: '' }).includes('qrIbanNeedsQrr'), true);
eq('QR-IBAN in EUR refused', Q.validateBill({ ...ok, currency: 'EUR' }).includes('qrIbanCurrency'), true);
eq('normal IBAN, no reference, EUR, no amount: ok', Q.validateBill({ ...ok, account: IBAN, referenceType: 'NON', reference: '', currency: 'EUR', amount: null, debtor: null }), []);
eq('missing postal code', Q.validateBill({ ...ok, creditor: { ...creditor, postalCode: '' } }).includes('creditor_postalCode'), true);
eq('message over 140 chars', Q.validateBill({ ...ok, message: 'x'.repeat(141) }).includes('message'), true);

// Payload (IG 4.2.2): 31 lines, structured address "S", ends with EPD, no trailing line feed
const payload = Q.buildPayload(ok);
const lines = payload.split('\n');
eq('payload has 31 lines', lines.length, 31);
eq('payload header', lines.slice(0, 4), ['SPC', '0200', '1', 'CH4431999123000889012']);
eq('creditor structured address', lines.slice(4, 11), ['S', 'Muster Malerei GmbH', 'Bahnhofstrasse', '12', '8001', 'Zürich', 'CH']);
eq('amount and currency', lines.slice(18, 20), ['1250.50', 'CHF']);
eq('reference type and value', lines.slice(27, 29), ['QRR', qrr]);
eq('trailer', lines[30], 'EPD');

// Rendering
const htmlDe = Q.renderHTML(ok, 'de');
eq('German headings', ['Zahlteil', 'Empfangsschein', 'Konto / Zahlbar an'].every((h) => htmlDe.includes(h)), true);
eq('French headings', ['Section paiement', 'Récépissé'].every((h) => Q.renderHTML(ok, 'fr').includes(h)), true);
eq('QR code level M fits', QRCode.encode(payload, { ecl: 'M' }).size > 0, true);

if (jsQR) {
  const qr = QRCode.encode(payload, { ecl: 'M' });
  const scale = 6; const quiet = 4; const n = (qr.size + 2 * quiet) * scale;
  const px = new Uint8ClampedArray(n * n * 4);
  for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
    const ix = Math.floor(x / scale - quiet); const iy = Math.floor(y / scale - quiet);
    const dark = ix >= 0 && iy >= 0 && ix < qr.size && iy < qr.size && qr.modules[iy][ix];
    const i = (y * n + x) * 4; px[i] = px[i + 1] = px[i + 2] = dark ? 0 : 255; px[i + 3] = 255;
  }
  const r = jsQR(px, n, n, { inversionAttempts: 'dontInvert' });
  eq('QR code decodes back to the exact payload', r && r.data, payload);
} else {
  console.log('skip decode test (jsqr not installed)');
}

console.log(`\n${pass} passed, ${fail} failed`);
if (fail) process.exit(1);
