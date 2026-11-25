// Swiss CV builder UI. Everything stays in this browser tab: no network, no cookies, no storage.
// The photo is read locally (FileReader + canvas) and never leaves the device.
import {
  PERMITS, LABELS, CV_LANGS, formatPeriod, parseSwissDate, formatSwissDate, sortAntichrono, sortLanguages,
  tasksToBullets, fixEszett, fileNameFor, validateCv, emptyCv, sanitizeDraft,
} from './cv.js';

const LANG = document.documentElement.lang.startsWith('fr') ? 'fr' : 'de';
const T = {
  de: {
    kind: { work: 'Berufserfahrung', edu: 'Ausbildung' },
    msg: {
      name: 'Vor- und Nachname fehlen.',
      contact: 'Geben Sie mindestens eine Telefonnummer oder eine E-Mail-Adresse an.',
      email: 'Die E-Mail-Adresse sieht nicht gültig aus.',
      address: 'Adresse unvollständig (Strasse und PLZ/Ort).',
      birthFormat: 'Geburtsdatum bitte als TT.MM.JJJJ eingeben, z. B. 21.04.1995.',
      birthAge: (p) => `Geburtsdatum prüfen: Das ergäbe ein Alter von ${p.age} Jahren.`,
      birthMissing: 'Das Geburtsdatum wird in der Schweiz meist erwartet.',
      nationality: 'Nationalität fehlt.',
      permit: 'Ohne Schweizer Pass: Bewilligung angeben (z. B. Ausweis B oder C).',
      empty: 'Fügen Sie mindestens eine Berufserfahrung oder eine Ausbildung hinzu.',
      fromMissing: (p) => `${p.kindName} ${p.n}: Beginn fehlt.`,
      toMissing: (p) => `${p.kindName} ${p.n}: Ende fehlt – oder «bis heute» ankreuzen.`,
      monthFormat: (p) => `${p.kindName} ${p.n}: «${p.value}» bitte als MM.JJJJ eingeben, z. B. 08.2021.`,
      endBeforeStart: (p) => `${p.kindName} ${p.n}: Das Ende liegt vor dem Beginn.`,
      future: (p) => `${p.kindName} ${p.n}: Der Beginn liegt in der Zukunft.`,
      workTitle: (p) => `Berufserfahrung ${p.n}: Funktion und Arbeitgeber angeben.`,
      tasks: (p) => `Berufserfahrung ${p.n}: Tätigkeiten stichwortartig ergänzen (eine pro Zeile).`,
      eduTitle: (p) => `Ausbildung ${p.n}: Abschluss und Schule angeben.`,
      gap: (p) => `Lücke von ${p.months} Monaten ab ${p.from}: kurz erklären (z. B. Reise, Familie, Stellensuche, Weiterbildung).`,
      langsMissing: 'Sprachen fehlen. Beginnen Sie mit Ihrer Muttersprache.',
      level: (p) => `${p.name}: Niveau wählen (Muttersprache oder A1 bis C2).`,
      native: 'Keine Muttersprache angegeben.',
      eszett: 'In der Schweiz schreibt man «ss» statt «ß».',
      refsAsk: 'Fragen Sie Ihre Referenzpersonen vorher um Erlaubnis.',
      photo: 'Foto: in der Schweiz üblich, aber freiwillig.',
      certs: (p) => `Legen Sie dem Dossier die Arbeitszeugnisse bei: ${p.list.join(', ')}.`,
      certsNone: 'Arbeitszeugnisse gehören in der Schweiz ins Bewerbungsdossier (als Beilage, nicht in den Lebenslauf).',
    },
    fixEszett: 'Alle «ß» ersetzen',
    allGood: 'Keine Fehler gefunden.',
    pages: (n) => `Vorschau: ${n} ${n === 1 ? 'Seite' : 'Seiten'} A4`,
    tooLong: 'Mehr als 2 Seiten: kürzen Sie ältere Stellen und Details.',
    page: (n) => `Seite ${n}`,
    photoBad: 'Bitte ein Bild im Format JPG, PNG oder WebP wählen.',
    draftBad: 'Diese Datei ist kein gültiger Entwurf.',
    confirmClear: 'Alle Eingaben löschen?',
    loaded: 'Entwurf geladen.',
    remove: 'Entfernen',
  },
  fr: {
    kind: { work: 'Expérience', edu: 'Formation' },
    msg: {
      name: 'Le prénom et le nom manquent.',
      contact: 'Indiquez au moins un numéro de téléphone ou une adresse e-mail.',
      email: 'L’adresse e-mail ne semble pas valable.',
      address: 'Adresse incomplète (rue et NPA/localité).',
      birthFormat: 'Saisissez la date de naissance au format JJ.MM.AAAA, p. ex. 21.04.1995.',
      birthAge: (p) => `Vérifiez la date de naissance : cela donnerait ${p.age} ans.`,
      birthMissing: 'La date de naissance est généralement attendue en Suisse.',
      nationality: 'La nationalité manque.',
      permit: 'Sans passeport suisse : indiquez votre permis (p. ex. permis B ou C).',
      empty: 'Ajoutez au moins une expérience ou une formation.',
      fromMissing: (p) => `${p.kindName} ${p.n} : le début manque.`,
      toMissing: (p) => `${p.kindName} ${p.n} : la fin manque – ou cochez « à ce jour ».`,
      monthFormat: (p) => `${p.kindName} ${p.n} : saisissez « ${p.value} » au format MM.AAAA, p. ex. 08.2021.`,
      endBeforeStart: (p) => `${p.kindName} ${p.n} : la fin précède le début.`,
      future: (p) => `${p.kindName} ${p.n} : le début est dans le futur.`,
      workTitle: (p) => `Expérience ${p.n} : indiquez la fonction et l’employeur.`,
      tasks: (p) => `Expérience ${p.n} : ajoutez les tâches en mots-clés (une par ligne).`,
      eduTitle: (p) => `Formation ${p.n} : indiquez le diplôme et l’école.`,
      gap: (p) => `Période vide de ${p.months} mois dès ${p.from} : expliquez-la brièvement (voyage, famille, recherche d’emploi, formation…).`,
      langsMissing: 'Les langues manquent. Commencez par votre langue maternelle.',
      level: (p) => `${p.name} : choisissez le niveau (langue maternelle ou A1 à C2).`,
      native: 'Aucune langue maternelle indiquée.',
      eszett: 'En Suisse alémanique, on écrit « ss » au lieu de « ß ».',
      refsAsk: 'Demandez d’abord l’accord de vos personnes de référence.',
      photo: 'Photo : courante en Suisse, mais facultative.',
      certs: (p) => `Joignez au dossier les certificats de travail : ${p.list.join(', ')}.`,
      certsNone: 'En Suisse, les certificats de travail font partie du dossier de candidature (en annexe, pas dans le CV).',
    },
    fixEszett: 'Remplacer tous les « ß »',
    allGood: 'Aucune erreur trouvée.',
    pages: (n) => `Aperçu : ${n} page${n === 1 ? '' : 's'} A4`,
    tooLong: 'Plus de 2 pages : raccourcissez les postes anciens et les détails.',
    page: (n) => `Page ${n}`,
    photoBad: 'Veuillez choisir une image JPG, PNG ou WebP.',
    draftBad: 'Ce fichier n’est pas un brouillon valable.',
    confirmClear: 'Effacer toutes les saisies ?',
    loaded: 'Brouillon chargé.',
    remove: 'Supprimer',
  },
}[LANG];

const EXAMPLE = {
  de: {
    v: 1, lang: 'de',
    person: { first: 'Laura', last: 'Beispiel', headline: 'Kauffrau EFZ', street: 'Musterweg 12', city: '3000 Bern', phone: '079 000 00 00', email: 'laura.beispiel@example.ch', birth: '14.05.1996', nationality: 'Italien', permit: 'C', origin: '', civil: '', license: 'Kat. B' },
    photo: '', profile: 'Kauffrau mit fünf Jahren Erfahrung in Administration und Kundendienst. Zuverlässig, genau und sicher im Umgang mit Kundinnen und Kunden auf Deutsch, Italienisch und Französisch.',
    work: [
      { from: '04.2022', to: '', current: true, role: 'Sachbearbeiterin Kundendienst', org: 'Beispiel Versicherungen AG', place: 'Bern', tasks: 'Bearbeitung von Kundenanfragen per Telefon und E-Mail\nErfassung und Kontrolle von Verträgen\nEinarbeitung von zwei neuen Mitarbeitenden', cert: true },
      { from: '08.2019', to: '03.2022', current: false, role: 'Kaufmännische Angestellte', org: 'Muster Treuhand GmbH', place: 'Thun', tasks: 'Debitoren- und Kreditorenbuchhaltung\nTerminplanung und Korrespondenz', cert: true },
    ],
    edu: [
      { from: '2023', to: '2024', current: false, title: 'Weiterbildung Sachbearbeiterin Personalwesen', school: 'Kaufmännische Berufsschule', place: 'Bern' },
      { from: '08.2016', to: '07.2019', current: false, title: 'Kauffrau EFZ, Profil E', school: 'Muster Treuhand GmbH und Berufsschule', place: 'Thun' },
    ],
    langs: [{ name: 'Italienisch', level: 'native' }, { name: 'Deutsch', level: 'C1' }, { name: 'Französisch', level: 'B2' }, { name: 'Englisch', level: 'B1' }],
    it: 'MS Office (sehr gut), Abacus, SAP (Grundkenntnisse)', interests: 'Volleyball im Verein, Kochen', refMode: 'request', refs: [],
  },
  fr: {
    v: 1, lang: 'fr',
    person: { first: 'Julie', last: 'Exemple', headline: 'Employée de commerce CFC', street: 'Chemin de l’Exemple 3', city: '1700 Fribourg', phone: '079 000 00 00', email: 'julie.exemple@example.ch', birth: '14.05.1996', nationality: 'Portugal', permit: 'C', origin: '', civil: '', license: 'Cat. B' },
    photo: '', profile: 'Employée de commerce avec cinq ans d’expérience en administration et service clientèle. Fiable, précise et à l’aise avec la clientèle en français, en portugais et en allemand.',
    work: [
      { from: '04.2022', to: '', current: true, role: 'Collaboratrice service clientèle', org: 'Exemple Assurances SA', place: 'Fribourg', tasks: 'Traitement des demandes de clients par téléphone et par e-mail\nSaisie et contrôle des contrats\nFormation de deux nouvelles collaboratrices', cert: true },
      { from: '08.2019', to: '03.2022', current: false, role: 'Employée de commerce', org: 'Fiduciaire Modèle Sàrl', place: 'Bulle', tasks: 'Comptabilité débiteurs et créanciers\nAgenda et correspondance', cert: true },
    ],
    edu: [
      { from: '2023', to: '2024', current: false, title: 'Assistante en ressources humaines', school: 'École professionnelle commerciale', place: 'Fribourg' },
      { from: '08.2016', to: '07.2019', current: false, title: 'CFC d’employée de commerce', school: 'Fiduciaire Modèle Sàrl et école professionnelle', place: 'Bulle' },
    ],
    langs: [{ name: 'Portugais', level: 'native' }, { name: 'Français', level: 'native' }, { name: 'Allemand', level: 'B2' }, { name: 'Anglais', level: 'B1' }],
    it: 'MS Office (très bon), Abacus, SAP (notions)', interests: 'Volleyball en club, cuisine', refMode: 'request', refs: [],
  },
}[LANG];

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

// Small DOM builder: text is always set with textContent (no HTML injection).
function h(tag, attrs = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === 'class') el.className = v;
    else el.setAttribute(k, v);
  }
  for (const kid of kids.flat(Infinity)) {
    if (kid === null || kid === undefined || kid === '') continue;
    el.append(kid instanceof Node ? kid : document.createTextNode(String(kid)));
  }
  return el;
}

function initCv(root) {
  document.body.classList.add('cv-print');
  const form = $('#cv-form', root);
  const sheet = $('#cv-sheet', root);
  const preview = $('.cv-preview', root);
  const checks = $('.cv-checks', root);
  const pagesOut = $('.cv-pages', root);
  const status = $('.cv-status', root);
  let photo = '';

  // ----- Repeatable lists -----
  function addRow(kind, values = {}) {
    const tpl = $(`#tpl-${kind}`);
    const frag = tpl.content.cloneNode(true);
    const row = frag.firstElementChild;
    const list = $(`[data-list="${kind}"]`, form);
    const n = list.children.length + 1;
    // Unique ids for label/input pairs.
    $$('[data-k]', row).forEach((input) => {
      const id = `${kind}-${n}-${input.dataset.k}-${Math.random().toString(36).slice(2, 7)}`;
      const label = $(`label[data-for="${input.dataset.k}"]`, row);
      input.id = id;
      if (label) label.htmlFor = id;
      const v = values[input.dataset.k];
      if (input.type === 'checkbox') input.checked = v === true;
      else if (v !== undefined) input.value = v;
    });
    $('[data-remove]', row).addEventListener('click', () => { row.remove(); renumber(kind); update(); });
    const cur = $('[data-k="current"]', row);
    const to = $('[data-k="to"]', row);
    if (cur && to) {
      const sync = () => { to.disabled = cur.checked; };
      cur.addEventListener('change', sync);
      sync();
    }
    list.append(row);
    renumber(kind);
    return row;
  }
  function renumber(kind) {
    $$(`[data-list="${kind}"] > *`, form).forEach((row, i) => {
      const num = $('.cv-num', row);
      if (num) num.textContent = String(i + 1);
    });
  }
  function readRows(kind) {
    return $$(`[data-list="${kind}"] > *`, form).map((row) => {
      const o = {};
      $$('[data-k]', row).forEach((input) => { o[input.dataset.k] = input.type === 'checkbox' ? input.checked : input.value; });
      return o;
    });
  }

  // ----- Read / write the whole form -----
  function read() {
    const d = emptyCv(form.cvlang.value);
    for (const k of Object.keys(d.person)) d.person[k] = form.elements[k] ? form.elements[k].value : '';
    d.photo = photo;
    d.profile = form.profile.value;
    d.work = readRows('work');
    d.edu = readRows('edu');
    d.langs = readRows('lang');
    d.it = form.it.value;
    d.interests = form.interests.value;
    d.refMode = form.refMode.value === 'list' ? 'list' : 'request';
    d.refs = readRows('ref');
    return d;
  }
  function write(d) {
    form.cvlang.value = d.lang;
    for (const [k, v] of Object.entries(d.person)) if (form.elements[k]) form.elements[k].value = v;
    form.profile.value = d.profile;
    form.it.value = d.it;
    form.interests.value = d.interests;
    form.refMode.value = d.refMode;
    for (const kind of ['work', 'edu', 'lang', 'ref']) $(`[data-list="${kind}"]`, form).replaceChildren();
    d.work.forEach((e) => addRow('work', e));
    d.edu.forEach((e) => addRow('edu', e));
    (d.langs.length ? d.langs : [{}]).forEach((e) => addRow('lang', e));
    d.refs.forEach((e) => addRow('ref', e));
    setPhoto(d.photo);
    syncRefs();
  }

  // ----- Photo (local only) -----
  function setPhoto(dataUrl) {
    photo = dataUrl || '';
    $('#cv-photo-remove', root).hidden = !photo;
    if (!photo) $('#cv-photo', root).value = '';
  }
  $('#cv-photo', root).addEventListener('change', (ev) => {
    const file = ev.target.files && ev.target.files[0];
    if (!file) return;
    if (!/^image\/(jpeg|png|webp)$/.test(file.type)) { status.textContent = T.photoBad; ev.target.value = ''; return; }
    const reader = new FileReader();
    reader.onload = () => {
      const img = new Image();
      img.onload = () => {
        // Crop to passport ratio 35:45 and shrink to keep drafts small.
        const ratio = 35 / 45;
        let sw = img.naturalWidth;
        let sh = img.naturalHeight;
        let sx = 0;
        let sy = 0;
        if (sw / sh > ratio) { sw = Math.round(sh * ratio); sx = Math.round((img.naturalWidth - sw) / 2); } else { sh = Math.round(sw / ratio); sy = Math.round((img.naturalHeight - sh) / 4); }
        const W = 420;
        const canvas = document.createElement('canvas');
        canvas.width = W;
        canvas.height = Math.round(W / ratio);
        canvas.getContext('2d').drawImage(img, sx, sy, sw, sh, 0, 0, canvas.width, canvas.height);
        setPhoto(canvas.toDataURL('image/jpeg', 0.88));
        update();
      };
      img.onerror = () => { status.textContent = T.photoBad; };
      img.src = reader.result;
    };
    reader.readAsDataURL(file);
  });
  $('#cv-photo-remove', root).addEventListener('click', () => { setPhoto(''); update(); });

  // ----- References: only show list when chosen -----
  function syncRefs() {
    const list = form.refMode.value === 'list';
    $('.cv-refs-list', form).hidden = !list;
    if (list && !$('[data-list="ref"]', form).children.length) addRow('ref');
  }
  $$('input[name="refMode"]', form).forEach((r) => r.addEventListener('change', () => { syncRefs(); update(); }));

  // ----- Preview -----
  function render(d) {
    const L = LABELS[d.lang];
    const p = d.person;
    const birth = parseSwissDate(p.birth);
    const rows = [
      [L.address, [p.street.trim(), p.city.trim()].filter(Boolean)],
      [L.phone, p.phone], [L.email, p.email],
      [L.birth, birth ? formatSwissDate(birth) : p.birth], [L.nationality, p.nationality],
      [L.permit, p.permit && PERMITS[p.permit] ? PERMITS[p.permit][d.lang] : ''],
      [L.origin, p.origin], [L.civil, p.civil], [L.license, p.license],
    ].filter(([, v]) => (Array.isArray(v) ? v.length : String(v || '').trim()));
    const dl = (pairs) => h('dl', { class: 'cv-dl' }, pairs.map(([k, v]) => [h('dt', {}, k), h('dd', {}, Array.isArray(v) ? v.flatMap((x, i) => (i ? [h('br'), x] : [x])) : v)]));
    const sec = (title, ...body) => h('section', { class: 'cv-sec' }, h('h3', {}, title), ...body);
    const entry = (when, ...what) => h('div', { class: 'cv-entry' }, h('div', { class: 'cv-when' }, when), h('div', { class: 'cv-what' }, ...what));

    const out = [];
    const name = `${p.first} ${p.last}`.trim();
    out.push(h('header', { class: 'cv-head' },
      h('div', {}, h('p', { class: 'cv-doc' }, L.title), h('p', { class: 'cv-name' }, name || ' '), p.headline.trim() ? h('p', { class: 'cv-headline' }, p.headline) : null),
      d.photo ? h('img', { class: 'cv-photo', src: d.photo, alt: '' }) : null));
    if (rows.length) out.push(sec(L.personal, dl(rows)));
    if (d.profile.trim()) out.push(sec(L.profile, h('p', {}, d.profile.trim())));
    const work = sortAntichrono(d.work.filter((e) => e.role.trim() || e.org.trim()));
    if (work.length) {
      out.push(sec(L.work, work.map((e) => {
        const bullets = tasksToBullets(e.tasks);
        return entry(formatPeriod(e, d.lang), h('p', { class: 'cv-role' }, e.role),
          h('p', {}, [e.org, e.place].map((x) => x.trim()).filter(Boolean).join(', ')),
          bullets.length ? h('ul', {}, bullets.map((b) => h('li', {}, b))) : null);
      })));
    }
    const edu = sortAntichrono(d.edu.filter((e) => e.title.trim() || e.school.trim()));
    if (edu.length) {
      out.push(sec(L.edu, edu.map((e) => entry(formatPeriod(e, d.lang), h('p', { class: 'cv-role' }, e.title),
        h('p', {}, [e.school, e.place].map((x) => x.trim()).filter(Boolean).join(', '))))));
    }
    const langs = sortLanguages(d.langs.filter((l) => l.name.trim()));
    if (langs.length) out.push(sec(L.langs, dl(langs.map((l) => [l.name, l.level === 'native' ? L.native : l.level || '']))));
    const more = [[L.it, d.it.trim()], [L.interests, d.interests.trim()]].filter(([, v]) => v);
    if (more.length) out.push(h('section', { class: 'cv-sec' }, dl(more)));
    if (d.refMode === 'list') {
      const refs = d.refs.filter((r) => r.name.trim());
      if (refs.length) {
        out.push(sec(L.refs, refs.map((r) => h('p', { class: 'cv-ref' }, h('strong', {}, r.name), [r.role, r.org].map((x) => x.trim()).filter(Boolean).length ? `, ${[r.role, r.org].map((x) => x.trim()).filter(Boolean).join(', ')}` : '', r.phone.trim() ? ` · ${r.phone.trim()}` : ''))));
      }
    } else out.push(sec(L.refs, h('p', {}, L.onRequest)));
    sheet.replaceChildren(...out);
    sheet.lang = { de: 'de-CH', fr: 'fr-CH', it: 'it-CH', en: 'en' }[d.lang];
  }

  // Page count and page-break guides (screen only), plus scaling to fit narrow screens.
  function layout() {
    sheet.style.transform = '';
    $$('.cv-break', sheet).forEach((x) => x.remove());
    const pxPerMm = sheet.offsetWidth / 210;
    const usable = 269 * pxPerMm;
    const contentH = Math.max(0, sheet.scrollHeight - 28 * pxPerMm);
    const pages = Math.max(1, Math.ceil(contentH / usable - 0.01));
    for (let i = 1; i < pages; i++) {
      sheet.append(h('div', { class: 'cv-break', style: `top:${(14 + 269 * i).toFixed(1)}mm`, 'aria-hidden': 'true' }, T.page(i + 1)));
    }
    pagesOut.textContent = T.pages(pages);
    pagesOut.classList.toggle('warn', pages > 2);
    if (pages > 2) pagesOut.textContent += ` – ${T.tooLong}`;
    const scale = Math.min(1, preview.clientWidth / sheet.offsetWidth);
    sheet.style.transform = scale < 1 ? `scale(${scale})` : '';
    preview.style.height = `${Math.ceil(sheet.offsetHeight * scale)}px`;
    return pages;
  }

  function showChecks(d) {
    const today = new Date();
    const list = validateCv(d, { y: today.getFullYear(), m: today.getMonth() + 1, d: today.getDate() });
    const items = list.map((c) => {
      const m = T.msg[c.code];
      const text = typeof m === 'function' ? m({ ...c, kindName: c.kind ? T.kind[c.kind] : '' }) : m;
      const li = h('li', { class: `flag ${c.level === 'error' ? 'err' : c.level === 'warn' ? 'warn' : 'info'}` }, text);
      if (c.code === 'eszett') {
        const b = h('button', { type: 'button', class: 'link-btn cv-inline' }, T.fixEszett);
        b.addEventListener('click', () => {
          $$('input[type=text], input:not([type]), textarea', form).forEach((el) => { el.value = fixEszett(el.value); });
          update();
        });
        li.append(' ', b);
      }
      return li;
    });
    if (!list.some((c) => c.level !== 'info')) items.unshift(h('li', { class: 'flag ok' }, T.allGood));
    checks.replaceChildren(...items);
  }

  let raf = 0;
  function update() {
    cancelAnimationFrame(raf);
    raf = requestAnimationFrame(() => {
      const d = read();
      render(d);
      layout();
      showChecks(d);
    });
  }

  // ----- Toolbar -----
  $('[data-act="add-work"]', root).addEventListener('click', () => { $('input', addRow('work')).focus(); update(); });
  $('[data-act="add-edu"]', root).addEventListener('click', () => { $('input', addRow('edu')).focus(); update(); });
  $('[data-act="add-lang"]', root).addEventListener('click', () => { $('input', addRow('lang')).focus(); update(); });
  $('[data-act="add-ref"]', root).addEventListener('click', () => { $('input', addRow('ref')).focus(); update(); });
  $('[data-act="example"]', root).addEventListener('click', () => { write(sanitizeDraft({ ...EXAMPLE, lang: form.cvlang.value })); update(); });
  $('[data-act="clear"]', root).addEventListener('click', () => {
    if (!window.confirm(T.confirmClear)) return;
    write(emptyCv(form.cvlang.value));
    update();
  });
  $('[data-act="print"]', root).addEventListener('click', () => {
    const d = read();
    const old = document.title;
    // Browsers use the page title as the default PDF file name.
    document.title = fileNameFor(d) || old;
    const restore = () => { document.title = old; window.removeEventListener('afterprint', restore); };
    window.addEventListener('afterprint', restore);
    sheet.style.transform = '';
    window.print();
    setTimeout(() => { restore(); layout(); }, 1000);
  });
  $('[data-act="save"]', root).addEventListener('click', () => {
    const d = read();
    const blob = new Blob([JSON.stringify(d, null, 1)], { type: 'application/json' });
    const a = h('a', { href: URL.createObjectURL(blob), download: `${fileNameFor(d) || 'cv'}.json` });
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  });
  $('#cv-open', root).addEventListener('change', (ev) => {
    const file = ev.target.files && ev.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        write(sanitizeDraft(JSON.parse(reader.result)));
        status.textContent = T.loaded;
        update();
      } catch {
        status.textContent = T.draftBad;
      }
      ev.target.value = '';
    };
    reader.readAsText(file);
  });

  form.addEventListener('input', update);
  form.addEventListener('change', update);
  form.addEventListener('submit', (e) => { e.preventDefault(); update(); });
  window.addEventListener('resize', () => layout());
  if (!CV_LANGS.includes(form.cvlang.value)) form.cvlang.value = LANG;
  write(emptyCv(form.cvlang.value));
  update();
}

const tool = document.querySelector('[data-tool="cv"]');
if (tool) initCv(tool);
