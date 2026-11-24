// Pure calculation functions (no DOM). Imported by js/ui.js and tests/calc.test.mjs.

/** Swiss VAT rates in percent (ESTV, valid since 1 January 2024). */
export const VAT_RATES = Object.freeze({ normal: 8.1, reduced: 2.6, accommodation: 3.8 });

/** Minimum breaks, Art. 15 para. 1 ArG: [daily working time above (minutes), break (minutes)]. */
export const BREAK_RULES = Object.freeze([
  [540, 60], // more than 9 h  -> 1 h
  [420, 30], // more than 7 h  -> 30 min
  [330, 15], // more than 5.5 h -> 15 min
]);

/** Weekly maximum working time, Art. 9 para. 1 ArG (hours). */
export const WEEKLY_MAX = Object.freeze({ industryOffice: 45, other: 50 });

/** Round to 2 decimals (half away from zero), robust against binary float noise. */
export function round2(x) {
  const n = Number(x);
  if (!Number.isFinite(n)) return NaN;
  const s = Math.sign(n) || 1;
  return (s * Math.round(Number((Math.abs(n) * 100).toFixed(6)))) / 100;
}

/** Round to the nearest 5 Rappen (0.05), half away from zero. */
export function roundTo5Rappen(x) {
  const n = Number(x);
  if (!Number.isFinite(n)) return NaN;
  const s = Math.sign(n) || 1;
  return round2((s * Math.round(Number((Math.abs(n) * 20).toFixed(6)))) / 20);
}

/** Parse user input: accepts "1'234.50", "1 234,5", "12,5". Returns NaN if invalid. */
export function parseNumber(input) {
  if (typeof input === 'number') return input;
  if (typeof input !== 'string') return NaN;
  const s = input.trim().replace(/[\s'’  ]/g, '').replace(',', '.');
  if (s === '' || !/^[-+]?(\d+\.?\d*|\.\d+)$/.test(s)) return NaN;
  return Number(s);
}

// ---------- VAT ----------

/** Net -> gross. With round5, the VAT amount is rounded to 5 Rappen. */
export function addVat(net, ratePct, round5 = false) {
  const vatRaw = (net * ratePct) / 100;
  const vat = round5 ? roundTo5Rappen(vatRaw) : round2(vatRaw);
  const n = round2(net);
  return { net: n, vat, gross: round2(n + vat) };
}

/** Gross -> net (VAT included in the amount). With round5, the VAT amount is rounded to 5 Rappen. */
export function removeVat(gross, ratePct, round5 = false) {
  const vatRaw = gross - gross / (1 + ratePct / 100);
  const vat = round5 ? roundTo5Rappen(vatRaw) : round2(vatRaw);
  const g = round2(gross);
  return { net: round2(g - vat), vat, gross: g };
}

// ---------- Percent ----------

/** X % of Y */
export function percentOf(pct, base) {
  return (pct * base) / 100;
}

/** X is how many % of Y (null if Y = 0) */
export function whatPercent(part, base) {
  return base === 0 ? null : (part / base) * 100;
}

/** Percentage change from A to B (null if A = 0) */
export function percentChange(from, to) {
  return from === 0 ? null : ((to - from) / Math.abs(from)) * 100;
}

/** Value plus (sign = 1) or minus (sign = -1) X % */
export function applyPercent(value, pct, sign = 1) {
  return value * (1 + (sign * pct) / 100);
}

// ---------- Working time ----------

/** "HH:MM" -> minutes since midnight, or NaN. Accepts "7:30", "07:30", "0730". */
export function parseTime(str) {
  if (typeof str !== 'string') return NaN;
  const m = str.trim().match(/^(\d{1,2})[:.h]?(\d{2})$/);
  if (!m) return NaN;
  const h = Number(m[1]);
  const min = Number(m[2]);
  if (h > 24 || min > 59 || (h === 24 && min !== 0)) return NaN;
  return h * 60 + min;
}

/** Minutes worked in one day. If end <= start, the shift crosses midnight. */
export function dayWork(startMin, endMin, pauseMin = 0) {
  if (![startMin, endMin].every(Number.isFinite)) return null;
  const pause = Number.isFinite(pauseMin) && pauseMin > 0 ? pauseMin : 0;
  let span = endMin - startMin;
  if (span <= 0) span += 1440;
  if (startMin === endMin) span = 0; // identical times: treated as empty, not 24 h
  return { span, pause, net: Math.max(0, span - pause), overnight: endMin < startMin };
}

/** Minimum break required by Art. 15 ArG for a given daily working time (minutes). */
export function requiredBreak(netMin) {
  for (const [above, brk] of BREAK_RULES) if (netMin > above) return brk;
  return 0;
}

/** Break check: is the entered pause at least the legal minimum? */
export function breakCheck(netMin, pauseMin) {
  const required = requiredBreak(netMin);
  return { required, ok: pauseMin >= required };
}

/** Weekly total check against Art. 9 ArG maxima (minutes in). */
export function weekCheck(totalMin) {
  return {
    hours: totalMin / 60,
    over45: totalMin > WEEKLY_MAX.industryOffice * 60,
    over50: totalMin > WEEKLY_MAX.other * 60,
  };
}

/** Minutes -> "h:mm" */
export function formatHM(min) {
  const sign = min < 0 ? '-' : '';
  const a = Math.round(Math.abs(min));
  return `${sign}${Math.floor(a / 60)}:${String(a % 60).padStart(2, '0')}`;
}

/** Minutes -> decimal hours, 2 decimals */
export function toDecimalHours(min) {
  return round2(min / 60);
}
