// UI for all calculators. Everything runs in the browser; nothing is sent anywhere.
import {
  parseNumber, addVat, removeVat,
  percentOf, whatPercent, percentChange, applyPercent,
  parseTime, dayWork, breakCheck, weekCheck, formatHM, toDecimalHours,
  validateIban, monthlyToHourly, hourlyToMonthly, daysBetween,
  grossToNet, PAYROLL_2026, rentAdjustment,
} from './calc.js';

const LANG = document.documentElement.lang.startsWith('fr') ? 'fr' : 'de';
const T = {
  de: {
    invalid: 'Bitte gültige Zahlen eingeben.',
    divZero: 'Division durch null ist nicht möglich.',
    day: 'Tag', start: 'Beginn', end: 'Ende', pause: 'Pause (Min.)', net: 'Arbeitszeit',
    remove: 'Entfernen', overnight: 'über Mitternacht',
    breakOk: (r) => r ? `Pause ok (Minimum ${r} Min.)` : 'Keine Mindestpause nötig',
    breakLow: (r) => `Pause zu kurz: mindestens ${r} Min. (Art. 15 ArG)`,
    total: 'Wochentotal',
    over50: 'Mehr als 50 Stunden: über der gesetzlichen Höchstarbeitszeit für alle Arbeitnehmenden (Art. 9 ArG).',
    over45: 'Mehr als 45 Stunden: über der Höchstarbeitszeit für Industrie, Büro, technische Angestellte und Verkauf im Grossdetailhandel (Art. 9 ArG).',
    under45: 'Innerhalb von 45 Stunden pro Woche.',
    vatLabel: 'MWST', netLabel: 'Netto', grossLabel: 'Brutto',
    is: 'ist', of: 'von', change: 'Veränderung',
    ibanOk: 'Format und Prüfziffer sind korrekt.',
    ibanNote: 'Ob das Konto existiert, kann dieser Test nicht prüfen.',
    ibanQr: 'QR-IBAN: nur für QR-Rechnungen mit QR-Referenz gedacht, nicht für normale Zahlungen.',
    ibanUnknown: (c) => `Für das Land ${c} ist keine Länge hinterlegt; geprüft wurde nur die Prüfziffer.`,
    ibanErr: { empty: 'Bitte eine IBAN eingeben.', chars: 'Unerlaubte Zeichen: erlaubt sind nur Buchstaben und Ziffern, beginnend mit Ländercode und zwei Prüfziffern.', country: 'Die IBAN muss mit einem Ländercode aus zwei Buchstaben beginnen (z. B. CH).', length: (n, e) => e ? `Falsche Länge: ${n} Zeichen, erwartet ${e}.` : `Unplausible Länge: ${n} Zeichen.`, checksum: 'Die Prüfziffer stimmt nicht: Vermutlich ist ein Zeichen falsch oder vertauscht.' },
    ibanInvalid: 'Ungültig',
    ibanValid: 'Gültig',
    hourly: 'Stundenlohn', monthly: 'Monatslohn', annual: 'Jahreslohn', hoursYear: 'Arbeitsstunden pro Jahr', perSalary: (n) => `(bei ${n} Löhnen)`,
    calDays: 'Kalendertage', workDays: 'Arbeitstage (Mo–Fr)', weeks: 'Wochen', and: 'und', days: 'Tage', day1: 'Tag',
    holEx: (n) => `Abgezogene feste Feiertage (Mo–Fr): ${n}`,
    swapped: 'Hinweis: Das Enddatum lag vor dem Startdatum; die Daten wurden vertauscht.',
    needDates: 'Bitte zwei gültige Daten eingeben.',
    perPay: 'pro Lohnzahlung', perYear: 'pro Jahr', grossL: 'Bruttolohn', ahvL: 'AHV/IV/EO', alvL: 'ALV', nbuL: 'NBU',
    ktgL: 'KTG', bvgL: 'BVG (Schätzung)', bvgOwnL: 'BVG (eigener Satz)', totalL: 'Total Abzüge', netL: 'Nettolohn vor Quellensteuer',
    coord: (c, r) => `Koordinierter Lohn BVG: ${c}; Arbeitnehmeranteil ${r} % davon.`,
    noBvg: (t) => `Jahreslohn nicht über ${t}: keine obligatorische BVG-Versicherung.`,
    young: 'Unter 25 Jahren gibt es noch keine Altersgutschriften; allfällige Risikobeiträge sind nicht eingerechnet.',
    old: 'Über 65 Jahren rechnet der Rechner keine BVG-Altersgutschriften; für Rentnerinnen und Rentner gelten bei AHV und ALV besondere Regeln, die hier nicht abgebildet sind.',
    alvCap: 'ALV nur auf dem Lohn bis CHF 148\u2019200 pro Jahr; darüber keine ALV-Beiträge.',
    taxNote: 'Ohne Quellensteuer und ohne Einkommenssteuer.',
    ageBad: 'Bitte ein Alter zwischen 18 und 70 eingeben.',
    refL: 'Referenzzinssatz', inflL: 'Teuerung (40 % des LIK)', costL: 'Allgemeine Kostensteigerung', totalPctL: 'Total Anpassung',
    newRentL: 'Neue Nettomiete (Schätzung)', diffL: 'Differenz pro Monat', diffYL: 'Differenz pro Jahr',
    steps: (n) => `${Math.abs(n)} Viertelprozent-${Math.abs(n) === 1 ? 'Schritt' : 'Schritte'} ${n < 0 ? 'nach unten' : 'nach oben'}`,
    noChange: 'Gleicher Referenzzinssatz: keine Anpassung aus dem Zinssatz.',
    months: (m) => `${m} volle Monate`,
    needDate: 'Für die Kostensteigerung bitte das Datum der letzten Anpassung und den Stichtag angeben.',
    needIdx: 'Für die Teuerung bitte beide Indexstände angeben (gleiche Basis).',
    lower: 'Sie können eine Senkung beantragen (schriftlich, am besten eingeschrieben).',
    higher: 'Der Vermieter könnte eine Erhöhung geltend machen – nur mit offiziellem Formular und auf einen Kündigungstermin.',
    legal: 'Schätzung, keine Rechtsberatung.',
  },
  fr: {
    invalid: 'Veuillez saisir des nombres valides.',
    divZero: 'La division par zéro n’est pas possible.',
    day: 'Jour', start: 'Début', end: 'Fin', pause: 'Pause (min)', net: 'Temps de travail',
    remove: 'Supprimer', overnight: 'après minuit',
    breakOk: (r) => r ? `Pause suffisante (minimum ${r} min)` : 'Aucune pause minimale requise',
    breakLow: (r) => `Pause trop courte : au moins ${r} min (art. 15 LTr)`,
    total: 'Total de la semaine',
    over50: 'Plus de 50 heures : au-delà de la durée maximale légale pour tous les travailleurs (art. 9 LTr).',
    over45: 'Plus de 45 heures : au-delà de la durée maximale pour l’industrie, les bureaux, le personnel technique et la vente dans le grand commerce de détail (art. 9 LTr).',
    under45: 'Dans la limite de 45 heures par semaine.',
    vatLabel: 'TVA', netLabel: 'Hors TVA', grossLabel: 'TVA incluse',
    is: 'représente', of: 'de', change: 'Variation',
    ibanOk: 'Le format et la clé de contrôle sont corrects.',
    ibanNote: 'Ce test ne peut pas vérifier si le compte existe.',
    ibanQr: 'QR-IBAN : prévue uniquement pour les QR-factures avec référence QR, pas pour les paiements ordinaires.',
    ibanUnknown: (c) => `Aucune longueur enregistrée pour le pays ${c} ; seule la clé de contrôle a été vérifiée.`,
    ibanErr: { empty: 'Veuillez saisir une IBAN.', chars: 'Caractères non autorisés : seulement des lettres et des chiffres, en commençant par le code pays et deux chiffres de contrôle.', country: 'L’IBAN doit commencer par un code pays de deux lettres (p. ex. CH).', length: (n, e) => e ? `Longueur incorrecte : ${n} caractères, ${e} attendus.` : `Longueur invraisemblable : ${n} caractères.`, checksum: 'La clé de contrôle ne correspond pas : un caractère est probablement faux ou inversé.' },
    ibanInvalid: 'Non valable',
    ibanValid: 'Valable',
    hourly: 'Salaire horaire', monthly: 'Salaire mensuel', annual: 'Salaire annuel', hoursYear: 'Heures de travail par an', perSalary: (n) => `(sur ${n} salaires)`,
    calDays: 'Jours calendaires', workDays: 'Jours ouvrés (lun–ven)', weeks: 'semaines', and: 'et', days: 'jours', day1: 'jour',
    holEx: (n) => `Jours fériés fixes déduits (lun–ven) : ${n}`,
    swapped: 'Remarque : la date de fin précédait la date de début ; les dates ont été inversées.',
    needDates: 'Veuillez saisir deux dates valables.',
    perPay: 'par versement', perYear: 'par an', grossL: 'Salaire brut', ahvL: 'AVS/AI/APG', alvL: 'AC', nbuL: 'AANP',
    ktgL: 'IJM', bvgL: 'LPP (estimation)', bvgOwnL: 'LPP (taux personnel)', totalL: 'Total des déductions', netL: 'Salaire net avant impôt à la source',
    coord: (c, r) => `Salaire coordonné LPP : ${c} ; part salariée ${r} % de ce montant.`,
    noBvg: (t) => `Salaire annuel ne dépassant pas ${t} : pas d’assurance LPP obligatoire.`,
    young: 'Avant 25 ans, il n’y a pas encore de bonifications de vieillesse ; d’éventuelles cotisations de risque ne sont pas comptées.',
    old: 'Au-delà de 65 ans, le calculateur ne compte pas de bonifications LPP ; pour les retraités, l’AVS et l’AC suivent des règles particulières non reprises ici.',
    alvCap: 'AC seulement sur le salaire jusqu’à CHF 148\u2019200 par an ; aucune cotisation AC au-delà.',
    taxNote: 'Sans impôt à la source et sans impôt sur le revenu.',
    ageBad: 'Veuillez saisir un âge entre 18 et 70 ans.',
    refL: 'Taux de référence', inflL: 'Renchérissement (40 % de l’IPC)', costL: 'Hausse générale des coûts', totalPctL: 'Adaptation totale',
    newRentL: 'Nouveau loyer net (estimation)', diffL: 'Différence par mois', diffYL: 'Différence par an',
    steps: (n) => `${Math.abs(n)} ${Math.abs(n) === 1 ? 'palier' : 'paliers'} d’un quart de point ${n < 0 ? 'vers le bas' : 'vers le haut'}`,
    noChange: 'Même taux de référence : pas d’adaptation liée au taux.',
    months: (m) => `${m} mois entiers`,
    needDate: 'Pour la hausse des coûts, indiquez la date de la dernière adaptation et la date de calcul.',
    needIdx: 'Pour le renchérissement, indiquez les deux niveaux d’indice (même base).',
    lower: 'Vous pouvez demander une baisse (par écrit, de préférence en recommandé).',
    higher: 'Le bailleur pourrait faire valoir une hausse – uniquement avec la formule officielle et pour un terme de résiliation.',
    legal: 'Estimation, pas un conseil juridique.',
  },
}[LANG];

const LOC = LANG === 'fr' ? 'fr-CH' : 'de-CH';
const chf = (x) => 'CHF ' + new Intl.NumberFormat('de-CH', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(x);
const num = (x, d = 2) => new Intl.NumberFormat(LOC, { maximumFractionDigits: d }).format(x);
const $ = (sel, root = document) => root.querySelector(sel);
const val = (el) => parseNumber(el.value);

// ---------- VAT ----------
function initVat(root) {
  const form = $('form', root);
  const out = $('.result', root);
  const run = () => {
    const amount = val(form.amount);
    const rate = Number(form.rate.value);
    const dir = form.dir.value;
    const round5 = form.round5.checked;
    if (!Number.isFinite(amount) || !Number.isFinite(rate)) { out.textContent = form.amount.value ? T.invalid : ''; return; }
    const r = dir === 'add' ? addVat(amount, rate, round5) : removeVat(amount, rate, round5);
    out.innerHTML = `<dl class="res-grid">
      <dt>${T.netLabel}</dt><dd>${chf(r.net)}</dd>
      <dt>${T.vatLabel} ${num(rate, 1)} %</dt><dd>${chf(r.vat)}</dd>
      <dt>${T.grossLabel}</dt><dd class="big">${chf(r.gross)}</dd></dl>`;
  };
  form.addEventListener('input', run);
  form.addEventListener('submit', (e) => { e.preventDefault(); run(); });
  run();
}

// ---------- Percent ----------
function initPercent(root) {
  root.querySelectorAll('form[data-mode]').forEach((form) => {
    const out = $('.result', form);
    const run = () => {
      const a = val(form.a);
      const b = val(form.b);
      if (form.a.value === '' || form.b.value === '') { out.textContent = ''; return; }
      if (!Number.isFinite(a) || !Number.isFinite(b)) { out.textContent = T.invalid; return; }
      let text;
      switch (form.dataset.mode) {
        case 'of': text = `${num(a, 4)} % ${T.of} ${num(b, 4)} = ${num(percentOf(a, b), 4)}`; break;
        case 'what': {
          const r = whatPercent(a, b);
          text = r === null ? T.divZero : `${num(a, 4)} ${T.is} ${num(r, 4)} % ${T.of} ${num(b, 4)}`; break;
        }
        case 'change': {
          const r = percentChange(a, b);
          text = r === null ? T.divZero : `${T.change}: ${r > 0 ? '+' : ''}${num(r, 4)} %`; break;
        }
        case 'apply': {
          const sign = form.sign.value === '-' ? -1 : 1;
          text = `${num(a, 4)} ${sign > 0 ? '+' : '−'} ${num(b, 4)} % = ${num(applyPercent(a, b, sign), 4)}`; break;
        }
        default: text = '';
      }
      out.textContent = text;
    };
    form.addEventListener('input', run);
    form.addEventListener('submit', (e) => { e.preventDefault(); run(); });
  });
}

// ---------- Working time ----------
function initWork(root) {
  const tbody = $('tbody', root);
  const addBtn = $('.add-day', root);
  const out = $('.result', root);
  const MAX = 7;

  let uid = 0;
  const rowHtml = (i, u) => `
    <td data-label="${T.day}">${i}</td>
    <td><label class="cell-label" for="s${u}">${T.start}<span class="sr-only"> ${T.day} ${i}</span></label><input type="time" id="s${u}" name="start" value="${i === 1 ? '08:00' : ''}"></td>
    <td><label class="cell-label" for="e${u}">${T.end}<span class="sr-only"> ${T.day} ${i}</span></label><input type="time" id="e${u}" name="end" value="${i === 1 ? '17:00' : ''}"></td>
    <td><label class="cell-label" for="p${u}">${T.pause}<span class="sr-only"> ${T.day} ${i}</span></label><input type="number" id="p${u}" name="pause" min="0" max="720" step="5" inputmode="numeric" value="${i === 1 ? '60' : ''}"></td>
    <td class="day-out" aria-live="polite"></td>
    <td>${i > 1 ? `<button type="button" class="link-btn rm" aria-label="${T.remove} ${T.day} ${i}">×</button>` : ''}</td>`;

  const addRow = () => {
    const n = tbody.rows.length + 1;
    if (n > MAX) return;
    const tr = document.createElement('tr');
    tr.innerHTML = rowHtml(n, ++uid);
    tbody.appendChild(tr);
    addBtn.disabled = n >= MAX;
    run();
  };

  const run = () => {
    let total = 0;
    let any = false;
    [...tbody.rows].forEach((tr) => {
      const cell = $('.day-out', tr);
      const s = parseTime($('[name=start]', tr).value);
      const e = parseTime($('[name=end]', tr).value);
      const p = Number($('[name=pause]', tr).value) || 0;
      const d = dayWork(s, e, p);
      if (!d) { cell.textContent = ''; return; }
      any = true;
      total += d.net;
      const bc = breakCheck(d.net, d.pause);
      cell.innerHTML = `<strong>${formatHM(d.net)}</strong> h · ${num(toDecimalHours(d.net))} h${d.overnight ? ` <span class="tag">${T.overnight}</span>` : ''}
        <span class="flag ${bc.ok ? 'ok' : 'warn'}">${bc.ok ? T.breakOk(bc.required) : T.breakLow(bc.required)}</span>`;
    });
    if (!any) { out.textContent = ''; return; }
    const w = weekCheck(total);
    const msg = w.over50 ? T.over50 : w.over45 ? T.over45 : T.under45;
    out.innerHTML = `<dl class="res-grid"><dt>${T.total}</dt><dd class="big">${formatHM(total)} h</dd>
      <dt></dt><dd>${num(toDecimalHours(total))} h</dd></dl>
      <p class="flag ${w.over45 ? 'warn' : 'ok'}">${msg}</p>`;
  };

  tbody.addEventListener('input', run);
  tbody.addEventListener('click', (ev) => {
    if (!ev.target.classList.contains('rm')) return;
    ev.target.closest('tr').remove();
    [...tbody.rows].forEach((tr, i) => { tr.cells[0].textContent = String(i + 1); });
    addBtn.disabled = false;
    run();
  });
  addBtn.addEventListener('click', addRow);
  addRow();
}

// ---------- IBAN ----------
function initIban(root) {
  const form = $('form', root);
  const out = $('.result', root);
  const esc = (x) => x.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const run = () => {
    if (!form.iban.value.trim()) { out.textContent = ''; return; }
    const r = validateIban(form.iban.value);
    const msgs = r.errors.map((e) => (e === 'length' ? T.ibanErr.length(r.iban.length, r.expectedLength) : T.ibanErr[e]));
    let h = `<p class="iban-out"><strong>${esc(r.formatted)}</strong></p>`;
    if (r.valid) {
      h += `<p class="flag ok">${T.ibanValid}: ${T.ibanOk}</p>`;
      if (!r.known) h += `<p class="flag warn">${T.ibanUnknown(esc(r.country))}</p>`;
      if (r.qr) h += `<p class="flag warn">${T.ibanQr}</p>`;
    } else {
      h += msgs.map((m) => `<p class="flag warn">${T.ibanInvalid}: ${m}</p>`).join('');
    }
    h += `<p class="note">${T.ibanNote}</p>`;
    out.innerHTML = h;
  };
  form.addEventListener('input', run);
  form.addEventListener('submit', (e) => { e.preventDefault(); run(); });
}

// ---------- Salary ----------
function initSalary(root) {
  const form = $('form', root);
  const out = $('.result', root);
  const run = () => {
    const amount = val(form.amount);
    const hours = val(form.hours);
    const weeks = val(form.weeks);
    const n = Number(form.salaries.value);
    if (form.amount.value.trim() === '') { out.textContent = ''; return; }
    if (![amount, hours, weeks].every(Number.isFinite) || hours <= 0 || weeks <= 0) { out.textContent = T.invalid; return; }
    let rows;
    if (form.dir.value === 'm2h') {
      const r = monthlyToHourly(amount, hours, n, weeks);
      rows = [[T.annual, chf(r.annual)], [T.hoursYear, num(r.hoursPerYear, 1) + ' h'], [T.hourly, chf(r.hourly), true]];
    } else {
      const r = hourlyToMonthly(amount, hours, n, weeks);
      rows = [[T.annual, chf(r.annual)], [T.hoursYear, num(r.hoursPerYear, 1) + ' h'], [`${T.monthly} ${T.perSalary(n)}`, chf(r.monthly), true]];
    }
    out.innerHTML = '<dl class="res-grid">' + rows.map(([k, v, big]) => `<dt>${k}</dt><dd${big ? ' class="big"' : ''}>${v}</dd>`).join('') + '</dl>';
  };
  form.addEventListener('input', run);
  form.addEventListener('change', run);
  form.addEventListener('submit', (e) => { e.preventDefault(); run(); });
  run();
}

// ---------- Days between dates ----------
function initDays(root) {
  const form = $('form', root);
  const out = $('.result', root);
  const run = () => {
    if (!form.start.value || !form.end.value) { out.textContent = ''; return; }
    const r = daysBetween(form.start.value, form.end.value, { includeEnd: form.includeEnd.checked, excludeFixedHolidays: form.holidays.checked });
    if (!r) { out.textContent = T.needDates; return; }
    const wk = `${r.weeks} ${T.weeks} ${T.and} ${r.restDays} ${r.restDays === 1 ? T.day1 : T.days}`;
    out.innerHTML = `<dl class="res-grid">
      <dt>${T.calDays}</dt><dd class="big">${num(r.calendar, 0)}</dd>
      <dt>${T.workDays}</dt><dd class="big">${num(r.weekdays, 0)}</dd>
      <dt>${T.weeks[0].toUpperCase() + T.weeks.slice(1)}</dt><dd>${wk}</dd></dl>`
      + (form.holidays.checked ? `<p class="note">${T.holEx(r.holidaysExcluded)}</p>` : '')
      + (r.swapped ? `<p class="flag warn">${T.swapped}</p>` : '');
  };
  form.addEventListener('input', run);
  form.addEventListener('change', run);
  form.addEventListener('submit', (e) => { e.preventDefault(); run(); });
  run();
}

// ---------- Gross -> net salary ----------
function initNet(root) {
  const form = $('form', root);
  const out = $('.result', root);
  const sync = () => { form.bvgPct.disabled = form.bvgMode.value !== 'own'; form.ktgPct.disabled = !form.ktg.checked; };
  const run = () => {
    sync();
    if (form.amount.value.trim() === '') { out.textContent = ''; return; }
    const gross = val(form.amount);
    const age = val(form.age);
    const nbuPct = val(form.nbuPct);
    const ktgPct = form.ktg.checked ? val(form.ktgPct) : 0;
    const bvgPct = form.bvgMode.value === 'own' ? val(form.bvgPct) : null;
    if (!Number.isFinite(age) || age < 18 || age > 70) { out.textContent = T.ageBad; return; }
    const r = grossToNet({ gross, period: form.period.value, salaries: Number(form.salaries.value), age, nbuPct, ktgPct, bvgPct });
    if (!r) { out.textContent = T.invalid; return; }
    const pct = (x) => `${num(x, 2)} %`;
    const money = (x) => (x < 0 ? `− ${chf(-x)}` : chf(x));
    const rows = [
      [T.grossL, r.grossPer, r.annual, 'strong'],
      [`${T.ahvL} ${pct(PAYROLL_2026.ahvIvEo)}`, -r.per.ahv, -r.lines.ahv],
      [`${T.alvL} ${pct(PAYROLL_2026.alv)}`, -r.per.alv, -r.lines.alv],
      [`${T.nbuL} ${pct(nbuPct)}`, -r.per.nbu, -r.lines.nbu],
    ];
    if (form.ktg.checked) rows.push([`${T.ktgL} ${pct(ktgPct)}`, -r.per.ktg, -r.lines.ktg]);
    rows.push([bvgPct === null ? T.bvgL : T.bvgOwnL, -r.per.bvg, -r.lines.bvg]);
    rows.push([T.totalL, -r.totalPer, -r.total, 'sum']);
    rows.push([T.netL, r.netPer, r.net, 'big']);
    const notes = [];
    if (r.coordinated > 0) notes.push(T.coord(chf(r.coordinated), num(r.bvgRate, 2)));
    else notes.push(T.noBvg(chf(PAYROLL_2026.bvgEntryThreshold)));
    if (bvgPct === null && age < 25 && r.coordinated > 0) notes.push(T.young);
    if (bvgPct === null && age > 65) notes.push(T.old);
    if (r.annual > PAYROLL_2026.alvCeiling) notes.push(T.alvCap);
    notes.push(T.taxNote);
    out.innerHTML = `<table class="res-table"><thead><tr><th scope="col"></th><th scope="col">${T.perPay}</th><th scope="col">${T.perYear}</th></tr></thead><tbody>`
      + rows.map(([k, a, b, cls]) => `<tr${cls ? ` class="${cls}"` : ''}><th scope="row">${k}</th><td>${money(a)}</td><td>${money(b)}</td></tr>`).join('')
      + '</tbody></table>' + notes.map((n) => `<p class="note">${n}</p>`).join('');
  };
  form.addEventListener('input', run);
  form.addEventListener('change', run);
  form.addEventListener('submit', (e) => { e.preventDefault(); run(); });
  run();
}

// ---------- Rent and reference rate ----------
function initRent(root) {
  const form = $('form', root);
  const out = $('.result', root);
  if (!form.refDate.value) {
    const d = new Date();
    form.refDate.value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  }
  const run = () => {
    if (form.rent.value.trim() === '') { out.textContent = ''; return; }
    const rent = val(form.rent);
    const hasIdx = form.oldIndex.value.trim() !== '' || form.newIndex.value.trim() !== '';
    if (hasIdx && (form.oldIndex.value.trim() === '' || form.newIndex.value.trim() === '')) { out.textContent = T.needIdx; return; }
    const cost = form.cost.value.trim() === '' ? 0 : val(form.cost);
    if (cost && (!form.lastDate.value || !form.refDate.value)) { out.textContent = T.needDate; return; }
    const r = rentAdjustment({
      rent, oldRate: Number(form.oldRate.value), newRate: Number(form.newRate.value),
      oldIndex: hasIdx ? val(form.oldIndex) : null, newIndex: hasIdx ? val(form.newIndex) : null,
      costPctPerYear: cost, lastDate: form.lastDate.value || null, refDate: form.refDate.value || null,
    });
    if (!r) { out.textContent = T.invalid; return; }
    const sp = (x) => `${x > 0 ? '+' : x < 0 ? '−' : ''}${num(Math.abs(x), 2)} %`;
    const sc = (x) => `${x > 0 ? '+' : x < 0 ? '−' : ''}${chf(Math.abs(x))}`;
    const rows = [[`${T.refL} ${num(Number(form.oldRate.value), 2)} % → ${num(Number(form.newRate.value), 2)} %`, sp(r.refPct)]];
    if (hasIdx) rows.push([T.inflL, sp(r.inflPct)]);
    if (cost) rows.push([`${T.costL} (${T.months(r.months)})`, sp(r.costPct)]);
    rows.push([T.totalPctL, sp(r.totalPct)]);
    out.innerHTML = '<dl class="res-grid">' + rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('')
      + `<dt>${T.newRentL}</dt><dd class="big">${chf(r.newRent)}</dd><dt>${T.diffL}</dt><dd>${sc(r.diff)}</dd><dt>${T.diffYL}</dt><dd>${sc(r.diffYear)}</dd></dl>`
      + `<p class="note">${r.steps === 0 ? T.noChange : T.steps(r.steps)}</p>`
      + (r.diff < 0 ? `<p class="flag ok">${T.lower}</p>` : r.diff > 0 ? `<p class="flag warn">${T.higher}</p>` : '')
      + `<p class="note">${T.legal}</p>`;
  };
  form.addEventListener('input', run);
  form.addEventListener('change', run);
  form.addEventListener('submit', (e) => { e.preventDefault(); run(); });
  run();
}

const tool = document.querySelector('[data-tool]');
if (tool) {
  ({ vat: initVat, percent: initPercent, work: initWork, iban: initIban, salary: initSalary, days: initDays, net: initNet, rent: initRent })[tool.dataset.tool]?.(tool);
}
