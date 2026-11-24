#!/usr/bin/env python3
"""One-off generator for /home/claude/rechner-site static pages. Not part of the site."""
import html, json, re, pathlib

ROOT = pathlib.Path('/home/claude/rechner-site')
BASE = 'https://schweizer-rechner.ch'
STAND = {'de': 'Stand: November 2026', 'fr': 'État : novembre 2026'}
SITE = {'de': 'Schweizer Rechner', 'fr': 'Calculateurs suisses'}
LOCALE = {'de': 'de_CH', 'fr': 'fr_CH'}

SRC = {
    'arg_de': 'https://www.fedlex.admin.ch/eli/cc/1966/57_57_57/de',
    'arg_fr': 'https://www.fedlex.admin.ch/eli/cc/1966/57_57_57/fr',
    'estv_de': 'https://www.estv.admin.ch/estv/de/home/mehrwertsteuer/mwst-steuersaetze.html',
    'estv_fr': 'https://www.estv.admin.ch/fr/taux-de-la-tva-suisse',
}

# Pairs of twin pages: key -> (de path, fr path)
PAIRS = {
    'home': ('/de/', '/fr/'),
    'work': ('/de/arbeitszeitrechner/', '/fr/calcul-heures-travail/'),
    'pct': ('/de/prozentrechner/', '/fr/calcul-pourcentage/'),
    'vat': ('/de/mwst-rechner/', '/fr/calcul-tva-suisse/'),
    'iban': ('/de/iban-pruefen/', '/fr/verifier-iban/'),
    'salary': ('/de/stundenlohn-rechner/', '/fr/calcul-salaire-horaire/'),
    'days': ('/de/tage-zwischen-zwei-daten/', '/fr/calcul-jours-entre-deux-dates/'),
    'imp': ('/de/impressum/', '/fr/mentions-legales/'),
    'priv': ('/de/datenschutz/', '/fr/confidentialite/'),
    'contact': ('/de/kontakt/', '/fr/contact/'),
}

LOGO = ('<svg width="26" height="26" viewBox="0 0 32 32" aria-hidden="true">'
        '<rect width="32" height="32" rx="7" fill="#c8102e"/>'
        '<path d="M13 7h6v6h6v6h-6v6h-6v-6H7v-6h6z" fill="#fff"/></svg>')
FAVICON_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
               '<rect width="32" height="32" rx="7" fill="#c8102e"/>'
               '<path d="M13 7h6v6h6v6h-6v6h-6v-6H7v-6h6z" fill="#fff"/></svg>')
FAVICON_URI = 'data:image/svg+xml,' + FAVICON_SVG.replace('"', "'").replace('#', '%23').replace('<', '%3C').replace('>', '%3E')

AD1 = ('<!-- AD SLOT 1 (below the result): reserved for a future advertising unit. '
       'Empty on purpose - no ad code. Add only after the consent banner exists. -->\n'
       '<div class="ad-slot"></div>')
AD2 = ('<!-- AD SLOT 2 (bottom of page): reserved for a future advertising unit. '
       'Empty on purpose - no ad code. -->\n<div class="ad-slot"></div>')

FOOT = {
    'de': [('/de/impressum/', 'Impressum'), ('/de/datenschutz/', 'Datenschutz'), ('/de/kontakt/', 'Kontakt')],
    'fr': [('/fr/mentions-legales/', 'Mentions légales'), ('/fr/confidentialite/', 'Confidentialité'), ('/fr/contact/', 'Contact')],
}
TOOLS = {
    'de': [('/de/arbeitszeitrechner/', 'Arbeitszeitrechner', 'Arbeitsstunden pro Tag und Woche, Pausen nach Arbeitsgesetz, Nachtschichten.'),
           ('/de/prozentrechner/', 'Prozentrechner', 'Prozent von, Anteil in Prozent, Veränderung, Wert plus oder minus Prozent.'),
           ('/de/mwst-rechner/', 'MWST-Rechner', 'Mehrwertsteuer hinzufügen oder herausrechnen, mit Rappenrundung.'),
           ('/de/stundenlohn-rechner/', 'Stundenlohn-Rechner', 'Monatslohn in Stundenlohn umrechnen und umgekehrt, mit 12 oder 13 Löhnen.'),
           ('/de/tage-zwischen-zwei-daten/', 'Tage zwischen zwei Daten', 'Kalendertage, Arbeitstage Montag bis Freitag und Wochen.'),
           ('/de/iban-pruefen/', 'IBAN prüfen', 'Länge und Prüfziffer einer IBAN offline prüfen, QR-IBAN erkennen.')],
    'fr': [('/fr/calcul-heures-travail/', 'Calcul des heures de travail', 'Heures par jour et par semaine, pauses selon la loi sur le travail, horaires de nuit.'),
           ('/fr/calcul-pourcentage/', 'Calcul de pourcentage', 'Pourcentage d’un montant, part en %, variation, montant plus ou moins %.'),
           ('/fr/calcul-tva-suisse/', 'Calcul de la TVA suisse', 'Ajouter ou extraire la TVA, avec arrondi à 5 centimes.'),
           ('/fr/calcul-salaire-horaire/', 'Calcul du salaire horaire', 'Salaire mensuel en salaire horaire et inversement, avec 12 ou 13 salaires.'),
           ('/fr/calcul-jours-entre-deux-dates/', 'Jours entre deux dates', 'Jours calendaires, jours ouvrés du lundi au vendredi et semaines.'),
           ('/fr/verifier-iban/', 'Vérifier une IBAN', 'Longueur et clé de contrôle d’une IBAN hors ligne, détection de la QR-IBAN.')],
}

ALL_PAGES = []  # (path, html_text)


def strip_tags(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', s))).strip()


def faq_html(faq, lang):
    h = 'Häufige Fragen' if lang == 'de' else 'Questions fréquentes'
    items = '\n'.join(f'<details><summary>{q}</summary><p>{a}</p></details>' for q, a in faq)
    return f'<section class="faq" aria-labelledby="faq-h"><h2 id="faq-h">{h}</h2>\n{items}\n</section>'


def jsonld_tool(lang, url, name, desc, faq, category):
    graph = [
        {'@type': 'WebApplication', 'name': name, 'url': url, 'description': desc,
         'inLanguage': 'de-CH' if lang == 'de' else 'fr-CH', 'applicationCategory': category,
         'operatingSystem': 'Any', 'browserRequirements': 'Requires JavaScript',
         'isAccessibleForFree': True,
         'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'CHF'}},
        {'@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': strip_tags(q),
             'acceptedAnswer': {'@type': 'Answer', 'text': strip_tags(a)}} for q, a in faq]},
    ]
    return {'@context': 'https://schema.org', '@graph': graph}


def page(key, lang, title, desc, body, jsonld=None, script=False, crumbs=None):
    de_path, fr_path = PAIRS[key]
    path = de_path if lang == 'de' else fr_path
    twin = fr_path if lang == 'de' else de_path
    url = BASE + path
    assert len(title) <= 60, (path, len(title), title)
    assert len(desc) <= 155, (path, len(desc), desc)
    other = 'fr' if lang == 'de' else 'de'
    lang_nav = (f'<nav class="lang" aria-label="{"Sprache" if lang == "de" else "Langue"}">'
                + (f'<span aria-current="page" lang="de-CH">DE</span><a href="{twin}" hreflang="fr-CH" lang="fr-CH">FR</a>'
                   if lang == 'de' else
                   f'<a href="{twin}" hreflang="de-CH" lang="de-CH">DE</a><span aria-current="page" lang="fr-CH">FR</span>')
                + '</nav>')
    ld = (f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False, separators=(",", ":"))}</script>\n'
          if jsonld else '')
    js = '<script type="module" src="/js/ui.js"></script>\n' if script else ''
    foot = ' · '.join(f'<a href="{h}">{t}</a>' for h, t in FOOT[lang])
    crumb_html = ''
    if crumbs:
        crumb_html = (f'<p class="crumbs"><a href="/{lang}/">{SITE[lang]}</a> › {crumbs}</p>\n')
    doc = f'''<!DOCTYPE html>
<html lang="{'de-CH' if lang == 'de' else 'fr-CH'}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title, quote=False)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="de-CH" href="{BASE}{de_path}">
<link rel="alternate" hreflang="fr-CH" href="{BASE}{fr_path}">
<link rel="alternate" hreflang="x-default" href="{BASE}{de_path}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE[lang]}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:locale" content="{LOCALE[lang]}">
<meta property="og:locale:alternate" content="{LOCALE[other]}">
<meta name="theme-color" content="#c8102e">
<link rel="icon" type="image/svg+xml" href="{FAVICON_URI}">
<link rel="stylesheet" href="/style.css">
{ld}{js}</head>
<body>
<a class="skip" href="#main">{"Zum Inhalt springen" if lang == "de" else "Aller au contenu"}</a>
<header class="site-header"><div class="wrap">
<a class="brand" href="/{lang}/">{LOGO}<span>{SITE[lang]}</span></a>
{lang_nav}
</div></header>
<main id="main" class="wrap">
{crumb_html}{body}
</main>
<footer class="site-footer"><div class="wrap">
<nav aria-label="{"Rechtliches" if lang == "de" else "Informations légales"}">{foot}</nav>
<p>{"Alle Berechnungen laufen nur in Ihrem Browser. Angaben ohne Gewähr." if lang == "de" else "Tous les calculs se font uniquement dans votre navigateur. Informations sans garantie."}</p>
</div></footer>
</body>
</html>
'''
    ALL_PAGES.append((path, doc, lang, key))
    return doc


def other_tools(lang, exclude):
    h = 'Weitere Rechner' if lang == 'de' else 'Autres calculateurs'
    items = ''.join(f'<li><a href="{u}"><strong>{n}</strong>{d}</a></li>' for u, n, d in TOOLS[lang] if u != exclude)
    return f'<h2>{h}</h2>\n<ul class="cards">{items}</ul>'


def tool_page(key, lang, title, desc, h1, lead, tool_html, article, faq, sources, category):
    path = PAIRS[key][0 if lang == 'de' else 1]
    src_h = 'Quellen' if lang == 'de' else 'Sources'
    src = ''
    if sources:
        src = (f'<section class="sources" aria-labelledby="src-h"><h2 id="src-h">{src_h}</h2><ul>'
               + ''.join(f'<li>{s}</li>' for s in sources) + '</ul></section>\n')
    body = f'''<h1>{h1}</h1>
<p class="lead">{lead}</p>
{tool_html}
{AD1}
<article>
{article}
{faq_html(faq, lang)}
</article>
{src}<p class="stand">{STAND[lang]}</p>
{AD2}
{other_tools(lang, path)}'''
    page(key, lang, title, desc, body, jsonld_tool(lang, BASE + path, h1, desc, faq, category),
         script=True, crumbs=h1)
    words = len(strip_tags(article + ' ' + ' '.join(q + ' ' + a for q, a in faq)).split())
    return words


WORDCOUNT = {}

# =====================================================================
# 1. Working time
# =====================================================================
WORK_TOOL = {
    'de': '''<section class="tool" data-tool="work" aria-labelledby="tool-h">
<h2 id="tool-h">Arbeitszeit berechnen</h2>
<table class="days">
<thead><tr><th scope="col">Tag</th><th scope="col">Beginn</th><th scope="col">Ende</th><th scope="col">Pause (Min.)</th><th scope="col">Arbeitszeit</th><th scope="col"><span class="sr-only">Aktion</span></th></tr></thead>
<tbody></tbody>
</table>
<p><button type="button" class="btn add-day">+ Tag hinzufügen (max. 7)</button></p>
<div class="result" aria-live="polite"></div>
<noscript><p>Für den Rechner wird JavaScript benötigt.</p></noscript>
</section>''',
    'fr': '''<section class="tool" data-tool="work" aria-labelledby="tool-h">
<h2 id="tool-h">Calculer le temps de travail</h2>
<table class="days">
<thead><tr><th scope="col">Jour</th><th scope="col">Début</th><th scope="col">Fin</th><th scope="col">Pause (min)</th><th scope="col">Temps de travail</th><th scope="col"><span class="sr-only">Action</span></th></tr></thead>
<tbody></tbody>
</table>
<p><button type="button" class="btn add-day">+ Ajouter un jour (max. 7)</button></p>
<div class="result" aria-live="polite"></div>
<noscript><p>Le calculateur nécessite JavaScript.</p></noscript>
</section>''',
}

WORK_ART_DE = '''<h2>So funktioniert der Rechner</h2>
<p>Geben Sie für jeden Arbeitstag Beginn, Ende und die Pause in Minuten ein. Mit «Tag hinzufügen» erfassen Sie bis zu sieben Tage, also eine ganze Woche. Der Rechner zeigt die Arbeitszeit pro Tag im Format Stunden:Minuten und als Dezimalzahl, darunter das Wochentotal. Liegt das Ende vor dem Beginn, rechnet er mit einer Schicht über Mitternacht, etwa von 22:00 bis 06:30.</p>
<h2>Formel</h2>
<p class="formula">Arbeitszeit = Ende − Beginn − Pause</p>
<p>Bei einer Nachtschicht werden 24 Stunden zum Ende addiert. Für Dezimalstunden teilen Sie die Minuten durch 60: 45 Minuten sind 0.75 Stunden. Dezimalstunden brauchen Sie, wenn Sie Stunden mit einem Stundenlohn multiplizieren oder in eine Tabelle übertragen.</p>
<h2>Beispiel</h2>
<p>Sie arbeiten von 07:30 bis 17:00 und machen 45 Minuten Mittagspause. Die Anwesenheit beträgt 9:30 Stunden, die Arbeitszeit 8:45 Stunden oder 8.75 Stunden. An fünf solchen Tagen kommen Sie auf 43:45 Stunden. Bei einem Stundenlohn von CHF 32.50 ergibt das 43.75 × 32.50 = CHF 1'421.88 brutto pro Woche.</p>
<h2>Pausen und Höchstarbeitszeit nach Arbeitsgesetz</h2>
<p>Das Arbeitsgesetz (ArG) verlangt in Art. 15 Mindestpausen: eine Viertelstunde bei einer täglichen Arbeitszeit von mehr als fünfeinhalb Stunden, eine halbe Stunde bei mehr als sieben Stunden und eine Stunde bei mehr als neun Stunden. Der Rechner vergleicht Ihre Pause mit diesem Minimum und markiert zu kurze Pausen.</p>
<p>Die wöchentliche Höchstarbeitszeit beträgt nach Art. 9 ArG 45 Stunden für Arbeitnehmende in industriellen Betrieben, für Büropersonal, technische und andere Angestellte sowie für das Verkaufspersonal in Grossbetrieben des Detailhandels, und 50 Stunden für alle übrigen Arbeitnehmenden. Die Hinweise sind eine Information, keine Rechtsberatung: Für manche Branchen und Betriebe gelten Sonderregeln, und Ihr Arbeitsvertrag oder ein Gesamtarbeitsvertrag kann engere Grenzen vorsehen.</p>'''

WORK_FAQ_DE = [
    ('Wie rechne ich Minuten in Dezimalstunden um?',
     'Teilen Sie die Minuten durch 60. 15 Minuten sind 0.25 Stunden, 30 Minuten 0.5 und 45 Minuten 0.75. Aus 7:20 Stunden werden so 7.33 Stunden.'),
    ('Funktioniert der Rechner auch für Nachtschichten?',
     'Ja. Ist das Ende früher als der Beginn, rechnet er über Mitternacht. 22:00 bis 06:30 mit 30 Minuten Pause ergibt 8:00 Stunden Arbeitszeit.'),
    ('Zählt die Pause zur Arbeitszeit?',
     'In der Regel nicht. Nach Art. 15 Abs. 2 ArG gelten Pausen aber als Arbeitszeit, wenn Sie den Arbeitsplatz nicht verlassen dürfen.'),
    ('Welche Pause gilt bei genau 7 Stunden Arbeit?',
     'Das Gesetz spricht von «mehr als» sieben Stunden. Bei genau 7:00 Stunden genügt eine Viertelstunde, ab 7:01 Stunden ist eine halbe Stunde nötig.'),
    ('Werden meine Eingaben gespeichert?',
     'Nein. Die Berechnung läuft nur in Ihrem Browser. Es wird nichts übermittelt und nichts gespeichert.'),
]

WORK_ART_FR = '''<h2>Mode d’emploi</h2>
<p>Pour chaque jour de travail, saisissez l’heure de début, l’heure de fin et la pause en minutes. Avec «Ajouter un jour», vous pouvez saisir jusqu’à sept jours. Le calculateur affiche le temps de travail de chaque jour en heures:minutes et en heures décimales, puis le total de la semaine. Si l’heure de fin précède l’heure de début, il considère que le service passe minuit, par exemple de 22:00 à 06:30.</p>
<h2>Formule</h2>
<p class="formula">Temps de travail = fin − début − pause</p>
<p>Pour un horaire de nuit, on ajoute 24 heures à l’heure de fin. Pour obtenir des heures décimales, divisez les minutes par 60 : 45 minutes valent 0,75 heure.</p>
<h2>Exemple</h2>
<p>Vous travaillez de 07:30 à 17:00 avec 45 minutes de pause de midi. La présence est de 9:30 heures, le temps de travail de 8:45 heures, soit 8,75 heures. Sur cinq jours identiques, vous totalisez 43:45 heures. Avec un salaire horaire de CHF 32.50, cela donne 43,75 × 32.50 = CHF 1'421.88 brut par semaine.</p>
<h2>Pauses et durée maximale selon la loi sur le travail</h2>
<p>La loi sur le travail (LTr) prévoit à l’art. 15 des pauses minimales : un quart d’heure si la journée de travail dure plus de cinq heures et demie, une demi-heure si elle dure plus de sept heures et une heure si elle dure plus de neuf heures. Le calculateur compare votre pause à ce minimum et signale une pause trop courte.</p>
<p>Selon l’art. 9 LTr, la durée maximale de la semaine de travail est de 45 heures pour les travailleurs des entreprises industrielles, le personnel de bureau, le personnel technique et les autres employés, y compris le personnel de vente des grandes entreprises de commerce de détail, et de 50 heures pour tous les autres travailleurs. Ces indications sont informatives et ne constituent pas un conseil juridique : certaines branches et entreprises ont des règles spéciales, et votre contrat ou une convention collective de travail peut fixer des limites plus basses.</p>'''

WORK_FAQ_FR = [
    ('Comment convertir des minutes en heures décimales ?',
     'Divisez les minutes par 60. 15 minutes valent 0,25 heure, 30 minutes 0,5 et 45 minutes 0,75. Ainsi, 7:20 heures deviennent 7,33 heures.'),
    ('Le calculateur fonctionne-t-il pour le travail de nuit ?',
     'Oui. Si l’heure de fin est plus tôt que l’heure de début, il calcule après minuit. De 22:00 à 06:30 avec 30 minutes de pause, cela fait 8:00 heures de travail.'),
    ('La pause compte-t-elle comme temps de travail ?',
     'En général non. Selon l’art. 15, al. 2 LTr, les pauses comptent toutefois comme temps de travail lorsque vous n’êtes pas autorisé à quitter votre place de travail.'),
    ('Quelle pause pour exactement 7 heures de travail ?',
     'La loi parle de «plus de» sept heures. Pour exactement 7:00 heures, un quart d’heure suffit ; dès 7:01 heures, une demi-heure est nécessaire.'),
    ('Mes données sont-elles enregistrées ?',
     'Non. Le calcul se fait uniquement dans votre navigateur. Rien n’est transmis ni enregistré.'),
]

WORKSRC = {
    'de': [f'Bundesgesetz über die Arbeit in Industrie, Gewerbe und Handel (Arbeitsgesetz, ArG), SR 822.11, Art. 9 und Art. 15: <a href="{SRC["arg_de"]}#art_9">{SRC["arg_de"]}</a>'],
    'fr': [f'Loi fédérale sur le travail dans l’industrie, l’artisanat et le commerce (loi sur le travail, LTr), RS 822.11, art. 9 et art. 15 : <a href="{SRC["arg_fr"]}#art_9">{SRC["arg_fr"]}</a>'],
}

WORDCOUNT['work_de'] = tool_page(
    'work', 'de', 'Arbeitszeitrechner Schweiz: Stunden, Pausen, Woche',
    'Arbeitszeit pro Tag und Woche berechnen, in h:mm und Dezimalstunden. Mit Pausen nach Art. 15 ArG und Nachtschichten über Mitternacht.',
    'Arbeitszeitrechner Schweiz',
    'Netto-Arbeitszeit aus Beginn, Ende und Pause berechnen – für einen Tag oder bis zu sieben Tage, auch über Mitternacht.',
    WORK_TOOL['de'], WORK_ART_DE, WORK_FAQ_DE, WORKSRC['de'], 'BusinessApplication')
WORDCOUNT['work_fr'] = tool_page(
    'work', 'fr', 'Calcul des heures de travail en Suisse',
    'Calculez vos heures de travail par jour et par semaine, en h:mm et en heures décimales, avec les pauses de l’art. 15 LTr et le travail de nuit.',
    'Calcul des heures de travail (Suisse)',
    'Temps de travail net à partir du début, de la fin et de la pause – pour un jour ou jusqu’à sept jours, même après minuit.',
    WORK_TOOL['fr'], WORK_ART_FR, WORK_FAQ_FR, WORKSRC['fr'], 'BusinessApplication')

# =====================================================================
# 2. Percent
# =====================================================================
def pct_tool(lang):
    if lang == 'de':
        L = dict(h='Prozent berechnen', of_h='1. X % von Y', p='Prozent (%)', base='Grundwert',
                 what_h='2. X ist wie viel % von Y?', part='Wert X', whole='Grundwert Y',
                 ch_h='3. Prozentuale Veränderung von A zu B', a='Alter Wert A', b='Neuer Wert B',
                 ap_h='4. Wert plus oder minus X %', v='Wert', plus='plus', minus='minus', op='Rechenart',
                 btn='Berechnen')
    else:
        L = dict(h='Calculer un pourcentage', of_h='1. X % de Y', p='Pourcentage (%)', base='Valeur de base',
                 what_h='2. X représente quel % de Y ?', part='Valeur X', whole='Valeur de base Y',
                 ch_h='3. Variation en % de A à B', a='Ancienne valeur A', b='Nouvelle valeur B',
                 ap_h='4. Valeur plus ou moins X %', v='Valeur', plus='plus', minus='moins', op='Opération',
                 btn='Calculer')
    def f(mode, title, la, lb, extra=''):
        return f'''<form data-mode="{mode}" aria-labelledby="h-{mode}" novalidate>
<h3 id="h-{mode}">{title}</h3>
<div class="row">
<div class="field"><label for="{mode}-a">{la}</label><input type="text" inputmode="decimal" id="{mode}-a" name="a" autocomplete="off"></div>
{extra}<div class="field"><label for="{mode}-b">{lb}</label><input type="text" inputmode="decimal" id="{mode}-b" name="b" autocomplete="off"></div>
</div>
<button type="submit" class="btn">{L['btn']}</button>
<div class="result" aria-live="polite"></div>
</form>'''
    sign = (f'<div class="field"><label for="apply-sign">{L["op"]}</label><select id="apply-sign" name="sign">'
            f'<option value="+">{L["plus"]}</option><option value="-">{L["minus"]}</option></select></div>\n')
    return (f'<section class="tool" data-tool="percent" aria-labelledby="tool-h">\n<h2 id="tool-h">{L["h"]}</h2>\n<div class="subtools">\n'
            + f('of', L['of_h'], L['p'], L['base']) + '\n'
            + f('what', L['what_h'], L['part'], L['whole']) + '\n'
            + f('change', L['ch_h'], L['a'], L['b']) + '\n'
            + f('apply', L['ap_h'], L['v'], L['p'], sign)
            + '\n</div>\n</section>')

PCT_ART_DE = '''<h2>So funktioniert der Rechner</h2>
<p>Wählen Sie den Block, der zu Ihrer Frage passt, und füllen Sie die zwei Felder aus. Das Ergebnis erscheint sofort. Dezimalstellen dürfen Sie mit Punkt oder Komma eingeben, Tausender auch mit Apostroph, etwa 1'250.50.</p>
<h2>Die vier Formeln</h2>
<p class="formula">1. X % von Y = Y × X ÷ 100<br>2. Anteil in % = X ÷ Y × 100<br>3. Veränderung in % = (B − A) ÷ A × 100<br>4. Y ± X % = Y × (1 ± X ÷ 100)</p>
<h2>Beispiele mit Franken</h2>
<p>Ein Velo kostet CHF 240 und ist 15 % reduziert: 240 × 15 ÷ 100 = CHF 36 Rabatt, Sie zahlen CHF 204. Von einem Budget von CHF 180 haben Sie CHF 45 ausgegeben: 45 ÷ 180 × 100 = 25 %. Ihre Krankenkassenprämie steigt von CHF 80 auf CHF 92: (92 − 80) ÷ 80 × 100 = +15 %. Ein Gerät für CHF 1'200 mit 20 % Rabatt kostet 1'200 × 0.8 = CHF 960.</p>
<h2>Typische Fehler</h2>
<p>Prozente beziehen sich immer auf einen Grundwert. Wer zuerst 10 % aufschlägt und danach 10 % abzieht, landet nicht beim Ausgangswert: CHF 100 werden zu CHF 110 und dann zu CHF 99, weil der Abzug vom höheren Betrag berechnet wird. Ebenso wichtig ist der Unterschied zwischen Prozent und Prozentpunkten: Steigt ein Zinssatz von 1.5 % auf 2 %, sind das 0.5 Prozentpunkte, aber eine Zunahme von rund 33 %.</p>'''

PCT_FAQ_DE = [
    ('Wie berechne ich den Preis nach einem Rabatt?',
     'Nehmen Sie Block 4 mit «minus». CHF 89.90 minus 30 % ergibt 89.90 × 0.7 = CHF 62.93.'),
    ('Wie finde ich den Preis vor dem Rabatt heraus?',
     "Teilen Sie den reduzierten Preis durch (1 − Rabatt ÷ 100). Bei CHF 960 nach 20 % Rabatt: 960 ÷ 0.8 = CHF 1'200."),
    ('Warum ergeben plus 10 % und minus 10 % nicht wieder den Anfangswert?',
     'Weil der zweite Schritt vom neuen, höheren Betrag ausgeht. Aus CHF 100 werden CHF 110 und danach CHF 99.'),
    ('Was bedeutet ein negatives Ergebnis bei der Veränderung?',
     'Ein Minus zeigt eine Abnahme. Von CHF 200 auf CHF 150 ist eine Veränderung von −25 %.'),
    ('Kann ich mit dem Rechner auch die Mehrwertsteuer berechnen?',
     'Für das Hinzufügen schon, für das Herausrechnen nicht direkt. Nutzen Sie dafür den <a href="/de/mwst-rechner/">MWST-Rechner</a>.'),
]

PCT_ART_FR = '''<h2>Mode d’emploi</h2>
<p>Choisissez le bloc qui correspond à votre question et remplissez les deux champs. Le résultat s’affiche immédiatement. Les décimales peuvent être saisies avec un point ou une virgule, les milliers aussi avec une apostrophe, par exemple 1'250.50.</p>
<h2>Les quatre formules</h2>
<p class="formula">1. X % de Y = Y × X ÷ 100<br>2. Part en % = X ÷ Y × 100<br>3. Variation en % = (B − A) ÷ A × 100<br>4. Y ± X % = Y × (1 ± X ÷ 100)</p>
<h2>Exemples en francs</h2>
<p>Un vélo coûte CHF 240 et bénéficie de 15 % de rabais : 240 × 15 ÷ 100 = CHF 36 de rabais, vous payez CHF 204. Sur un budget de CHF 180, vous avez dépensé CHF 45 : 45 ÷ 180 × 100 = 25 %. Votre prime d’assurance passe de CHF 80 à CHF 92 : (92 − 80) ÷ 80 × 100 = +15 %. Un appareil à CHF 1'200 avec 20 % de rabais coûte 1'200 × 0,8 = CHF 960.</p>
<h2>Erreurs fréquentes</h2>
<p>Un pourcentage se rapporte toujours à une valeur de base. Si l’on ajoute 10 % puis qu’on retire 10 %, on ne retrouve pas le montant de départ : CHF 100 deviennent CHF 110, puis CHF 99, car la baisse est calculée sur le montant plus élevé. Il faut aussi distinguer pour cent et points de pourcentage : si un taux d’intérêt passe de 1,5 % à 2 %, il augmente de 0,5 point, mais de 33 % environ en valeur relative.</p>'''

PCT_FAQ_FR = [
    ('Comment calculer un prix après rabais ?',
     'Utilisez le bloc 4 avec «moins». CHF 89.90 moins 30 % donne 89,90 × 0,7 = CHF 62.93.'),
    ('Comment retrouver le prix avant le rabais ?',
     "Divisez le prix réduit par (1 − rabais ÷ 100). Pour CHF 960 après 20 % de rabais : 960 ÷ 0,8 = CHF 1'200."),
    ('Pourquoi plus 10 % puis moins 10 % ne redonnent-ils pas le montant de départ ?',
     'Parce que la deuxième étape part du nouveau montant, plus élevé. CHF 100 deviennent CHF 110, puis CHF 99.'),
    ('Que signifie un résultat négatif pour la variation ?',
     'Un signe moins indique une baisse. De CHF 200 à CHF 150, la variation est de −25 %.'),
    ('Puis-je aussi calculer la TVA avec cet outil ?',
     'Pour l’ajouter oui, mais pas directement pour l’extraire. Utilisez plutôt le <a href="/fr/calcul-tva-suisse/">calcul de la TVA suisse</a>.'),
]

WORDCOUNT['pct_de'] = tool_page(
    'pct', 'de', 'Prozentrechner: Prozent, Anteil und Veränderung',
    'Prozentrechner mit 4 Modi: X % von Y, Anteil in Prozent, prozentuale Veränderung und Wert plus/minus Prozent. Mit Beispielen in Franken.',
    'Prozentrechner', 'Vier Prozentrechnungen in einem Werkzeug – mit Formeln und Beispielen aus dem Schweizer Alltag.',
    pct_tool('de'), PCT_ART_DE, PCT_FAQ_DE, [], 'UtilitiesApplication')
WORDCOUNT['pct_fr'] = tool_page(
    'pct', 'fr', 'Calcul de pourcentage : part, variation, rabais',
    'Calculateur de pourcentage en 4 modes : X % de Y, part en %, variation en % et valeur plus ou moins %. Avec exemples en francs suisses.',
    'Calcul de pourcentage', 'Quatre calculs de pourcentage en un seul outil – avec formules et exemples de la vie courante en Suisse.',
    pct_tool('fr'), PCT_ART_FR, PCT_FAQ_FR, [], 'UtilitiesApplication')

# =====================================================================
# 3. VAT
# =====================================================================
def vat_tool(lang):
    if lang == 'de':
        L = dict(h='MWST berechnen', amt='Betrag in CHF', dir='Richtung', add='Netto → Brutto (MWST hinzufügen)',
                 rem='Brutto → Netto (MWST herausrechnen)', rate='Steuersatz', n='Normalsatz 8.1 %',
                 r='Reduzierter Satz 2.6 %', a='Beherbergung 3.8 %', round='MWST-Betrag auf 5 Rappen runden', btn='Berechnen')
    else:
        L = dict(h='Calculer la TVA', amt='Montant en CHF', dir='Sens du calcul', add='Hors TVA → TVA incluse (ajouter)',
                 rem='TVA incluse → hors TVA (extraire)', rate='Taux', n='Taux normal 8,1 %',
                 r='Taux réduit 2,6 %', a='Hébergement 3,8 %', round='Arrondir la TVA à 5 centimes', btn='Calculer')
    return f'''<section class="tool" data-tool="vat" aria-labelledby="tool-h">
<h2 id="tool-h">{L['h']}</h2>
<form novalidate>
<div class="field"><label for="vat-amount">{L['amt']}</label><input type="text" inputmode="decimal" id="vat-amount" name="amount" value="100.00" autocomplete="off"></div>
<fieldset><legend>{L['dir']}</legend><div class="choice">
<label><input type="radio" name="dir" value="add" checked> {L['add']}</label>
<label><input type="radio" name="dir" value="remove"> {L['rem']}</label>
</div></fieldset>
<div class="field"><label for="vat-rate">{L['rate']}</label><select id="vat-rate" name="rate">
<option value="8.1">{L['n']}</option><option value="2.6">{L['r']}</option><option value="3.8">{L['a']}</option></select></div>
<div class="choice field"><label><input type="checkbox" name="round5"> {L['round']}</label></div>
<button type="submit" class="btn">{L['btn']}</button>
</form>
<div class="result" aria-live="polite"></div>
<noscript><p>JavaScript</p></noscript>
</section>'''

VAT_ART_DE = '''<h2>So funktioniert der Rechner</h2>
<p>Geben Sie einen Betrag ein und wählen Sie die Richtung: «Netto → Brutto» schlägt die Mehrwertsteuer auf einen Preis ohne MWST auf, «Brutto → Netto» rechnet sie aus einem Preis heraus, in dem sie bereits enthalten ist. Danach wählen Sie den Steuersatz. Auf Wunsch wird der MWST-Betrag auf 5 Rappen gerundet.</p>
<h2>Die Schweizer MWST-Sätze</h2>
<p>Seit dem 1. Januar 2024 gelten laut der Eidgenössischen Steuerverwaltung (ESTV) drei Sätze: der Normalsatz von 8.1 %, der reduzierte Satz von 2.6 % und der Sondersatz für Beherbergungsleistungen von 3.8 %. Welcher Satz für eine Leistung gilt, hängt von der Leistung selbst ab; im Zweifel gibt die ESTV Auskunft.</p>
<h2>Formeln</h2>
<p class="formula">Brutto = Netto × (1 + Satz ÷ 100)<br>Netto = Brutto ÷ (1 + Satz ÷ 100)<br>MWST = Brutto − Netto</p>
<p>Ein häufiger Fehler: Die enthaltene Steuer ist nicht Brutto × 8.1 %. Bei CHF 108.10 brutto wären das CHF 8.76, richtig sind 108.10 − 108.10 ÷ 1.081 = CHF 8.10.</p>
<h2>Beispiele</h2>
<p>Eine Rechnung über netto CHF 250.00 zum Normalsatz: 250.00 × 8.1 % = CHF 20.25 MWST, total CHF 270.25. Eine Übernachtung zu netto CHF 180.00 zum Beherbergungssatz: CHF 6.84 MWST, total CHF 186.84.</p>
<h2>Rappenrundung</h2>
<p>Weil die kleinste Münze in der Schweiz 5 Rappen ist, werden Beträge oft auf 0.05 gerundet. Mit der Option rundet der Rechner den MWST-Betrag auf 5 Rappen und berechnet den anderen Betrag daraus. Beispiel: netto CHF 47.30 ergibt CHF 3.8313 MWST, gerundet CHF 3.85, total CHF 51.15.</p>'''

VAT_FAQ_DE = [
    ('Wie rechne ich die MWST aus einem Bruttobetrag heraus?',
     'Teilen Sie den Bruttobetrag durch 1.081 (Normalsatz). Die Differenz zum Bruttobetrag ist die MWST. Aus CHF 540.50 werden so CHF 500.00 netto und CHF 40.50 MWST.'),
    ('Warum ergibt Netto plus 8.1 % und danach minus 8.1 % nicht den Ausgangsbetrag?',
     'Weil der Abzug von 8.1 % auf dem höheren Bruttobetrag berechnet wird. Zum Herausrechnen muss man durch 1.081 teilen, nicht 8.1 % abziehen.'),
    ('Welcher Satz gilt für mein Produkt?',
     'Das hängt von der Art der Leistung ab. Prüfen Sie die Angaben der ESTV oder fragen Sie Ihre Treuhänderin oder Ihren Treuhänder.'),
    ('Muss ich die Rappenrundung verwenden?',
     'Der Rechner bietet sie als Option an. Wie Sie in Ihrer Buchhaltung runden, klären Sie am besten mit Ihrer Treuhand oder der ESTV.'),
    ('Werden meine Beträge gespeichert?',
     'Nein. Die Berechnung läuft nur in Ihrem Browser, es wird nichts übermittelt.'),
]

VAT_ART_FR = '''<h2>Mode d’emploi</h2>
<p>Saisissez un montant et choisissez le sens du calcul : «hors TVA → TVA incluse» ajoute la taxe à un prix hors TVA, «TVA incluse → hors TVA» l’extrait d’un prix qui la contient déjà. Choisissez ensuite le taux. Si vous le souhaitez, le montant de TVA est arrondi à 5 centimes.</p>
<h2>Les taux de TVA en Suisse</h2>
<p>Depuis le 1er janvier 2024, selon l’Administration fédérale des contributions (AFC), trois taux s’appliquent : le taux normal de 8,1 %, le taux réduit de 2,6 % et le taux spécial de 3,8 % pour les prestations d’hébergement. Le taux applicable dépend de la prestation elle-même ; en cas de doute, l’AFC renseigne.</p>
<h2>Formules</h2>
<p class="formula">TVA incluse = hors TVA × (1 + taux ÷ 100)<br>Hors TVA = TVA incluse ÷ (1 + taux ÷ 100)<br>TVA = TVA incluse − hors TVA</p>
<p>Erreur fréquente : la taxe contenue dans un prix n’est pas prix × 8,1 %. Pour CHF 108.10 TVA incluse, cela donnerait CHF 8.76 ; le bon résultat est 108,10 − 108,10 ÷ 1,081 = CHF 8.10.</p>
<h2>Exemples</h2>
<p>Une facture de CHF 250.00 hors TVA au taux normal : 250,00 × 8,1 % = CHF 20.25 de TVA, total CHF 270.25. Une nuitée à CHF 180.00 hors TVA au taux de l’hébergement : CHF 6.84 de TVA, total CHF 186.84.</p>
<h2>Arrondi à 5 centimes</h2>
<p>La plus petite pièce en Suisse étant de 5 centimes, les montants sont souvent arrondis à 0,05. Avec cette option, le calculateur arrondit la TVA à 5 centimes et en déduit l’autre montant. Exemple : CHF 47.30 hors TVA donnent CHF 3.8313 de TVA, arrondis à CHF 3.85, total CHF 51.15.</p>'''

VAT_FAQ_FR = [
    ('Comment extraire la TVA d’un montant TVA incluse ?',
     'Divisez le montant par 1,081 (taux normal). La différence avec le montant de départ est la TVA. CHF 540.50 donnent ainsi CHF 500.00 hors TVA et CHF 40.50 de TVA.'),
    ('Pourquoi ajouter 8,1 % puis retirer 8,1 % ne redonne-t-il pas le montant de départ ?',
     'Parce que la déduction de 8,1 % est calculée sur le montant plus élevé. Pour extraire la TVA, il faut diviser par 1,081 et non retirer 8,1 %.'),
    ('Quel taux s’applique à mon produit ?',
     'Cela dépend de la nature de la prestation. Consultez les informations de l’AFC ou demandez à votre fiduciaire.'),
    ('Dois-je utiliser l’arrondi à 5 centimes ?',
     'Le calculateur le propose en option. La manière d’arrondir dans votre comptabilité se règle de préférence avec votre fiduciaire ou l’AFC.'),
    ('Mes montants sont-ils enregistrés ?',
     'Non. Le calcul se fait uniquement dans votre navigateur, rien n’est transmis.'),
]

VATSRC = {
    'de': [f'Eidgenössische Steuerverwaltung ESTV, MWST-Steuersätze: <a href="{SRC["estv_de"]}">{SRC["estv_de"]}</a>'],
    'fr': [f'Administration fédérale des contributions AFC, taux de TVA : <a href="{SRC["estv_fr"]}">{SRC["estv_fr"]}</a>'],
}

WORDCOUNT['vat_de'] = tool_page(
    'vat', 'de', 'MWST-Rechner Schweiz: 8.1 %, 2.6 % und 3.8 %',
    'Mehrwertsteuer Schweiz hinzufügen oder herausrechnen: Netto ↔ Brutto mit 8.1 %, 2.6 % und 3.8 %, optional mit Rundung auf 5 Rappen.',
    'MWST-Rechner Schweiz', 'Mehrwertsteuer aufschlagen oder herausrechnen – mit den aktuellen Sätzen der ESTV und optionaler Rappenrundung.',
    vat_tool('de'), VAT_ART_DE, VAT_FAQ_DE, VATSRC['de'], 'FinanceApplication')
WORDCOUNT['vat_fr'] = tool_page(
    'vat', 'fr', 'Calcul TVA Suisse : 8,1 %, 2,6 % et 3,8 %',
    'Ajouter ou extraire la TVA suisse : hors TVA ↔ TVA incluse avec 8,1 %, 2,6 % et 3,8 %, avec arrondi à 5 centimes en option.',
    'Calcul de la TVA suisse', 'Ajouter ou extraire la TVA – avec les taux actuels de l’AFC et un arrondi à 5 centimes en option.',
    vat_tool('fr'), VAT_ART_FR, VAT_FAQ_FR, VATSRC['fr'], 'FinanceApplication')

# =====================================================================
# 6. IBAN check
# =====================================================================
def iban_tool(lang):
    L = dict(h='IBAN prüfen', lab='IBAN', btn='Prüfen', hint='Mit oder ohne Leerzeichen, z. B. CH93 0076 2011 6238 5295 7') if lang == 'de' else \
        dict(h='Vérifier une IBAN', lab='IBAN', btn='Vérifier', hint='Avec ou sans espaces, p. ex. CH93 0076 2011 6238 5295 7')
    return f'''<section class="tool" data-tool="iban" aria-labelledby="tool-h">
<h2 id="tool-h">{L['h']}</h2>
<form novalidate>
<div class="field"><label for="iban-input">{L['lab']}</label><input type="text" id="iban-input" name="iban" autocomplete="off" autocapitalize="characters" spellcheck="false" maxlength="50" aria-describedby="iban-hint"><span class="note" id="iban-hint">{L['hint']}</span></div>
<button type="submit" class="btn">{L['btn']}</button>
</form>
<div class="result" aria-live="polite"></div>
<noscript><p>JavaScript</p></noscript>
</section>'''

IBAN_ART_DE = '''<h2>So funktioniert die Prüfung</h2>
<p>Fügen Sie die IBAN ein, mit oder ohne Leerzeichen. Der Rechner entfernt Leerzeichen, wandelt Kleinbuchstaben um und zeigt die IBAN in Vierergruppen, so wie sie auf Rechnungen steht. Dann prüft er den Ländercode, die Länge für dieses Land und die zweistellige Prüfziffer. Alles läuft in Ihrem Browser; die IBAN wird nirgendwohin gesendet.</p>
<p><strong>Wichtig:</strong> Eine korrekte Prüfziffer heisst nur, dass die IBAN richtig aufgebaut ist. Ob das Konto existiert, offen ist oder wem es gehört, kann kein Offline-Test feststellen. Das weiss nur die Bank.</p>
<h2>Aufbau einer Schweizer IBAN</h2>
<p>Eine Schweizer IBAN hat 21 Zeichen: «CH», zwei Prüfziffern, eine fünfstellige Bank-Identifikation (IID) und eine zwölfstellige Kontonummer. Liechtensteiner IBAN haben ebenfalls 21 Zeichen, deutsche 22, österreichische 20, französische und italienische 27.</p>
<h2>Die Formel: Modulo 97</h2>
<p>Die Prüfziffer folgt der Norm ISO 13616. Man stellt die ersten vier Zeichen ans Ende, ersetzt jeden Buchstaben durch eine Zahl (A = 10, B = 11 … Z = 35) und teilt die so entstandene lange Zahl durch 97.</p>
<p class="formula">gültig, wenn Rest (umgestellte IBAN ÷ 97) = 1</p>
<p>So fallen fast alle Tippfehler und vertauschten Ziffern auf.</p>
<h2>Beispiel</h2>
<p>Eine Kundin gibt für eine Rückerstattung von CHF 180.00 die IBAN CH93 0076 2011 6238 5295 7 an. Der Rechner meldet: gültig. Hätte sie als letzte Ziffer eine 8 statt einer 7 geschrieben, wäre die Prüfziffer falsch, und Sie bemerken den Fehler, bevor Sie die Zahlung erfassen.</p>
<h2>QR-IBAN erkennen</h2>
<p>Für QR-Rechnungen mit QR-Referenz verwenden Schweizer Banken eine besondere IBAN, die QR-IBAN. Sie ist daran erkennbar, dass die Bank-Identifikation (Stellen 5 bis 9) zwischen 30000 und 31999 liegt. Der Rechner weist darauf hin, denn eine QR-IBAN ist nur zusammen mit einer QR-Referenz gedacht.</p>'''

IBAN_FAQ_DE = [
    ('Bedeutet «gültig», dass das Konto existiert?',
     'Nein. Geprüft werden nur Aufbau, Länge und Prüfziffer. Ob das Konto existiert und wem es gehört, kann nur die Bank bestätigen.'),
    ('Warum wird meine IBAN als zu kurz gemeldet?',
     'Meist fehlt beim Abtippen ein Zeichen. Vergleichen Sie die Vierergruppen mit der Vorlage: Eine Schweizer IBAN hat 21 Zeichen, also fünf volle Gruppen und ein einzelnes Zeichen.'),
    ('Was ist der Unterschied zwischen IBAN und QR-IBAN?',
     'Die QR-IBAN hat denselben Aufbau, aber eine Bank-Identifikation zwischen 30000 und 31999. Sie dient für QR-Rechnungen mit QR-Referenz, nicht für normale Überweisungen.'),
    ('Welche Länder kennt der Rechner?',
     'Die Länge ist unter anderem für CH, LI, DE, AT, FR und IT hinterlegt. Bei anderen Ländern wird nur die Prüfziffer kontrolliert, und der Rechner sagt das auch.'),
    ('Wird meine IBAN gespeichert oder übermittelt?',
     'Nein. Die Prüfung läuft vollständig in Ihrem Browser. Es wird nichts gesendet und nichts gespeichert.'),
]

IBAN_ART_FR = '''<h2>Comment fonctionne la vérification</h2>
<p>Collez l’IBAN, avec ou sans espaces. Le calculateur supprime les espaces, met les lettres en majuscules et affiche l’IBAN par groupes de quatre, comme sur une facture. Il contrôle ensuite le code pays, la longueur prévue pour ce pays et les deux chiffres de contrôle. Tout se passe dans votre navigateur ; l’IBAN n’est envoyée nulle part.</p>
<p><strong>Important :</strong> une clé de contrôle correcte signifie seulement que l’IBAN est bien construite. Aucun test hors ligne ne peut dire si le compte existe, s’il est ouvert ou à qui il appartient. Seule la banque le sait.</p>
<h2>Structure d’une IBAN suisse</h2>
<p>Une IBAN suisse compte 21 caractères : «CH», deux chiffres de contrôle, un identifiant de banque à cinq chiffres (IID) et un numéro de compte à douze caractères. Les IBAN du Liechtenstein ont aussi 21 caractères, celles d’Allemagne 22, d’Autriche 20, de France et d’Italie 27.</p>
<h2>La formule : modulo 97</h2>
<p>La clé de contrôle suit la norme ISO 13616. On place les quatre premiers caractères à la fin, on remplace chaque lettre par un nombre (A = 10, B = 11 … Z = 35) et on divise le long nombre obtenu par 97.</p>
<p class="formula">valable si reste (IBAN réarrangée ÷ 97) = 1</p>
<p>Ce contrôle détecte presque toutes les fautes de frappe et les chiffres inversés.</p>
<h2>Exemple</h2>
<p>Une cliente indique l’IBAN CH93 0076 2011 6238 5295 7 pour un remboursement de CHF 180.00. Le calculateur répond : valable. Si elle avait écrit un 8 au lieu du 7 final, la clé serait fausse et vous verriez l’erreur avant de saisir le paiement.</p>
<h2>Reconnaître une QR-IBAN</h2>
<p>Pour les QR-factures avec référence QR, les banques suisses utilisent une IBAN particulière, la QR-IBAN. On la reconnaît à son identifiant de banque (positions 5 à 9) compris entre 30000 et 31999. Le calculateur le signale, car une QR-IBAN est prévue uniquement avec une référence QR.</p>'''

IBAN_FAQ_FR = [
    ('«Valable» signifie-t-il que le compte existe ?',
     'Non. Seuls la structure, la longueur et la clé de contrôle sont vérifiés. Seule la banque peut confirmer que le compte existe et à qui il appartient.'),
    ('Pourquoi mon IBAN est-elle signalée comme trop courte ?',
     'Le plus souvent, un caractère a été oublié. Comparez les groupes de quatre avec l’original : une IBAN suisse compte 21 caractères, soit cinq groupes complets et un caractère seul.'),
    ('Quelle différence entre IBAN et QR-IBAN ?',
     'La QR-IBAN a la même structure, mais un identifiant de banque entre 30000 et 31999. Elle sert aux QR-factures avec référence QR, pas aux virements ordinaires.'),
    ('Quels pays le calculateur connaît-il ?',
     'La longueur est enregistrée notamment pour CH, LI, DE, AT, FR et IT. Pour les autres pays, seule la clé de contrôle est vérifiée, et le calculateur l’indique.'),
    ('Mon IBAN est-elle enregistrée ou transmise ?',
     'Non. La vérification se fait entièrement dans votre navigateur. Rien n’est envoyé ni enregistré.'),
]

WORDCOUNT['iban_de'] = tool_page(
    'iban', 'de', 'IBAN prüfen: Prüfziffer, Länge und QR-IBAN',
    'IBAN offline prüfen: Länge, Prüfziffer nach ISO 13616 (Modulo 97), Vierergruppen und Erkennung der Schweizer QR-IBAN. Nichts wird gesendet.',
    'IBAN prüfen', 'Prüfen Sie eine IBAN auf Länge, Zeichen und Prüfziffer – offline, mit Erkennung der Schweizer QR-IBAN.',
    iban_tool('de'), IBAN_ART_DE, IBAN_FAQ_DE, [], 'FinanceApplication')
WORDCOUNT['iban_fr'] = tool_page(
    'iban', 'fr', 'Vérifier une IBAN : clé de contrôle et QR-IBAN',
    'Vérifiez une IBAN hors ligne : longueur, clé de contrôle ISO 13616 (modulo 97), groupes de quatre et détection de la QR-IBAN suisse.',
    'Vérifier une IBAN', 'Contrôlez la longueur, les caractères et la clé d’une IBAN – hors ligne, avec détection de la QR-IBAN suisse.',
    iban_tool('fr'), IBAN_ART_FR, IBAN_FAQ_FR, [], 'FinanceApplication')

# =====================================================================
# 7. Hourly wage
# =====================================================================
def salary_tool(lang):
    if lang == 'de':
        L = dict(h='Lohn umrechnen', dir='Richtung', m2h='Monatslohn → Stundenlohn', h2m='Stundenlohn → Monatslohn',
                 amt='Betrag in CHF (brutto)', hours='Wochenstunden', sal='Löhne pro Jahr', s12='12 Monatslöhne',
                 s13='13 Monatslöhne', weeks='Wochen pro Jahr', btn='Berechnen',
                 hint='Voreinstellung 42 Stunden und 52 Wochen: eine Annahme, die Sie anpassen können.')
    else:
        L = dict(h='Convertir un salaire', dir='Sens du calcul', m2h='Salaire mensuel → horaire', h2m='Salaire horaire → mensuel',
                 amt='Montant en CHF (brut)', hours='Heures par semaine', sal='Salaires par an', s12='12 salaires mensuels',
                 s13='13 salaires mensuels', weeks='Semaines par an', btn='Calculer',
                 hint='Valeurs par défaut 42 heures et 52 semaines : une hypothèse que vous pouvez modifier.')
    return f'''<section class="tool" data-tool="salary" aria-labelledby="tool-h">
<h2 id="tool-h">{L['h']}</h2>
<form novalidate>
<fieldset><legend>{L['dir']}</legend><div class="choice">
<label><input type="radio" name="dir" value="m2h" checked> {L['m2h']}</label>
<label><input type="radio" name="dir" value="h2m"> {L['h2m']}</label>
</div></fieldset>
<div class="field"><label for="sal-amount">{L['amt']}</label><input type="text" inputmode="decimal" id="sal-amount" name="amount" value="5500" autocomplete="off"></div>
<div class="row">
<div class="field"><label for="sal-hours">{L['hours']}</label><input type="text" inputmode="decimal" id="sal-hours" name="hours" value="42" autocomplete="off"></div>
<div class="field"><label for="sal-n">{L['sal']}</label><select id="sal-n" name="salaries"><option value="12">{L['s12']}</option><option value="13">{L['s13']}</option></select></div>
<div class="field"><label for="sal-weeks">{L['weeks']}</label><input type="text" inputmode="decimal" id="sal-weeks" name="weeks" value="52" autocomplete="off"></div>
</div>
<p class="note">{L['hint']}</p>
<button type="submit" class="btn">{L['btn']}</button>
</form>
<div class="result" aria-live="polite"></div>
<noscript><p>JavaScript</p></noscript>
</section>'''

SAL_ART_DE = '''<h2>So funktioniert der Rechner</h2>
<p>Wählen Sie die Richtung, geben Sie den Bruttobetrag in Franken ein und passen Sie die Annahmen an: Wochenstunden, Anzahl Löhne pro Jahr und Wochen pro Jahr. Voreingestellt sind 42 Stunden pro Woche und 52 Wochen. Das ist eine Annahme, keine Vorgabe: Ihre Arbeitszeit steht im Arbeitsvertrag oder im Gesamtarbeitsvertrag, und Sie können jeden Wert ändern.</p>
<h2>Formeln</h2>
<p class="formula">Stundenlohn = Monatslohn × Löhne pro Jahr ÷ (Wochenstunden × Wochen)<br>Monatslohn = Stundenlohn × Wochenstunden × Wochen ÷ Löhne pro Jahr</p>
<h2>Beispiel mit 13. Monatslohn</h2>
<p>Sie verdienen CHF 5'500 brutto pro Monat, 13-mal im Jahr, bei 42 Stunden pro Woche. Jahreslohn: 5'500 × 13 = CHF 71'500. Arbeitsstunden: 42 × 52 = 2'184. Stundenlohn: 71'500 ÷ 2'184 = CHF 32.74. Ohne 13. Monatslohn wären es CHF 30.22; der 13. Lohn macht also rund CHF 2.50 pro Stunde aus.</p>
<p>Umgekehrt entspricht ein Angebot von CHF 32.50 pro Stunde bei 42 Stunden und 52 Wochen einem Jahreslohn von CHF 70'980, also CHF 5'915 pro Monat bei 12 Löhnen.</p>
<h2>Warum 52 Wochen?</h2>
<p>Beim Monatslohn sind Ferien und Feiertage bezahlt. Mit allen 52 Wochen erhalten Sie deshalb den Stundenlohn, der Ihrem Monatslohn entspricht. Möchten Sie wissen, was Sie pro tatsächlich gearbeitete Stunde verdienen, setzen Sie weniger Wochen ein, nämlich 52 minus Ihre Ferien- und Feiertagswochen. Der Stundenlohn steigt dann entsprechend. Alle Beträge sind brutto, also vor Abzügen für Sozialversicherungen und Pensionskasse.</p>'''

SAL_FAQ_DE = [
    ('Wie berücksichtige ich den 13. Monatslohn?',
     'Wählen Sie «13 Monatslöhne». Der Jahreslohn wird dann mit 13 multipliziert, und der Stundenlohn steigt entsprechend.'),
    ('Ist das Ergebnis brutto oder netto?',
     'Brutto. Der Rechner zieht keine Sozialversicherungsbeiträge, Pensionskassenbeiträge oder Steuern ab.'),
    ('Welche Wochenstunden soll ich eingeben?',
     'Die Arbeitszeit aus Ihrem Vertrag. Die 42 Stunden sind nur eine Voreinstellung; viele Verträge nennen eine andere Zahl.'),
    ('Warum unterscheidet sich mein Stundenlohn im Vertrag?',
     'Oft wegen anderer Wochenstunden oder weil bei Stundenlohn Ferien und Feiertage separat als Zuschlag bezahlt werden. Vergleichen Sie die Annahmen mit Ihrem Vertrag.'),
    ('Werden meine Angaben gespeichert?',
     'Nein. Die Berechnung läuft nur in Ihrem Browser, es wird nichts übermittelt.'),
]

SAL_ART_FR = '''<h2>Mode d’emploi</h2>
<p>Choisissez le sens du calcul, saisissez le montant brut en francs et adaptez les hypothèses : heures par semaine, nombre de salaires par an et semaines par an. Par défaut, le calculateur utilise 42 heures par semaine et 52 semaines. Il s’agit d’une hypothèse, pas d’une règle : votre temps de travail figure dans votre contrat ou dans la convention collective, et vous pouvez modifier chaque valeur.</p>
<h2>Formules</h2>
<p class="formula">Salaire horaire = salaire mensuel × salaires par an ÷ (heures par semaine × semaines)<br>Salaire mensuel = salaire horaire × heures par semaine × semaines ÷ salaires par an</p>
<h2>Exemple avec 13e salaire</h2>
<p>Vous gagnez CHF 5'500 brut par mois, 13 fois par an, pour 42 heures par semaine. Salaire annuel : 5'500 × 13 = CHF 71'500. Heures de travail : 42 × 52 = 2'184. Salaire horaire : 71'500 ÷ 2'184 = CHF 32.74. Sans 13e salaire, ce serait CHF 30.22 ; le 13e salaire représente donc environ CHF 2.50 par heure.</p>
<p>À l’inverse, une offre à CHF 32.50 de l’heure, pour 42 heures et 52 semaines, correspond à un salaire annuel de CHF 70'980, soit CHF 5'915 par mois sur 12 salaires.</p>
<h2>Pourquoi 52 semaines ?</h2>
<p>Avec un salaire mensuel, les vacances et les jours fériés sont payés. En comptant les 52 semaines, vous obtenez donc le salaire horaire équivalent à votre salaire mensuel. Pour savoir ce que vous gagnez par heure réellement travaillée, saisissez moins de semaines : 52 moins vos semaines de vacances et de jours fériés. Le salaire horaire augmente alors. Tous les montants sont bruts, avant les déductions pour les assurances sociales et la caisse de pension.</p>'''

SAL_FAQ_FR = [
    ('Comment tenir compte du 13e salaire ?',
     'Choisissez «13 salaires mensuels». Le salaire annuel est alors multiplié par 13 et le salaire horaire augmente d’autant.'),
    ('Le résultat est-il brut ou net ?',
     'Brut. Le calculateur ne déduit ni cotisations sociales, ni caisse de pension, ni impôts.'),
    ('Combien d’heures par semaine dois-je saisir ?',
     'Le temps de travail de votre contrat. Les 42 heures ne sont qu’une valeur par défaut ; beaucoup de contrats prévoient un autre chiffre.'),
    ('Pourquoi mon salaire horaire contractuel est-il différent ?',
     'Souvent à cause d’un autre nombre d’heures, ou parce qu’avec un salaire horaire, les vacances et les jours fériés sont payés à part sous forme de supplément. Comparez les hypothèses avec votre contrat.'),
    ('Mes données sont-elles enregistrées ?',
     'Non. Le calcul se fait uniquement dans votre navigateur, rien n’est transmis.'),
]

WORDCOUNT['sal_de'] = tool_page(
    'salary', 'de', 'Stundenlohn-Rechner Schweiz: Monatslohn umrechnen',
    'Monatslohn in Stundenlohn umrechnen und umgekehrt: mit 12 oder 13 Löhnen, Wochenstunden und Wochen pro Jahr frei wählbar. Beispiel in CHF.',
    'Stundenlohn-Rechner Schweiz', 'Monatslohn in Stundenlohn umrechnen und umgekehrt – mit 12 oder 13 Monatslöhnen und Ihren eigenen Arbeitsstunden.',
    salary_tool('de'), SAL_ART_DE, SAL_FAQ_DE, [], 'FinanceApplication')
WORDCOUNT['sal_fr'] = tool_page(
    'salary', 'fr', 'Calcul du salaire horaire en Suisse',
    'Convertissez un salaire mensuel en salaire horaire et inversement : 12 ou 13 salaires, heures et semaines par an modifiables. Exemple en CHF.',
    'Calcul du salaire horaire (Suisse)', 'Convertir un salaire mensuel en salaire horaire et inversement – avec 12 ou 13 salaires et vos propres heures.',
    salary_tool('fr'), SAL_ART_FR, SAL_FAQ_FR, [], 'FinanceApplication')

# =====================================================================
# 8. Days between dates
# =====================================================================
def days_tool(lang):
    if lang == 'de':
        L = dict(h='Tage berechnen', s='Startdatum', e='Enddatum', inc='Enddatum mitzählen',
                 hol='Neujahr (1.1.), Bundesfeiertag (1.8.) und Weihnachten (25.12.) abziehen', btn='Berechnen')
    else:
        L = dict(h='Calculer les jours', s='Date de début', e='Date de fin', inc='Compter la date de fin',
                 hol='Déduire Nouvel An (1.1), fête nationale (1.8) et Noël (25.12)', btn='Calculer')
    return f'''<section class="tool" data-tool="days" aria-labelledby="tool-h">
<h2 id="tool-h">{L['h']}</h2>
<form novalidate>
<div class="row">
<div class="field"><label for="d-start">{L['s']}</label><input type="date" id="d-start" name="start" value="2027-03-01"></div>
<div class="field"><label for="d-end">{L['e']}</label><input type="date" id="d-end" name="end" value="2027-06-01"></div>
</div>
<div class="choice field"><label><input type="checkbox" name="includeEnd"> {L['inc']}</label>
<label><input type="checkbox" name="holidays"> {L['hol']}</label></div>
<button type="submit" class="btn">{L['btn']}</button>
</form>
<div class="result" aria-live="polite"></div>
<noscript><p>JavaScript</p></noscript>
</section>'''

DAYS_ART_DE = '''<h2>So funktioniert der Rechner</h2>
<p>Wählen Sie Start- und Enddatum. Standardmässig zählt der Starttag mit, der Endtag nicht, so wie bei der Frage «in wie vielen Tagen?». Mit «Enddatum mitzählen» wird auch der letzte Tag gezählt, etwa für die Dauer von Ferien oder eines Einsatzes. Als Arbeitstage gelten alle Tage von Montag bis Freitag im gewählten Zeitraum.</p>
<h2>Feiertage</h2>
<p>Auf Wunsch zieht der Rechner drei Feiertage mit festem Datum ab: Neujahr (1. Januar), den Bundesfeiertag (1. August) und Weihnachten (25. Dezember), sofern sie auf einen Werktag fallen. Weitere Feiertage wie Karfreitag, Ostermontag, Auffahrt, Pfingstmontag, Berchtoldstag oder Stephanstag sind von Kanton zu Kanton verschieden und werden <strong>nicht</strong> berücksichtigt. Ziehen Sie diese für Ihren Kanton selbst ab.</p>
<h2>Formel</h2>
<p class="formula">Kalendertage = Enddatum − Startdatum (+ 1, wenn der Endtag mitzählt)<br>Wochen = Kalendertage ÷ 7, der Rest sind einzelne Tage</p>
<h2>Beispiele</h2>
<p>Ein Auftrag läuft vom 1. März 2027 bis zum 1. Juni 2027, der Endtag zählt nicht. Das sind 92 Kalendertage oder 13 Wochen und 1 Tag, davon 66 Arbeitstage von Montag bis Freitag. Bei einem Tagessatz von CHF 650 ergibt das höchstens 66 × 650 = CHF 42'900, bevor kantonale Feiertage wie Ostermontag oder Auffahrt abgezogen werden.</p>
<p>Über den Jahreswechsel, vom 21. Dezember 2026 bis und mit 8. Januar 2027, zählt der Rechner 19 Kalendertage und 15 Arbeitstage. Mit der Feiertagsoption bleiben 13, weil der 25. Dezember 2026 und der 1. Januar 2027 auf einen Freitag fallen.</p>'''

DAYS_FAQ_DE = [
    ('Zählt der Starttag mit?',
     'Ja, der Starttag wird immer gezählt. Den Endtag zählen Sie mit der Option «Enddatum mitzählen» dazu.'),
    ('Werden Ostern, Auffahrt oder kantonale Feiertage berücksichtigt?',
     'Nein. Abgezogen werden auf Wunsch nur der 1. Januar, der 1. August und der 25. Dezember. Alle anderen Feiertage müssen Sie für Ihren Kanton selbst abziehen.'),
    ('Was passiert, wenn das Enddatum vor dem Startdatum liegt?',
     'Der Rechner vertauscht die beiden Daten, rechnet normal weiter und weist Sie darauf hin.'),
    ('Werden Schaltjahre berücksichtigt?',
     'Ja. Vom 1. Februar bis zum 1. März 2028 zählt der Rechner zum Beispiel 29 Tage, weil 2028 ein Schaltjahr ist.'),
    ('Kann ich damit rechtliche Fristen berechnen?',
     'Nur als grobe Hilfe. Für rechtliche Fristen gelten eigene Regeln; verlassen Sie sich dafür nicht allein auf diesen Rechner.'),
]

DAYS_ART_FR = '''<h2>Mode d’emploi</h2>
<p>Choisissez la date de début et la date de fin. Par défaut, le jour de début est compté, mais pas le jour de fin, comme pour la question «dans combien de jours ?». Avec «Compter la date de fin», le dernier jour est aussi compté, par exemple pour la durée de vacances ou d’une mission. Les jours ouvrés sont tous les jours du lundi au vendredi de la période choisie.</p>
<h2>Jours fériés</h2>
<p>Si vous le souhaitez, le calculateur déduit trois jours fériés à date fixe : le Nouvel An (1er janvier), la fête nationale (1er août) et Noël (25 décembre), lorsqu’ils tombent un jour de semaine. Les autres jours fériés, comme le Vendredi saint, le lundi de Pâques, l’Ascension, le lundi de Pentecôte, le 2 janvier ou le 26 décembre, varient d’un canton à l’autre et ne sont <strong>pas</strong> pris en compte. Déduisez-les vous-même pour votre canton.</p>
<h2>Formule</h2>
<p class="formula">Jours calendaires = date de fin − date de début (+ 1 si le jour de fin compte)<br>Semaines = jours calendaires ÷ 7, le reste en jours</p>
<h2>Exemples</h2>
<p>Un mandat court du 1er mars 2027 au 1er juin 2027, jour de fin non compté. Cela fait 92 jours calendaires, soit 13 semaines et 1 jour, dont 66 jours ouvrés du lundi au vendredi. Avec un tarif journalier de CHF 650, cela donne au maximum 66 × 650 = CHF 42'900, avant déduction des fériés cantonaux comme le lundi de Pâques ou l’Ascension.</p>
<p>Autour du Nouvel An, du 21 décembre 2026 au 8 janvier 2027 inclus, le calculateur compte 19 jours calendaires et 15 jours ouvrés. Avec l’option des jours fériés, il en reste 13, car le 25 décembre 2026 et le 1er janvier 2027 tombent un vendredi.</p>'''

DAYS_FAQ_FR = [
    ('Le jour de début est-il compté ?',
     'Oui, toujours. Le jour de fin s’ajoute avec l’option «Compter la date de fin».'),
    ('Pâques, l’Ascension ou les fériés cantonaux sont-ils pris en compte ?',
     'Non. Sur demande, seuls le 1er janvier, le 1er août et le 25 décembre sont déduits. Les autres jours fériés doivent être déduits selon votre canton.'),
    ('Que se passe-t-il si la date de fin précède la date de début ?',
     'Le calculateur inverse les deux dates, calcule normalement et vous le signale.'),
    ('Les années bissextiles sont-elles prises en compte ?',
     'Oui. Du 1er février au 1er mars 2028, le calculateur compte par exemple 29 jours, car 2028 est une année bissextile.'),
    ('Puis-je calculer des délais juridiques ?',
     'Seulement comme aide approximative. Les délais juridiques suivent leurs propres règles ; ne vous fiez pas uniquement à ce calculateur.'),
]

WORDCOUNT['days_de'] = tool_page(
    'days', 'de', 'Tage zwischen zwei Daten: Kalender- und Arbeitstage',
    'Tage zwischen zwei Daten berechnen: Kalendertage, Arbeitstage Montag bis Freitag und Wochen. Optional ohne 1.1., 1.8. und 25.12.',
    'Tage zwischen zwei Daten', 'Kalendertage, Arbeitstage von Montag bis Freitag und Wochen zwischen zwei Daten berechnen.',
    days_tool('de'), DAYS_ART_DE, DAYS_FAQ_DE, [], 'UtilitiesApplication')
WORDCOUNT['days_fr'] = tool_page(
    'days', 'fr', 'Jours entre deux dates : calendaires et ouvrés',
    'Calculez les jours entre deux dates : jours calendaires, jours ouvrés du lundi au vendredi et semaines. En option sans 1.1, 1.8 et 25.12.',
    'Jours entre deux dates', 'Jours calendaires, jours ouvrés du lundi au vendredi et semaines entre deux dates.',
    days_tool('fr'), DAYS_ART_FR, DAYS_FAQ_FR, [], 'UtilitiesApplication')

# =====================================================================
# 4. Home pages
# =====================================================================
def home(lang):
    if lang == 'de':
        body = f'''<h1>Schweizer Rechner</h1>
<p class="lead">Einfache Online-Rechner für den Alltag in der Schweiz: Arbeitszeit, Lohn, Prozent, Mehrwertsteuer, Datum und IBAN.</p>
<ul class="cards">{''.join(f'<li><a href="{u}"><strong>{n}</strong>{d}</a></li>' for u, n, d in TOOLS['de'])}</ul>
<h2>Was diese Seite ist</h2>
<p>Diese Seite sammelt kleine Rechner für Fragen, die im Schweizer Berufsalltag immer wieder vorkommen: Wie viele Stunden habe ich diese Woche gearbeitet? War meine Pause lang genug? Wie viel Mehrwertsteuer steckt in einer Rechnung? Um wie viel Prozent ist ein Preis gestiegen? Was ist mein Monatslohn pro Stunde wert? Stimmt diese IBAN?</p>
<p>Jeder Rechner erklärt die Formel, zeigt ein Beispiel in Franken und beantwortet häufige Fragen. Gesetzliche Werte wie MWST-Sätze oder Mindestpausen stammen aus offiziellen Quellen des Bundes, die auf der jeweiligen Seite verlinkt sind.</p>
<h2>Ihre Daten bleiben bei Ihnen</h2>
<p>Alle Berechnungen laufen direkt in Ihrem Browser. Es werden keine Eingaben übermittelt oder gespeichert, und die Seite setzt keine Cookies. Mehr dazu in der <a href="/de/datenschutz/">Datenschutzerklärung</a>.</p>
<p>Die Seite gibt es auch auf <a href="/fr/" hreflang="fr-CH" lang="fr-CH">Französisch</a>.</p>
<p class="stand">{STAND['de']}</p>'''
        title, desc = 'Schweizer Rechner: Arbeitszeit, Lohn, MWST, IBAN', 'Kostenlose Rechner für die Schweiz: Arbeitszeit nach ArG, Stundenlohn, Prozent, MWST, Tage zwischen Daten und IBAN-Prüfung. Ohne Cookies.'
    else:
        body = f'''<h1>Calculateurs suisses</h1>
<p class="lead">Des calculateurs simples pour le quotidien en Suisse : heures de travail, salaire, pourcentages, TVA, dates et IBAN.</p>
<ul class="cards">{''.join(f'<li><a href="{u}"><strong>{n}</strong>{d}</a></li>' for u, n, d in TOOLS['fr'])}</ul>
<h2>À propos de ce site</h2>
<p>Ce site réunit de petits calculateurs pour des questions qui reviennent sans cesse dans la vie professionnelle en Suisse : combien d’heures ai-je travaillé cette semaine ? Ma pause était-elle assez longue ? Quelle TVA contient cette facture ? De combien de pour cent un prix a-t-il augmenté ? Combien vaut mon salaire mensuel à l’heure ? Cette IBAN est-elle correcte ?</p>
<p>Chaque calculateur explique la formule, donne un exemple en francs et répond aux questions fréquentes. Les valeurs légales, comme les taux de TVA ou les pauses minimales, proviennent de sources officielles de la Confédération, citées sur chaque page.</p>
<h2>Vos données restent chez vous</h2>
<p>Tous les calculs se font directement dans votre navigateur. Aucune saisie n’est transmise ni enregistrée, et le site n’utilise pas de cookies. Plus de détails dans la <a href="/fr/confidentialite/">politique de confidentialité</a>.</p>
<p>Le site existe aussi en <a href="/de/" hreflang="de-CH" lang="de-CH">allemand</a>.</p>
<p class="stand">{STAND['fr']}</p>'''
        title, desc = 'Calculateurs suisses : heures, salaire, TVA, IBAN', 'Calculateurs gratuits pour la Suisse : heures de travail selon la LTr, salaire horaire, pourcentage, TVA, jours entre dates et IBAN. Sans cookies.'
    path = PAIRS['home'][0 if lang == 'de' else 1]
    ld = {'@context': 'https://schema.org', '@type': 'WebSite', 'name': SITE[lang], 'url': BASE + path,
          'inLanguage': 'de-CH' if lang == 'de' else 'fr-CH'}
    page('home', lang, title, desc, body, ld)

home('de'); home('fr')

# =====================================================================
# 5. Legal pages
# =====================================================================
page('imp', 'de', 'Impressum – Schweizer Rechner', 'Impressum von Schweizer Rechner: Betreiber, Adresse und Kontakt.', f'''<h1>Impressum</h1>
<h2>Betreiber</h2>
<p>Thibaut Keller<br>Route des Riaux 1<br>1782 Lossy<br>Schweiz</p>
<h2>Kontakt</h2>
<p>E-Mail: <a href="mailto:kontakt@schweizer-rechner.ch">kontakt@schweizer-rechner.ch</a></p>
<h2>Haftung</h2>
<p>Die Rechner und Texte werden sorgfältig erstellt. Trotzdem kann keine Gewähr für Richtigkeit, Vollständigkeit und Aktualität übernommen werden. Die Ergebnisse ersetzen keine Rechts-, Steuer- oder Treuhandberatung.</p>
<h2>Links auf andere Websites</h2>
<p>Für Inhalte von verlinkten externen Seiten sind ausschliesslich deren Betreiber verantwortlich.</p>
<p class="stand">{STAND['de']}</p>''', crumbs='Impressum')

page('imp', 'fr', 'Mentions légales – Calculateurs suisses', 'Mentions légales de Calculateurs suisses : exploitant, adresse et contact.', f'''<h1>Mentions légales</h1>
<h2>Exploitant</h2>
<p>Thibaut Keller<br>Route des Riaux 1<br>1782 Lossy<br>Suisse</p>
<h2>Contact</h2>
<p>E-mail : <a href="mailto:kontakt@schweizer-rechner.ch">kontakt@schweizer-rechner.ch</a></p>
<h2>Responsabilité</h2>
<p>Les calculateurs et les textes sont rédigés avec soin. Aucune garantie n’est toutefois donnée quant à leur exactitude, leur exhaustivité ou leur actualité. Les résultats ne remplacent pas un conseil juridique, fiscal ou fiduciaire.</p>
<h2>Liens vers d’autres sites</h2>
<p>Les exploitants des sites externes liés sont seuls responsables de leur contenu.</p>
<p class="stand">{STAND['fr']}</p>''', crumbs='Mentions légales')

page('priv', 'de', 'Datenschutzerklärung – Schweizer Rechner', 'Datenschutz bei Schweizer Rechner: keine Cookies, keine Tracker, alle Berechnungen nur im Browser.', f'''<h1>Datenschutzerklärung</h1>
<h2>Verantwortlich</h2>
<p>Thibaut Keller, Route des Riaux 1, 1782 Lossy, Schweiz. E-Mail: <a href="mailto:kontakt@schweizer-rechner.ch">kontakt@schweizer-rechner.ch</a></p>
<h2>Grundsatz</h2>
<p>Diese Website ist so gebaut, dass möglichst wenige Personendaten anfallen. Sie richtet sich nach dem Schweizer Bundesgesetz über den Datenschutz (DSG).</p>
<h2>Berechnungen</h2>
<p>Alle Rechner laufen ausschliesslich in Ihrem Browser. Ihre Eingaben (Zeiten, Beträge, Prozentwerte) werden nicht an uns oder an Dritte übermittelt und nicht gespeichert.</p>
<h2>Cookies und Tracking</h2>
<p>Die Website setzt derzeit keine Cookies und verwendet keine Analyse- oder Tracking-Werkzeuge.</p>
<h2>Hosting und Server-Logdaten</h2>
<p>Die Website wird bei GitHub Pages (GitHub Inc., USA) gehostet. Beim Aufruf einer Seite kann der Hosting-Anbieter technisch notwendige Daten verarbeiten, zum Beispiel IP-Adresse, Datum und Uhrzeit, aufgerufene Seite und Browsertyp. Diese Daten dienen dem sicheren Betrieb der Website.</p>
<h2>Geplant: Werbung mit Google AdSense</h2>
<p>Es ist geplant, die Website künftig mit Werbung über Google AdSense zu finanzieren. Google kann dabei eigene Cookies und ähnliche Technologien einsetzen. Bevor Werbung eingebunden wird, wird diese Datenschutzerklärung angepasst und, wo nötig, ein Einwilligungsbanner eingerichtet, mit dem Sie selbst entscheiden können.</p>
<h2>E-Mail-Kontakt</h2>
<p>Wenn Sie uns per E-Mail schreiben, verwenden wir Ihre Angaben nur, um Ihre Anfrage zu beantworten.</p>
<h2>Ihre Rechte</h2>
<p>Sie können Auskunft über Ihre Daten verlangen sowie deren Berichtigung oder Löschung beantragen. Schreiben Sie dazu an die oben genannte E-Mail-Adresse.</p>
<p class="stand">{STAND['de']}</p>''', crumbs='Datenschutz')

page('priv', 'fr', 'Politique de confidentialité – Calculateurs suisses', 'Confidentialité sur Calculateurs suisses : pas de cookies, pas de traceurs, tous les calculs dans le navigateur.', f'''<h1>Politique de confidentialité</h1>
<h2>Responsable</h2>
<p>Thibaut Keller, Route des Riaux 1, 1782 Lossy, Suisse. E-mail : <a href="mailto:kontakt@schweizer-rechner.ch">kontakt@schweizer-rechner.ch</a></p>
<h2>Principe</h2>
<p>Ce site est conçu pour traiter le moins possible de données personnelles. Il suit la loi fédérale suisse sur la protection des données (LPD).</p>
<h2>Calculs</h2>
<p>Tous les calculateurs fonctionnent uniquement dans votre navigateur. Vos saisies (horaires, montants, pourcentages) ne sont transmises ni à nous ni à des tiers, et ne sont pas enregistrées.</p>
<h2>Cookies et suivi</h2>
<p>Le site n’utilise actuellement aucun cookie ni aucun outil d’analyse ou de suivi.</p>
<h2>Hébergement et journaux du serveur</h2>
<p>Le site est hébergé chez GitHub Pages (GitHub Inc., USA). Lors de la consultation d’une page, l’hébergeur peut traiter des données techniquement nécessaires, par exemple l’adresse IP, la date et l’heure, la page consultée et le type de navigateur. Ces données servent au fonctionnement sûr du site.</p>
<h2>Prévu : publicité avec Google AdSense</h2>
<p>Il est prévu de financer le site à l’avenir par de la publicité via Google AdSense. Google peut alors utiliser ses propres cookies et technologies similaires. Avant l’intégration de publicités, cette politique sera mise à jour et, si nécessaire, une bannière de consentement sera mise en place pour vous laisser choisir.</p>
<h2>Contact par e-mail</h2>
<p>Si vous nous écrivez par e-mail, nous utilisons vos données uniquement pour répondre à votre demande.</p>
<h2>Vos droits</h2>
<p>Vous pouvez demander l’accès à vos données ainsi que leur rectification ou leur effacement en écrivant à l’adresse e-mail ci-dessus.</p>
<p class="stand">{STAND['fr']}</p>''', crumbs='Confidentialité')

page('contact', 'de', 'Kontakt – Schweizer Rechner', 'Kontakt zu Schweizer Rechner: Fragen, Fehlerhinweise und Vorschläge für neue Rechner per E-Mail.', f'''<h1>Kontakt</h1>
<p>Haben Sie einen Fehler gefunden, eine Frage zu einer Berechnung oder einen Vorschlag für einen neuen Rechner? Schreiben Sie uns eine E-Mail:</p>
<p><a href="mailto:kontakt@schweizer-rechner.ch">kontakt@schweizer-rechner.ch</a></p>
<p>Bitte beachten Sie: Wir können keine individuelle Rechts- oder Steuerberatung leisten.</p>''', crumbs='Kontakt')

page('contact', 'fr', 'Contact – Calculateurs suisses', 'Contacter Calculateurs suisses : questions, erreurs signalées et idées de nouveaux calculateurs par e-mail.', f'''<h1>Contact</h1>
<p>Vous avez trouvé une erreur, une question sur un calcul ou une idée de nouveau calculateur ? Écrivez-nous :</p>
<p><a href="mailto:kontakt@schweizer-rechner.ch">kontakt@schweizer-rechner.ch</a></p>
<p>Veuillez noter que nous ne pouvons pas fournir de conseil juridique ou fiscal individuel.</p>''', crumbs='Contact')

# =====================================================================
# Write files
# =====================================================================
for path, doc, _, _ in ALL_PAGES:
    out = ROOT / path.lstrip('/') / 'index.html'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding='utf-8')

# Root redirect
(ROOT / 'index.html').write_text(f'''<!DOCTYPE html>
<html lang="de-CH">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Schweizer Rechner – Calculateurs suisses</title>
<meta name="description" content="Rechner für Arbeitszeit, Prozent und MWST in der Schweiz. Calculateurs suisses pour heures de travail, pourcentage et TVA.">
<link rel="canonical" href="{BASE}/de/">
<link rel="alternate" hreflang="de-CH" href="{BASE}/de/">
<link rel="alternate" hreflang="fr-CH" href="{BASE}/fr/">
<link rel="alternate" hreflang="x-default" href="{BASE}/de/">
<meta http-equiv="refresh" content="0; url=/de/">
<link rel="icon" type="image/svg+xml" href="{FAVICON_URI}">
<link rel="stylesheet" href="/style.css">
</head>
<body>
<main class="wrap">
<p>Weiter zu <a href="/de/">Schweizer Rechner (Deutsch)</a> · <a href="/fr/" lang="fr-CH">Calculateurs suisses (français)</a></p>
</main>
</body>
</html>
''', encoding='utf-8')

# 404
(ROOT / '404.html').write_text(f'''<!DOCTYPE html>
<html lang="de-CH">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Seite nicht gefunden – Page introuvable</title>
<meta name="description" content="Diese Seite existiert nicht. Cette page n’existe pas.">
<meta name="robots" content="noindex">
<link rel="icon" type="image/svg+xml" href="{FAVICON_URI}">
<link rel="stylesheet" href="/style.css">
</head>
<body>
<header class="site-header"><div class="wrap"><a class="brand" href="/de/">{LOGO}<span>Schweizer Rechner</span></a></div></header>
<main id="main" class="wrap">
<h1>Seite nicht gefunden</h1>
<p>Die gesuchte Seite existiert nicht oder wurde verschoben. Zur <a href="/de/">Startseite</a>.</p>
<h2 lang="fr-CH">Page introuvable</h2>
<p lang="fr-CH">La page demandée n’existe pas ou a été déplacée. Vers la <a href="/fr/">page d’accueil</a>.</p>
</main>
</body>
</html>
''', encoding='utf-8')

(ROOT / 'favicon.svg').write_text(FAVICON_SVG + '\n', encoding='utf-8')
(ROOT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n', encoding='utf-8')

# Sitemap with hreflang alternates
urls = []
for key, (de, fr) in PAIRS.items():
    for p in (de, fr):
        urls.append(f'''  <url>
    <loc>{BASE}{p}</loc>
    <lastmod>2026-11-24</lastmod>
    <xhtml:link rel="alternate" hreflang="de-CH" href="{BASE}{de}"/>
    <xhtml:link rel="alternate" hreflang="fr-CH" href="{BASE}{fr}"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="{BASE}{de}"/>
  </url>''')
(ROOT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
    + '\n'.join(urls) + '\n</urlset>\n', encoding='utf-8')

for k, v in WORDCOUNT.items():
    print(f'{k}: {v} words')
print(len(ALL_PAGES), 'pages + index.html + 404.html')
