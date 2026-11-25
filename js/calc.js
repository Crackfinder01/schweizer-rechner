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

// ---------- Gross -> net salary (employee deductions, 2026) ----------

/**
 * Employee-side payroll figures valid in 2026.
 * AHV/IV/EO 5.3 %: ahv-iv.ch leaflet 2.01 (Stand 1.1.2026). ALV 1.1 % up to CHF 148'200, nothing above
 * (since 1.1.2023): ahv-iv.ch leaflet 2.08, kmu.admin.ch. UVG max. insured earnings CHF 148'200: suva.ch.
 * BVG thresholds 2026: BSV "Masszahlen 2025/2026", Art. 2, 7, 8 BVG (fedlex). Age credits: Art. 16 BVG.
 */
export const PAYROLL_2026 = Object.freeze({
  ahvIvEo: 5.3,
  alv: 1.1,
  alvCeiling: 148200,
  uvgMaxInsured: 148200,
  bvgEntryThreshold: 22680,
  bvgCoordinationDeduction: 26460,
  bvgUpperLimit: 90720,
  bvgMinCoordinated: 3780,
});

/** Art. 16 BVG: retirement credits in % of the coordinated salary, by age [from, to, rate]. */
export const BVG_CREDITS = Object.freeze([[25, 34, 7], [35, 44, 10], [45, 54, 15], [55, 65, 18]]);

/** BVG retirement-credit rate for an age (age reached in the calendar year). 0 outside 25-65. */
export function bvgCreditRate(age) {
  for (const [from, to, rate] of BVG_CREDITS) if (age >= from && age <= to) return rate;
  return 0;
}

/** Coordinated salary under the BVG minimum (Art. 7 and 8 BVG). 0 if the annual salary is not above the entry threshold. */
export function bvgCoordinatedSalary(annual, P = PAYROLL_2026) {
  if (!(annual > P.bvgEntryThreshold)) return 0;
  const c = Math.min(annual, P.bvgUpperLimit) - P.bvgCoordinationDeduction;
  return Math.max(c, P.bvgMinCoordinated);
}

/**
 * Employee deductions and net salary. Withholding tax (Quellensteuer) is NOT included.
 * opts: { gross, period: 'month'|'year', salaries: 12|13, age, nbuPct, ktgPct, bvgPct (custom % of coordinated salary, or null = estimate) }
 * BVG estimate = half of the Art. 16 credit (employer pays at least half, Art. 66 BVG); risk premiums and costs are not included.
 * Returns annual amounts and amounts per salary payment (annual / salaries), or null on invalid input.
 */
export function grossToNet({ gross, period = 'month', salaries = 12, age = 40, nbuPct = 1, ktgPct = 0, bvgPct = null }, P = PAYROLL_2026) {
  if (![gross, salaries, age, nbuPct, ktgPct].every(Number.isFinite) || gross < 0 || salaries <= 0 || nbuPct < 0 || ktgPct < 0) return null;
  if (bvgPct !== null && !(Number.isFinite(bvgPct) && bvgPct >= 0)) return null;
  const annual = period === 'year' ? gross : gross * salaries;
  const coordinated = bvgCoordinatedSalary(annual, P);
  const creditRate = bvgCreditRate(age);
  const bvgRate = bvgPct === null ? creditRate / 2 : bvgPct;
  const lines = {
    ahv: round2((annual * P.ahvIvEo) / 100),
    alv: round2((Math.min(annual, P.alvCeiling) * P.alv) / 100),
    nbu: round2((Math.min(annual, P.uvgMaxInsured) * nbuPct) / 100),
    ktg: round2((annual * ktgPct) / 100),
    bvg: round2((coordinated * bvgRate) / 100),
  };
  const per = Object.fromEntries(Object.entries(lines).map(([k, v]) => [k, round2(v / salaries)]));
  const total = round2(Object.values(lines).reduce((a, b) => a + b, 0));
  const totalPer = round2(Object.values(per).reduce((a, b) => a + b, 0));
  const grossPer = round2(annual / salaries);
  return {
    annual: round2(annual), grossPer, coordinated, creditRate, bvgRate,
    lines, per, total, totalPer,
    net: round2(annual - total), netPer: round2(grossPer - totalPer),
  };
}

// ---------- Rent and reference interest rate (VMWG / OBLF) ----------

/** Reference rate for rents (BWO), as published; checked on 25.11.2026 (next publication 01.12.2026). */
export const REFERENCE_RATE = Object.freeze({ current: 1.25, since: '2025-09-02' });

/** History of the reference rate (BWO): [valid from, rate %]. */
export const REFERENCE_RATE_HISTORY = Object.freeze([
  ['2008-09-10', 3.5], ['2009-06-03', 3.25], ['2009-09-02', 3], ['2010-12-02', 2.75], ['2011-12-02', 2.5],
  ['2012-06-02', 2.25], ['2013-09-03', 2], ['2015-06-02', 1.75], ['2017-06-02', 1.5], ['2020-03-03', 1.25],
  ['2023-06-02', 1.5], ['2023-12-02', 1.75], ['2025-03-04', 1.5], ['2025-09-02', 1.25],
]);

/** Art. 13 para. 1 VMWG: max. rent change in % for a quarter-point step ending at this mortgage rate level. */
export function quarterStepPct(rateAfterStep) {
  if (rateAfterStep > 6) return 2;
  if (rateAfterStep >= 5) return 2.5;
  return 3;
}

/**
 * Rent change in % caused by a reference-rate change (Art. 13 VMWG).
 * Increase: per-step percentages are added (e.g. 2 steps below 5 % = +6 %).
 * Decrease: the inverse, -(1 - 1/(1 + x)) (e.g. 1 step = -2.91 %, 2 steps = -5.66 %), as published by the BWO.
 * Returns { steps, pct } or null if a rate is not a multiple of 0.25.
 */
export function referenceRateChange(oldRate, newRate) {
  const q = (r) => Math.round(r * 4);
  if (![oldRate, newRate].every(Number.isFinite) || Math.abs(oldRate * 4 - q(oldRate)) > 1e-9 || Math.abs(newRate * 4 - q(newRate)) > 1e-9) return null;
  const a = q(oldRate);
  const b = q(newRate);
  const lo = Math.min(a, b);
  const hi = Math.max(a, b);
  let x = 0;
  for (let k = lo + 1; k <= hi; k++) x += quarterStepPct(k / 4);
  const pct = b >= a ? x : -(1 - 1 / (1 + x / 100)) * 100;
  return { steps: b - a, pct };
}

/** Art. 16 VMWG: inflation compensation = 40 % of the change of the consumer price index (LIK / IPC). */
export function inflationCompensationPct(oldIndex, newIndex) {
  if (!(oldIndex > 0) || !(newIndex > 0)) return null;
  return 0.4 * (newIndex / oldIndex - 1) * 100;
}

/** Whole months from date a to date b ("YYYY-MM-DD"), 0 if b <= a, null if invalid. */
export function wholeMonthsBetween(aStr, bStr) {
  const pa = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(aStr ?? ''));
  const pb = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(bStr ?? ''));
  if (!pa || !pb || !Number.isFinite(parseIsoDate(aStr)) || !Number.isFinite(parseIsoDate(bStr))) return null;
  let m = (Number(pb[1]) - Number(pa[1])) * 12 + (Number(pb[2]) - Number(pa[2]));
  if (Number(pb[3]) < Number(pa[3])) m -= 1;
  return Math.max(0, m);
}

/**
 * Estimated new net rent. Percentages of the three factors are added, then applied to the current net rent.
 * opts: { rent, oldRate, newRate, oldIndex?, newIndex?, costPctPerYear?, lastDate?, refDate? }
 * costPctPerYear is applied pro rata for the whole months between lastDate and refDate.
 */
export function rentAdjustment({ rent, oldRate, newRate, oldIndex = null, newIndex = null, costPctPerYear = 0, lastDate = null, refDate = null }) {
  if (!(rent > 0)) return null;
  const ref = referenceRateChange(oldRate, newRate);
  if (!ref) return null;
  let inflPct = 0;
  if (oldIndex !== null || newIndex !== null) {
    inflPct = inflationCompensationPct(oldIndex, newIndex);
    if (inflPct === null) return null;
  }
  let months = null;
  let costPct = 0;
  if (costPctPerYear) {
    months = wholeMonthsBetween(lastDate, refDate);
    if (months === null || !Number.isFinite(costPctPerYear)) return null;
    costPct = (costPctPerYear * months) / 12;
  }
  const totalPct = ref.pct + inflPct + costPct;
  const newRent = round2(rent * (1 + totalPct / 100));
  return { steps: ref.steps, refPct: ref.pct, inflPct, costPct, months, totalPct, newRent, diff: round2(newRent - rent), diffYear: round2((newRent - rent) * 12) };
}
