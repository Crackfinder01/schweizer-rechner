// UI for the three calculators. Everything runs in the browser; nothing is sent anywhere.
import {
  parseNumber, addVat, removeVat,
  percentOf, whatPercent, percentChange, applyPercent,
  parseTime, dayWork, breakCheck, weekCheck, formatHM, toDecimalHours,
  validateIban, monthlyToHourly, hourlyToMonthly, daysBetween,
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

const tool = document.querySelector('[data-tool]');
if (tool) {
  ({ vat: initVat, percent: initPercent, work: initWork, iban: initIban, salary: initSalary, days: initDays })[tool.dataset.tool]?.(tool);
}
