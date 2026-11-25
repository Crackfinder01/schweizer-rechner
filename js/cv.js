// Swiss CV (Lebenslauf / CV) logic. Pure functions, no DOM, no network, no storage.
// Everything the user types (including the photo) stays in the browser.

export const CV_LANGS = Object.freeze(['de', 'fr', 'it', 'en']);

// Residence permits (Ausweise). Names: canton of Fribourg (L, B, C, G, Ci) and SEM (F, N, S).
export const PERMITS = Object.freeze({
  B: { de: 'Ausweis B (Aufenthaltsbewilligung)', fr: 'Permis B (autorisation de séjour)', it: 'Permesso B (permesso di dimora)', en: 'Permit B (residence permit)' },
  C: { de: 'Ausweis C (Niederlassungsbewilligung)', fr: 'Permis C (autorisation d’établissement)', it: 'Permesso C (permesso di domicilio)', en: 'Permit C (settlement permit)' },
  G: { de: 'Ausweis G (Grenzgängerbewilligung)', fr: 'Permis G (autorisation frontalière)', it: 'Permesso G (permesso per frontalieri)', en: 'Permit G (cross-border commuter permit)' },
  L: { de: 'Ausweis L (Kurzaufenthaltsbewilligung)', fr: 'Permis L (autorisation de courte durée)', it: 'Permesso L (permesso di breve durata)', en: 'Permit L (short-term residence permit)' },
  Ci: { de: 'Ausweis Ci', fr: 'Permis Ci', it: 'Permesso Ci', en: 'Permit Ci' },
  F: { de: 'Ausweis F (vorläufig aufgenommen)', fr: 'Permis F (admission provisoire)', it: 'Permesso F (ammissione provvisoria)', en: 'Permit F (provisionally admitted)' },
  N: { de: 'Ausweis N (Asylsuchende)', fr: 'Permis N (requérant d’asile)', it: 'Permesso N (richiedenti l’asilo)', en: 'Permit N (asylum seeker)' },
  S: { de: 'Ausweis S (Schutzstatus S)', fr: 'Permis S (statut de protection S)', it: 'Permesso S (statuto di protezione S)', en: 'Permit S (protection status S)' },
});

// Language levels: Common European Framework of Reference (CEFR / GER / CECR / QCER).
export const LEVELS = Object.freeze(['native', 'C2', 'C1', 'B2', 'B1', 'A2', 'A1']);

export const LABELS = Object.freeze({
  de: {
    title: 'Lebenslauf', personal: 'Persönliche Angaben', address: 'Adresse', phone: 'Telefon', email: 'E-Mail',
    birth: 'Geburtsdatum', nationality: 'Nationalität', permit: 'Bewilligung', origin: 'Heimatort', civil: 'Zivilstand',
    license: 'Führerausweis', profile: 'Profil', work: 'Berufserfahrung', edu: 'Aus- und Weiterbildung', langs: 'Sprachen',
    it: 'IT-Kenntnisse', interests: 'Interessen', refs: 'Referenzen', onRequest: 'Auf Anfrage', present: 'heute', native: 'Muttersprache',
    file: 'Lebenslauf',
  },
  fr: {
    title: 'Curriculum vitae', personal: 'Données personnelles', address: 'Adresse', phone: 'Téléphone', email: 'E-mail',
    birth: 'Date de naissance', nationality: 'Nationalité', permit: 'Permis', origin: 'Lieu d’origine', civil: 'État civil',
    license: 'Permis de conduire', profile: 'Profil', work: 'Expérience professionnelle', edu: 'Formation et formation continue', langs: 'Langues',
    it: 'Informatique', interests: 'Centres d’intérêt', refs: 'Références', onRequest: 'Sur demande', present: 'aujourd’hui', native: 'langue maternelle',
    file: 'CV',
  },
  it: {
    title: 'Curriculum vitae', personal: 'Dati personali', address: 'Indirizzo', phone: 'Telefono', email: 'E-mail',
    birth: 'Data di nascita', nationality: 'Nazionalità', permit: 'Permesso', origin: 'Luogo d’origine', civil: 'Stato civile',
    license: 'Licenza di condurre', profile: 'Profilo', work: 'Esperienza professionale', edu: 'Formazione e formazione continua', langs: 'Lingue',
    it: 'Informatica', interests: 'Interessi', refs: 'Referenze', onRequest: 'Su richiesta', present: 'oggi', native: 'lingua madre',
    file: 'CV',
  },
  en: {
    title: 'Curriculum Vitae', personal: 'Personal details', address: 'Address', phone: 'Phone', email: 'Email',
    birth: 'Date of birth', nationality: 'Nationality', permit: 'Permit', origin: 'Place of origin', civil: 'Marital status',
    license: 'Driving licence', profile: 'Profile', work: 'Work experience', edu: 'Education and training', langs: 'Languages',
    it: 'IT skills', interests: 'Interests', refs: 'References', onRequest: 'Available on request', present: 'present', native: 'native',
    file: 'CV',
  },
});

const clean = (s) => (typeof s === 'string' ? s.trim() : '');

// ---------- Dates ----------
// Month input: "03.2021", "3/2021", "03-2021", "2021-03", or a bare year "2021" (month unknown).
export function parseMonth(input) {
  const s = clean(input);
  let m;
  if ((m = s.match(/^(\d{1,2})\s*[./-]\s*(\d{4})$/))) return mk(+m[2], +m[1]);
  if ((m = s.match(/^(\d{4})\s*[./-]\s*(\d{1,2})$/))) return mk(+m[1], +m[2]);
  if ((m = s.match(/^(\d{4})$/))) return mk(+m[1], 0);
  return null;
  function mk(y, mo) {
    if (y < 1900 || y > 2100 || mo < 0 || mo > 12) return null;
    return { y, m: mo };
  }
}

// Months since year 0; a bare year counts as January for ordering and gaps.
export function monthIndex(p) {
  return p.y * 12 + (p.m ? p.m - 1 : 0);
}

export function formatMonth(p) {
  if (!p) return '';
  return p.m ? `${String(p.m).padStart(2, '0')}.${p.y}` : String(p.y);
}

export function formatPeriod(entry, lang = 'de') {
  const a = parseMonth(entry.from);
  const b = entry.current ? null : parseMonth(entry.to);
  const from = formatMonth(a);
  const to = entry.current ? LABELS[lang].present : formatMonth(b);
  if (from && to) return from === to ? from : `${from} – ${to}`;
  return from || to;
}

// Swiss date "dd.mm.yyyy" (also accepts "yyyy-mm-dd" from date pickers).
export function parseSwissDate(input) {
  const s = clean(input);
  let m;
  let y; let mo; let d;
  if ((m = s.match(/^(\d{1,2})\.(\d{1,2})\.(\d{4})$/))) [d, mo, y] = [+m[1], +m[2], +m[3]];
  else if ((m = s.match(/^(\d{4})-(\d{2})-(\d{2})$/))) [y, mo, d] = [+m[1], +m[2], +m[3]];
  else return null;
  const dt = new Date(Date.UTC(y, mo - 1, d));
  if (dt.getUTCFullYear() !== y || dt.getUTCMonth() !== mo - 1 || dt.getUTCDate() !== d) return null;
  return { y, m: mo, d };
}

export function formatSwissDate(p) {
  return p ? `${String(p.d).padStart(2, '0')}.${String(p.m).padStart(2, '0')}.${p.y}` : '';
}

export function ageAt(birth, today) {
  let age = today.y - birth.y;
  if (today.m < birth.m || (today.m === birth.m && today.d < birth.d)) age--;
  return age;
}

// ---------- Ordering ----------
// Anti-chronological: ongoing first, then by end date, then by start date (most recent first).
export function sortAntichrono(entries) {
  const key = (e) => {
    const a = parseMonth(e.from);
    const b = e.current ? null : parseMonth(e.to);
    const end = e.current ? Infinity : b ? monthIndex(b) : a ? monthIndex(a) : -Infinity;
    const start = a ? monthIndex(a) : -Infinity;
    return [end, start];
  };
  return entries
    .map((e, i) => ({ e, i, k: key(e) }))
    .sort((x, y) => (y.k[0] - x.k[0]) || (y.k[1] - x.k[1]) || (x.i - y.i))
    .map((x) => x.e);
}

// Mother tongue(s) first, then from the highest to the lowest level; entries without level last.
export function sortLanguages(langs) {
  const rank = (l) => {
    const r = LEVELS.indexOf(l.level);
    return r === -1 ? LEVELS.length : r;
  };
  return langs.map((l, i) => ({ l, i })).sort((a, b) => (rank(a.l) - rank(b.l)) || (a.i - b.i)).map((x) => x.l);
}

// ---------- Text helpers ----------
export function hasEszett(s) {
  return /[ßẞ]/.test(s);
}

// Swiss Standard German has no ß: replace with ss (capital ẞ with SS).
export function fixEszett(s) {
  return s.replace(/ẞ/g, 'SS').replace(/ß/g, 'ss');
}

export function tasksToBullets(text) {
  return clean(text).split(/\r?\n/).map((l) => l.replace(/^\s*[-•*–·]\s*/, '').trim()).filter(Boolean);
}

const SWISS = ['schweiz', 'schweizerin', 'schweizer', 'suisse', 'svizzera', 'svizzero', 'svizzera', 'switzerland', 'swiss', 'ch'];
export function isSwissNationality(s) {
  const parts = clean(s).toLowerCase().split(/[\s,/;+&]+|\bund\b|\bet\b|\be\b|\band\b/).filter(Boolean);
  return parts.some((p) => SWISS.includes(p));
}

export function isEmail(s) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(clean(s));
}

// File name for the PDF, e.g. "Lebenslauf_Anna_Muster". Keeps letters (with accents), digits and hyphens.
export function fileNameFor(data) {
  const p = data.person || {};
  const parts = [LABELS[data.lang] ? LABELS[data.lang].file : 'CV', p.first, p.last]
    .map((x) => clean(x).normalize('NFC').replace(/[^\p{L}\p{N}-]+/gu, '-').replace(/^-+|-+$/g, ''))
    .filter(Boolean);
  return parts.join('_');
}

// ---------- Gaps ----------
// Gaps between periods of work and education longer than minMonths (default 6).
export function findGaps(entries, today, minMonths = 6) {
  const spans = [];
  for (const e of entries) {
    const a = parseMonth(e.from);
    if (!a) continue;
    const b = e.current ? { y: today.y, m: today.m } : parseMonth(e.to) || a;
    const start = monthIndex(a);
    const end = b.m ? monthIndex(b) : b.y * 12 + 11;
    if (end >= start) spans.push([start, end]);
  }
  spans.sort((x, y) => x[0] - y[0]);
  const gaps = [];
  let reach = null;
  for (const [s, e] of spans) {
    if (reach !== null && s - reach - 1 > minMonths) {
      gaps.push({ from: { y: Math.floor((reach + 1) / 12), m: ((reach + 1) % 12) + 1 }, months: s - reach - 1 });
    }
    reach = reach === null ? e : Math.max(reach, e);
  }
  return gaps;
}

// ---------- Validation ----------
// Returns a list of { level: 'error' | 'warn' | 'info', code, ...params }. The UI translates codes.
export function validateCv(data, today) {
  const out = [];
  const p = data.person || {};
  const add = (level, code, extra = {}) => out.push({ level, code, ...extra });

  if (!clean(p.first) || !clean(p.last)) add('error', 'name');
  if (!clean(p.phone) && !clean(p.email)) add('error', 'contact');
  if (clean(p.email) && !isEmail(p.email)) add('error', 'email');
  if (!clean(p.street) || !clean(p.city)) add('warn', 'address');

  if (clean(p.birth)) {
    const b = parseSwissDate(p.birth);
    if (!b) add('error', 'birthFormat');
    else {
      const age = ageAt(b, today);
      if (age < 13 || age > 80) add('warn', 'birthAge', { age });
    }
  } else add('warn', 'birthMissing');

  if (!clean(p.nationality)) add('warn', 'nationality');
  else if (!isSwissNationality(p.nationality) && !clean(p.permit)) add('warn', 'permit');

  const work = data.work || [];
  const edu = data.edu || [];
  if (!work.length && !edu.length) add('error', 'empty');
  const checkDates = (list, kind) => list.forEach((e, i) => {
    const a = parseMonth(e.from);
    const b = parseMonth(e.to);
    const n = i + 1;
    if (!clean(e.from)) add('warn', 'fromMissing', { kind, n });
    else if (!a) add('error', 'monthFormat', { kind, n, value: clean(e.from) });
    if (!e.current && clean(e.to) && !b) add('error', 'monthFormat', { kind, n, value: clean(e.to) });
    if (!e.current && !clean(e.to) && clean(e.from)) add('warn', 'toMissing', { kind, n });
    if (a && b && !e.current && monthIndex(b) < monthIndex(a)) add('error', 'endBeforeStart', { kind, n });
    if (a && monthIndex(a) > monthIndex({ y: today.y, m: today.m })) add('warn', 'future', { kind, n });
  });
  checkDates(work, 'work');
  checkDates(edu, 'edu');
  work.forEach((e, i) => {
    if (!clean(e.role) || !clean(e.org)) add('error', 'workTitle', { n: i + 1 });
    if (!tasksToBullets(e.tasks || '').length) add('warn', 'tasks', { n: i + 1 });
  });
  edu.forEach((e, i) => {
    if (!clean(e.title) || !clean(e.school)) add('error', 'eduTitle', { n: i + 1 });
  });

  for (const g of findGaps([...work, ...edu], today)) add('warn', 'gap', { from: formatMonth(g.from), months: g.months });

  const langs = (data.langs || []).filter((l) => clean(l.name));
  if (!langs.length) add('warn', 'langsMissing');
  langs.forEach((l) => { if (!LEVELS.includes(l.level)) add('error', 'level', { name: clean(l.name) }); });
  if (langs.length && !langs.some((l) => l.level === 'native')) add('warn', 'native');

  if (data.lang === 'de' && hasEszett(JSON.stringify({ ...data, photo: '' }))) add('warn', 'eszett');

  if (data.refMode === 'list' && (data.refs || []).some((r) => clean(r.name))) add('info', 'refsAsk');
  if (!data.photo) add('info', 'photo');
  const certs = work.filter((e) => e.cert && clean(e.org)).map((e) => clean(e.org));
  if (certs.length) add('info', 'certs', { list: certs });
  else if (work.length) add('info', 'certsNone');
  return out;
}

// ---------- Draft files ----------
const str = (v, max = 2000) => (typeof v === 'string' ? v.slice(0, max) : '');
export function emptyCv(lang = 'de') {
  return {
    v: 1, lang,
    person: { first: '', last: '', headline: '', street: '', city: '', phone: '', email: '', birth: '', nationality: '', permit: '', origin: '', civil: '', license: '' },
    photo: '', profile: '', work: [], edu: [], langs: [], it: '', interests: '', refMode: 'request', refs: [],
  };
}

// Normalise anything read from a draft file: unknown keys dropped, types forced, sizes capped.
export function sanitizeDraft(obj) {
  const o = obj && typeof obj === 'object' ? obj : {};
  const d = emptyCv(CV_LANGS.includes(o.lang) ? o.lang : 'de');
  const p = o.person && typeof o.person === 'object' ? o.person : {};
  for (const k of Object.keys(d.person)) d.person[k] = str(p[k], 300);
  if (!Object.prototype.hasOwnProperty.call(PERMITS, d.person.permit)) d.person.permit = '';
  d.photo = typeof o.photo === 'string' && /^data:image\/(png|jpeg|webp);base64,[A-Za-z0-9+/=]+$/.test(o.photo) && o.photo.length < 3_000_000 ? o.photo : '';
  d.profile = str(o.profile);
  d.it = str(o.it, 600);
  d.interests = str(o.interests, 600);
  d.refMode = o.refMode === 'list' ? 'list' : 'request';
  const arr = (a, n = 30) => (Array.isArray(a) ? a.slice(0, n).filter((x) => x && typeof x === 'object') : []);
  d.work = arr(o.work).map((e) => ({ from: str(e.from, 20), to: str(e.to, 20), current: e.current === true, role: str(e.role, 200), org: str(e.org, 200), place: str(e.place, 120), tasks: str(e.tasks), cert: e.cert === true }));
  d.edu = arr(o.edu).map((e) => ({ from: str(e.from, 20), to: str(e.to, 20), current: e.current === true, title: str(e.title, 200), school: str(e.school, 200), place: str(e.place, 120) }));
  d.langs = arr(o.langs).map((l) => ({ name: str(l.name, 60), level: LEVELS.includes(l.level) ? l.level : '' }));
  d.refs = arr(o.refs, 6).map((r) => ({ name: str(r.name, 120), role: str(r.role, 120), org: str(r.org, 120), phone: str(r.phone, 40) }));
  return d;
}
