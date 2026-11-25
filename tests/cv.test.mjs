// Run: node tests/cv.test.mjs
import {
  PERMITS, LEVELS, LABELS, CV_LANGS, parseMonth, monthIndex, formatMonth, formatPeriod, parseSwissDate, formatSwissDate, ageAt,
  sortAntichrono, sortLanguages, hasEszett, fixEszett, tasksToBullets, isSwissNationality, isEmail, fileNameFor,
  findGaps, validateCv, emptyCv, sanitizeDraft,
} from '../js/cv.js';

let pass = 0;
let fail = 0;
function eq(name, actual, expected) {
  const ok = JSON.stringify(actual) === JSON.stringify(expected);
  if (ok) { pass++; console.log(`ok   ${name}`); }
  else { fail++; console.log(`FAIL ${name}\n     expected ${JSON.stringify(expected)}\n     got      ${JSON.stringify(actual)}`); }
}
const TODAY = { y: 2026, m: 11, d: 25 };
const codes = (list) => list.map((x) => x.code);

// Constants
eq('4 CV languages', CV_LANGS, ['de', 'fr', 'it', 'en']);
eq('labels for every CV language have the same keys', CV_LANGS.map((l) => Object.keys(LABELS[l]).join()), CV_LANGS.map(() => Object.keys(LABELS.de).join()));
eq('permits B C G L Ci F N S', Object.keys(PERMITS), ['B', 'C', 'G', 'L', 'Ci', 'F', 'N', 'S']);
eq('every permit named in 4 languages', Object.values(PERMITS).every((p) => CV_LANGS.every((l) => p[l])), true);
eq('CEFR levels', LEVELS, ['native', 'C2', 'C1', 'B2', 'B1', 'A2', 'A1']);

// Months
eq('parse 03.2021', parseMonth('03.2021'), { y: 2021, m: 3 });
eq('parse 3/2021', parseMonth('3/2021'), { y: 2021, m: 3 });
eq('parse 2021-03', parseMonth('2021-03'), { y: 2021, m: 3 });
eq('parse bare year', parseMonth(' 2019 '), { y: 2019, m: 0 });
eq('reject month 13', parseMonth('13.2021'), null);
eq('reject text', parseMonth('März 2021'), null);
eq('reject empty', parseMonth(''), null);
eq('format month', formatMonth({ y: 2021, m: 3 }), '03.2021');
eq('format bare year', formatMonth({ y: 2019, m: 0 }), '2019');
eq('period de', formatPeriod({ from: '8.2018', to: '2.2021' }), '08.2018 – 02.2021');
eq('period current de', formatPeriod({ from: '03.2021', current: true }, 'de'), '03.2021 – heute');
eq('period current fr', formatPeriod({ from: '03.2021', current: true }, 'fr'), '03.2021 – aujourd’hui');
eq('period current it', formatPeriod({ from: '03.2021', current: true }, 'it'), '03.2021 – oggi');
eq('period current en', formatPeriod({ from: '03.2021', current: true }, 'en'), '03.2021 – present');
eq('period same month', formatPeriod({ from: '06.2020', to: '06.2020' }), '06.2020');
eq('month index order', monthIndex({ y: 2021, m: 1 }) - monthIndex({ y: 2020, m: 12 }), 1);

// Dates
eq('parse 21.04.1989', parseSwissDate('21.04.1989'), { y: 1989, m: 4, d: 21 });
eq('parse ISO', parseSwissDate('1989-04-21'), { y: 1989, m: 4, d: 21 });
eq('reject 31.02.2000', parseSwissDate('31.02.2000'), null);
eq('accept 29.02.2024', parseSwissDate('29.02.2024'), { y: 2024, m: 2, d: 29 });
eq('format date pads', formatSwissDate({ y: 1989, m: 4, d: 1 }), '01.04.1989');
eq('age before birthday', ageAt({ y: 1990, m: 12, d: 1 }, TODAY), 35);
eq('age on birthday', ageAt({ y: 1990, m: 11, d: 25 }, TODAY), 36);

// Ordering
const jobs = [
  { from: '2010', to: '2012', role: 'A' },
  { from: '03.2021', current: true, role: 'C' },
  { from: '01.2015', to: '02.2021', role: 'B' },
];
eq('anti-chronological', sortAntichrono(jobs).map((j) => j.role), ['C', 'B', 'A']);
eq('sort keeps input untouched', jobs.map((j) => j.role), ['A', 'C', 'B']);
eq('two current: latest start first', sortAntichrono([{ from: '2019', current: true, r: 1 }, { from: '2022', current: true, r: 2 }]).map((x) => x.r), [2, 1]);
eq('languages: native first, then level', sortLanguages([
  { name: 'Englisch', level: 'B2' }, { name: 'Italienisch', level: '' }, { name: 'Deutsch', level: 'native' }, { name: 'Französisch', level: 'C1' },
]).map((l) => l.name), ['Deutsch', 'Französisch', 'Englisch', 'Italienisch']);

// Text
eq('eszett found', hasEszett('Strasse und Straße'), true);
eq('no eszett', hasEszett('Strasse'), false);
eq('fix eszett', fixEszett('Große Straße, GROẞ'), 'Grosse Strasse, GROSS');
eq('bullets from lines', tasksToBullets('- Kasse\n• Beratung\n\n  * Inventar '), ['Kasse', 'Beratung', 'Inventar']);
eq('swiss de', isSwissNationality('Schweiz'), true);
eq('swiss double', isSwissNationality('Schweiz / Italien'), true);
eq('swiss fr', isSwissNationality('Suisse et France'), true);
eq('swiss it lowercase', isSwissNationality('svizzera'), true);
eq('not swiss', isSwissNationality('Portugal'), false);
eq('not swiss: Schweden', isSwissNationality('Schweden'), false);
eq('email ok', isEmail('anna.muster@example.ch'), true);
eq('email bad', isEmail('anna@example'), false);
eq('file name de', fileNameFor({ lang: 'de', person: { first: 'Anna', last: 'Müller Rossi' } }), 'Lebenslauf_Anna_Müller-Rossi');
eq('file name fr strips slashes', fileNameFor({ lang: 'fr', person: { first: 'Zoé', last: 'D/Ami' } }), 'CV_Zoé_D-Ami');

// Gaps
eq('gap of 8 months', findGaps([{ from: '01.2018', to: '06.2019' }, { from: '03.2020', current: true }], TODAY), [{ from: { y: 2019, m: 7 }, months: 8 }]);
eq('no gap of 6 months exactly', findGaps([{ from: '01.2018', to: '06.2019' }, { from: '01.2020', to: '12.2020' }], TODAY), []);
eq('overlap is no gap', findGaps([{ from: '01.2015', to: '12.2020' }, { from: '06.2016', to: '06.2017' }, { from: '01.2021', current: true }], TODAY), []);
eq('bare years: full year covered', findGaps([{ from: '2010', to: '2012' }, { from: '2013', to: '2014' }], TODAY), []);

// Validation
const good = {
  ...emptyCv('de'),
  person: { ...emptyCv().person, first: 'Anna', last: 'Muster', street: 'Musterweg 1', city: '3000 Bern', phone: '079 000 00 00', email: 'anna@example.ch', birth: '01.02.1990', nationality: 'Portugal', permit: 'C' },
  photo: '',
  work: [{ from: '03.2021', current: true, role: 'Verkäuferin', org: 'Muster AG', place: 'Bern', tasks: 'Beratung\nKasse', cert: true }],
  edu: [{ from: '08.2018', to: '07.2021', title: 'EFZ Detailhandel', school: 'Berufsschule', place: 'Bern' }],
  langs: [{ name: 'Portugiesisch', level: 'native' }, { name: 'Deutsch', level: 'B2' }],
};
eq('good CV: no errors or warnings', validateCv(good, TODAY).filter((x) => x.level !== 'info').map((x) => x.code), []);
eq('good CV: infos photo + certs', codes(validateCv(good, TODAY)), ['photo', 'certs']);
eq('certs list', validateCv(good, TODAY).find((x) => x.code === 'certs').list, ['Muster AG']);
eq('missing permit for foreign nationality', codes(validateCv({ ...good, person: { ...good.person, permit: '' } }, TODAY)).includes('permit'), true);
eq('no permit needed for Swiss', codes(validateCv({ ...good, person: { ...good.person, nationality: 'Schweiz', permit: '' } }, TODAY)).includes('permit'), false);
eq('bad email', codes(validateCv({ ...good, person: { ...good.person, email: 'x@y' } }, TODAY)).includes('email'), true);
eq('no contact', codes(validateCv({ ...good, person: { ...good.person, email: '', phone: '' } }, TODAY)).includes('contact'), true);
eq('bad birth date', codes(validateCv({ ...good, person: { ...good.person, birth: '31.02.1990' } }, TODAY)).includes('birthFormat'), true);
eq('implausible age', validateCv({ ...good, person: { ...good.person, birth: '01.01.2020' } }, TODAY).find((x) => x.code === 'birthAge').age, 6);
eq('end before start', codes(validateCv({ ...good, edu: [{ ...good.edu[0], from: '08.2021', to: '07.2018' }] }, TODAY)).includes('endBeforeStart'), true);
eq('month format error carries value', validateCv({ ...good, edu: [{ ...good.edu[0], from: 'Sommer 18' }] }, TODAY).find((x) => x.code === 'monthFormat').value, 'Sommer 18');
eq('language without level', codes(validateCv({ ...good, langs: [...good.langs, { name: 'Englisch', level: '' }] }, TODAY)).includes('level'), true);
eq('no mother tongue', codes(validateCv({ ...good, langs: [{ name: 'Deutsch', level: 'B2' }] }, TODAY)).includes('native'), true);
eq('eszett warning in German CV', codes(validateCv({ ...good, person: { ...good.person, street: 'Hauptstraße 1' } }, TODAY)).includes('eszett'), true);
eq('no eszett warning in English CV', codes(validateCv({ ...good, lang: 'en', person: { ...good.person, street: 'Hauptstraße 1' } }, TODAY)).includes('eszett'), false);
eq('work without tasks', codes(validateCv({ ...good, work: [{ ...good.work[0], tasks: '' }] }, TODAY)).includes('tasks'), true);
eq('gap reported', validateCv({ ...good, edu: [{ ...good.edu[0], from: '08.2015', to: '07.2018' }], work: [{ ...good.work[0], from: '03.2020' }] }, TODAY).find((x) => x.code === 'gap'), { level: 'warn', code: 'gap', from: '08.2018', months: 19 });
eq('empty CV errors', codes(validateCv(emptyCv('fr'), TODAY)).filter((c) => ['name', 'contact', 'empty'].includes(c)), ['name', 'contact', 'empty']);
eq('referees named: ask first', codes(validateCv({ ...good, refMode: 'list', refs: [{ name: 'Max Beispiel' }] }, TODAY)).includes('refsAsk'), true);

// Draft files
const s = sanitizeDraft({ lang: 'it', person: { first: 'Luca', permit: 'X', evil: 'x' }, photo: 'javascript:alert(1)', work: [{ role: 'R', current: 'yes' }], langs: [{ name: 'Italiano', level: 'native' }, { name: 'X', level: 'Z9' }], refMode: 'other' });
eq('sanitize keeps lang', s.lang, 'it');
eq('sanitize drops unknown permit', s.person.permit, '');
eq('sanitize drops unknown keys', Object.keys(s.person).includes('evil'), false);
eq('sanitize rejects non-image photo', s.photo, '');
eq('sanitize forces booleans', s.work[0].current, false);
eq('sanitize drops unknown level', s.langs.map((l) => l.level), ['native', '']);
eq('sanitize refMode default', s.refMode, 'request');
eq('sanitize accepts png data url', sanitizeDraft({ photo: 'data:image/png;base64,iVBORw0KGgo=' }).photo, 'data:image/png;base64,iVBORw0KGgo=');
eq('sanitize garbage input', sanitizeDraft(null).lang, 'de');
eq('round trip', sanitizeDraft(JSON.parse(JSON.stringify(good))).work[0].role, 'Verkäuferin');

console.log(`\n${pass} passed, ${fail} failed`);
if (fail) process.exit(1);
