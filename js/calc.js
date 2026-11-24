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

// ---------- IBAN (ISO 13616, offline check only) ----------

/** IBAN length per country (ISO 13616 registry). Countries not listed: only the mod-97 check is done. */
export const IBAN_LENGTHS = Object.freeze({
  AT: 20, BE: 16, CH: 21, DE: 22, DK: 18, ES: 24, FI: 18, FR: 27, GB: 22,
  IE: 22, IT: 27, LI: 21, LU: 20, NL: 18, NO: 15, PT: 25, SE: 24,
});

/** Remove spaces and dashes, upper-case. */
export function normalizeIban(input) {
  return String(input ?? '').replace(/[\s\-.]/g, '').toUpperCase();
}

/** Group by 4 characters: "CH93 0076 2011 6238 5295 7" */
export function formatIban(input) {
  return normalizeIban(input).replace(/(.{4})(?=.)/g, '$1 ');
}

/** ISO 7064 MOD 97-10 on the rearranged IBAN, computed piecewise (no BigInt needed). */
export function ibanMod97(iban) {
  const s = iban.slice(4) + iban.slice(0, 4);
  let rem = 0;
  for (const ch of s) {
    const v = ch >= 'A' && ch <= 'Z' ? String(ch.charCodeAt(0) - 55) : ch;
    for (const d of v) rem = (rem * 10 + Number(d)) % 97;
  }
  return rem;
}

/** Swiss / Liechtenstein QR-IBAN: IID (positions 5-9) between 30000 and 31999. */
export function isQrIban(input) {
  const s = normalizeIban(input);
  if (!/^(CH|LI)\d{7}/.test(s)) return false;
  const iid = Number(s.slice(4, 9));
  return iid >= 30000 && iid <= 31999;
}

/**
 * Validate format and check digits. Does NOT check that the account exists.
 * Returns { valid, iban, formatted, country, errors: [code], qr, expectedLength }.
 * Error codes: empty, chars, country, length, checksum.
 */
export function validateIban(input) {
  const iban = normalizeIban(input);
  const errors = [];
  const country = iban.slice(0, 2);
  const expectedLength = IBAN_LENGTHS[country] ?? null;
  if (!iban) errors.push('empty');
  else if (!/^[A-Z]{2}\d{2}[A-Z0-9]+$/.test(iban)) errors.push(/^[A-Z]{2}/.test(iban) ? 'chars' : 'country');
  if (iban && expectedLength !== null && iban.length !== expectedLength) errors.push('length');
  if (iban && expectedLength === null && (iban.length < 15 || iban.length > 34)) errors.push('length');
  if (!errors.length && ibanMod97(iban) !== 1) errors.push('checksum');
  if (iban && (country === 'CH' || country === 'LI') && !/^\d+$/.test(iban.slice(4, 9))) {
    if (!errors.includes('chars')) errors.push('chars');
  }
  return {
    valid: errors.length === 0,
    iban,
    formatted: formatIban(iban),
    country,
    known: expectedLength !== null,
    expectedLength,
    qr: errors.length === 0 && isQrIban(iban),
    errors,
  };
}

// ---------- Hourly / monthly salary ----------

export const SALARY_DEFAULTS = Object.freeze({ weeklyHours: 42, weeksPerYear: 52, salariesPerYear: 12 });

/** Monthly salary -> hourly wage. Annual = monthly x salaries; hours = weekly hours x weeks. */
export function monthlyToHourly(monthly, weeklyHours = 42, salariesPerYear = 12, weeksPerYear = 52) {
  const hours = weeklyHours * weeksPerYear;
  if (!(hours > 0) || !(salariesPerYear > 0)) return null;
  const annual = monthly * salariesPerYear;
  return { annual, hoursPerYear: hours, hourly: annual / hours };
}

/** Hourly wage -> monthly salary (per salary payment). */
export function hourlyToMonthly(hourly, weeklyHours = 42, salariesPerYear = 12, weeksPerYear = 52) {
  const hours = weeklyHours * weeksPerYear;
  if (!(hours > 0) || !(salariesPerYear > 0)) return null;
  const annual = hourly * hours;
  return { annual, hoursPerYear: hours, monthly: annual / salariesPerYear };
}

// ---------- Days between two dates ----------

const DAY_MS = 86400000;

/** "YYYY-MM-DD" -> UTC day number (days since 1970-01-01), or NaN. */
export function parseIsoDate(str) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(str ?? '').trim());
  if (!m) return NaN;
  const [y, mo, d] = [Number(m[1]), Number(m[2]), Number(m[3])];
  const t = Date.UTC(y, mo - 1, d);
  const back = new Date(t);
  if (back.getUTCFullYear() !== y || back.getUTCMonth() !== mo - 1 || back.getUTCDate() !== d) return NaN;
  return t / DAY_MS;
}

/** Fixed holidays offered as an option: 1 January, 1 August, 25 December. [month, day] */
export const FIXED_HOLIDAYS = Object.freeze([[1, 1], [8, 1], [12, 25]]);

/**
 * Days from start to end. The start day counts, the end day only with includeEnd.
 * Returns { calendar, weekdays, holidaysExcluded, weeks, restDays, swapped } or null.
 * weekdays = Monday to Friday; with excludeFixedHolidays, the fixed holidays falling on Mon-Fri are removed.
 */
export function daysBetween(startStr, endStr, { includeEnd = false, excludeFixedHolidays = false } = {}) {
  let a = parseIsoDate(startStr);
  let b = parseIsoDate(endStr);
  if (!Number.isFinite(a) || !Number.isFinite(b)) return null;
  const swapped = b < a;
  if (swapped) [a, b] = [b, a];
  const last = includeEnd ? b : b - 1; // inclusive last day counted
  const calendar = last - a + 1;
  let weekdays = 0;
  let holidaysExcluded = 0;
  for (let day = a; day <= last; day++) {
    const dt = new Date(day * DAY_MS);
    const wd = dt.getUTCDay(); // 0 = Sunday
    if (wd === 0 || wd === 6) continue;
    if (excludeFixedHolidays && FIXED_HOLIDAYS.some(([mo, d]) => dt.getUTCMonth() + 1 === mo && dt.getUTCDate() === d)) {
      holidaysExcluded++;
      continue;
    }
    weekdays++;
  }
  return { calendar, weekdays, holidaysExcluded, weeks: Math.floor(calendar / 7), restDays: calendar % 7, swapped };
}
