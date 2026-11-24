// Run: node tests/calc.test.mjs
import {
  VAT_RATES, round2, roundTo5Rappen, parseNumber, addVat, removeVat,
  percentOf, whatPercent, percentChange, applyPercent,
  parseTime, dayWork, requiredBreak, breakCheck, weekCheck, formatHM, toDecimalHours,
  validateIban, formatIban, isQrIban, IBAN_LENGTHS,
  monthlyToHourly, hourlyToMonthly, parseIsoDate, daysBetween,
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

console.log(`\n${pass} passed, ${fail} failed`);
if (fail) process.exit(1);
