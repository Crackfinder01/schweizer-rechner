// Run: node tests/calc.test.mjs
import {
  VAT_RATES, round2, roundTo5Rappen, parseNumber, addVat, removeVat,
  percentOf, whatPercent, percentChange, applyPercent,
  parseTime, dayWork, requiredBreak, breakCheck, weekCheck, formatHM, toDecimalHours,
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

console.log(`\n${pass} passed, ${fail} failed`);
if (fail) process.exit(1);
