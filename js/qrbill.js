/*
 * Swiss QR-bill (payment part + receipt) — data, validation, payload and HTML.
 * Follows "Swiss Implementation Guidelines for the QR-bill" v2.4 (SIX, valid from 14.11.2026):
 * (SIX, Swiss Payment Standards: IG QR-bill v2.4, document link on the tool page)
 * - structured addresses only (address type "S")
 * - QR-IBAN (QR-IID 30000-31999) => QR reference (QRR), CHF only
 * - normal IBAN => Creditor Reference ISO 11649 (SCOR) or no reference (NON)
 * - error correction level M, Swiss cross 7 x 7 mm, QR code 46 x 46 mm, 210 x 105 mm layout
 * Pure functions, no network. Browser: window.QRBill (needs window.QRCode). Node: module.exports.
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory(require('./qrcode.js'));
  } else {
    root.QRBill = factory(root.QRCode);
  }
})(typeof self !== 'undefined' ? self : this, function (QRCode) {
  'use strict';

  var MAX_PAYLOAD = 997;
  var MAX_AMOUNT = 999999999.99;

  // Official headings (IG v2.4, Annex C).
  var LABELS = {
    fr: {
      paymentPart: 'Section paiement', receipt: 'Récépissé', account: 'Compte / Payable à', reference: 'Référence',
      additionalInfo: 'Informations supplémentaires', payableBy: 'Payable par', payableByBlank: 'Payable par (nom/adresse)',
      currency: 'Monnaie', amount: 'Montant', acceptancePoint: 'Point de dépôt', separate: 'A détacher avant le versement'
    },
    de: {
      paymentPart: 'Zahlteil', receipt: 'Empfangsschein', account: 'Konto / Zahlbar an', reference: 'Referenz',
      additionalInfo: 'Zusätzliche Informationen', payableBy: 'Zahlbar durch', payableByBlank: 'Zahlbar durch (Name/Adresse)',
      currency: 'Währung', amount: 'Betrag', acceptancePoint: 'Annahmestelle', separate: 'Vor der Einzahlung abzutrennen'
    },
    it: {
      paymentPart: 'Sezione pagamento', receipt: 'Ricevuta', account: 'Conto / Pagabile a', reference: 'Riferimento',
      additionalInfo: 'Informazioni supplementari', payableBy: 'Pagabile da', payableByBlank: 'Pagabile da (nome/indirizzo)',
      currency: 'Valuta', amount: 'Importo', acceptancePoint: 'Punto di accettazione', separate: 'Da staccare prima del versamento'
    },
    en: {
      paymentPart: 'Payment part', receipt: 'Receipt', account: 'Account / Payable to', reference: 'Reference',
      additionalInfo: 'Additional information', payableBy: 'Payable by', payableByBlank: 'Payable by (name/address)',
      currency: 'Currency', amount: 'Amount', acceptancePoint: 'Acceptance point', separate: 'Separate before paying in'
    }
  };

  var MONTHS = {
    fr: ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'],
    de: ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']
  };

  // ---------- characters (IG 4.1.1) ----------
  function allowedChar(cp) {
    return (cp >= 0x20 && cp <= 0x7E) || (cp >= 0xA0 && cp <= 0x17F) ||
      (cp >= 0x218 && cp <= 0x21B) || cp === 0x20AC;
  }

  var REPLACE = { '‘': "'", '’': "'", '‚': "'", '‛': "'", '′': "'",
    '“': '"', '”': '"', '„': '"', '″': '"',
    '‐': '-', '‑': '-', '‒': '-', '–': '-', '—': '-', '−': '-',
    '…': '...', ' ': ' ', ' ': ' ', ' ': ' ' };

  /** Make a value safe for one QR line: allowed characters only, no line breaks, trimmed, max length. */
  function sanitize(value, maxLen) {
    var s = String(value === null || value === undefined ? '' : value);
    var out = '';
    for (var i = 0; i < s.length; i++) {
      var ch = s.charAt(i);
      if (REPLACE[ch] !== undefined) { out += REPLACE[ch]; continue; }
      if (/[\r\n\t]/.test(ch)) { out += ' '; continue; }
      var cp = s.codePointAt(i);
      if (cp > 0xFFFF) i++; // surrogate pair (emoji...) => dropped
      if (allowedChar(cp)) out += ch;
    }
    out = out.replace(/ {2,}/g, ' ').trim();
    if (maxLen && out.length > maxLen) out = out.slice(0, maxLen).trim();
    return out;
  }

  // ---------- IBAN ----------
  function cleanIban(s) { return String(s || '').replace(/\s+/g, '').toUpperCase(); }

  function mod97(str) {
    var rem = 0;
    for (var i = 0; i < str.length; i++) {
      var c = str.charAt(i);
      var v = /[0-9]/.test(c) ? c : String(c.charCodeAt(0) - 55);
      for (var j = 0; j < v.length; j++) rem = (rem * 10 + Number(v.charAt(j))) % 97;
    }
    return rem;
  }

  function isQrIban(iban) {
    var s = cleanIban(iban);
    if (!/^(CH|LI)\d{7}/.test(s)) return false;
    var iid = Number(s.slice(4, 9));
    return iid >= 30000 && iid <= 31999;
  }

  /**
   * Validate a Swiss/Liechtenstein IBAN (21 characters, ISO 13616 mod 97 check).
   * Returns { valid, iban, qr, error } with error in: 'empty' | 'country' | 'format' | 'checksum' | null.
   */
  function validateIban(input) {
    var iban = cleanIban(input);
    var res = { valid: false, iban: iban, qr: false, error: null };
    if (!iban) { res.error = 'empty'; return res; }
    if (!/^(CH|LI)/.test(iban)) { res.error = 'country'; return res; }
    if (!/^(CH|LI)\d{2}\d{5}[0-9A-Z]{12}$/.test(iban)) { res.error = 'format'; return res; }
    if (mod97(iban.slice(4) + iban.slice(0, 4)) !== 1) { res.error = 'checksum'; return res; }
    res.valid = true;
    res.qr = isQrIban(iban);
    return res;
  }

  // ---------- references ----------
  var MOD10_TABLE = [0, 9, 4, 6, 8, 2, 7, 1, 3, 5];

  /** Check digit "modulo 10 recursive" (IG Annex B) of a string of digits. */
  function mod10Recursive(digits) {
    var carry = 0;
    var s = String(digits);
    for (var i = 0; i < s.length; i++) carry = MOD10_TABLE[(carry + Number(s.charAt(i))) % 10];
    return (10 - carry) % 10;
  }

  function isValidQrReference(ref) {
    var s = String(ref || '').replace(/\s+/g, '');
    if (!/^\d{27}$/.test(s) || /^0+$/.test(s)) return false;
    return mod10Recursive(s.slice(0, 26)) === Number(s.charAt(26));
  }

  /** QR reference: optional bank prefix (digits) + zero padding + base digits (26) + check digit. */
  function makeQrReference(base, prefix) {
    var b = String(base || '').replace(/\D/g, '');
    var p = String(prefix || '').replace(/\D/g, '');
    if (p.length + b.length > 26) throw new Error('QR reference too long');
    var body = p + new Array(26 - p.length - b.length + 1).join('0') + b;
    if (/^0+$/.test(body)) throw new Error('QR reference must not be zero');
    return body + mod10Recursive(body);
  }

  /** Creditor Reference ISO 11649: "RF" + 2 check digits + payload (1-21 alphanumeric). */
  function makeCreditorReference(payload) {
    var p = String(payload || '').replace(/\s+/g, '').toUpperCase();
    if (!/^[0-9A-Z]{1,21}$/.test(p)) throw new Error('Invalid creditor reference payload');
    var check = 98 - mod97(p + 'RF00');
    return 'RF' + (check < 10 ? '0' : '') + check + p;
  }

  function isValidCreditorReference(ref) {
    var s = String(ref || '').replace(/\s+/g, '').toUpperCase();
    if (!/^RF\d{2}[0-9A-Z]{1,21}$/.test(s)) return false;
    return mod97(s.slice(4) + s.slice(0, 4)) === 1;
  }

  // ---------- formatting for the visible part ----------
  function groups(s, size, firstLen) {
    var out = [];
    var i = 0;
    if (firstLen) { out.push(s.slice(0, firstLen)); i = firstLen; }
    for (; i < s.length; i += size) out.push(s.slice(i, i + size));
    return out.join(' ');
  }

  function formatIban(iban) { return groups(cleanIban(iban), 4); }

  function formatReference(type, ref) {
    var s = String(ref || '').replace(/\s+/g, '');
    if (type === 'QRR') return groups(s, 5, 2);
    if (type === 'SCOR') return groups(s, 4);
    return '';
  }

  /** Amount for the QR payload: "1590.00" (no thousands separator). */
  function payloadAmount(n) { return (Math.round(Number(n) * 100) / 100).toFixed(2); }

  /** Amount for the visible part: "1 590.00" (space as thousands separator). */
  function formatAmount(n) {
    var parts = payloadAmount(n).split('.');
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
    return parts.join('.');
  }

  // ---------- data model ----------
  function addressComplete(a) {
    return !!(a && sanitize(a.name) && sanitize(a.postalCode) && sanitize(a.town));
  }

  function cleanAddress(a) {
    return {
      name: sanitize(a.name),
      street: sanitize(a.street),
      buildingNo: sanitize(a.buildingNo),
      postalCode: sanitize(a.postalCode),
      town: sanitize(a.town),
      country: sanitize(a.country || 'CH').toUpperCase()
    };
  }

  /**
   * Validate a bill. Returns an array of error codes (empty = OK):
   * iban_empty|iban_country|iban_format|iban_checksum, creditor_name, creditor_postalCode, creditor_town,
   * creditor_country, creditor_tooLong, currency, amount, qrIbanNeedsQrr, qrrNeedsQrIban, qrIbanCurrency,
   * reference, debtor, message, payloadTooLong.
   */
  function validateBill(bill) {
    var errors = [];
    var iv = validateIban(bill.account);
    if (!iv.valid) errors.push('iban_' + iv.error);
    var c = bill.creditor || {};
    if (!sanitize(c.name)) errors.push('creditor_name');
    if (!sanitize(c.postalCode)) errors.push('creditor_postalCode');
    if (!sanitize(c.town)) errors.push('creditor_town');
    if (!/^[A-Z]{2}$/.test(String(c.country || ''))) errors.push('creditor_country');
    if (sanitize(c.name).length > 70 || sanitize(c.street).length > 70 || sanitize(c.buildingNo).length > 16 ||
      sanitize(c.postalCode).length > 16 || sanitize(c.town).length > 35) errors.push('creditor_tooLong');
    if (bill.currency !== 'CHF' && bill.currency !== 'EUR') errors.push('currency');
    if (bill.amount !== null && bill.amount !== undefined) {
      var a = Number(bill.amount);
      if (!isFinite(a) || a < 0.01 || a > MAX_AMOUNT) errors.push('amount');
    }
    var type = bill.referenceType;
    if (iv.valid && iv.qr && type !== 'QRR') errors.push('qrIbanNeedsQrr');
    if (iv.valid && !iv.qr && type === 'QRR') errors.push('qrrNeedsQrIban');
    if (iv.valid && iv.qr && bill.currency !== 'CHF') errors.push('qrIbanCurrency');
    if (type === 'QRR' && !isValidQrReference(bill.reference)) errors.push('reference');
    if (type === 'SCOR' && !isValidCreditorReference(bill.reference)) errors.push('reference');
    if (type === 'NON' && bill.reference) errors.push('reference');
    if (['QRR', 'SCOR', 'NON'].indexOf(type) === -1) errors.push('reference');
    if (bill.debtor && !addressComplete(bill.debtor)) errors.push('debtor');
    if (sanitize(bill.message).length > 140) errors.push('message');
    if (!errors.length && buildPayload(bill).length > MAX_PAYLOAD) errors.push('payloadTooLong');
    return errors;
  }

  /** Swiss QR Code content (IG 4.2.2), lines separated by LF, no line after "EPD". */
  function buildPayload(bill) {
    var c = cleanAddress(bill.creditor || {});
    var d = bill.debtor ? cleanAddress(bill.debtor) : null;
    var hasAmount = bill.amount !== null && bill.amount !== undefined && bill.amount !== '';
    var lines = [
      'SPC', '0200', '1',
      cleanIban(bill.account),
      'S', c.name, c.street, c.buildingNo, c.postalCode, c.town, c.country,
      '', '', '', '', '', '', '', // ultimate creditor: must stay empty
      hasAmount ? payloadAmount(bill.amount) : '',
      bill.currency,
      d ? 'S' : '', d ? d.name : '', d ? d.street : '', d ? d.buildingNo : '', d ? d.postalCode : '', d ? d.town : '', d ? d.country : '',
      bill.referenceType,
      bill.referenceType === 'NON' ? '' : String(bill.reference || '').replace(/\s+/g, '').toUpperCase(),
      sanitize(bill.message, 140),
      'EPD'
    ];
    return lines.join('\n');
  }

  // ---------- from an invoice of the app ----------
  function pad(n, len) { var s = String(n); while (s.length < len) s = '0' + s; return s; }

  /** Digits identifying one invoice: YYYYMM + 4-digit sequence (e.g. "2026110001"). */
  function invoiceRefBase(month, seq) {
    return String(month).replace('-', '') + pad(seq, 4);
  }

  function monthLabel(month, lang) {
    var p = String(month).split('-');
    var names = MONTHS[lang] || MONTHS.fr;
    return names[Number(p[1]) - 1] + ' ' + p[0];
  }

  /**
   * Build the bill of one invoice.
   * settings: stableName, street, buildingNo, postalCode, town, country, iban, refType ('SCOR'|'NON'), qrrPrefix, currency
   * owner: name, street, buildingNo, postalCode, town, country (debtor left empty when incomplete)
   * info: { month, seq, number, horses: [names], lang }
   * Returns { bill, errors }.
   */
  function fromInvoice(settings, owner, amount, info) {
    var s = settings || {};
    var iv = validateIban(s.iban);
    var currency = s.currency === 'EUR' ? 'EUR' : 'CHF';
    var lang = info.lang === 'de' ? 'de' : 'fr';
    var base = invoiceRefBase(info.month, info.seq);
    var type;
    var reference = '';
    try {
      if (iv.valid && iv.qr) {
        type = 'QRR';
        reference = makeQrReference(base, s.qrrPrefix);
      } else if (s.refType === 'NON') {
        type = 'NON';
      } else {
        type = 'SCOR';
        reference = makeCreditorReference(base);
      }
    } catch (e) {
      type = 'QRR';
      reference = '';
    }
    var word = lang === 'de' ? 'Rechnung' : 'Facture';
    var horses = (info.horses || []).map(function (h) { return sanitize(h); }).filter(Boolean);
    var message = word + ' ' + info.number + ' - ' + monthLabel(info.month, lang) + (horses.length ? ' - ' + horses.join(', ') : '');
    message = sanitize(message);
    if (message.length > 140) message = message.slice(0, 137).trim() + '...';
    var debtor = null;
    if (owner && addressComplete(owner)) {
      debtor = cleanAddress(owner);
      debtor.name = debtor.name.slice(0, 70);
      debtor.street = debtor.street.slice(0, 70);
      debtor.buildingNo = debtor.buildingNo.slice(0, 16);
      debtor.postalCode = debtor.postalCode.slice(0, 16);
      debtor.town = debtor.town.slice(0, 35);
      if (!/^[A-Z]{2}$/.test(debtor.country)) debtor.country = 'CH';
    }
    var bill = {
      account: iv.iban,
      creditor: {
        name: s.stableName, street: s.street, buildingNo: s.buildingNo,
        postalCode: s.postalCode, town: s.town, country: String(s.country || 'CH').trim().toUpperCase()
      },
      amount: amount,
      currency: currency,
      debtor: debtor,
      referenceType: type,
      reference: reference,
      message: message
    };
    return { bill: bill, errors: validateBill(bill) };
  }

  // ---------- HTML (210 x 105 mm) ----------
  function esc(s) {
    return String(s === null || s === undefined ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function addressLines(a) {
    var c = cleanAddress(a);
    var lines = [c.name];
    var street = (c.street + ' ' + c.buildingNo).trim();
    if (street) lines.push(street);
    lines.push((c.country !== 'CH' ? c.country + '-' : '') + (c.postalCode + ' ' + c.town).trim());
    return lines;
  }

  /** Blank field with corner marks (IG 3.5.4 / 3.6.2), size in mm, line 0.75 pt. */
  function cornerBox(w, h, cls) {
    var k = 3;
    var path = 'M0 ' + k + 'V0H' + k + 'M' + (w - k) + ' 0H' + w + 'V' + k +
      'M' + w + ' ' + (h - k) + 'V' + h + 'H' + (w - k) + 'M' + k + ' ' + h + 'H0V' + (h - k);
    return '<svg class="' + cls + '" width="' + w + 'mm" height="' + h + 'mm" viewBox="-0.15 -0.15 ' + (w + 0.3) + ' ' + (h + 0.3) + '" aria-hidden="true">' +
      '<path d="' + path + '" fill="none" stroke="#000" stroke-width="0.2646"/></svg>';
  }

  var SCISSORS = '<svg class="qrb-scissors" viewBox="0 0 24 24" aria-hidden="true"><g fill="none" stroke="#000" stroke-width="1.6">' +
    '<circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M8.2 7.8 20 18M8.2 16.2 20 6"/></g></svg>';

  /** Swiss QR Code as SVG: 46 x 46 mm, Swiss cross 7 x 7 mm in the centre. */
  function qrSvg(payload) {
    var qr = QRCode.encode(payload, { ecl: 'M' });
    var n = qr.size;
    var c = n * 7 / 46;           // cross logo: 7 mm
    var o = (n - c) / 2;
    var b = c / 14;               // white border
    var s = c - 2 * b;            // black square
    var arm = s * 6 / 32 * 1.25;  // cross arm width
    var len = s * 20 / 32 * 1.05; // cross length
    var cx = n / 2;
    return '<svg class="qrb-code" width="46mm" height="46mm" viewBox="0 0 ' + n + ' ' + n + '" shape-rendering="crispEdges" ' +
      'role="img" aria-label="Swiss QR Code" data-version="' + qr.version + '" data-size="' + n + '">' +
      '<rect width="' + n + '" height="' + n + '" fill="#fff"/>' +
      '<path d="' + QRCode.toPath(qr) + '" fill="#000"/>' +
      '<g shape-rendering="geometricPrecision">' +
      '<rect x="' + o + '" y="' + o + '" width="' + c + '" height="' + c + '" fill="#fff"/>' +
      '<rect x="' + (o + b) + '" y="' + (o + b) + '" width="' + s + '" height="' + s + '" fill="#000"/>' +
      '<rect x="' + (cx - arm / 2) + '" y="' + (cx - len / 2) + '" width="' + arm + '" height="' + len + '" fill="#fff"/>' +
      '<rect x="' + (cx - len / 2) + '" y="' + (cx - arm / 2) + '" width="' + len + '" height="' + arm + '" fill="#fff"/>' +
      '</g></svg>';
  }

  function block(heading, lines) {
    return '<h4>' + esc(heading) + '</h4><p>' + lines.map(esc).join('<br>') + '</p>';
  }

  /** HTML of the payment part with receipt. lang: 'fr' | 'de' | 'it' | 'en'. */
  function renderHTML(bill, lang) {
    var L = LABELS[lang] || LABELS.fr;
    var payload = buildPayload(bill);
    var account = [formatIban(bill.account)].concat(addressLines(bill.creditor));
    var ref = bill.referenceType !== 'NON' ? formatReference(bill.referenceType, bill.reference) : '';
    var hasAmount = bill.amount !== null && bill.amount !== undefined && bill.amount !== '';
    var amount = hasAmount ? formatAmount(bill.amount) : '';
    var message = sanitize(bill.message, 140);

    function debtorBlock(receipt) {
      if (bill.debtor) return block(L.payableBy, addressLines(bill.debtor));
      return '<h4>' + esc(L.payableByBlank) + '</h4>' + (receipt ? cornerBox(52, 20, 'qrb-box') : cornerBox(65, 25, 'qrb-box'));
    }

    function amountBlock(receipt) {
      return '<div class="qrb-cur"><h4>' + esc(L.currency) + '</h4><p>' + esc(bill.currency) + '</p></div>' +
        '<div class="qrb-amt"><h4>' + esc(L.amount) + '</h4>' +
        (hasAmount ? '<p>' + esc(amount) + '</p>' : (receipt ? cornerBox(30, 10, 'qrb-box') : cornerBox(40, 15, 'qrb-box'))) + '</div>';
    }

    return '<div class="qrb" lang="' + esc(lang) + '" data-payload="' + esc(payload) + '">' +
      '<span class="qrb-cut-h" title="' + esc(L.separate) + '">' + SCISSORS + '</span>' +
      '<span class="qrb-cut-v" title="' + esc(L.separate) + '">' + SCISSORS + '</span>' +
      '<section class="qrb-receipt">' +
      '<h3 class="qrb-title">' + esc(L.receipt) + '</h3>' +
      '<div class="qrb-r-info">' + block(L.account, account) + (ref ? block(L.reference, [ref]) : '') + debtorBlock(true) + '</div>' +
      '<div class="qrb-r-amount">' + amountBlock(true) + '</div>' +
      '<div class="qrb-r-accept">' + esc(L.acceptancePoint) + '</div>' +
      '</section>' +
      '<section class="qrb-pay">' +
      '<h3 class="qrb-title">' + esc(L.paymentPart) + '</h3>' +
      '<div class="qrb-qr">' + qrSvg(payload) + '</div>' +
      '<div class="qrb-p-amount">' + amountBlock(false) + '</div>' +
      '<div class="qrb-p-info">' + block(L.account, account) + (ref ? block(L.reference, [ref]) : '') +
      (message ? block(L.additionalInfo, [message]) : '') + debtorBlock(false) + '</div>' +
      '</section></div>';
  }

  return {
    LABELS: LABELS,
    sanitize: sanitize,
    cleanIban: cleanIban,
    validateIban: validateIban,
    isQrIban: isQrIban,
    mod10Recursive: mod10Recursive,
    isValidQrReference: isValidQrReference,
    makeQrReference: makeQrReference,
    makeCreditorReference: makeCreditorReference,
    isValidCreditorReference: isValidCreditorReference,
    formatIban: formatIban,
    formatReference: formatReference,
    formatAmount: formatAmount,
    payloadAmount: payloadAmount,
    invoiceRefBase: invoiceRefBase,
    validateBill: validateBill,
    buildPayload: buildPayload,
    fromInvoice: fromInvoice,
    renderHTML: renderHTML,
    qrSvg: qrSvg
  };
});
