// Run: node tests/calc.test.mjs
import {
  VAT_RATES, round2, roundTo5Rappen, parseNumber, addVat, removeVat,
  percentOf, whatPercent, percentChange, applyPercent,
  parseTime, dayWork, requiredBreak, breakCheck, weekCheck, formatHM, toDecimalHours,
  validateIban, formatIban, isQrIban, IBAN_LENGTHS,
  monthlyToHourly, hourlyToMonthly, parseIsoDate, daysBetween,
  PAYROLL_2026, bvgCreditRate, bvgCoordinatedSalary, grossToNet,
  REFERENCE_RATE, REFERENCE_RATE_HISTORY, quarterStepPct, referenceRateChange, inflationCompensationPct,
  wholeMonthsBetween, rentAdjustment,
} from '../js/calc.js';

let pass = 0;
let fail = 0;
function eq(name, actual, expected) {
  const ok = typeof expected === 'number' && typeof actual === 'number'
    ? Math.abs(actual - expected) < 1e-9
    : JSON.stringify(actual) === JSON.stringify(expected);
  if (ok) { pass++; console.log(`ok   ${name}`); }
  else { fail++; console.log(`FAIL ${name}\n     expected ${JSON.stringify(expected)}\n     got      ${JSON.stringify(actual)}`); }
}

// Rates
eq('VAT rates 8.1 / 2.6 / 3.8', [VAT_RATES.normal, VAT_RATES.reduced, VAT_RATES.accommodation], [8.1, 2.6, 3.8]);

// VAT add
eq('add 8.1% to 250.00', addVat(250, 8.1), { net: 250, vat: 20.25, gross: 270.25 });
eq('add 2.6% to 40.00', addVat(40, 2.6), { net: 40, vat: 1.04, gross: 41.04 });
eq('add 3.8% to 180.00', addVat(180, 3.8), { net: 180, vat: 6.84, gross: 186.84 });
eq('add 8.1% to 100.00', addVat(100, 8.1), { net: 100, vat: 8.1, gross: 108.1 });

// VAT remove
eq('remove 8.1% from 108.10', removeVat(108.1, 8.1), { net: 100, vat: 8.1, gross: 108.1 });
eq('remove 2.6% from 41.04', removeVat(41.04, 2.6), { net: 40, vat: 1.04, gross: 41.04 });
eq('remove 3.8% from 186.84', removeVat(186.84, 3.8), { net: 180, vat: 6.84, gross: 186.84 });
eq('remove 8.1% from 50.00', removeVat(50, 8.1), { net: 46.25, vat: 3.75, gross: 50 });

// 5-Rappen rounding
eq('5 Rp: 3.8313 -> 3.85', roundTo5Rappen(3.8313), 3.85);
eq('5 Rp: 1.024 -> 1.00', roundTo5Rappen(1.024), 1.0);
eq('5 Rp: 1.025 -> 1.05 (half up)', roundTo5Rappen(1.025), 1.05);
eq('5 Rp: 12.97 -> 12.95', roundTo5Rappen(12.97), 12.95);
eq('add 8.1% to 47.30 with 5 Rp', addVat(47.3, 8.1, true), { net: 47.3, vat: 3.85, gross: 51.15 });
eq('remove 8.1% from 51.20 with 5 Rp', removeVat(51.2, 8.1, true), { net: 47.35, vat: 3.85, gross: 51.2 });
eq('round2 1.005 -> 1.01', round2(1.005), 1.01);

// Input parsing
eq('parse "1\'234.50"', parseNumber("1'234.50"), 1234.5);
eq('parse "12,5"', parseNumber('12,5'), 12.5);
eq('parse "abc" -> NaN', Number.isNaN(parseNumber('abc')), true);

// Percent
eq('15 % of 240', percentOf(15, 240), 36);
eq('45 is 25 % of 180', whatPercent(45, 180), 25);
eq('what % of 0 -> null', whatPercent(5, 0), null);
eq('change 80 -> 92 = +15 %', percentChange(80, 92), 15);
eq('change 200 -> 150 = -25 %', percentChange(200, 150), -25);
eq('60 plus 15 %', applyPercent(60, 15, 1), 69);
eq('1200 minus 20 %', applyPercent(1200, 20, -1), 960);

// Working time
eq('parseTime 07:30', parseTime('07:30'), 450);
eq('parseTime 25:00 invalid', Number.isNaN(parseTime('25:00')), true);
eq('day 07:30-17:00 pause 45', dayWork(450, 1020, 45), { span: 570, pause: 45, net: 525, overnight: false });
eq('night 22:00-06:30 pause 30', dayWork(1320, 390, 30), { span: 510, pause: 30, net: 480, overnight: true });
eq('night 23:00-00:00 = 1 h', dayWork(1380, 0, 0).net, 60);
eq('formatHM 525 -> 8:45', formatHM(525), '8:45');
eq('decimal 525 min -> 8.75', toDecimalHours(525), 8.75);

// Break flags (Art. 15 ArG)
eq('5:30 exactly -> no break', requiredBreak(330), 0);
eq('5:31 -> 15 min', requiredBreak(331), 15);
eq('7:00 exactly -> 15 min', requiredBreak(420), 15);
eq('7:01 -> 30 min', requiredBreak(421), 30);
eq('9:01 -> 60 min', requiredBreak(541), 60);
eq('8:45 worked, 45 min pause -> ok', breakCheck(525, 45), { required: 30, ok: true });
eq('9:15 worked, 30 min pause -> flag', breakCheck(555, 30), { required: 60, ok: false });

// Weekly maximum (Art. 9 ArG)
eq('43:45 h week -> under 45', weekCheck(2625), { hours: 43.75, over45: false, over50: false });
eq('47 h week -> over 45', weekCheck(2820).over45 && !weekCheck(2820).over50, true);
eq('51 h week -> over 50', weekCheck(3060).over50, true);

// IBAN
eq('IBAN CH9300762011623852957 valid', validateIban('CH9300762011623852957').valid, true);
eq('IBAN DE89370400440532013000 valid', validateIban('DE89370400440532013000').valid, true);
eq('IBAN with spaces/lowercase valid', validateIban('ch93 0076 2011 6238 5295 7').valid, true);
eq('IBAN FR (letters in BBAN) valid', validateIban('FR1420041010050500013M02606').valid, true);
eq('IBAN AT valid', validateIban('AT611904300234573201').valid, true);
eq('IBAN LI valid', validateIban('LI21088100002324013AA').valid, true);
eq('IBAN IT valid', validateIban('IT60X0542811101000000123456').valid, true);
eq('IBAN wrong check digit -> checksum', validateIban('CH9300762011623852958').errors, ['checksum']);
eq('IBAN DE swapped digits -> checksum', validateIban('DE89370400440532013001').errors, ['checksum']);
eq('IBAN CH too short -> length', validateIban('CH930076201162385295').errors, ['length']);
eq('IBAN invalid char -> chars', validateIban('CH93007620116238529_7').errors.includes('chars'), true);
eq('IBAN empty -> empty', validateIban('  ').errors, ['empty']);
eq('IBAN lengths CH/LI/DE/FR/IT/AT', ['CH', 'LI', 'DE', 'FR', 'IT', 'AT'].map((c) => IBAN_LENGTHS[c]), [21, 21, 22, 27, 27, 20]);
eq('format groups of 4', formatIban('CH9300762011623852957'), 'CH93 0076 2011 6238 5295 7');
eq('QR-IBAN CH44 3199 9... detected', validateIban('CH4431999123000889012').qr, true);
eq('normal CH IBAN is not QR', isQrIban('CH9300762011623852957'), false);
eq('QR-IID bounds 30000 / 31999 / 32000', [isQrIban('CH0030000000000000000'), isQrIban('CH0031999000000000000'), isQrIban('CH0032000000000000000')], [true, true, false]);

// Salary
eq('5500 x 13 / (42 x 52) = 32.74 /h', round2(monthlyToHourly(5500, 42, 13, 52).hourly), 32.74);
eq('5500 x 12 / (42 x 52) = 30.22 /h', round2(monthlyToHourly(5500, 42, 12, 52).hourly), 30.22);
eq('32.50 /h x 42 x 52 / 12 = 5915', hourlyToMonthly(32.5, 42, 12, 52).monthly, 5915);
eq('round trip monthly -> hourly -> monthly', round2(hourlyToMonthly(monthlyToHourly(6200, 40, 13, 50).hourly, 40, 13, 50).monthly), 6200);
eq('salary zero hours -> null', monthlyToHourly(5000, 0, 12, 52), null);

// Days between dates
eq('parseIsoDate invalid 2027-02-29', Number.isNaN(parseIsoDate('2027-02-29')), true);
eq('2027-03-01 -> 2027-06-01: 92 days, 66 weekdays', (({ calendar, weekdays }) => [calendar, weekdays])(daysBetween('2027-03-01', '2027-06-01')), [92, 66]);
eq('include end day adds 1', daysBetween('2027-03-01', '2027-03-01', { includeEnd: true }).calendar, 1);
eq('same day, end excluded = 0', daysBetween('2027-03-01', '2027-03-01').calendar, 0);
eq('leap year 2028-02-01 -> 2028-03-01 = 29', daysBetween('2028-02-01', '2028-03-01').calendar, 29);
eq('21.12.2026-08.01.2027 incl.: 15 weekdays', daysBetween('2026-12-21', '2027-01-08', { includeEnd: true }).weekdays, 15);
eq('same with fixed holidays: 13 (25.12 + 1.1 on Fridays)', daysBetween('2026-12-21', '2027-01-08', { includeEnd: true, excludeFixedHolidays: true }).weekdays, 13);
eq('1 Aug 2027 is a Sunday: nothing extra removed', daysBetween('2027-07-26', '2027-08-06', { includeEnd: true, excludeFixedHolidays: true }).holidaysExcluded, 0);
eq('reversed dates are swapped', (({ calendar, swapped }) => [calendar, swapped])(daysBetween('2027-06-01', '2027-03-01')), [92, true]);
eq('weeks + rest days', (({ weeks, restDays }) => [weeks, restDays])(daysBetween('2027-03-01', '2027-06-01')), [13, 1]);

// Gross -> net salary 2026 (hand-computed)
eq('2026 constants (AHV 5.3, ALV 1.1, ceilings, BVG)', [PAYROLL_2026.ahvIvEo, PAYROLL_2026.alv, PAYROLL_2026.alvCeiling, PAYROLL_2026.uvgMaxInsured, PAYROLL_2026.bvgEntryThreshold, PAYROLL_2026.bvgCoordinationDeduction, PAYROLL_2026.bvgUpperLimit, PAYROLL_2026.bvgMinCoordinated], [5.3, 1.1, 148200, 148200, 22680, 26460, 90720, 3780]);
eq('BVG credit by age 24/25/34/35/45/55/65/66', [24, 25, 34, 35, 45, 55, 65, 66].map(bvgCreditRate), [0, 7, 7, 10, 15, 18, 18, 0]);
eq('coordinated: 84500 -> 58040', bvgCoordinatedSalary(84500), 58040);
eq('coordinated: 180000 -> max 64260', bvgCoordinatedSalary(180000), 64260);
eq('coordinated: 24000 -> min 3780', bvgCoordinatedSalary(24000), 3780);
eq('coordinated: 22680 exactly -> 0 (must be more than)', bvgCoordinatedSalary(22680), 0);
eq('coordinated: 21600 -> 0', bvgCoordinatedSalary(21600), 0);
{
  // 6500 x 13 = 84500; AHV 4478.50; ALV 929.50; NBU 1 % 845.00; BVG 58040 x 5 % = 2902.00; total 9155.00
  const r = grossToNet({ gross: 6500, period: 'month', salaries: 13, age: 40, nbuPct: 1 });
  eq('6500 x 13, age 40: annual lines', r.lines, { ahv: 4478.5, alv: 929.5, nbu: 845, ktg: 0, bvg: 2902 });
  eq('6500 x 13, age 40: total / net per year', [r.total, r.net], [9155, 75345]);
  eq('6500 x 13, age 40: per payment 344.50 / 71.50 / 65.00 / 223.23', [r.per.ahv, r.per.alv, r.per.nbu, r.per.bvg], [344.5, 71.5, 65, 223.23]);
  eq('6500 x 13, age 40: net per payment 5795.77', r.netPer, 5795.77);
}
{
  // 15000 x 12 = 180000; ALV on 148200 = 1630.20; NBU on 148200 = 1482; BVG 64260 x 7.5 % = 4819.50
  const r = grossToNet({ gross: 15000, period: 'month', salaries: 12, age: 50, nbuPct: 1 });
  eq('15000 x 12, age 50: ALV and NBU capped at 148200', [r.lines.alv, r.lines.nbu], [1630.2, 1482]);
  eq('15000 x 12, age 50: AHV 9540, BVG 4819.50', [r.lines.ahv, r.lines.bvg], [9540, 4819.5]);
  eq('15000 x 12, age 50: per month 795 / 135.85 / 123.50 / 401.63 -> net 13544.02', [r.per.ahv, r.per.alv, r.per.nbu, r.per.bvg, r.netPer], [795, 135.85, 123.5, 401.63, 13544.02]);
}
eq('1800 x 12 below BVG threshold: net 1666.80, no BVG', (({ netPer, lines }) => [netPer, lines.bvg])(grossToNet({ gross: 1800, salaries: 12, age: 30, nbuPct: 1 })), [1666.8, 0]);
eq('annual input 62400, age 28, NBU 1.2 %, KTG 0.5 %: lines', grossToNet({ gross: 62400, period: 'year', salaries: 12, age: 28, nbuPct: 1.2, ktgPct: 0.5 }).lines, { ahv: 3307.2, alv: 686.4, nbu: 748.8, ktg: 312, bvg: 1257.9 });
eq('custom BVG 6 % of coordinated 58040 = 3482.40', grossToNet({ gross: 84500, period: 'year', salaries: 12, age: 40, nbuPct: 0, bvgPct: 6 }).lines.bvg, 3482.4);
eq('age 22: no BVG savings credit', grossToNet({ gross: 5000, salaries: 12, age: 22, nbuPct: 1 }).lines.bvg, 0);
eq('NBU 0 (under 8 h per week)', grossToNet({ gross: 1000, salaries: 12, age: 30, nbuPct: 0 }).lines.nbu, 0);
eq('invalid salary -> null', grossToNet({ gross: NaN, salaries: 12, age: 30 }), null);
eq('negative NBU -> null', grossToNet({ gross: 5000, salaries: 12, age: 30, nbuPct: -1 }), null);

// Rent and reference rate (Art. 13 / 16 VMWG; BWO)
eq('current reference rate 1.25 % since 2025-09-02', [REFERENCE_RATE.current, REFERENCE_RATE.since], [1.25, '2025-09-02']);
eq('history last entry = current rate', REFERENCE_RATE_HISTORY[REFERENCE_RATE_HISTORY.length - 1], ['2025-09-02', 1.25]);
eq('history first entry 3.5 % from 2008-09-10', REFERENCE_RATE_HISTORY[0], ['2008-09-10', 3.5]);
eq('quarter step 3 / 2.5 / 2.5 / 2 (below 5, 5, 6, above 6)', [quarterStepPct(4.75), quarterStepPct(5), quarterStepPct(6), quarterStepPct(6.25)], [3, 2.5, 2.5, 2]);
eq('1.50 -> 1.25 = -2.91 %', round2(referenceRateChange(1.5, 1.25).pct), -2.91);
eq('1.75 -> 1.25 = -5.66 %', round2(referenceRateChange(1.75, 1.25).pct), -5.66);
eq('2.00 -> 1.25 = -8.26 %', round2(referenceRateChange(2, 1.25).pct), -8.26);
eq('2.25 -> 1.25 = -10.71 %', round2(referenceRateChange(2.25, 1.25).pct), -10.71);
eq('1.25 -> 1.50 = +3 %', referenceRateChange(1.25, 1.5), { steps: 1, pct: 3 });
eq('1.25 -> 2.00 = +9 %', referenceRateChange(1.25, 2), { steps: 3, pct: 9 });
eq('same rate = 0', referenceRateChange(1.25, 1.25), { steps: 0, pct: 0 });
eq('4.75 -> 5.25 = 2.5 + 2.5 = +5 %', referenceRateChange(4.75, 5.25).pct, 5);
eq('rate not a quarter -> null', referenceRateChange(1.3, 1.25), null);
eq('LIK 105.0 -> 107.1: 40 % of 2 % = 0.8 %', round2(inflationCompensationPct(105, 107.1)), 0.8);
eq('LIK falls 100 -> 99: -0.4 %', round2(inflationCompensationPct(100, 99)), -0.4);
eq('months 2023-12-01 -> 2026-12-01 = 36', wholeMonthsBetween('2023-12-01', '2026-12-01'), 36);
eq('months 2024-01-31 -> 2024-03-30 = 1', wholeMonthsBetween('2024-01-31', '2024-03-30'), 1);
eq('months reversed -> 0', wholeMonthsBetween('2026-12-01', '2026-01-01'), 0);
{
  // 1800 x (1 - 5.6604 % + 0.8 %) = 1712.51
  const r = rentAdjustment({ rent: 1800, oldRate: 1.75, newRate: 1.25, oldIndex: 105, newIndex: 107.1 });
  eq('rent 1800, 1.75 -> 1.25, LIK +2 %: new rent 1712.51', [r.newRent, r.diff, r.diffYear], [1712.51, -87.49, -1049.88]);
  eq('rent example total -4.86 %', round2(r.totalPct), -4.86);
  const c = rentAdjustment({ rent: 1800, oldRate: 1.75, newRate: 1.25, oldIndex: 105, newIndex: 107.1, costPctPerYear: 0.5, lastDate: '2023-12-01', refDate: '2026-12-01' });
  eq('with 0.5 %/year for 36 months: +1.5 %, new rent 1739.51', [round2(c.costPct), c.months, c.newRent], [1.5, 36, 1739.51]);
}
eq('rent 1450, 1.50 -> 1.25 only: 1407.77', rentAdjustment({ rent: 1450, oldRate: 1.5, newRate: 1.25 }).newRent, 1407.77);
eq('rent 1500, 1.25 -> 1.50: +3 % = 1545', rentAdjustment({ rent: 1500, oldRate: 1.25, newRate: 1.5 }).newRent, 1545);
eq('rent: one index missing -> null', rentAdjustment({ rent: 1500, oldRate: 1.5, newRate: 1.25, oldIndex: 100 }), null);
eq('rent: cost without dates -> null', rentAdjustment({ rent: 1500, oldRate: 1.5, newRate: 1.25, costPctPerYear: 0.5 }), null);
eq('rent 0 -> null', rentAdjustment({ rent: 0, oldRate: 1.5, newRate: 1.25 }), null);

console.log(`\n${pass} passed, ${fail} failed`);
if (fail) process.exit(1);
