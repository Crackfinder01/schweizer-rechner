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
    'net': ('/de/brutto-netto-rechner/', '/fr/salaire-brut-net-suisse/'),
    'rent': ('/de/mietzinsrechner/', '/fr/calcul-loyer-taux-reference/'),
    'cv': ('/de/lebenslauf-schweiz/', '/fr/cv-suisse/'),
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
           ('/de/brutto-netto-rechner/', 'Brutto-Netto-Rechner', 'Nettolohn 2026 nach AHV/IV/EO, ALV, NBU und Pensionskasse, ohne Quellensteuer.'),
           ('/de/stundenlohn-rechner/', 'Stundenlohn-Rechner', 'Monatslohn in Stundenlohn umrechnen und umgekehrt, mit 12 oder 13 Löhnen.'),
           ('/de/mietzinsrechner/', 'Mietzinsrechner', 'Mietzinssenkung oder -erhöhung nach Referenzzinssatz, Teuerung und Kosten.'),
           ('/de/tage-zwischen-zwei-daten/', 'Tage zwischen zwei Daten', 'Kalendertage, Arbeitstage Montag bis Freitag und Wochen.'),
           ('/de/iban-pruefen/', 'IBAN prüfen', 'Länge und Prüfziffer einer IBAN offline prüfen, QR-IBAN erkennen.'),
           ('/de/lebenslauf-schweiz/', 'Lebenslauf Schweiz', 'Lebenslauf nach Schweizer Standard erstellen und prüfen, als A4-PDF.')],
    'fr': [('/fr/calcul-heures-travail/', 'Calcul des heures de travail', 'Heures par jour et par semaine, pauses selon la loi sur le travail, horaires de nuit.'),
           ('/fr/calcul-pourcentage/', 'Calcul de pourcentage', 'Pourcentage d’un montant, part en %, variation, montant plus ou moins %.'),
           ('/fr/calcul-tva-suisse/', 'Calcul de la TVA suisse', 'Ajouter ou extraire la TVA, avec arrondi à 5 centimes.'),
           ('/fr/salaire-brut-net-suisse/', 'Salaire brut-net', 'Salaire net 2026 après AVS/AI/APG, AC, AANP et LPP, sans impôt à la source.'),
           ('/fr/calcul-salaire-horaire/', 'Calcul du salaire horaire', 'Salaire mensuel en salaire horaire et inversement, avec 12 ou 13 salaires.'),
           ('/fr/calcul-loyer-taux-reference/', 'Loyer et taux de référence', 'Baisse ou hausse de loyer selon le taux de référence, le renchérissement et les coûts.'),
           ('/fr/calcul-jours-entre-deux-dates/', 'Jours entre deux dates', 'Jours calendaires, jours ouvrés du lundi au vendredi et semaines.'),
           ('/fr/verifier-iban/', 'Vérifier une IBAN', 'Longueur et clé de contrôle d’une IBAN hors ligne, détection de la QR-IBAN.'),
           ('/fr/cv-suisse/', 'CV suisse', 'Créer et vérifier un CV aux normes suisses, en PDF A4.')],
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
    js = (f'<script type="module" src="{script if isinstance(script, str) else "/js/ui.js"}"></script>\n' if script else '')
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
<script defer src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{{"token": "c6c40acee4024671ab11eac33bb28de7"}}'></script>
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


def tool_page(key, lang, title, desc, h1, lead, tool_html, article, faq, sources, category, stand_extra='', script=True):
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
{src}<p class="stand">{STAND[lang]}{stand_extra}</p>
{AD2}
{other_tools(lang, path)}'''
    page(key, lang, title, desc, body, jsonld_tool(lang, BASE + path, h1, desc, faq, category),
         script=script, crumbs=h1)
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
    iban_tool('de'), IBAN_ART_DE, IBAN_FAQ_DE, [], 'FinanceApplication',
    ' · Quelle QR-IID (30000–31999): <a href="https://www.six-group.com/de/products-services/banking-services/payment-standardization/standards/iban.html" rel="noopener">SIX – IBAN überprüfen</a>')
WORDCOUNT['iban_fr'] = tool_page(
    'iban', 'fr', 'Vérifier une IBAN : clé de contrôle et QR-IBAN',
    'Vérifiez une IBAN hors ligne : longueur, clé de contrôle ISO 13616 (modulo 97), groupes de quatre et détection de la QR-IBAN suisse.',
    'Vérifier une IBAN', 'Contrôlez la longueur, les caractères et la clé d’une IBAN – hors ligne, avec détection de la QR-IBAN suisse.',
    iban_tool('fr'), IBAN_ART_FR, IBAN_FAQ_FR, [], 'FinanceApplication',
    ' · Source QR-IID (30000–31999) : <a href="https://www.six-group.com/fr/products-services/banking-services/payment-standardization/standards/iban.html" rel="noopener">SIX – Vérifier un IBAN</a>')

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
# 9. Gross -> net salary (Brutto-Netto)
# =====================================================================
NET_SRC = {
    'ahv_de': 'https://www.ahv-iv.ch/p/2.01.d', 'ahv_fr': 'https://www.ahv-iv.ch/p/2.01.f',
    'alv_de': 'https://www.ahv-iv.ch/p/2.08.d', 'alv_fr': 'https://www.ahv-iv.ch/p/2.08.f',
    'kmu_de': 'https://www.kmu.admin.ch/de/arbeitslosenversicherung-alv', 'kmu_fr': 'https://www.kmu.admin.ch/fr/assurance-chomage-ac',
    'bvg_de': 'https://www.fedlex.admin.ch/eli/cc/1983/797_797_797/de', 'bvg_fr': 'https://www.fedlex.admin.ch/eli/cc/1983/797_797_797/fr',
    'bsv': 'https://www.bsv.admin.ch/dam/de/sd-web/GZplHByBJoFc/Internet_Masszahlenarticles_25_26_d.pdf',
    'uvg_de': 'https://www.fedlex.admin.ch/eli/cc/1982/1676_1676_1676/de', 'uvg_fr': 'https://www.fedlex.admin.ch/eli/cc/1982/1676_1676_1676/fr',
    'uvv_de': 'https://www.fedlex.admin.ch/eli/cc/1983/38_38_38/de', 'uvv_fr': 'https://www.fedlex.admin.ch/eli/cc/1983/38_38_38/fr',
    'suva_de': 'https://www.suva.ch/de-ch/unfall/leistungen-der-suva/geldleistungen', 'suva_fr': 'https://www.suva.ch/fr-ch/accident/prestations-de-la-suva/prestations-en-especes',
    'qst_de': 'https://www.estv.admin.ch/de/quellensteuer', 'qst_fr': 'https://www.estv.admin.ch/fr/impot-a-la-source',
}


def net_tool(lang):
    if lang == 'de':
        L = dict(h='Nettolohn berechnen', amt='Bruttolohn in CHF', per='Betrag ist', pm='pro Monat', py='pro Jahr',
                 sal='Löhne pro Jahr', s12='12 Monatslöhne', s13='13 Monatslöhne', age='Alter im Jahr 2026',
                 age_h='2026 minus Geburtsjahr; nur für die Pensionskasse.', nbu='NBU-Satz in %',
                 nbu_h='Voreinstellung 1.0 %: runder Annahmewert, kein offizieller Durchschnitt. Ihr Satz steht auf der Lohnabrechnung.',
                 bvg='Pensionskasse (BVG)', est='Schätzung nach BVG-Minimum', own='Eigener Satz', bvgp='Eigener Arbeitnehmerbeitrag in % des koordinierten Lohns',
                 ktg='Krankentaggeld (KTG) vom Lohn abziehen', ktgp='KTG-Arbeitnehmeranteil in %', btn='Berechnen')
    else:
        L = dict(h='Calculer le salaire net', amt='Salaire brut en CHF', per='Le montant est', pm='par mois', py='par an',
                 sal='Salaires par an', s12='12 salaires mensuels', s13='13 salaires mensuels', age='Âge atteint en 2026',
                 age_h='2026 moins l’année de naissance ; sert seulement pour la LPP.', nbu='Taux AANP en %',
                 nbu_h='Valeur par défaut 1,0 % : hypothèse arrondie, pas une moyenne officielle. Votre taux figure sur la fiche de salaire.',
                 bvg='Caisse de pension (LPP)', est='Estimation selon le minimum LPP', own='Taux personnel', bvgp='Cotisation salariée en % du salaire coordonné',
                 ktg='Déduire une assurance perte de gain maladie (IJM)', ktgp='Part salariée IJM en %', btn='Calculer')
    return f'''<section class="tool" data-tool="net" aria-labelledby="tool-h">
<h2 id="tool-h">{L['h']}</h2>
<form novalidate>
<div class="row">
<div class="field"><label for="net-amount">{L['amt']}</label><input type="text" inputmode="decimal" id="net-amount" name="amount" value="6500" autocomplete="off"></div>
<div class="field"><label for="net-period">{L['per']}</label><select id="net-period" name="period"><option value="month">{L['pm']}</option><option value="year">{L['py']}</option></select></div>
<div class="field"><label for="net-n">{L['sal']}</label><select id="net-n" name="salaries"><option value="12">{L['s12']}</option><option value="13" selected>{L['s13']}</option></select></div>
</div>
<div class="row top">
<div class="field"><label for="net-age">{L['age']}</label><input type="text" inputmode="numeric" id="net-age" name="age" value="40" autocomplete="off" aria-describedby="net-age-h"><span class="note" id="net-age-h">{L['age_h']}</span></div>
<div class="field"><label for="net-nbu">{L['nbu']}</label><input type="text" inputmode="decimal" id="net-nbu" name="nbuPct" value="1.0" autocomplete="off" aria-describedby="net-nbu-h"><span class="note" id="net-nbu-h">{L['nbu_h']}</span></div>
</div>
<fieldset><legend>{L['bvg']}</legend><div class="choice">
<label><input type="radio" name="bvgMode" value="estimate" checked> {L['est']}</label>
<label><input type="radio" name="bvgMode" value="own"> {L['own']}</label>
</div>
<div class="field"><label for="net-bvg">{L['bvgp']}</label><input type="text" inputmode="decimal" id="net-bvg" name="bvgPct" value="" autocomplete="off" disabled></div>
</fieldset>
<div class="choice field"><label><input type="checkbox" name="ktg"> {L['ktg']}</label></div>
<div class="field"><label for="net-ktg">{L['ktgp']}</label><input type="text" inputmode="decimal" id="net-ktg" name="ktgPct" value="" autocomplete="off" disabled></div>
<button type="submit" class="btn">{L['btn']}</button>
</form>
<div class="result" aria-live="polite"></div>
<noscript><p>JavaScript</p></noscript>
</section>'''


NET_ART_DE = '''<h2>So funktioniert der Rechner</h2>
<p>Geben Sie Ihren Bruttolohn ein und wählen Sie, ob es ein Monats- oder ein Jahreslohn ist. Bei einem Monatslohn legen Sie fest, ob Sie ihn 12- oder 13-mal im Jahr erhalten. Das Alter braucht der Rechner nur für die Pensionskasse: Massgebend ist das Alter, das Sie im Jahr 2026 erreichen, also 2026 minus Ihr Geburtsjahr. Den Satz der Nichtberufsunfallversicherung (NBU) können Sie ändern, ebenso den Pensionskassenbeitrag und ein allfälliges Krankentaggeld (KTG). Der Rechner zeigt jeden Abzug pro Lohnzahlung und pro Jahr. Pro Lohnzahlung heisst: Jahresbetrag geteilt durch die Anzahl Löhne.</p>
<h2>Die Lohnabzüge 2026 im Überblick</h2>
<table class="data-table">
<thead><tr><th scope="col">Abzug</th><th scope="col">Anteil Arbeitnehmende</th><th scope="col">Berechnet auf</th></tr></thead>
<tbody>
<tr><td>AHV/IV/EO</td><td>5.3 % (AHV 4.35 %, IV 0.7 %, EO 0.25 %)</td><td>ganzer Lohn, ohne Obergrenze</td></tr>
<tr><td>Arbeitslosenversicherung (ALV)</td><td>1.1 %</td><td>Lohn bis CHF 148'200 pro Jahr</td></tr>
<tr><td>Nichtberufsunfall (NBU)</td><td>je nach Versicherer</td><td>Lohn bis CHF 148'200 pro Jahr</td></tr>
<tr><td>Pensionskasse (BVG)</td><td>je nach Pensionskasse</td><td>koordinierter Lohn</td></tr>
<tr><td>Krankentaggeld (KTG)</td><td>nur wenn vereinbart</td><td>je nach Vertrag</td></tr>
</tbody>
</table>
<p>Die Arbeitgeberin bezahlt bei AHV/IV/EO und ALV noch einmal gleich viel wie Sie. Diese Arbeitgeberbeiträge sind kein Abzug von Ihrem Lohn und erscheinen deshalb nicht im Ergebnis. Auf dem Lohnanteil über CHF 148'200 wird seit dem 1. Januar 2023 keine ALV mehr erhoben.</p>
<h2>Formeln</h2>
<p class="formula">AHV/IV/EO = Jahreslohn × 5.3 %<br>ALV = min(Jahreslohn; 148'200) × 1.1 %<br>NBU = min(Jahreslohn; 148'200) × NBU-Satz<br>Koordinierter Lohn = min(Jahreslohn; 90'720) − 26'460, mindestens 3'780<br>BVG (Schätzung) = koordinierter Lohn × Altersgutschrift ÷ 2<br>Nettolohn = Bruttolohn − alle Abzüge</p>
<h2>Pensionskasse: bewusst nur eine Schätzung</h2>
<p>Obligatorisch versichert sind Arbeitnehmende mit einem Jahreslohn von mehr als CHF 22'680 bei einer Arbeitgeberin (Art. 2 und 7 BVG). Versichert ist der koordinierte Lohn, also der Teil des Jahreslohns von CHF 26'460 bis CHF 90'720; ist er kleiner als CHF 3'780, wird er auf diesen Betrag aufgerundet (Art. 8 BVG). Ab dem Jahr, in dem Sie 25 werden, erhalten Sie Altersgutschriften: 7 % des koordinierten Lohns von 25 bis 34 Jahren, 10 % von 35 bis 44, 15 % von 45 bis 54 und 18 % von 55 bis 65 (Art. 16 BVG). Die Arbeitgeberin muss mindestens die Hälfte der Beiträge tragen (Art. 66 BVG). Der Rechner nimmt deshalb an, dass Sie genau die Hälfte der Altersgutschrift selbst bezahlen.</p>
<p><strong>Ihre echte Pensionskasse rechnet fast immer anders.</strong> Viele Kassen versichern mehr als das gesetzliche Minimum, verwenden einen anderen Koordinationsabzug, teilen die Beiträge anders auf oder verlangen zusätzlich Risikobeiträge und Verwaltungskosten, die hier fehlen. Den genauen Betrag finden Sie auf Ihrer Lohnabrechnung oder im Vorsorgeausweis. Kennen Sie den Prozentsatz Ihrer Kasse, wählen Sie «Eigener Satz»; er wird ebenfalls auf den koordinierten Lohn nach BVG-Minimum angewendet.</p>
<h2>NBU und Krankentaggeld</h2>
<p>Die Prämie für Nichtberufsunfälle geht nach Art. 91 UVG zulasten der Arbeitnehmenden, ausser es ist etwas Günstigeres vereinbart. Den Satz legt der Unfallversicherer Ihrer Arbeitgeberin fest; er ist von Betrieb zu Betrieb verschieden. Die Voreinstellung von 1.0 % ist deshalb nur ein runder Annahmewert, kein offizieller Durchschnitt: Ersetzen Sie ihn durch den Satz auf Ihrer Lohnabrechnung. Die Prämie wird höchstens auf CHF 148'200 Jahreslohn erhoben, dem Höchstbetrag des versicherten Verdienstes (Art. 22 UVV). Wer bei einer Arbeitgeberin weniger als acht Stunden pro Woche arbeitet, ist dort nicht gegen Nichtberufsunfälle versichert (Art. 13 UVV); setzen Sie dann 0 ein. Ein Krankentaggeld ist nicht obligatorisch. Zieht Ihre Arbeitgeberin einen Teil der Prämie vom Lohn ab, aktivieren Sie die Option und tragen Sie diesen Satz ein.</p>
<h2>Warum die Quellensteuer nicht abgezogen wird</h2>
<p>Der angezeigte Nettolohn ist der Lohn vor Steuern. Wer das Schweizer Bürgerrecht oder die Niederlassungsbewilligung C hat, zahlt die Einkommenssteuer über die Steuererklärung; sie wird nicht vom Lohn abgezogen. Bei Personen mit Wohnsitz in der Schweiz ohne Ausweis C und bei Personen ohne Wohnsitz in der Schweiz, zum Beispiel Grenzgängerinnen und Grenzgängern, zieht die Arbeitgeberin dagegen die Quellensteuer direkt vom Lohn ab. Der Tarif ist kantonsabhängig und hängt zudem von der persönlichen Situation ab. Ein einziger Satz für die ganze Schweiz wäre falsch; den richtigen Tarif erhalten Sie bei der Steuerverwaltung Ihres Kantons.</p>
<h2>Beispiele</h2>
<p><strong>Monatslohn CHF 6'500, 13-mal, Alter 40, NBU 1.0 %.</strong> Jahreslohn: 6'500 × 13 = CHF 84'500. AHV/IV/EO: 84'500 × 5.3 % = CHF 4'478.50. ALV: 84'500 × 1.1 % = CHF 929.50. NBU: CHF 845.00. Koordinierter Lohn: 84'500 − 26'460 = CHF 58'040; Altersgutschrift 10 %, davon die Hälfte: 58'040 × 5 % = CHF 2'902.00. Abzüge total CHF 9'155.00, Nettolohn CHF 75'345.00 pro Jahr oder CHF 5'795.77 pro Lohnzahlung.</p>
<p><strong>Monatslohn CHF 15'000, 12-mal, Alter 50.</strong> Die ALV wird nur auf CHF 148'200 erhoben: CHF 1'630.20 pro Jahr oder CHF 135.85 pro Monat. Der koordinierte Lohn erreicht sein Maximum von CHF 64'260. Mit AHV/IV/EO von CHF 795.00, NBU von CHF 123.50 und der BVG-Schätzung von CHF 401.63 bleiben CHF 13'544.02 netto pro Monat.</p>
<p><strong>Teilzeit mit CHF 1'800 pro Monat, 12-mal.</strong> Der Jahreslohn von CHF 21'600 liegt nicht über der Eintrittsschwelle von CHF 22'680, es gibt also keinen obligatorischen BVG-Abzug. Netto bleiben CHF 1'666.80 pro Monat.</p>'''

NET_FAQ_DE = [
    ('Ist das Ergebnis der Betrag, der auf meinem Konto landet?',
     'Nur ungefähr. Abweichen können vor allem der Pensionskassenbeitrag, der NBU-Satz, ein Krankentaggeld und die Quellensteuer. Familienzulagen, Spesen oder andere Zulagen kommen auf der Lohnabrechnung oft noch dazu.'),
    ('Werden auch auf dem 13. Monatslohn Abzüge gemacht?',
     'Ja. AHV/IV/EO, ALV und NBU werden auch auf dem 13. Monatslohn erhoben, und er zählt für die BVG-Eintrittsschwelle zum Jahreslohn. Der Rechner verteilt alle Abzüge gleichmässig auf die Lohnzahlungen; manche Pensionskassen ziehen ihren Beitrag nur zwölfmal ab.'),
    ('Warum zahle ich über CHF 148\'200 keine ALV mehr?',
     'Seit dem 1. Januar 2023 werden auf dem Lohnanteil über CHF 148\'200 pro Jahr keine ALV-Beiträge mehr erhoben. Der Rechner berücksichtigt das automatisch.'),
    ('Was ist der koordinierte Lohn?',
     'Der Teil des Jahreslohns, der in der Pensionskasse obligatorisch versichert ist: Jahreslohn bis höchstens CHF 90\'720 minus Koordinationsabzug von CHF 26\'460, mindestens CHF 3\'780. Bei CHF 84\'500 Jahreslohn sind es CHF 58\'040.'),
    ('Ich bin unter 25. Zahle ich in die Pensionskasse?',
     'Ab dem 1. Januar nach dem 17. Geburtstag sind Sie für Tod und Invalidität versichert, das Alterssparen beginnt ab dem 1. Januar nach dem 24. Geburtstag (Art. 7 BVG). Vor 25 rechnet der Rechner deshalb keinen Sparbeitrag; Risikobeiträge Ihrer Kasse kommen allenfalls dazu.'),
    ('Werden meine Angaben gespeichert?',
     'Nein. Die Berechnung läuft nur in Ihrem Browser. Ihr Lohn wird weder übermittelt noch gespeichert.'),
]

NET_ART_FR = '''<h2>Mode d’emploi</h2>
<p>Saisissez votre salaire brut et indiquez s’il s’agit d’un salaire mensuel ou annuel. Pour un salaire mensuel, choisissez s’il est versé 12 ou 13 fois par an. L’âge ne sert qu’à la caisse de pension : c’est l’âge que vous atteignez en 2026, soit 2026 moins votre année de naissance. Vous pouvez modifier le taux de l’assurance contre les accidents non professionnels (AANP), la cotisation de caisse de pension et une éventuelle assurance perte de gain maladie (indemnités journalières, IJM). Le calculateur affiche chaque déduction par versement et par an. Par versement signifie : montant annuel divisé par le nombre de salaires.</p>
<h2>Les déductions 2026 en bref</h2>
<table class="data-table">
<thead><tr><th scope="col">Déduction</th><th scope="col">Part salariée</th><th scope="col">Calculée sur</th></tr></thead>
<tbody>
<tr><td>AVS/AI/APG</td><td>5,3 % (AVS 4,35 %, AI 0,7 %, APG 0,25 %)</td><td>tout le salaire, sans plafond</td></tr>
<tr><td>Assurance-chômage (AC)</td><td>1,1 %</td><td>salaire jusqu’à CHF 148'200 par an</td></tr>
<tr><td>Accidents non professionnels (AANP)</td><td>selon l’assureur</td><td>salaire jusqu’à CHF 148'200 par an</td></tr>
<tr><td>Caisse de pension (LPP)</td><td>selon la caisse</td><td>salaire coordonné</td></tr>
<tr><td>Perte de gain maladie (IJM)</td><td>seulement si convenu</td><td>selon le contrat</td></tr>
</tbody>
</table>
<p>Pour l’AVS/AI/APG et l’AC, l’employeur paie encore une fois le même montant que vous. Ces cotisations patronales ne sont pas retenues sur votre salaire et n’apparaissent donc pas dans le résultat. Depuis le 1er janvier 2023, aucune cotisation AC n’est prélevée sur la part du salaire qui dépasse CHF 148'200.</p>
<h2>Formules</h2>
<p class="formula">AVS/AI/APG = salaire annuel × 5,3 %<br>AC = min(salaire annuel ; 148'200) × 1,1 %<br>AANP = min(salaire annuel ; 148'200) × taux AANP<br>Salaire coordonné = min(salaire annuel ; 90'720) − 26'460, au moins 3'780<br>LPP (estimation) = salaire coordonné × bonification de vieillesse ÷ 2<br>Salaire net = salaire brut − toutes les déductions</p>
<h2>Caisse de pension : volontairement une estimation</h2>
<p>Sont assurés obligatoirement les salariés qui touchent d’un même employeur un salaire annuel supérieur à CHF 22'680 (art. 2 et 7 LPP). Le salaire assuré est le salaire coordonné, c’est-à-dire la part du salaire annuel comprise entre CHF 26'460 et CHF 90'720 ; s’il est inférieur à CHF 3'780, il est arrondi à ce montant (art. 8 LPP). Dès l’année de vos 25 ans, la caisse crédite des bonifications de vieillesse : 7 % du salaire coordonné de 25 à 34 ans, 10 % de 35 à 44 ans, 15 % de 45 à 54 ans et 18 % de 55 à 65 ans (art. 16 LPP). L’employeur doit payer au moins la moitié des cotisations (art. 66 LPP). Le calculateur suppose donc que vous payez exactement la moitié de la bonification.</p>
<p><strong>Votre vraie caisse de pension calcule presque toujours autrement.</strong> Beaucoup de caisses assurent plus que le minimum légal, utilisent une autre déduction de coordination, répartissent les cotisations autrement ou prélèvent en plus des cotisations de risque et des frais, qui ne sont pas comptés ici. Le montant exact figure sur votre fiche de salaire ou votre certificat de prévoyance. Si vous connaissez le taux de votre caisse, choisissez «Taux personnel» ; il est lui aussi appliqué au salaire coordonné selon le minimum LPP.</p>
<h2>AANP et perte de gain maladie</h2>
<p>Selon l’art. 91 LAA, la prime pour les accidents non professionnels est à la charge du salarié, sauf accord plus favorable. Le taux est fixé par l’assureur-accidents de l’employeur et varie d’une entreprise à l’autre. La valeur par défaut de 1,0 % n’est donc qu’une hypothèse arrondie, pas une moyenne officielle : remplacez-la par le taux de votre fiche de salaire. La prime est prélevée au plus sur CHF 148'200 de salaire annuel, le montant maximal du gain assuré (art. 22 OLAA). Une personne qui travaille moins de huit heures par semaine chez un employeur n’y est pas assurée contre les accidents non professionnels (art. 13 OLAA) ; saisissez alors 0. L’assurance perte de gain maladie n’est pas obligatoire. Si votre employeur retient une partie de la prime sur le salaire, cochez l’option et saisissez ce taux.</p>
<h2>Pourquoi l’impôt à la source n’est pas déduit</h2>
<p>Le salaire net affiché est un salaire avant impôts. Les personnes de nationalité suisse ou titulaires d’un permis d’établissement C paient l’impôt sur le revenu par la déclaration d’impôt ; il n’est pas retenu sur le salaire. Pour les personnes domiciliées en Suisse sans permis C et pour les personnes sans domicile en Suisse, par exemple les frontaliers, l’employeur retient en revanche l’impôt à la source directement sur le salaire. Le barème dépend du canton et de la situation personnelle. Un taux unique pour toute la Suisse serait faux ; le bon barème est disponible auprès de l’administration fiscale de votre canton.</p>
<h2>Exemples</h2>
<p><strong>Salaire mensuel de CHF 6'500, 13 fois, 40 ans, AANP 1,0 %.</strong> Salaire annuel : 6'500 × 13 = CHF 84'500. AVS/AI/APG : 84'500 × 5,3 % = CHF 4'478.50. AC : 84'500 × 1,1 % = CHF 929.50. AANP : CHF 845.00. Salaire coordonné : 84'500 − 26'460 = CHF 58'040 ; bonification de 10 %, dont la moitié : 58'040 × 5 % = CHF 2'902.00. Total des déductions CHF 9'155.00, salaire net CHF 75'345.00 par an ou CHF 5'795.77 par versement.</p>
<p><strong>Salaire mensuel de CHF 15'000, 12 fois, 50 ans.</strong> L’AC n’est prélevée que sur CHF 148'200 : CHF 1'630.20 par an, soit CHF 135.85 par mois. Le salaire coordonné atteint son maximum de CHF 64'260. Avec CHF 795.00 d’AVS/AI/APG, CHF 123.50 d’AANP et CHF 401.63 de LPP estimée, il reste CHF 13'544.02 net par mois.</p>
<p><strong>Temps partiel à CHF 1'800 par mois, 12 fois.</strong> Le salaire annuel de CHF 21'600 ne dépasse pas le seuil d’entrée de CHF 22'680 : pas de déduction LPP obligatoire. Il reste CHF 1'666.80 net par mois.</p>'''

NET_FAQ_FR = [
    ('Le résultat est-il le montant versé sur mon compte ?',
     'Seulement approximativement. Peuvent surtout différer la cotisation de caisse de pension, le taux AANP, une assurance perte de gain et l’impôt à la source. Les allocations familiales, frais ou autres suppléments s’ajoutent souvent sur la fiche de salaire.'),
    ('Le 13e salaire subit-il aussi des déductions ?',
     'Oui. L’AVS/AI/APG, l’AC et l’AANP sont aussi prélevées sur le 13e salaire, et il compte dans le salaire annuel pour le seuil d’entrée LPP. Le calculateur répartit toutes les déductions de façon égale sur les versements ; certaines caisses de pension ne prélèvent leur cotisation que 12 fois.'),
    ('Pourquoi ne paie-je plus d’AC au-delà de CHF 148\'200 ?',
     'Depuis le 1er janvier 2023, aucune cotisation AC n’est prélevée sur la part du salaire annuel qui dépasse CHF 148\'200. Le calculateur en tient compte automatiquement.'),
    ('Qu’est-ce que le salaire coordonné ?',
     'La part du salaire annuel assurée obligatoirement dans la caisse de pension : salaire annuel jusqu’à CHF 90\'720 au plus, moins la déduction de coordination de CHF 26\'460, au moins CHF 3\'780. Pour CHF 84\'500 de salaire annuel, cela donne CHF 58\'040.'),
    ('J’ai moins de 25 ans. Est-ce que je cotise à la caisse de pension ?',
     'Dès le 1er janvier qui suit vos 17 ans, vous êtes assuré contre le décès et l’invalidité ; l’épargne vieillesse commence le 1er janvier qui suit vos 24 ans (art. 7 LPP). Avant 25 ans, le calculateur ne compte donc pas de cotisation d’épargne ; des cotisations de risque de votre caisse peuvent s’y ajouter.'),
    ('Mes données sont-elles enregistrées ?',
     'Non. Le calcul se fait uniquement dans votre navigateur. Votre salaire n’est ni transmis ni enregistré.'),
]

NETSRC = {
    'de': [
        f'Informationsstelle AHV/IV, Merkblatt 2.01 «Beiträge an die AHV, IV und EO», Stand 1. Januar 2026: <a href="{NET_SRC["ahv_de"]}">{NET_SRC["ahv_de"]}</a>',
        f'Informationsstelle AHV/IV, Merkblatt 2.08 zur Arbeitslosenversicherung: <a href="{NET_SRC["alv_de"]}">{NET_SRC["alv_de"]}</a>',
        f'KMU-Portal des Bundes, Arbeitslosenversicherung (2.2 % bis CHF 148\'200, kein Solidaritätsbeitrag): <a href="{NET_SRC["kmu_de"]}">{NET_SRC["kmu_de"]}</a>',
        f'Bundesgesetz über die berufliche Vorsorge (BVG), SR 831.40, Art. 2, 7, 8, 16 und 66: <a href="{NET_SRC["bvg_de"]}">{NET_SRC["bvg_de"]}</a>',
        f'Bundesamt für Sozialversicherungen BSV, BVG-Masszahlen 2025 und 2026: <a href="{NET_SRC["bsv"]}">{NET_SRC["bsv"]}</a>',
        f'Bundesgesetz über die Unfallversicherung (UVG), SR 832.20, Art. 91: <a href="{NET_SRC["uvg_de"]}">{NET_SRC["uvg_de"]}</a>',
        f'Verordnung über die Unfallversicherung (UVV), SR 832.202, Art. 13 und 22: <a href="{NET_SRC["uvv_de"]}">{NET_SRC["uvv_de"]}</a>',
        f'Suva, höchstversicherter Jahresverdienst CHF 148\'200: <a href="{NET_SRC["suva_de"]}">{NET_SRC["suva_de"]}</a>',
        f'Eidgenössische Steuerverwaltung ESTV, Quellensteuer: <a href="{NET_SRC["qst_de"]}">{NET_SRC["qst_de"]}</a>',
    ],
    'fr': [
        f'Centre d’information AVS/AI, mémento 2.01 sur les cotisations AVS, AI et APG, état au 1er janvier 2026 : <a href="{NET_SRC["ahv_fr"]}">{NET_SRC["ahv_fr"]}</a>',
        f'Centre d’information AVS/AI, mémento 2.08 sur l’assurance-chômage : <a href="{NET_SRC["alv_fr"]}">{NET_SRC["alv_fr"]}</a>',
        f'Portail PME de la Confédération, assurance-chômage (2,2 % jusqu’à CHF 148\'200, pas de cotisation de solidarité) : <a href="{NET_SRC["kmu_fr"]}">{NET_SRC["kmu_fr"]}</a>',
        f'Loi fédérale sur la prévoyance professionnelle (LPP), RS 831.40, art. 2, 7, 8, 16 et 66 : <a href="{NET_SRC["bvg_fr"]}">{NET_SRC["bvg_fr"]}</a>',
        f'Office fédéral des assurances sociales OFAS, valeurs LPP 2025 et 2026 (document en allemand) : <a href="{NET_SRC["bsv"]}">{NET_SRC["bsv"]}</a>',
        f'Loi fédérale sur l’assurance-accidents (LAA), RS 832.20, art. 91 : <a href="{NET_SRC["uvg_fr"]}">{NET_SRC["uvg_fr"]}</a>',
        f'Ordonnance sur l’assurance-accidents (OLAA), RS 832.202, art. 13 et 22 : <a href="{NET_SRC["uvv_fr"]}">{NET_SRC["uvv_fr"]}</a>',
        f'Suva, gain annuel assuré maximal de CHF 148\'200 : <a href="{NET_SRC["suva_fr"]}">{NET_SRC["suva_fr"]}</a>',
        f'Administration fédérale des contributions AFC, impôt à la source : <a href="{NET_SRC["qst_fr"]}">{NET_SRC["qst_fr"]}</a>',
    ],
}

WORDCOUNT['net_de'] = tool_page(
    'net', 'de', 'Brutto-Netto-Rechner Schweiz 2026: Lohnrechner',
    'Nettolohn aus Bruttolohn berechnen: AHV/IV/EO, ALV, NBU und Pensionskasse (BVG) mit den Werten 2026. 12 oder 13 Löhne, ohne Quellensteuer.',
    'Brutto-Netto-Lohnrechner Schweiz 2026',
    'Vom Bruttolohn zum Nettolohn: alle Lohnabzüge der Arbeitnehmenden mit den Sätzen und Grenzbeträgen 2026 – pro Lohnzahlung und pro Jahr.',
    net_tool('de'), NET_ART_DE, NET_FAQ_DE, NETSRC['de'], 'FinanceApplication')
WORDCOUNT['net_fr'] = tool_page(
    'net', 'fr', 'Salaire brut net Suisse 2026 : calcul du salaire net',
    'Calcul du salaire net en Suisse : AVS/AI/APG, AC, AANP et caisse de pension (LPP) avec les valeurs 2026. 12 ou 13 salaires, sans impôt à la source.',
    'Calcul du salaire brut-net en Suisse (2026)',
    'Du salaire brut au salaire net : toutes les déductions du salarié avec les taux et montants limites 2026 – par versement et par an.',
    net_tool('fr'), NET_ART_FR, NET_FAQ_FR, NETSRC['fr'], 'FinanceApplication')

# =====================================================================
# 10. Rent and reference interest rate (Mietzins / loyer)
# =====================================================================
RENT_SRC = {
    'vmwg_de': 'https://www.fedlex.admin.ch/eli/cc/1990/835_835_835/de', 'vmwg_fr': 'https://www.fedlex.admin.ch/eli/cc/1990/835_835_835/fr',
    'or_de': 'https://www.fedlex.admin.ch/eli/cc/27/317_321_377/de', 'or_fr': 'https://www.fedlex.admin.ch/eli/cc/27/317_321_377/fr',
    'bwo_de': 'https://www.bwo.admin.ch/de/referenzzinssatz', 'bwo_fr': 'https://www.bwo.admin.ch/fr/taux-de-reference',
    'hist_de': 'https://www.bwo.admin.ch/de/entwicklung-referenzzinssatz-und-durchschnittszinssatz',
    'hist_fr': 'https://www.bwo.admin.ch/fr/evolution-du-taux-de-reference-et-du-taux-dinteret-moyen',
    'lik_de': 'https://www.bfs.admin.ch/bfs/de/home/statistiken/preise/landesindex-konsumentenpreise.html',
    'lik_fr': 'https://www.bfs.admin.ch/bfs/fr/home/statistiques/prix/indice-prix-consommation.html',
    'mv': 'https://www.mieterverband.ch', 'asloca': 'https://www.asloca.ch',
}
# BWO history (checked 25.11.2026): [valid from, rate]
REF_HISTORY = [('10.09.2008', '3.50'), ('03.06.2009', '3.25'), ('02.09.2009', '3.00'), ('02.12.2010', '2.75'),
               ('02.12.2011', '2.50'), ('02.06.2012', '2.25'), ('03.09.2013', '2.00'), ('02.06.2015', '1.75'),
               ('02.06.2017', '1.50'), ('03.03.2020', '1.25'), ('02.06.2023', '1.50'), ('02.12.2023', '1.75'),
               ('04.03.2025', '1.50'), ('02.09.2025', '1.25')]
REF_CURRENT = '1.25'


def ref_table(lang):
    fr = lang == 'fr'
    cap = ('Taux de référence publiés par l’Office fédéral du logement (OFL), du plus récent au plus ancien' if fr
           else 'Vom Bundesamt für Wohnungswesen (BWO) publizierte Referenzzinssätze, die neuesten zuerst')
    h1, h2 = ('Valable dès', 'Taux') if fr else ('Gültig ab', 'Satz')
    rows = ''.join(f'<tr><td>{d}</td><td>{r.replace(".", ",") if fr else r} %</td></tr>' for d, r in reversed(REF_HISTORY))
    return (f'<table class="data-table"><caption>{cap}</caption><thead><tr><th scope="col">{h1}</th><th scope="col">{h2}</th></tr></thead>'
            f'<tbody>{rows}</tbody></table>')


def rent_tool(lang):
    fr = lang == 'fr'
    if not fr:
        L = dict(h='Mietzins berechnen', rent='Heutige Nettomiete pro Monat (CHF)', old='Referenzzinssatz, auf dem die Miete beruht',
                 old_h='Steht im Mietvertrag oder in der letzten Mietzinsanpassung.', new='Neuer Referenzzinssatz', cur='aktuell',
                 infl='Teuerung (optional)', infl_h='Landesindex der Konsumentenpreise (LIK) des Bundesamts für Statistik, beide Werte auf derselben Basis.',
                 oi='LIK bei der letzten Anpassung', ni='LIK heute', cost='Allgemeine Kostensteigerung (optional)',
                 cost_h='Nur wenn Ihr Vermieter eine Pauschale geltend macht. Leer lassen = keine.',
                 cp='Pauschale in % pro Jahr', ld='Datum der letzten Mietzinsanpassung', rd='Stichtag der Berechnung', btn='Berechnen')
    else:
        L = dict(h='Calculer le loyer', rent='Loyer net actuel par mois (CHF)', old='Taux de référence sur lequel repose le loyer',
                 old_h='Il figure dans le bail ou dans la dernière adaptation du loyer.', new='Nouveau taux de référence', cur='actuel',
                 infl='Renchérissement (facultatif)', infl_h='Indice suisse des prix à la consommation (IPC) de l’Office fédéral de la statistique, les deux valeurs sur la même base.',
                 oi='IPC lors de la dernière adaptation', ni='IPC aujourd’hui', cost='Hausse générale des coûts (facultatif)',
                 cost_h='Seulement si votre bailleur fait valoir un forfait. Vide = aucun.',
                 cp='Forfait en % par an', ld='Date de la dernière adaptation du loyer', rd='Date du calcul', btn='Calculer')
    rates = [r for _, r in REF_HISTORY]
    uniq = sorted(set(rates), key=float, reverse=True)
    fmt = (lambda r: r.replace('.', ',')) if fr else (lambda r: r)
    opt_old = ''.join(f'<option value="{r}"{" selected" if r == "1.75" else ""}>{fmt(r)} %</option>' for r in uniq)
    opt_new = ''.join(f'<option value="{r}"{" selected" if r == REF_CURRENT else ""}>{fmt(r)} %{" (" + L["cur"] + ")" if r == REF_CURRENT else ""}</option>' for r in uniq)
    return f'''<section class="tool" data-tool="rent" aria-labelledby="tool-h">
<h2 id="tool-h">{L['h']}</h2>
<form novalidate>
<div class="field"><label for="rent-amount">{L['rent']}</label><input type="text" inputmode="decimal" id="rent-amount" name="rent" value="1800" autocomplete="off"></div>
<div class="row top">
<div class="field"><label for="rent-old">{L['old']}</label><select id="rent-old" name="oldRate" aria-describedby="rent-old-h">{opt_old}</select><span class="note" id="rent-old-h">{L['old_h']}</span></div>
<div class="field"><label for="rent-new">{L['new']}</label><select id="rent-new" name="newRate">{opt_new}</select></div>
</div>
<fieldset><legend>{L['infl']}</legend>
<p class="note">{L['infl_h']}</p>
<div class="row">
<div class="field"><label for="rent-oi">{L['oi']}</label><input type="text" inputmode="decimal" id="rent-oi" name="oldIndex" value="" autocomplete="off"></div>
<div class="field"><label for="rent-ni">{L['ni']}</label><input type="text" inputmode="decimal" id="rent-ni" name="newIndex" value="" autocomplete="off"></div>
</div>
</fieldset>
<fieldset><legend>{L['cost']}</legend>
<p class="note">{L['cost_h']}</p>
<div class="row">
<div class="field"><label for="rent-cost">{L['cp']}</label><input type="text" inputmode="decimal" id="rent-cost" name="cost" value="" autocomplete="off"></div>
<div class="field"><label for="rent-last">{L['ld']}</label><input type="date" id="rent-last" name="lastDate" value=""></div>
<div class="field"><label for="rent-ref">{L['rd']}</label><input type="date" id="rent-ref" name="refDate" value=""></div>
</div>
</fieldset>
<button type="submit" class="btn">{L['btn']}</button>
</form>
<div class="result" aria-live="polite"></div>
<noscript><p>JavaScript</p></noscript>
</section>'''


RENT_ART_DE = f'''<h2>So funktioniert der Rechner</h2>
<p>Geben Sie Ihre heutige Nettomiete ein, also die Miete ohne Heiz- und Nebenkosten. Wählen Sie dann den Referenzzinssatz, auf dem Ihre Miete beruht. Er steht meist im Mietvertrag; wurde die Miete seither wegen des Referenzzinssatzes angepasst und nicht angefochten, gilt der Satz der letzten Anpassung. Als neuer Satz ist der aktuelle Referenzzinssatz vorausgewählt. Optional können Sie die Teuerung und eine Pauschale für allgemeine Kostensteigerungen erfassen, die der Vermieter mit einer Senkung verrechnen darf. Der Rechner zeigt jeden Anteil in Prozent, die geschätzte neue Nettomiete und die Differenz pro Monat und pro Jahr.</p>
<h2>Aktueller Referenzzinssatz: 1.25 %</h2>
<p>Der hypothekarische Referenzzinssatz für Mietverhältnisse beträgt 1.25 %. Er gilt seit dem 2. September 2025 und wurde zuletzt am 1. September 2026 unverändert bestätigt. Das Bundesamt für Wohnungswesen (BWO) publiziert ihn vierteljährlich; die nächste Publikation ist für den 1. Dezember 2026 angekündigt. Der Satz stützt sich auf den Durchschnittszinssatz der inländischen Hypotheken und wird auf Viertelprozente gerundet (Art. 12a VMWG). Stand dieser Seite: 25. November 2026.</p>
{ref_table('de')}
<h2>Die Regeln der Verordnung</h2>
<p>Nach Art. 13 der Verordnung über die Miete und Pacht von Wohn- und Geschäftsräumen (VMWG) berechtigt eine Erhöhung des Hypothekarzinses um einen Viertelprozentpunkt in der Regel zu einer Mietzinserhöhung von höchstens 3 %, solange der Satz unter 5 % liegt; zwischen 5 und 6 % sind es 2.5 %, über 6 % noch 2 %. Bei einer Senkung sind die Mietzinse entsprechend herabzusetzen. Daraus ergibt sich bei einer Senkung um einen Viertelprozentpunkt ein Anspruch von 2.91 %, denn 1 − 1 ÷ 1.03 = 2.91 %. Mehrere Schritte werden zusammengezählt:</p>
<table class="data-table">
<thead><tr><th scope="col">Veränderung</th><th scope="col">Erhöhung</th><th scope="col">Senkung</th></tr></thead>
<tbody><tr><td>0.25 Prozentpunkte</td><td>+3.00 %</td><td>−2.91 %</td></tr><tr><td>0.50 Prozentpunkte</td><td>+6.00 %</td><td>−5.66 %</td></tr><tr><td>0.75 Prozentpunkte</td><td>+9.00 %</td><td>−8.26 %</td></tr><tr><td>1.00 Prozentpunkt</td><td>+12.00 %</td><td>−10.71 %</td></tr></tbody>
</table>
<p>Zum Ausgleich der Teuerung darf der Mietzins um höchstens 40 % der Steigerung des Landesindexes der Konsumentenpreise (LIK) erhöht werden (Art. 16 VMWG). Der Vermieter darf eine Senkung ausserdem mit anderen Kostensteigerungen verrechnen, zum Beispiel höheren Gebühren. Viele Vermieter machen dafür eine jährliche Pauschale geltend; ob und in welcher Höhe sie zulässig ist, hängt vom Einzelfall ab. Deshalb ist das Feld leer voreingestellt.</p>
<h2>Formel</h2>
<p class="formula">Zinsanteil (Senkung) = −(1 − 1 ÷ (1 + 3 % × Anzahl Schritte))<br>Zinsanteil (Erhöhung) = +3 % × Anzahl Schritte<br>Teuerung = 40 % × (LIK heute ÷ LIK alt − 1)<br>Kosten = Pauschale pro Jahr × volle Monate ÷ 12<br>Neue Nettomiete = Nettomiete × (1 + Zinsanteil + Teuerung + Kosten)</p>
<p>Der Rechner zählt die drei Prozentsätze zusammen und wendet sie auf die heutige Nettomiete an. Die Formel mit 3 % gilt für Sätze unter 5 %, also für alle bisher publizierten Referenzzinssätze. Einzelne Rechner und Schlichtungsbehörden runden oder kombinieren leicht anders; das Ergebnis ist eine Schätzung.</p>
<h2>Beispiel</h2>
<p>Ihre Nettomiete beträgt CHF 1'800 und beruht auf einem Referenzzinssatz von 1.75 %. Heute gilt 1.25 %, das sind zwei Schritte nach unten: −5.66 %. Der LIK ist seit der letzten Anpassung von 105.0 auf 107.1 Punkte gestiegen (angenommene Werte für das Beispiel), also um 2 %; davon darf der Vermieter 40 % anrechnen, +0.80 %. Total −4.86 %: Die neue Nettomiete beträgt CHF 1'712.51, das sind CHF 87.49 weniger pro Monat oder CHF 1'049.88 pro Jahr. Macht der Vermieter zusätzlich eine Pauschale von 0.5 % pro Jahr für 36 Monate geltend (ebenfalls eine Annahme), kommen +1.50 % dazu; die Miete sinkt dann noch auf CHF 1'739.51.</p>
<h2>So verlangen Sie eine Senkung</h2>
<p>Die Senkung erfolgt nicht automatisch. Sie stellen dem Vermieter ein schriftliches Herabsetzungsbegehren, am besten eingeschrieben, und zwar auf den nächstmöglichen Kündigungstermin (Art. 270a OR). Der Vermieter muss innert 30 Tagen Stellung nehmen. Lehnt er ab, verrechnet er oder antwortet er nicht, können Sie innert weiteren 30 Tagen die Schlichtungsbehörde Ihres Kantons anrufen. Das Verfahren dort ist in der Regel kostenlos.</p>
<p><strong>Wichtig:</strong> Das Ergebnis ist eine Schätzung, keine Rechtsberatung. Ob und wie viel Ihre Miete sinken muss, hängt von Ihrem Vertrag und weiteren Faktoren ab. Lassen Sie Ihren Fall im Zweifel vom <a href="{RENT_SRC['mv']}" rel="noopener">Mieterinnen- und Mieterverband</a> oder von der Schlichtungsbehörde prüfen.</p>'''

RENT_FAQ_DE = [
    ('Wo finde ich den Referenzzinssatz meiner Miete?',
     'Meist im Mietvertrag oder auf dem Formular der letzten Mietzinsanpassung. Massgebend ist der Satz bei Vertragsabschluss oder, falls die Miete seither wegen des Referenzzinssatzes angepasst und nicht angefochten wurde, der Satz dieser Anpassung.'),
    ('Warum 2.91 % und nicht 3 %?',
     'Eine Erhöhung um 3 % macht aus CHF 100 CHF 103. Um wieder auf CHF 100 zu kommen, muss man 3 von 103 abziehen, also 2.91 %. Bei zwei Schritten sind es 6 von 106 oder 5.66 %.'),
    ('Darf der Vermieter die Senkung ablehnen?',
     'Er darf sie mit gestiegenen Kosten und mit 40 % der Teuerung verrechnen und muss erklären, warum. Sind Sie nicht einverstanden, können Sie innert 30 Tagen die Schlichtungsbehörde anrufen.'),
    ('Gilt die Senkung auch für die Nebenkosten?',
     'Nein. Der Referenzzinssatz betrifft nur die Nettomiete. Separat vereinbarte Heiz- und Nebenkosten ändern sich dadurch nicht.'),
    ('Gilt das auch bei einer Indexmiete?',
     'Bei einem indexierten Mietzins nach Art. 269b OR folgt die Miete dem Landesindex der Konsumentenpreise, nicht dem Referenzzinssatz. Bei Staffelmieten gelten ebenfalls eigene Regeln. Lassen Sie solche Verträge im Zweifel prüfen.'),
    ('Werden meine Angaben gespeichert?',
     'Nein. Die Berechnung läuft nur in Ihrem Browser. Ihre Miete wird weder übermittelt noch gespeichert.'),
]

RENT_ART_FR = f'''<h2>Mode d’emploi</h2>
<p>Saisissez votre loyer net actuel, c’est-à-dire le loyer sans les frais de chauffage et les frais accessoires. Choisissez ensuite le taux de référence sur lequel repose votre loyer. Il figure en général dans le bail ; si le loyer a depuis été adapté en raison du taux de référence et que cette adaptation n’a pas été contestée, c’est le taux de cette adaptation qui compte. Le taux de référence actuel est présélectionné comme nouveau taux. Vous pouvez aussi saisir le renchérissement et un forfait pour la hausse générale des coûts, que le bailleur peut compenser avec une baisse. Le calculateur affiche chaque part en pour cent, le nouveau loyer net estimé et la différence par mois et par an.</p>
<h2>Taux de référence actuel : 1,25 %</h2>
<p>Le taux d’intérêt de référence applicable aux contrats de bail est de 1,25 %. Il est valable depuis le 2 septembre 2025 et a été confirmé sans changement le 1er septembre 2026. L’Office fédéral du logement (OFL) le publie chaque trimestre ; la prochaine publication est annoncée pour le 1er décembre 2026. Le taux repose sur le taux d’intérêt moyen des créances hypothécaires en Suisse, arrondi au quart de pour cent (art. 12a OBLF). État de cette page : 25 novembre 2026.</p>
{ref_table('fr')}
<h2>Les règles de l’ordonnance</h2>
<p>Selon l’art. 13 de l’ordonnance sur le bail à loyer et le bail à ferme d’habitations et de locaux commerciaux (OBLF), une hausse du taux hypothécaire d’un quart de point autorise en règle générale une hausse de loyer de 3 % au plus tant que le taux est inférieur à 5 % ; entre 5 et 6 %, c’est 2,5 %, au-delà de 6 %, 2 %. En cas de baisse, les loyers doivent être baissés en conséquence. Pour une baisse d’un quart de point, cela donne un droit à une réduction de 2,91 %, car 1 − 1 ÷ 1,03 = 2,91 %. Plusieurs paliers s’additionnent :</p>
<table class="data-table">
<thead><tr><th scope="col">Variation</th><th scope="col">Hausse</th><th scope="col">Baisse</th></tr></thead>
<tbody><tr><td>0,25 point</td><td>+3,00 %</td><td>−2,91 %</td></tr><tr><td>0,50 point</td><td>+6,00 %</td><td>−5,66 %</td></tr><tr><td>0,75 point</td><td>+9,00 %</td><td>−8,26 %</td></tr><tr><td>1,00 point</td><td>+12,00 %</td><td>−10,71 %</td></tr></tbody>
</table>
<p>Pour compenser le renchérissement, le loyer peut être augmenté au plus de 40 % de la hausse de l’indice suisse des prix à la consommation (IPC) (art. 16 OBLF). Le bailleur peut aussi compenser une baisse avec d’autres hausses de coûts, par exemple des taxes plus élevées. Beaucoup de bailleurs font valoir pour cela un forfait annuel ; son admissibilité et son montant dépendent du cas concret. C’est pourquoi le champ est vide par défaut.</p>
<h2>Formule</h2>
<p class="formula">Part du taux (baisse) = −(1 − 1 ÷ (1 + 3 % × nombre de paliers))<br>Part du taux (hausse) = +3 % × nombre de paliers<br>Renchérissement = 40 % × (IPC actuel ÷ IPC ancien − 1)<br>Coûts = forfait annuel × mois entiers ÷ 12<br>Nouveau loyer net = loyer net × (1 + part du taux + renchérissement + coûts)</p>
<p>Le calculateur additionne les trois pourcentages et les applique au loyer net actuel. La formule avec 3 % vaut pour les taux inférieurs à 5 %, donc pour tous les taux de référence publiés jusqu’ici. Certains calculateurs et autorités de conciliation arrondissent ou combinent un peu autrement ; le résultat est une estimation.</p>
<h2>Exemple</h2>
<p>Votre loyer net est de CHF 1'800 et repose sur un taux de référence de 1,75 %. Aujourd’hui, le taux est de 1,25 %, soit deux paliers à la baisse : −5,66 %. L’IPC est passé de 105,0 à 107,1 points depuis la dernière adaptation (valeurs supposées pour l’exemple), soit +2 % ; le bailleur peut en compter 40 %, soit +0,80 %. Au total −4,86 % : le nouveau loyer net est de CHF 1'712.51, soit CHF 87.49 de moins par mois ou CHF 1'049.88 par an. Si le bailleur fait valoir en plus un forfait de 0,5 % par an sur 36 mois (également une hypothèse), il faut ajouter +1,50 % ; le loyer ne baisse alors plus qu’à CHF 1'739.51.</p>
<h2>Comment demander une baisse de loyer</h2>
<p>La baisse n’est pas automatique. Vous adressez au bailleur une demande écrite de diminution, de préférence en recommandé, pour le prochain terme de résiliation (art. 270a CO). Le bailleur doit se prononcer dans les 30 jours. S’il refuse, compense ou ne répond pas, vous pouvez saisir l’autorité de conciliation de votre canton dans un nouveau délai de 30 jours. La procédure y est en général gratuite.</p>
<p><strong>Important :</strong> le résultat est une estimation, pas un conseil juridique. La baisse à laquelle vous avez droit dépend de votre bail et d’autres facteurs. En cas de doute, faites vérifier votre situation par l’<a href="{RENT_SRC['asloca']}" rel="noopener">ASLOCA</a>, le Mieterverband en Suisse alémanique ou l’office de conciliation.</p>'''

RENT_FAQ_FR = [
    ('Où trouver le taux de référence de mon loyer ?',
     'En général dans le bail ou sur la formule de la dernière adaptation du loyer. Le taux déterminant est celui en vigueur à la conclusion du bail ou, si le loyer a depuis été adapté en raison du taux de référence sans contestation, celui de cette adaptation.'),
    ('Pourquoi 2,91 % et pas 3 % ?',
     'Une hausse de 3 % transforme CHF 100 en CHF 103. Pour revenir à CHF 100, il faut retirer 3 sur 103, soit 2,91 %. Pour deux paliers, c’est 6 sur 106, soit 5,66 %.'),
    ('Le bailleur peut-il refuser la baisse ?',
     'Il peut la compenser avec des hausses de coûts et 40 % du renchérissement, et doit expliquer pourquoi. Si vous n’êtes pas d’accord, vous pouvez saisir l’autorité de conciliation dans les 30 jours.'),
    ('La baisse s’applique-t-elle aux frais accessoires ?',
     'Non. Le taux de référence concerne seulement le loyer net. Les frais de chauffage et frais accessoires convenus séparément ne changent pas.'),
    ('Et pour un loyer indexé ?',
     'Avec un loyer indexé selon l’art. 269b CO, le loyer suit l’indice suisse des prix à la consommation et non le taux de référence. Les loyers échelonnés suivent aussi leurs propres règles. En cas de doute, faites vérifier ce type de bail.'),
    ('Mes données sont-elles enregistrées ?',
     'Non. Le calcul se fait uniquement dans votre navigateur. Votre loyer n’est ni transmis ni enregistré.'),
]

RENTSRC = {
    'de': [
        f'Verordnung über die Miete und Pacht von Wohn- und Geschäftsräumen (VMWG), SR 221.213.11, Art. 12a, 13 und 16: <a href="{RENT_SRC["vmwg_de"]}">{RENT_SRC["vmwg_de"]}</a>',
        f'Obligationenrecht (OR), SR 220, Art. 269b und 270a: <a href="{RENT_SRC["or_de"]}">{RENT_SRC["or_de"]}</a>',
        f'Bundesamt für Wohnungswesen BWO, Referenzzinssatz (1.25 %, Stand 1. September 2026) und Fragen zur Mietzinsanpassung: <a href="{RENT_SRC["bwo_de"]}">{RENT_SRC["bwo_de"]}</a>',
        f'BWO, Entwicklung Referenzzinssatz und Durchschnittszinssatz: <a href="{RENT_SRC["hist_de"]}">{RENT_SRC["hist_de"]}</a>',
        f'Bundesamt für Statistik BFS, Landesindex der Konsumentenpreise: <a href="{RENT_SRC["lik_de"]}">{RENT_SRC["lik_de"]}</a>',
    ],
    'fr': [
        f'Ordonnance sur le bail à loyer et le bail à ferme d’habitations et de locaux commerciaux (OBLF), RS 221.213.11, art. 12a, 13 et 16 : <a href="{RENT_SRC["vmwg_fr"]}">{RENT_SRC["vmwg_fr"]}</a>',
        f'Code des obligations (CO), RS 220, art. 269b et 270a : <a href="{RENT_SRC["or_fr"]}">{RENT_SRC["or_fr"]}</a>',
        f'Office fédéral du logement OFL, taux de référence (1,25 %, état au 1er septembre 2026) et questions sur l’adaptation des loyers : <a href="{RENT_SRC["bwo_fr"]}">{RENT_SRC["bwo_fr"]}</a>',
        f'OFL, évolution du taux de référence et du taux d’intérêt moyen : <a href="{RENT_SRC["hist_fr"]}">{RENT_SRC["hist_fr"]}</a>',
        f'Office fédéral de la statistique OFS, indice suisse des prix à la consommation : <a href="{RENT_SRC["lik_fr"]}">{RENT_SRC["lik_fr"]}</a>',
    ],
}

WORDCOUNT['rent_de'] = tool_page(
    'rent', 'de', 'Mietzinsrechner: Referenzzinssatz und Mietzinssenkung',
    'Mietzinssenkung nach Referenzzinssatz berechnen: Viertelprozent-Schritte nach Art. 13 VMWG, 40 % Teuerung und Kostensteigerung. Aktuell 1.25 %.',
    'Mietzinsrechner Referenzzinssatz',
    'Prüfen Sie, ob Ihre Miete mit dem aktuellen Referenzzinssatz von 1.25 % sinken könnte – mit Teuerung und Kostensteigerung nach Mietrecht.',
    rent_tool('de'), RENT_ART_DE, RENT_FAQ_DE, RENTSRC['de'], 'FinanceApplication',
    ' · Referenzzinssatz geprüft am 25.11.2026; nächste Publikation des BWO: 1.12.2026')
WORDCOUNT['rent_fr'] = tool_page(
    'rent', 'fr', 'Baisse de loyer et taux de référence : calcul en ligne',
    'Calculez une baisse de loyer selon le taux de référence : paliers d’un quart de point (art. 13 OBLF), 40 % du renchérissement et coûts. Actuel 1,25 %.',
    'Calcul du loyer selon le taux de référence',
    'Vérifiez si votre loyer peut baisser avec le taux de référence actuel de 1,25 % – avec le renchérissement et la hausse des coûts selon le droit du bail.',
    rent_tool('fr'), RENT_ART_FR, RENT_FAQ_FR, RENTSRC['fr'], 'FinanceApplication',
    ' · Taux de référence vérifié le 25.11.2026 ; prochaine publication de l’OFL : 1.12.2026')

# =====================================================================
# 3b. Swiss CV (Lebenslauf / CV)
# =====================================================================
CV_SRC = {
    'sdbb_de': 'https://www.berufsberatung.ch/de/lehre-und-schule/lehrstellenbewerbung/sich-um-eine-lehrstelle-bewerben/lebenslauf-erstellen',
    'sdbb_fr': 'https://www.orientation.ch/fr/creer-un-curriculum-vitae',
    'job_de': 'https://www.berufsberatung.ch/dyn/show/22269',
    'job_fr': 'https://www.orientation.ch/dyn/show/22269?lang=fr',
    'zhaw': 'https://www.zhaw.ch/storage/hochschule/career-services/Dokumente/Anleitung_Bewerbungsunterlagen.pdf',
    'vd': 'https://www.vd.ch/fileadmin/user_upload/themes/formation/orientation/fichiers_pdf/publications/postuler_adultes_1curriculum_web.pdf',
    'fr_de': 'https://www.fr.ch/de/alltag/aufenthaltsbewilligungen-und-einbuergerung/die-verschiedenen-bewilligungsarten-0',
    'fr_fr': 'https://www.fr.ch/vie-quotidienne/permis-de-sejour-et-naturalisation/les-types-de-permis-de-sejour',
    'sem': 'https://www.sem.admin.ch/en/residence-permits-for-non-eu-efta-nationals',
    'or_de': 'https://www.fedlex.admin.ch/eli/cc/27/317_321_377/de#art_330_a',
    'or_fr': 'https://www.fedlex.admin.ch/eli/cc/27/317_321_377/fr#art_330_a',
}

CV_PERMITS = {
    'de': [('B', 'Ausweis B (Aufenthaltsbewilligung)'), ('C', 'Ausweis C (Niederlassungsbewilligung)'), ('G', 'Ausweis G (Grenzgängerbewilligung)'),
           ('L', 'Ausweis L (Kurzaufenthaltsbewilligung)'), ('Ci', 'Ausweis Ci'), ('F', 'Ausweis F (vorläufig aufgenommen)'),
           ('N', 'Ausweis N (Asylsuchende)'), ('S', 'Ausweis S (Schutzstatus S)')],
    'fr': [('B', 'Permis B (autorisation de séjour)'), ('C', 'Permis C (autorisation d’établissement)'), ('G', 'Permis G (autorisation frontalière)'),
           ('L', 'Permis L (autorisation de courte durée)'), ('Ci', 'Permis Ci'), ('F', 'Permis F (admission provisoire)'),
           ('N', 'Permis N (requérant d’asile)'), ('S', 'Permis S (statut de protection S)')],
}


def cv_tool(lang):
    fr = lang == 'fr'
    L = dict(
        h='Lebenslauf erstellen', personal='Persönliche Angaben', first='Vorname', last='Nachname',
        headline='Beruf oder gesuchte Stelle (optional)', street='Strasse und Nr.', city='PLZ und Ort', phone='Telefon', email='E-Mail',
        birth='Geburtsdatum', birth_h='TT.MM.JJJJ', nat='Nationalität', nat_h='z. B. Schweiz, Italien, Portugal',
        permit='Bewilligung (ohne Schweizer Pass)', none='– keine / Schweizer Pass –', origin='Heimatort (optional)',
        civil='Zivilstand (optional)', license='Führerausweis (optional)', license_h='z. B. Kat. B',
        photo='Foto (optional)', photo_h='Wird nur in Ihrem Browser verarbeitet und auf das Passformat 35 × 45 zugeschnitten. Nichts wird hochgeladen.',
        photo_rm='Foto entfernen', profile='Kurzprofil (optional, 2–4 Sätze)',
        work='Berufserfahrung', add_work='+ Stelle hinzufügen', edu='Aus- und Weiterbildung', add_edu='+ Ausbildung hinzufügen',
        langs='Sprachen', add_lang='+ Sprache hinzufügen', more='Weitere Angaben', it='IT-Kenntnisse', interests='Interessen und Hobbys',
        refs='Referenzen', ref_req='«Auf Anfrage» (empfohlen)', ref_list='Personen angeben', add_ref='+ Referenz hinzufügen',
        cvlang='Sprache des Lebenslaufs', print='Als PDF speichern', print_h='Öffnet das Druckfenster: wählen Sie «Als PDF speichern» und Papierformat A4.',
        example='Beispiel laden', save='Entwurf speichern (Datei)', open='Entwurf öffnen', clear='Alles löschen',
        checks='Prüfung nach Schweizer Standard', preview='Vorschau',
        from_='Von', to='Bis', month_h='MM.JJJJ', current='bis heute', role='Funktion', org='Arbeitgeber', place='Ort',
        tasks='Tätigkeiten und Erfolge (eine pro Zeile)', cert='Arbeitszeugnis vorhanden', title='Abschluss oder Kurs', school='Schule oder Institution',
        lang='Sprache', level='Niveau', choose='– wählen –', native='Muttersprache', name='Name', func='Funktion', firm='Firma',
        remove='Entfernen', job='Stelle', training='Ausbildung', reference='Referenz', privacy='Ihre Angaben und Ihr Foto bleiben in diesem Browserfenster. Nichts wird gesendet oder gespeichert – wer die Seite schliesst, verliert die Eingaben, ausser er speichert den Entwurf als Datei auf dem eigenen Gerät.',
        noscript='Für den Lebenslauf-Generator wird JavaScript benötigt.',
    ) if not fr else dict(
        h='Créer son CV', personal='Données personnelles', first='Prénom', last='Nom',
        headline='Métier ou poste visé (facultatif)', street='Rue et n°', city='NPA et localité', phone='Téléphone', email='E-mail',
        birth='Date de naissance', birth_h='JJ.MM.AAAA', nat='Nationalité', nat_h='p. ex. Suisse, Italie, Portugal',
        permit='Permis (sans passeport suisse)', none='– aucun / passeport suisse –', origin='Lieu d’origine (facultatif)',
        civil='État civil (facultatif)', license='Permis de conduire (facultatif)', license_h='p. ex. cat. B',
        photo='Photo (facultative)', photo_h='Traitée uniquement dans votre navigateur et recadrée au format passeport 35 × 45. Rien n’est envoyé.',
        photo_rm='Retirer la photo', profile='Profil (facultatif, 2 à 4 phrases)',
        work='Expérience professionnelle', add_work='+ Ajouter un poste', edu='Formation et formation continue', add_edu='+ Ajouter une formation',
        langs='Langues', add_lang='+ Ajouter une langue', more='Autres informations', it='Informatique', interests='Centres d’intérêt',
        refs='Références', ref_req='« Sur demande » (recommandé)', ref_list='Indiquer des personnes', add_ref='+ Ajouter une référence',
        cvlang='Langue du CV', print='Enregistrer en PDF', print_h='Ouvre la fenêtre d’impression : choisissez « Enregistrer au format PDF » et le format A4.',
        example='Charger un exemple', save='Enregistrer le brouillon (fichier)', open='Ouvrir un brouillon', clear='Tout effacer',
        checks='Contrôle selon les usages suisses', preview='Aperçu',
        from_='Du', to='Au', month_h='MM.AAAA', current='à ce jour', role='Fonction', org='Employeur', place='Lieu',
        tasks='Tâches et réalisations (une par ligne)', cert='Certificat de travail disponible', title='Diplôme ou cours', school='École ou institution',
        lang='Langue', level='Niveau', choose='– choisir –', native='Langue maternelle', name='Nom', func='Fonction', firm='Entreprise',
        remove='Supprimer', job='Poste', training='Formation', reference='Référence', privacy='Vos données et votre photo restent dans cette fenêtre du navigateur. Rien n’est envoyé ni enregistré : en fermant la page, vous perdez la saisie, sauf si vous enregistrez le brouillon comme fichier sur votre appareil.',
        noscript='Le générateur de CV nécessite JavaScript.',
    )
    f = lambda name, label, hint='', typ='text', extra='': (
        f'<div class="field"><label for="cv-{name}">{label}</label><input type="{typ}" id="cv-{name}" name="{name}"{extra}'
        + (f' aria-describedby="cv-{name}-h"' if hint else '') + '>'
        + (f'<span class="note" id="cv-{name}-h">{hint}</span>' if hint else '') + '</div>')
    permits = ''.join(f'<option value="{k}">{n}</option>' for k, n in CV_PERMITS[lang])
    levels = ''.join(f'<option value="{v}">{t}</option>' for v, t in [('native', L['native']), ('C2', 'C2'), ('C1', 'C1'), ('B2', 'B2'), ('B1', 'B1'), ('A2', 'A2'), ('A1', 'A1')])
    cvlangs = ''.join(f'<option value="{v}"{" selected" if v == lang else ""} lang="{v}">{t}</option>' for v, t in
                      [('de', 'Deutsch'), ('fr', 'Français'), ('it', 'Italiano'), ('en', 'English')])
    rm = f'<button type="button" class="link-btn" data-remove aria-label="{L["remove"]}" title="{L["remove"]}">×</button>'
    lf = lambda k, label, hint='', typ='text', extra='': (
        f'<div class="field"><label data-for="{k}">{label}</label><input type="{typ}" data-k="{k}"{extra}'
        + (f' placeholder="{hint}"' if hint else '') + '></div>')
    return f'''<section class="tool cv-tool" data-tool="cv" aria-labelledby="tool-h">
<h2 id="tool-h">{L['h']}</h2>
<p class="note cv-privacy">{L['privacy']}</p>
<form id="cv-form" class="cv-form" novalidate autocomplete="off">
<div class="row">
<div class="field"><label for="cv-cvlang">{L['cvlang']}</label><select id="cv-cvlang" name="cvlang">{cvlangs}</select></div>
<div class="field"><button type="button" class="btn-sec" data-act="example">{L['example']}</button></div>
</div>
<fieldset><legend>{L['personal']}</legend>
<div class="row">{f('first', L['first'], extra=' autocomplete="given-name"')}{f('last', L['last'], extra=' autocomplete="family-name"')}</div>
{f('headline', L['headline'])}
<div class="row">{f('street', L['street'], extra=' autocomplete="street-address"')}{f('city', L['city'])}</div>
<div class="row">{f('phone', L['phone'], typ='tel', extra=' autocomplete="tel"')}{f('email', L['email'], typ='email', extra=' autocomplete="email"')}</div>
<div class="row">{f('birth', L['birth'], L['birth_h'], extra=' inputmode="numeric" maxlength="10"')}{f('nationality', L['nat'], L['nat_h'])}</div>
<div class="row"><div class="field"><label for="cv-permit">{L['permit']}</label><select id="cv-permit" name="permit"><option value="">{L['none']}</option>{permits}</select></div>{f('origin', L['origin'])}</div>
<div class="row">{f('civil', L['civil'])}{f('license', L['license'], L['license_h'])}</div>
<div class="field"><label for="cv-photo">{L['photo']}</label><input type="file" id="cv-photo" accept="image/jpeg,image/png,image/webp" aria-describedby="cv-photo-h"><span class="note" id="cv-photo-h">{L['photo_h']}</span>
<button type="button" class="btn-sec" id="cv-photo-remove" hidden>{L['photo_rm']}</button></div>
<div class="field"><label for="cv-profile">{L['profile']}</label><textarea id="cv-profile" name="profile" rows="3"></textarea></div>
</fieldset>
<fieldset><legend>{L['work']}</legend>
<div data-list="work" class="cv-list"></div>
<button type="button" class="btn-sec" data-act="add-work">{L['add_work']}</button>
</fieldset>
<fieldset><legend>{L['edu']}</legend>
<div data-list="edu" class="cv-list"></div>
<button type="button" class="btn-sec" data-act="add-edu">{L['add_edu']}</button>
</fieldset>
<fieldset><legend>{L['langs']}</legend>
<div data-list="lang" class="cv-list cv-langs"></div>
<button type="button" class="btn-sec" data-act="add-lang">{L['add_lang']}</button>
</fieldset>
<fieldset><legend>{L['more']}</legend>
<div class="row">{f('it', L['it'])}{f('interests', L['interests'])}</div>
</fieldset>
<fieldset><legend>{L['refs']}</legend>
<div class="choice"><label><input type="radio" name="refMode" value="request" checked> {L['ref_req']}</label><label><input type="radio" name="refMode" value="list"> {L['ref_list']}</label></div>
<div class="cv-refs-list" hidden><div data-list="ref" class="cv-list"></div>
<button type="button" class="btn-sec" data-act="add-ref">{L['add_ref']}</button></div>
</fieldset>
</form>
<template id="tpl-work"><div class="cv-item"><p class="cv-item-h"><span>{L['job']} <span class="cv-num"></span></span> {rm}</p>
<div class="row">{lf('from', L['from_'], L['month_h'])}{lf('to', L['to'], L['month_h'])}<div class="field"><label class="cv-check"><input type="checkbox" data-k="current"> {L['current']}</label></div></div>
<div class="row">{lf('role', L['role'])}{lf('org', L['org'])}{lf('place', L['place'])}</div>
<div class="field"><label data-for="tasks">{L['tasks']}</label><textarea data-k="tasks" rows="3"></textarea></div>
<label class="cv-check"><input type="checkbox" data-k="cert"> {L['cert']}</label></div></template>
<template id="tpl-edu"><div class="cv-item"><p class="cv-item-h"><span>{L['training']} <span class="cv-num"></span></span> {rm}</p>
<div class="row">{lf('from', L['from_'], L['month_h'])}{lf('to', L['to'], L['month_h'])}<div class="field"><label class="cv-check"><input type="checkbox" data-k="current"> {L['current']}</label></div></div>
<div class="row">{lf('title', L['title'])}{lf('school', L['school'])}{lf('place', L['place'])}</div></div></template>
<template id="tpl-lang"><div class="cv-item cv-item-inline"><div class="row">{lf('name', L['lang'])}<div class="field"><label data-for="level">{L['level']}</label><select data-k="level"><option value="">{L['choose']}</option>{levels}</select></div><div class="field cv-rm">{rm}</div></div></div></template>
<template id="tpl-ref"><div class="cv-item"><p class="cv-item-h"><span>{L['reference']} <span class="cv-num"></span></span> {rm}</p>
<div class="row">{lf('name', L['name'])}{lf('role', L['func'])}{lf('org', L['firm'])}{lf('phone', L['phone'], typ='tel')}</div></div></template>
<h3>{L['checks']}</h3>
<ul class="cv-checks" aria-live="polite"></ul>
<div class="cv-actions">
<button type="button" class="btn" data-act="print" aria-describedby="cv-print-h">{L['print']}</button>
<button type="button" class="btn-sec" data-act="save">{L['save']}</button>
<label class="btn-sec cv-file">{L['open']}<input type="file" id="cv-open" accept="application/json,.json"></label>
<button type="button" class="btn-sec" data-act="clear">{L['clear']}</button>
</div>
<p class="note" id="cv-print-h">{L['print_h']}</p>
<p class="note cv-status" role="status"></p>
<h3>{L['preview']} <span class="cv-pages note"></span></h3>
<div class="cv-preview"><div class="cv-sheet" id="cv-sheet"></div></div>
<noscript><p>{L['noscript']}</p></noscript>
</section>'''


CV_ART_DE = f'''<h2>So funktioniert der Lebenslauf-Generator</h2>
<p>Füllen Sie die Felder aus. Rechts davon, beziehungsweise darunter auf dem Handy, sehen Sie sofort die A4-Vorschau. Die Reihenfolge erledigt das Werkzeug selbst: Die neueste Stelle und die neueste Ausbildung stehen zuoberst, die Muttersprache steht bei den Sprachen an erster Stelle. Gleichzeitig prüft es Ihre Angaben nach den Gepflogenheiten in der Schweiz und zeigt, was fehlt oder falsch aussieht: eine fehlende Bewilligung, ein Sprachniveau ohne Angabe, ein Enddatum vor dem Beginn, eine Lücke von mehr als sechs Monaten oder ein «ß», das in der Schweiz nicht verwendet wird.</p>
<p>Mit <strong>Als PDF speichern</strong> öffnet sich das Druckfenster Ihres Browsers. Wählen Sie dort «Als PDF speichern» (oder «Microsoft Print to PDF») und das Format A4. Der Dateiname wird automatisch vorgeschlagen, zum Beispiel <em>Lebenslauf_Laura_Beispiel.pdf</em>.</p>
<p><strong>Datenschutz:</strong> Alles läuft in Ihrem Browser – auch das Foto. Es gibt kein Konto, keine Cookies und keinen Server, der Ihre Daten sieht. Weil nichts gespeichert wird, können Sie Ihren Entwurf als kleine Datei auf Ihr Gerät herunterladen und später wieder öffnen.</p>
<h2>Was in einen Schweizer Lebenslauf gehört</h2>
<p>Die Berufs-, Studien- und Laufbahnberatung und die Career Services der Hochschulen beschreiben einen ähnlichen Aufbau:</p>
<ul>
<li><strong>Persönliche Angaben:</strong> Name, Adresse, Telefon, E-Mail, vollständiges Geburtsdatum und Nationalität. Wer keinen Schweizer Pass hat, gibt die Bewilligung an, zum Beispiel Ausweis B oder C. Den Heimatort nennen viele Schweizerinnen und Schweizer zusätzlich; Zivilstand und Familie sind freiwillig.</li>
<li><strong>Berufserfahrung:</strong> Funktion, Arbeitgeber, Ort und Zeitraum mit Monat und Jahr, darunter die wichtigsten Tätigkeiten und Erfolge in Stichworten.</li>
<li><strong>Aus- und Weiterbildung:</strong> Abschluss, Schule, Ort und Zeitraum, ebenfalls von neu nach alt.</li>
<li><strong>Sprachen:</strong> zuerst die Muttersprache, dann die übrigen Sprachen mit Niveau nach dem Europäischen Referenzrahmen, von A1 bis C2.</li>
<li><strong>IT-Kenntnisse, Interessen</strong> und am Schluss <strong>Referenzen</strong>, meist mit dem Vermerk «Auf Anfrage».</li>
</ul>
<h2>Die Schweizer Besonderheiten</h2>
<ul>
<li><strong>Foto:</strong> In der Schweiz verbreitet, aber rechtlich keine Pflicht. Wenn, dann ein aktuelles, professionelles Bild, kein Selfie. Der Generator schneidet es auf das Passformat 35 × 45 zu.</li>
<li><strong>Umgekehrt chronologisch:</strong> Die aktuelle oder letzte Tätigkeit steht oben.</li>
<li><strong>Länge:</strong> in der Regel eine bis zwei Seiten. Die Vorschau zeigt die Seitenumbrüche und warnt ab der dritten Seite.</li>
<li><strong>Kein «ß»:</strong> In der Schweiz schreibt man «Strasse» und «gross». Ein Klick ersetzt alle «ß» im Lebenslauf.</li>
<li><strong>Keine Unterschrift</strong> und kein Datum auf dem Lebenslauf nötig.</li>
<li><strong>Arbeitszeugnisse:</strong> Sie haben in der Schweiz grosses Gewicht und gehören als Beilage ins Bewerbungsdossier, nicht in den Lebenslauf selbst. Arbeitnehmende können jederzeit ein Zeugnis verlangen (Art. 330a OR). Kreuzen Sie bei jeder Stelle an, ob Sie ein Zeugnis haben: Der Generator erinnert Sie daran, welche Zeugnisse Sie beilegen sollten.</li>
</ul>
<h2>Bewilligungen im Überblick</h2>
<table class="data-table"><caption>Ausweise für Ausländerinnen und Ausländer</caption>
<thead><tr><th scope="col">Ausweis</th><th scope="col">Bezeichnung</th></tr></thead>
<tbody>{''.join(f'<tr><td>{k}</td><td>{n.split("(", 1)[1].rstrip(")") if "(" in n else "–"}</td></tr>' for k, n in CV_PERMITS['de'])}</tbody></table>
<h2>Beispiel</h2>
<p>Laura Beispiel, 30, Italienerin mit Ausweis C, bewirbt sich in Bern als Sachbearbeiterin. Ihr Lebenslauf beginnt mit Name, Beruf und Foto. Darunter stehen Adresse, Telefon, E-Mail, Geburtsdatum, Nationalität und «Ausweis C (Niederlassungsbewilligung)». Es folgen ihre zwei Stellen, die aktuelle zuerst, je mit zwei bis drei Stichworten, dann ihre Weiterbildung und die kaufmännische Lehre. Bei den Sprachen steht Italienisch als Muttersprache, danach Deutsch C1, Französisch B2 und Englisch B1. Ganz unten: «Referenzen: Auf Anfrage». Ergebnis: eine Seite A4. Die zwei Arbeitszeugnisse legt sie dem Dossier als PDF bei. Mit «Beispiel laden» sehen Sie diesen Lebenslauf direkt im Generator.</p>
<p>Weitere Werkzeuge für die Stellensuche: der <a href="/de/brutto-netto-rechner/">Brutto-Netto-Rechner</a> für die Lohnfrage und der <a href="/de/stundenlohn-rechner/">Stundenlohn-Rechner</a>.</p>'''

CV_FAQ_DE = [
    ('Ist ein Foto im Lebenslauf in der Schweiz Pflicht?',
     'Nein. Ein Foto ist üblich und wird oft erwartet, rechtlich ist es aber freiwillig. Bei Bewerbungen in englischsprachige Länder lässt man es meist weg. Im Generator ist das Foto optional.'),
    ('Muss ich meine Aufenthaltsbewilligung angeben?',
     'Wer keinen Schweizer Pass hat, nennt sie üblicherweise bei den persönlichen Angaben, zum Beispiel «Ausweis B». So sieht der Arbeitgeber sofort, ob eine Arbeitsbewilligung nötig ist.'),
    ('Wie lang darf ein Lebenslauf sein?',
     'In der Regel eine bis zwei Seiten A4. Nur bei sehr langer Erfahrung oder einer akademischen Laufbahn sind mehr Seiten üblich. Die Vorschau zeigt, wie viele Seiten Ihr Lebenslauf hat.'),
    ('Wie gebe ich Sprachkenntnisse richtig an?',
     'Zuerst die Muttersprache, dann jede weitere Sprache mit Niveau nach dem Europäischen Referenzrahmen: A1 und A2 für Grundkenntnisse, B1 und B2 für selbständige Sprachverwendung, C1 und C2 für sehr gute Kenntnisse.'),
    ('Gehören Arbeitszeugnisse in den Lebenslauf?',
     'Nein, sie kommen als Beilage ins Bewerbungsdossier, zusammen mit Diplomen. Der Lebenslauf nennt die Stellen; die Zeugnisse belegen sie.'),
    ('Werden meine Daten oder mein Foto gespeichert?',
     'Nein. Alles bleibt in Ihrem Browserfenster, nichts wird gesendet. Damit Sie später weiterarbeiten können, speichern Sie den Entwurf als Datei auf Ihrem eigenen Gerät.'),
]

CV_ART_FR = f'''<h2>Comment fonctionne le générateur de CV</h2>
<p>Remplissez les champs : l’aperçu A4 se met à jour aussitôt. L’outil gère l’ordre tout seul : le poste et la formation les plus récents viennent en premier, et la langue maternelle ouvre la rubrique des langues. En même temps, il vérifie vos données selon les usages suisses et signale ce qui manque ou semble faux : un permis absent, une langue sans niveau, une date de fin antérieure au début, une période vide de plus de six mois, ou un « ß » dans un CV en allemand.</p>
<p>Le bouton <strong>Enregistrer en PDF</strong> ouvre la fenêtre d’impression de votre navigateur. Choisissez « Enregistrer au format PDF » (ou « Microsoft Print to PDF ») et le format A4. Le nom du fichier est proposé automatiquement, par exemple <em>CV_Julie_Exemple.pdf</em>.</p>
<p><strong>Protection des données :</strong> tout se passe dans votre navigateur – la photo aussi. Pas de compte, pas de cookies, aucun serveur ne voit vos données. Comme rien n’est enregistré, vous pouvez télécharger votre brouillon sous forme de petit fichier sur votre appareil et le rouvrir plus tard.</p>
<h2>Ce que contient un CV suisse</h2>
<p>L’orientation professionnelle, les offices cantonaux et les services carrière des hautes écoles décrivent une structure semblable :</p>
<ul>
<li><strong>Données personnelles :</strong> nom, adresse, téléphone, e-mail, date de naissance et nationalité. Sans passeport suisse, on indique son permis, par exemple permis B ou C. Les Suisses ajoutent souvent leur lieu d’origine ; l’état civil est facultatif.</li>
<li><strong>Expérience professionnelle :</strong> fonction, employeur, lieu et période (mois et année), avec les principales tâches et réalisations en mots-clés.</li>
<li><strong>Formation et formation continue :</strong> diplôme, école, lieu et période, du plus récent au plus ancien.</li>
<li><strong>Langues :</strong> d’abord la langue maternelle, puis les autres langues avec leur niveau selon le Cadre européen commun de référence (CECR), de A1 à C2.</li>
<li><strong>Informatique, centres d’intérêt</strong> et, à la fin, les <strong>références</strong>, le plus souvent avec la mention « sur demande ».</li>
</ul>
<h2>Les particularités suisses</h2>
<ul>
<li><strong>Photo :</strong> courante en Suisse, mais pas obligatoire. Si vous en mettez une : récente, soignée, sur fond neutre, pas de selfie. Le générateur la recadre au format passeport 35 × 45.</li>
<li><strong>Ordre antichronologique :</strong> le poste actuel ou le dernier en premier.</li>
<li><strong>Longueur :</strong> une à deux pages en général. L’aperçu montre les sauts de page et avertit dès la troisième page.</li>
<li><strong>Pas de signature</strong> ni de date sur le CV.</li>
<li><strong>Certificats de travail :</strong> ils comptent beaucoup en Suisse et se joignent en annexe au dossier de candidature, pas dans le CV lui-même. Le travailleur peut demander un certificat en tout temps (art. 330a CO). Cochez pour chaque poste si vous avez un certificat : le générateur vous rappelle lesquels joindre.</li>
<li><strong>CV en allemand :</strong> en Suisse, on écrit « ss » au lieu de « ß ». Un clic corrige tout le CV.</li>
</ul>
<h2>Les permis en bref</h2>
<table class="data-table"><caption>Permis pour les personnes de nationalité étrangère</caption>
<thead><tr><th scope="col">Permis</th><th scope="col">Désignation</th></tr></thead>
<tbody>{''.join(f'<tr><td>{k}</td><td>{n.split("(", 1)[1].rstrip(")") if "(" in n else "–"}</td></tr>' for k, n in CV_PERMITS['fr'])}</tbody></table>
<h2>Exemple</h2>
<p>Julie Exemple, 30 ans, Portugaise avec permis C, postule à Fribourg comme collaboratrice administrative. Son CV commence par son nom, son métier et sa photo. Viennent ensuite l’adresse, le téléphone, l’e-mail, la date de naissance, la nationalité et « Permis C (autorisation d’établissement) ». Puis ses deux postes, le plus récent d’abord, chacun avec deux ou trois mots-clés, sa formation continue et son CFC. Côté langues : portugais et français comme langues maternelles, allemand B2, anglais B1. Tout en bas : « Références : sur demande ». Résultat : une page A4. Elle joint ses deux certificats de travail en PDF à son dossier. Le bouton « Charger un exemple » affiche ce CV dans le générateur.</p>
<p>Autres outils utiles pour la recherche d’emploi : le calculateur <a href="/fr/salaire-brut-net-suisse/">salaire brut-net</a> et le <a href="/fr/calcul-salaire-horaire/">calcul du salaire horaire</a>.</p>'''

CV_FAQ_FR = [
    ('La photo est-elle obligatoire sur un CV en Suisse ?',
     'Non. Elle est courante et souvent attendue, mais facultative. Pour une candidature dans un pays anglophone, on l’omet en général. Dans le générateur, la photo est facultative.'),
    ('Dois-je indiquer mon permis de séjour ?',
     'Sans passeport suisse, on l’indique en général dans les données personnelles, par exemple « Permis B ». L’employeur voit ainsi tout de suite si une autorisation de travail est nécessaire.'),
    ('Quelle longueur pour un CV suisse ?',
     'En général une à deux pages A4. Plus de pages ne se justifient qu’avec une très longue expérience ou un parcours académique. L’aperçu indique le nombre de pages.'),
    ('Comment indiquer ses langues ?',
     'D’abord la langue maternelle, puis chaque langue avec son niveau CECR : A1 et A2 pour un niveau élémentaire, B1 et B2 pour un niveau indépendant, C1 et C2 pour un niveau expérimenté.'),
    ('Les certificats de travail vont-ils dans le CV ?',
     'Non, ils se joignent en annexe au dossier de candidature, avec les diplômes. Le CV cite les postes ; les certificats les attestent.'),
    ('Mes données ou ma photo sont-elles enregistrées ?',
     'Non. Tout reste dans votre fenêtre de navigateur, rien n’est envoyé. Pour reprendre plus tard, enregistrez le brouillon comme fichier sur votre propre appareil.'),
]

CVSRC = {
    'de': [
        f'Berufs-, Studien- und Laufbahnberatung (SDBB), Lebenslauf erstellen: <a href="{CV_SRC["sdbb_de"]}">{CV_SRC["sdbb_de"]}</a>',
        f'SDBB, Eine Stelle suchen (Bewerbungsdossier mit Arbeitszeugnissen, PDF): <a href="{CV_SRC["job_de"]}">{CV_SRC["job_de"]}</a>',
        f'ZHAW Career Services, Anleitung Bewerbungsunterlagen (Reihenfolge, Länge, Foto, Bewilligung, Sprachniveau, kein ß): <a href="{CV_SRC["zhaw"]}">{CV_SRC["zhaw"]}</a>',
        f'Kanton Waadt, Office cantonal d’orientation scolaire et professionnelle, Créer un curriculum vitae: <a href="{CV_SRC["vd"]}">{CV_SRC["vd"]}</a>',
        f'Kanton Freiburg, Die verschiedenen Bewilligungsarten (L, B, C, G, Ci): <a href="{CV_SRC["fr_de"]}">{CV_SRC["fr_de"]}</a>',
        f'Staatssekretariat für Migration SEM, Ausweise F, N, S, Ci und G: <a href="{CV_SRC["sem"]}">{CV_SRC["sem"]}</a>',
        f'Obligationenrecht (OR), SR 220, Art. 330a (Arbeitszeugnis): <a href="{CV_SRC["or_de"]}">{CV_SRC["or_de"]}</a>',
    ],
    'fr': [
        f'Orientation professionnelle, universitaire et de carrière (CSFO), Créer un curriculum vitæ : <a href="{CV_SRC["sdbb_fr"]}">{CV_SRC["sdbb_fr"]}</a>',
        f'CSFO, Rechercher un emploi (dossier avec certificats de travail, PDF) : <a href="{CV_SRC["job_fr"]}">{CV_SRC["job_fr"]}</a>',
        f'Canton de Vaud, Office cantonal d’orientation scolaire et professionnelle, Créer un curriculum vitae (une page, antichronologique, niveau CECR, références sur demande) : <a href="{CV_SRC["vd"]}">{CV_SRC["vd"]}</a>',
        f'ZHAW Career Services, Anleitung Bewerbungsunterlagen (en allemand ; longueur, photo, permis, langues) : <a href="{CV_SRC["zhaw"]}">{CV_SRC["zhaw"]}</a>',
        f'Canton de Fribourg, Les types de permis de séjour (L, B, C, G, Ci) : <a href="{CV_SRC["fr_fr"]}">{CV_SRC["fr_fr"]}</a>',
        f'Secrétariat d’État aux migrations SEM, permis F, N, S, Ci et G (en anglais) : <a href="{CV_SRC["sem"]}">{CV_SRC["sem"]}</a>',
        f'Code des obligations (CO), RS 220, art. 330a (certificat de travail) : <a href="{CV_SRC["or_fr"]}">{CV_SRC["or_fr"]}</a>',
    ],
}

WORDCOUNT['cv_de'] = tool_page(
    'cv', 'de', 'Lebenslauf Schweiz erstellen: gratis, mit Prüfung',
    'Lebenslauf nach Schweizer Standard erstellen und prüfen: Bewilligung, Sprachniveau A1–C2, Foto freiwillig, A4-PDF. Ohne Konto, Daten bleiben im Browser.',
    'Lebenslauf für die Schweiz erstellen',
    'Damit Ihr Lebenslauf in der Schweiz nichts falsch macht: Das Werkzeug ordnet, prüft und gestaltet ihn nach Schweizer Gepflogenheiten – als PDF im Format A4.',
    cv_tool('de'), CV_ART_DE, CV_FAQ_DE, CVSRC['de'], 'BusinessApplication',
    ' · Quellen geprüft am 25.11.2026', script='/js/cv-ui.js')
WORDCOUNT['cv_fr'] = tool_page(
    'cv', 'fr', 'CV suisse : créer et vérifier son CV gratuitement',
    'Créez un CV aux normes suisses et vérifiez-le : permis, langues A1–C2, photo facultative, PDF A4. Sans compte, vos données restent dans le navigateur.',
    'Créer un CV aux normes suisses',
    'Pour que votre CV ne commette aucune erreur en Suisse : l’outil le trie, le vérifie et le met en page selon les usages suisses – en PDF au format A4.',
    cv_tool('fr'), CV_ART_FR, CV_FAQ_FR, CVSRC['fr'], 'BusinessApplication',
    ' · Sources vérifiées le 25.11.2026', script='/js/cv-ui.js')


# =====================================================================
# 4. Home pages
# =====================================================================
def home(lang):
    if lang == 'de':
        body = f'''<h1>Schweizer Rechner</h1>
<p class="lead">Einfache Online-Rechner für den Alltag in der Schweiz: Arbeitszeit, Brutto-Netto-Lohn, Miete, Prozent, Mehrwertsteuer, Datum und IBAN – und ein Lebenslauf nach Schweizer Standard.</p>
<ul class="cards">{''.join(f'<li><a href="{u}"><strong>{n}</strong>{d}</a></li>' for u, n, d in TOOLS['de'])}</ul>
<h2>Was diese Seite ist</h2>
<p>Diese Seite sammelt kleine Rechner für Fragen, die im Schweizer Berufsalltag immer wieder vorkommen: Wie viele Stunden habe ich diese Woche gearbeitet? War meine Pause lang genug? Wie viel Mehrwertsteuer steckt in einer Rechnung? Um wie viel Prozent ist ein Preis gestiegen? Was ist mein Monatslohn pro Stunde wert? Wie viel bleibt vom Bruttolohn netto? Darf meine Miete wegen des Referenzzinssatzes sinken? Stimmt diese IBAN? Und wie sieht ein Lebenslauf aus, der in der Schweiz alles richtig macht?</p>
<p>Jeder Rechner erklärt die Formel, zeigt ein Beispiel in Franken und beantwortet häufige Fragen. Gesetzliche Werte wie MWST-Sätze oder Mindestpausen stammen aus offiziellen Quellen des Bundes, die auf der jeweiligen Seite verlinkt sind.</p>
<h2>Ihre Daten bleiben bei Ihnen</h2>
<p>Alle Berechnungen laufen direkt in Ihrem Browser. Es werden keine Eingaben übermittelt oder gespeichert, und die Seite setzt keine Cookies. Mehr dazu in der <a href="/de/datenschutz/">Datenschutzerklärung</a>.</p>
<p>Die Seite gibt es auch auf <a href="/fr/" hreflang="fr-CH" lang="fr-CH">Französisch</a>.</p>
<p class="stand">{STAND['de']}</p>'''
        title, desc = 'Schweizer Rechner: Arbeitszeit, Lohn, MWST, IBAN', 'Kostenlose Rechner für die Schweiz: Brutto-Netto-Lohn, Mietzins, Arbeitszeit, Stundenlohn, Prozent, MWST, Daten, IBAN und Lebenslauf.'
    else:
        body = f'''<h1>Calculateurs suisses</h1>
<p class="lead">Des calculateurs simples pour le quotidien en Suisse : heures de travail, salaire brut-net, loyer, pourcentages, TVA, dates et IBAN – et un CV aux normes suisses.</p>
<ul class="cards">{''.join(f'<li><a href="{u}"><strong>{n}</strong>{d}</a></li>' for u, n, d in TOOLS['fr'])}</ul>
<h2>À propos de ce site</h2>
<p>Ce site réunit de petits calculateurs pour des questions qui reviennent sans cesse dans la vie professionnelle en Suisse : combien d’heures ai-je travaillé cette semaine ? Ma pause était-elle assez longue ? Quelle TVA contient cette facture ? De combien de pour cent un prix a-t-il augmenté ? Combien vaut mon salaire mensuel à l’heure ? Que reste-t-il du salaire brut une fois les cotisations déduites ? Mon loyer peut-il baisser avec le taux de référence ? Cette IBAN est-elle correcte ? Et à quoi ressemble un CV qui respecte les usages suisses ?</p>
<p>Chaque calculateur explique la formule, donne un exemple en francs et répond aux questions fréquentes. Les valeurs légales, comme les taux de TVA ou les pauses minimales, proviennent de sources officielles de la Confédération, citées sur chaque page.</p>
<h2>Vos données restent chez vous</h2>
<p>Tous les calculs se font directement dans votre navigateur. Aucune saisie n’est transmise ni enregistrée, et le site n’utilise pas de cookies. Plus de détails dans la <a href="/fr/confidentialite/">politique de confidentialité</a>.</p>
<p>Le site existe aussi en <a href="/de/" hreflang="de-CH" lang="de-CH">allemand</a>.</p>
<p class="stand">{STAND['fr']}</p>'''
        title, desc = 'Calculateurs suisses : heures, salaire, TVA, IBAN', 'Calculateurs gratuits pour la Suisse : salaire brut-net, loyer, heures de travail, salaire horaire, TVA, dates, IBAN et CV suisse.'
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

page('priv', 'de', 'Datenschutzerklärung – Schweizer Rechner', 'Datenschutz bei Schweizer Rechner: keine Cookies, anonyme Besucherzählung ohne Cookies, alle Berechnungen nur im Browser.', f'''<h1>Datenschutzerklärung</h1>
<h2>Verantwortlich</h2>
<p>Thibaut Keller, Route des Riaux 1, 1782 Lossy, Schweiz. E-Mail: <a href="mailto:kontakt@schweizer-rechner.ch">kontakt@schweizer-rechner.ch</a></p>
<h2>Grundsatz</h2>
<p>Diese Website ist so gebaut, dass möglichst wenige Personendaten anfallen. Sie richtet sich nach dem Schweizer Bundesgesetz über den Datenschutz (DSG).</p>
<h2>Berechnungen</h2>
<p>Alle Rechner laufen ausschliesslich in Ihrem Browser. Ihre Eingaben (Zeiten, Beträge, Prozentwerte, Angaben im Lebenslauf und ein allfälliges Foto) werden nicht an uns oder an Dritte übermittelt und nicht gespeichert. Einen Lebenslauf-Entwurf können Sie selbst als Datei auf Ihr Gerät herunterladen; diese Datei erhalten wir nicht.</p>
<h2>Cookies und Tracking</h2>
<p>Die Website setzt keine Cookies. Um zu sehen, welche Seiten genutzt werden, zählen wir Seitenaufrufe mit Cloudflare Web Analytics (Cloudflare Inc., USA). Dieser Dienst setzt keine Cookies, verwendet keinen Fingerabdruck des Browsers und erstellt keine Profile von Besucherinnen und Besuchern; wir sehen nur zusammengefasste Zahlen (z. B. Aufrufe pro Seite, Land, Gerätetyp). Ihre Eingaben in den Rechnern werden dabei nie übermittelt.</p>
<h2>Hosting und Server-Logdaten</h2>
<p>Die Website wird bei GitHub Pages (GitHub Inc., USA) gehostet. Beim Aufruf einer Seite kann der Hosting-Anbieter technisch notwendige Daten verarbeiten, zum Beispiel IP-Adresse, Datum und Uhrzeit, aufgerufene Seite und Browsertyp. Diese Daten dienen dem sicheren Betrieb der Website.</p>
<h2>Geplant: Werbung mit Google AdSense</h2>
<p>Es ist geplant, die Website künftig mit Werbung über Google AdSense zu finanzieren. Google kann dabei eigene Cookies und ähnliche Technologien einsetzen. Bevor Werbung eingebunden wird, wird diese Datenschutzerklärung angepasst und, wo nötig, ein Einwilligungsbanner eingerichtet, mit dem Sie selbst entscheiden können.</p>
<h2>E-Mail-Kontakt</h2>
<p>Wenn Sie uns per E-Mail schreiben, verwenden wir Ihre Angaben nur, um Ihre Anfrage zu beantworten.</p>
<h2>Ihre Rechte</h2>
<p>Sie können Auskunft über Ihre Daten verlangen sowie deren Berichtigung oder Löschung beantragen. Schreiben Sie dazu an die oben genannte E-Mail-Adresse.</p>
<p class="stand">{STAND['de']}</p>''', crumbs='Datenschutz')

page('priv', 'fr', 'Politique de confidentialité – Calculateurs suisses', 'Confidentialité sur Calculateurs suisses : pas de cookies, comptage anonyme des visites sans cookie, tous les calculs dans le navigateur.', f'''<h1>Politique de confidentialité</h1>
<h2>Responsable</h2>
<p>Thibaut Keller, Route des Riaux 1, 1782 Lossy, Suisse. E-mail : <a href="mailto:kontakt@schweizer-rechner.ch">kontakt@schweizer-rechner.ch</a></p>
<h2>Principe</h2>
<p>Ce site est conçu pour traiter le moins possible de données personnelles. Il suit la loi fédérale suisse sur la protection des données (LPD).</p>
<h2>Calculs</h2>
<p>Tous les calculateurs fonctionnent uniquement dans votre navigateur. Vos saisies (horaires, montants, pourcentages, données du CV et photo éventuelle) ne sont transmises ni à nous ni à des tiers, et ne sont pas enregistrées. Vous pouvez télécharger vous-même un brouillon de CV sous forme de fichier sur votre appareil ; nous ne recevons pas ce fichier.</p>
<h2>Cookies et suivi</h2>
<p>Le site n’utilise aucun cookie. Pour savoir quelles pages sont utilisées, nous comptons les pages vues avec Cloudflare Web Analytics (Cloudflare Inc., États-Unis). Ce service ne dépose aucun cookie, n’utilise pas d’empreinte du navigateur et ne crée pas de profil des visiteurs ; nous ne voyons que des chiffres globaux (par ex. visites par page, pays, type d’appareil). Vos saisies dans les calculateurs ne sont jamais transmises.</p>
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
# Tool and home pages changed on 2026-11-25 (new tools, new links); privacy page updated for the CV tool.
LASTMOD = {k: '2026-11-25' for k in PAIRS if k not in ('imp', 'contact')}
urls = []
for key, (de, fr) in PAIRS.items():
    for p in (de, fr):
        urls.append(f'''  <url>
    <loc>{BASE}{p}</loc>
    <lastmod>{LASTMOD.get(key, '2026-11-24')}</lastmod>
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
