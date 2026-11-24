// UI for the three calculators. Everything runs in the browser; nothing is sent anywhere.
import {
  parseNumber, addVat, removeVat,
  percentOf, whatPercent, percentChange, applyPercent,
  parseTime, dayWork, breakCheck, weekCheck, formatHM, toDecimalHours,
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

const tool = document.querySelector('[data-tool]');
if (tool) {
  ({ vat: initVat, percent: initPercent, work: initWork })[tool.dataset.tool]?.(tool);
}
