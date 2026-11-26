// Swiss QR-bill generator UI. Everything stays in this browser tab: no network, no cookies, no storage.
import './qrcode.js';
import './qrbill.js';

const Q = window.QRBill;
const LANG = document.documentElement.lang.startsWith('fr') ? 'fr' : 'de';
const T = {
  de: {
    iban_empty: 'IBAN fehlt.',
    iban_country: 'Nur Schweizer (CH) oder Liechtensteiner (LI) IBAN sind für die QR-Rechnung zulässig.',
    iban_format: 'IBAN unvollständig oder falsch aufgebaut (21 Zeichen).',
    iban_checksum: 'Prüfziffer der IBAN stimmt nicht – Tippfehler?',
    creditor_name: 'Name des Zahlungsempfängers fehlt.',
    creditor_postalCode: 'PLZ des Zahlungsempfängers fehlt.',
    creditor_town: 'Ort des Zahlungsempfängers fehlt.',
    creditor_country: 'Land: zwei Buchstaben, z. B. CH.',
    creditor_tooLong: 'Eine Angabe des Zahlungsempfängers ist zu lang (Name max. 70, Ort max. 35 Zeichen).',
    currency: 'Währung: CHF oder EUR.',
    amount: 'Betrag zwischen 0.01 und 999 999 999.99 eingeben – oder leer lassen.',
    qrIbanNeedsQrr: 'Mit einer QR-IBAN ist eine QR-Referenz (27 Ziffern) Pflicht. Tipp: Rechnungsnummer eingeben und «Referenz erzeugen» klicken.',
    qrrNeedsQrIban: 'Eine QR-Referenz geht nur mit einer QR-IBAN.',
    qrIbanCurrency: 'Mit einer QR-IBAN ist nur CHF möglich.',
    reference: 'Referenz ungültig. Mit normaler IBAN: leer lassen oder eine RF-Referenz (Creditor Reference).',
    debtor: 'Zahlungspflichtiger: Name, PLZ und Ort angeben – oder das Häkchen entfernen.',
    message: 'Zusätzliche Informationen: höchstens 140 Zeichen.',
    payloadTooLong: 'Zu viele Angaben für den QR-Code – Texte kürzen.',
    ok: 'Alles korrekt: Der Zahlteil kann gedruckt oder als PDF gespeichert werden.',
    noNumber: 'Zuerst eine Rechnungsnummer eingeben.',
    badNumber: 'Für eine QR-Referenz braucht die Rechnungsnummer Ziffern (max. 26).',
    badNumberRf: 'Für eine RF-Referenz: 1 bis 21 Buchstaben oder Ziffern.',
    qrHint: 'QR-IBAN erkannt: QR-Referenz nötig.',
    ibanHint: 'Normale IBAN: Referenz leer lassen oder RF-Referenz.',
    fix: 'Bitte korrigieren:',
  },
  fr: {
    iban_empty: 'IBAN manquante.',
    iban_country: 'Seules les IBAN suisses (CH) ou liechtensteinoises (LI) sont admises pour la QR-facture.',
    iban_format: 'IBAN incomplète ou mal construite (21 caractères).',
    iban_checksum: 'La clé de contrôle de l’IBAN est fausse – faute de frappe ?',
    creditor_name: 'Nom du bénéficiaire manquant.',
    creditor_postalCode: 'NPA du bénéficiaire manquant.',
    creditor_town: 'Localité du bénéficiaire manquante.',
    creditor_country: 'Pays : deux lettres, p. ex. CH.',
    creditor_tooLong: 'Une donnée du bénéficiaire est trop longue (nom 70, localité 35 caractères au maximum).',
    currency: 'Monnaie : CHF ou EUR.',
    amount: 'Montant entre 0.01 et 999 999 999.99 – ou laisser vide.',
    qrIbanNeedsQrr: 'Avec une QR-IBAN, une référence QR (27 chiffres) est obligatoire. Astuce : saisissez le numéro de facture et cliquez sur « Créer la référence ».',
    qrrNeedsQrIban: 'Une référence QR ne fonctionne qu’avec une QR-IBAN.',
    qrIbanCurrency: 'Avec une QR-IBAN, seul le CHF est possible.',
    reference: 'Référence invalide. Avec une IBAN normale : laisser vide ou une référence RF (Creditor Reference).',
    debtor: 'Payeur : indiquer nom, NPA et localité – ou décocher la case.',
    message: 'Informations supplémentaires : 140 caractères au maximum.',
    payloadTooLong: 'Trop de données pour le code QR – raccourcissez les textes.',
    ok: 'Tout est correct : la section paiement peut être imprimée ou enregistrée en PDF.',
    noNumber: 'Saisissez d’abord un numéro de facture.',
    badNumber: 'Pour une référence QR, le numéro de facture doit contenir des chiffres (26 au maximum).',
    badNumberRf: 'Pour une référence RF : 1 à 21 lettres ou chiffres.',
    qrHint: 'QR-IBAN détectée : référence QR nécessaire.',
    ibanHint: 'IBAN normale : laisser la référence vide ou une référence RF.',
    fix: 'À corriger :',
  },
}[LANG];

const EXAMPLE = {
  iban: 'CH44 3199 9123 0008 8901 2', name: 'Muster Malerei GmbH', street: 'Bahnhofstrasse', no: '12',
  zip: '8001', town: 'Zürich', country: 'CH', amount: '1250.50', currency: 'CHF', number: '2026117',
  message: LANG === 'de' ? 'Rechnung 2026117 vom 26.11.2026' : 'Facture 2026117 du 26.11.2026',
  debtor: true, d_name: 'Anna Beispiel', d_street: 'Rue du Lac', d_no: '5', d_zip: '1003', d_town: 'Lausanne', d_country: 'CH',
};

const tool = document.querySelector('[data-tool="qr"]');
if (tool && Q) {
  const form = tool.querySelector('form');
  const $ = (id) => form.querySelector(`[name="${id}"]`);
  const result = tool.querySelector('.result');
  const hint = tool.querySelector('#qr-ref-hint');
  const preview = tool.querySelector('.qr-preview');
  const sheet = tool.querySelector('.qr-sheet');
  const debtorBox = tool.querySelector('.qr-debtor');
  const v = (id) => ($(id).value || '').trim();

  function readBill() {
    const iban = Q.validateIban(v('iban'));
    let ref = v('reference').replace(/\s+/g, '').toUpperCase();
    let type = 'NON';
    if (iban.valid && iban.qr) type = 'QRR';
    else if (/^\d{27}$/.test(ref)) type = 'QRR';
    else if (ref) type = 'SCOR';
    const amountTxt = v('amount').replace(/['’\s]/g, '').replace(',', '.');
    const bill = {
      account: v('iban'),
      creditor: { name: v('name'), street: v('street'), buildingNo: v('no'), postalCode: v('zip'), town: v('town'), country: v('country').toUpperCase() || 'CH' },
      amount: amountTxt === '' ? null : Number(amountTxt),
      currency: v('currency'),
      debtor: $('debtor').checked
        ? { name: v('d_name'), street: v('d_street'), buildingNo: v('d_no'), postalCode: v('d_zip'), town: v('d_town'), country: v('d_country').toUpperCase() || 'CH' }
        : null,
      referenceType: type,
      reference: type === 'NON' ? '' : ref,
      message: v('message'),
    };
    return { bill, iban };
  }

  function update() {
    debtorBox.hidden = !$('debtor').checked;
    const { bill, iban } = readBill();
    if (!v('iban') && !v('name') && !v('zip') && !v('town')) {
      result.innerHTML = '';
      result.classList.remove('warn');
      hint.textContent = '';
      sheet.innerHTML = '';
      preview.hidden = true;
      return;
    }
    hint.textContent = iban.valid ? (iban.qr ? T.qrHint : T.ibanHint) : '';
    let errors = Q.validateBill(bill);
    if (iban.valid && iban.qr && !bill.reference) errors = errors.map((c) => (c === 'reference' ? 'qrIbanNeedsQrr' : c));
    const uniq = [...new Set(errors)];
    if (uniq.length) {
      result.innerHTML = `<p><strong>${T.fix}</strong></p><ul>${uniq.map((c) => `<li>${T[c] || c}</li>`).join('')}</ul>`;
      result.classList.add('warn');
      sheet.innerHTML = '';
      preview.hidden = true;
      tool.querySelector('.qr-print').disabled = true;
      return;
    }
    result.classList.remove('warn');
    result.innerHTML = `<p>${T.ok}</p>`;
    sheet.innerHTML = Q.renderHTML(bill, v('billlang'));
    preview.hidden = false;
    tool.querySelector('.qr-print').disabled = false;
    fit();
  }

  function fit() {
    const qrb = sheet.querySelector('.qrb');
    if (!qrb) return;
    qrb.style.transform = '';
    const full = qrb.getBoundingClientRect().width;
    const avail = preview.clientWidth;
    const k = full > avail && avail > 0 ? avail / full : 1;
    qrb.style.transform = k < 1 ? `scale(${k})` : '';
    qrb.style.transformOrigin = '0 0';
    sheet.style.height = `${qrb.getBoundingClientRect().height}px`;
  }

  function makeRef() {
    const num = v('number').replace(/\s+/g, '');
    const { iban } = readBill();
    try {
      if (!num) throw new Error(T.noNumber);
      if (iban.valid && iban.qr) {
        const digits = num.replace(/\D/g, '');
        if (!digits || digits.length > 26) throw new Error(T.badNumber);
        $('reference').value = Q.formatReference('QRR', Q.makeQrReference(digits));
      } else {
        const p = num.toUpperCase().replace(/[^0-9A-Z]/g, '');
        if (!p || p.length > 21) throw new Error(T.badNumberRf);
        $('reference').value = Q.formatReference('SCOR', Q.makeCreditorReference(p));
      }
      update();
    } catch (e) {
      result.innerHTML = `<p>${e.message}</p>`;
      result.classList.add('warn');
    }
  }

  form.addEventListener('input', update);
  form.addEventListener('change', update);
  form.addEventListener('submit', (e) => { e.preventDefault(); update(); });
  tool.querySelector('.qr-makeref').addEventListener('click', makeRef);
  tool.querySelector('.qr-example').addEventListener('click', () => {
    for (const [k, val] of Object.entries(EXAMPLE)) {
      const el = $(k);
      if (!el) continue;
      if (el.type === 'checkbox') el.checked = !!val; else el.value = val;
    }
    $('reference').value = '';
    makeRef();
  });
  tool.querySelector('.qr-clear').addEventListener('click', () => {
    form.reset();
    $('reference').value = '';
    update();
  });
  tool.querySelector('.qr-print').addEventListener('click', () => {
    document.body.classList.add('qr-print-mode');
    window.print();
  });
  window.addEventListener('afterprint', () => document.body.classList.remove('qr-print-mode'));
  window.addEventListener('resize', fit);
  update();
}
