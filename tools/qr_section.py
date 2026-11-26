# QR-bill page section, exec'd by gen_site.py inside its namespace (uses tool_page, WORDCOUNT).
# =====================================================================
# 11. Swiss QR-bill generator (QR-Rechnung / facture QR)
# =====================================================================
QR_SRC = {
    'ig_de': 'https://www.six-group.com/dam/download/banking-services/standardization/qr-bill/ig-qr-bill-v2.4-de.pdf',
    'ig_fr': 'https://www.six-group.com/dam/download/banking-services/standardization/qr-bill/ig-qr-bill-v2.4-fr.pdf',
    'sme_de': 'https://www.six-group.com/dam/download/banking-services/standardization/qr-bill/factsheet-qr-bill-transition-period-sme-de.pdf',
    'pf_de': 'https://www.postfinance.ch/de/unternehmen/wissen/news/adressen-anpassungen.html',
}


def qr_tool(lang):
    de = lang == 'de'
    L = dict(
        h='QR-Rechnung erstellen', cred='Zahlungsempfänger (Konto / Zahlbar an)', iban='IBAN oder QR-IBAN',
        iban_h='Nur CH- oder LI-IBAN, z. B. CH44 3199 9123 0008 8901 2', name='Name oder Firma', street='Strasse',
        no='Nr.', zip='PLZ', town='Ort', country='Land', pay='Zahlung', amount='Betrag (leer = Zahler füllt aus)',
        cur='Währung', ref='Referenz', number='Rechnungsnummer', makeref='Referenz erzeugen', refl='Referenz',
        ref_h='Mit QR-IBAN: QR-Referenz (27 Ziffern). Mit normaler IBAN: leer lassen oder RF-Referenz.',
        msg='Zusätzliche Informationen (max. 140 Zeichen)', msg_h='z. B. Rechnung 2026117 vom 26.11.2026',
        debtor='Adresse des Zahlungspflichtigen angeben', dhead='Zahlungspflichtiger (Zahlbar durch)',
        billlang='Sprache des Zahlteils', print='Drucken / als PDF speichern',
        print_h='Druckt eine A4-Seite mit dem Zahlteil unten (210 × 105 mm). Im Druckfenster «Als PDF speichern» wählen, Skalierung 100 %.',
        example='Beispiel laden', clear='Alles löschen', preview='Vorschau des Zahlteils',
        privacy='Ihre Angaben bleiben in diesem Browserfenster. Nichts wird gesendet oder gespeichert.',
        noscript='Für den QR-Rechnungs-Generator wird JavaScript benötigt.',
    ) if de else dict(
        h='Créer une facture QR', cred='Bénéficiaire (Compte / Payable à)', iban='IBAN ou QR-IBAN',
        iban_h='IBAN CH ou LI uniquement, p. ex. CH44 3199 9123 0008 8901 2', name='Nom ou entreprise', street='Rue',
        no='N°', zip='NPA', town='Localité', country='Pays', pay='Paiement', amount='Montant (vide = le payeur le remplit)',
        cur='Monnaie', ref='Référence', number='Numéro de facture', makeref='Créer la référence', refl='Référence',
        ref_h='Avec une QR-IBAN : référence QR (27 chiffres). Avec une IBAN normale : laisser vide ou référence RF.',
        msg='Informations supplémentaires (140 caractères max.)', msg_h='p. ex. Facture 2026117 du 26.11.2026',
        debtor='Indiquer l’adresse du payeur', dhead='Payeur (Payable par)',
        billlang='Langue de la section paiement', print='Imprimer / enregistrer en PDF',
        print_h='Imprime une page A4 avec la section paiement en bas (210 × 105 mm). Dans la fenêtre d’impression, choisissez « Enregistrer au format PDF », échelle 100 %.',
        example='Charger un exemple', clear='Tout effacer', preview='Aperçu de la section paiement',
        privacy='Vos données restent dans cette fenêtre du navigateur. Rien n’est envoyé ni enregistré.',
        noscript='Le générateur de facture QR nécessite JavaScript.',
    )

    def f(name, label, hint='', extra='', typ='text'):
        return (f'<div class="field"><label for="qr-{name}">{label}</label>'
                f'<input type="{typ}" id="qr-{name}" name="{name}" autocomplete="off"{extra}'
                + (f' aria-describedby="qr-{name}-h"' if hint else '') + '>'
                + (f'<span class="note" id="qr-{name}-h">{hint}</span>' if hint else '') + '</div>')

    def addr(p, head):
        ml = lambda n: ' maxlength="%d"' % n
        name = f(p + 'name', L['name'], extra=ml(70))
        street = f(p + 'street', L['street'], extra=ml(70))
        no = f(p + 'no', L['no'], extra=ml(16))
        zp = f(p + 'zip', L['zip'], extra=ml(16))
        town = f(p + 'town', L['town'], extra=ml(35))
        country = f(p + 'country', L['country'], extra=' value="CH" maxlength="2" autocapitalize="characters"')
        return (f'<div class="row">{name}</div><div class="row">{street}{no}</div>'
                f'<div class="row">{zp}{town}{country}</div>')

    langs = ''.join(f'<option value="{v}"{" selected" if v == lang else ""} lang="{v}">{t}</option>'
                    for v, t in [('de', 'Deutsch'), ('fr', 'Français'), ('it', 'Italiano'), ('en', 'English')])
    return f'''<section class="tool qr-tool" data-tool="qr" aria-labelledby="tool-h">
<h2 id="tool-h">{L['h']}</h2>
<p class="note">{L['privacy']}</p>
<p><button type="button" class="btn-sec qr-example">{L['example']}</button> <button type="button" class="btn-sec qr-clear">{L['clear']}</button></p>
<form novalidate>
<fieldset><legend>{L['cred']}</legend>
{f('iban', L['iban'], L['iban_h'], ' spellcheck="false" autocapitalize="characters" maxlength="34"')}
{addr('', L['cred'])}
</fieldset>
<fieldset><legend>{L['pay']}</legend>
<div class="row">{f('amount', L['amount'], extra=' inputmode="decimal"')}
<div class="field"><label for="qr-currency">{L['cur']}</label><select id="qr-currency" name="currency"><option>CHF</option><option>EUR</option></select></div></div>
<div class="row">{f('number', L['number'], extra=' maxlength="26"')}
<div class="field"><button type="button" class="btn-sec qr-makeref">{L['makeref']}</button></div></div>
<div class="field"><label for="qr-reference">{L['refl']}</label><input type="text" id="qr-reference" name="reference" autocomplete="off" spellcheck="false" maxlength="40" aria-describedby="qr-ref-h qr-ref-hint"><span class="note" id="qr-ref-h">{L['ref_h']}</span><span class="note" id="qr-ref-hint" aria-live="polite"></span></div>
{f('message', L['msg'], L['msg_h'], ' maxlength="140"')}
</fieldset>
<div class="choice field"><label><input type="checkbox" name="debtor"> {L['debtor']}</label></div>
<fieldset class="qr-debtor" hidden><legend>{L['dhead']}</legend>
{addr('d_', L['dhead'])}
</fieldset>
<div class="field"><label for="qr-billlang">{L['billlang']}</label><select id="qr-billlang" name="billlang">{langs}</select></div>
</form>
<div class="result" aria-live="polite"></div>
<div class="qr-preview" hidden>
<h3>{L['preview']}</h3>
<div class="qr-sheet"></div>
<p><button type="button" class="btn qr-print" disabled>{L['print']}</button></p>
<p class="note">{L['print_h']}</p>
</div>
<noscript><p>{L['noscript']}</p></noscript>
</section>'''


QR_ART_DE = '''<h2>So funktioniert der Generator</h2>
<p>Geben Sie Ihre IBAN und Ihre Adresse als Zahlungsempfänger ein, dann den Betrag und eine Mitteilung. Der Generator prüft jede Angabe sofort und zeigt den fertigen Zahlteil mit Empfangsschein und Swiss QR Code. Mit «Drucken / als PDF speichern» erhalten Sie eine A4-Seite mit dem Zahlteil unten, so wie ihn Banken und Post erwarten. Sie können die Seite ausdrucken oder als PDF an Ihre Rechnung anhängen.</p>
<p>Der Betrag ist freiwillig: Lassen Sie ihn leer, erscheint ein Feld mit Eckmarken, in das der Zahler den Betrag selbst schreibt – praktisch für Spenden oder Mitgliederbeiträge.</p>
<h2>IBAN oder QR-IBAN: welche Referenz?</h2>
<p>Mit einer <strong>normalen IBAN</strong> können Sie ohne Referenz arbeiten oder eine RF-Referenz (Creditor Reference nach ISO 11649) verwenden. Mit einer <strong>QR-IBAN</strong> – erkennbar an der Bank-Identifikation 30000 bis 31999 an den Stellen 5 bis 9 – ist eine QR-Referenz mit 27 Ziffern Pflicht. Die QR-IBAN gibt Ihnen die Bank, wenn Sie Zahlungen automatisch zuordnen wollen. Geben Sie Ihre Rechnungsnummer ein und klicken Sie auf «Referenz erzeugen»: Der Generator baut daraus die passende QR-Referenz (mit Prüfziffer Modulo 10 rekursiv) oder RF-Referenz (Modulo 97).</p>
<h2>Strukturierte Adressen seit November 2025</h2>
<p>Seit dem 21. November 2025 sind im Swiss QR Code nur noch strukturierte Adressen erlaubt: Strasse, Hausnummer, PLZ und Ort stehen in getrennten Feldern (Adresstyp «S»). Die alte, kombinierte Adresse in zwei Freitextzeilen (Typ «K») gilt nicht mehr. Für die QR-Rechnung sind mindestens Name, PLZ, Ort und Land nötig. Dieser Generator erstellt ausschliesslich strukturierte Adressen.</p>
<h2>Beispiel</h2>
<p>Eine Malerfirma in Zürich stellt einer Kundin in Lausanne CHF 1'250.50 in Rechnung, Rechnungsnummer 2026117. Mit ihrer QR-IBAN erzeugt der Generator die QR-Referenz 00 00000 00000 00000 00202 61178 und den Zahlteil mit beiden Adressen. Die Kundin scannt den QR-Code in ihrer Banking-App: Betrag, Konto und Referenz sind sofort ausgefüllt, und die Firma sieht beim Zahlungseingang, welche Rechnung bezahlt ist.</p>
<h2>Grenzen des Generators</h2>
<p>Der Generator erstellt einen Zahlteil pro Seite, ohne Rechnungsbriefkopf, ohne Alternative Verfahren und ohne Rechnungsinformationen (Swico-Syntax). Für viele Rechnungen pro Monat ist eine Buchhaltungssoftware praktischer. Vor dem ersten Versand: Drucken Sie den Zahlteil in Originalgrösse (100 %) und scannen Sie ihn einmal mit Ihrer eigenen Banking-App.</p>'''

QR_FAQ_DE = [
    ('Ist der QR-Rechnungs-Generator kostenlos?',
     'Ja, ohne Anmeldung und ohne Wasserzeichen. Alles läuft in Ihrem Browser; Ihre IBAN und Adressen werden nicht gesendet und nicht gespeichert.'),
    ('Brauche ich eine QR-IBAN?',
     'Nein. Eine normale IBAN genügt, dann ohne Referenz oder mit RF-Referenz. Die QR-IBAN mit QR-Referenz lohnt sich, wenn Ihre Bank Zahlungseingänge automatisch Ihren Rechnungen zuordnen soll.'),
    ('Warum meldet der Generator meine Adresse als unvollständig?',
     'Seit November 2025 verlangt die QR-Rechnung strukturierte Adressen. Name, PLZ, Ort und Land sind Pflicht; Strasse und Hausnummer gehören in getrennte Felder.'),
    ('Kann ich eine QR-Rechnung ohne Betrag erstellen?',
     'Ja. Lassen Sie das Feld Betrag leer. Auf dem Zahlteil erscheint dann ein leeres Feld mit Eckmarken, in das der Zahler den Betrag schreibt.'),
    ('Kann ich eine QR-Rechnung in Euro erstellen?',
     'Ja, mit einer normalen CH- oder LI-IBAN. Mit einer QR-IBAN und QR-Referenz ist nur CHF möglich.'),
    ('Wie drucke ich den Zahlteil richtig?',
     'Auf weissem A4-Papier, Skalierung 100 % (nicht «an Seite anpassen»). Der Zahlteil misst 210 × 105 mm und steht unten auf der Seite; die gestrichelten Linien zeigen, wo abgetrennt wird.'),
]

QR_ART_FR = '''<h2>Comment fonctionne le générateur</h2>
<p>Saisissez votre IBAN et votre adresse de bénéficiaire, puis le montant et une communication. Le générateur contrôle chaque donnée immédiatement et affiche la section paiement complète avec le récépissé et le Swiss QR Code. Avec « Imprimer / enregistrer en PDF », vous obtenez une page A4 avec la section paiement en bas, comme l’attendent les banques et la Poste. Vous pouvez l’imprimer ou la joindre en PDF à votre facture.</p>
<p>Le montant est facultatif : si vous le laissez vide, un champ avec des coins apparaît, dans lequel le payeur inscrit lui-même le montant – pratique pour des dons ou des cotisations.</p>
<h2>IBAN ou QR-IBAN : quelle référence ?</h2>
<p>Avec une <strong>IBAN normale</strong>, vous pouvez travailler sans référence ou utiliser une référence RF (Creditor Reference selon ISO 11649). Avec une <strong>QR-IBAN</strong> – reconnaissable à son identifiant de banque entre 30000 et 31999 aux positions 5 à 9 – une référence QR à 27 chiffres est obligatoire. La banque vous attribue une QR-IBAN si vous voulez que les paiements soient rapprochés automatiquement. Saisissez votre numéro de facture et cliquez sur « Créer la référence » : le générateur en tire la référence QR (clé modulo 10 récursif) ou la référence RF (modulo 97).</p>
<h2>Adresses structurées depuis novembre 2025</h2>
<p>Depuis le 21 novembre 2025, seules les adresses structurées sont admises dans le Swiss QR Code : rue, numéro, NPA et localité figurent dans des champs séparés (type d’adresse « S »). L’ancienne adresse combinée en deux lignes libres (type « K ») n’est plus valable. Pour la QR-facture, au moins le nom, le NPA, la localité et le pays sont nécessaires. Ce générateur crée uniquement des adresses structurées.</p>
<h2>Exemple</h2>
<p>Une entreprise de peinture de Zurich facture CHF 1'250.50 à une cliente de Lausanne, facture n° 2026117. Avec sa QR-IBAN, le générateur crée la référence QR 00 00000 00000 00000 00202 61178 et la section paiement avec les deux adresses. La cliente scanne le code QR dans son app bancaire : montant, compte et référence sont remplis, et l’entreprise voit à l’encaissement quelle facture est payée.</p>
<h2>Limites du générateur</h2>
<p>Le générateur crée une section paiement par page, sans en-tête de facture, sans procédures alternatives et sans informations de facture (syntaxe Swico). Pour de nombreuses factures par mois, un logiciel de comptabilité est plus pratique. Avant le premier envoi : imprimez la section paiement en taille réelle (100 %) et scannez-la une fois avec votre propre app bancaire.</p>'''

QR_FAQ_FR = [
    ('Le générateur de facture QR est-il gratuit ?',
     'Oui, sans inscription et sans filigrane. Tout se passe dans votre navigateur ; votre IBAN et vos adresses ne sont ni envoyées ni enregistrées.'),
    ('Ai-je besoin d’une QR-IBAN ?',
     'Non. Une IBAN normale suffit, sans référence ou avec une référence RF. La QR-IBAN avec référence QR est utile si votre banque doit rapprocher automatiquement les paiements de vos factures.'),
    ('Pourquoi le générateur signale-t-il mon adresse comme incomplète ?',
     'Depuis novembre 2025, la QR-facture exige des adresses structurées. Nom, NPA, localité et pays sont obligatoires ; la rue et le numéro vont dans des champs séparés.'),
    ('Peut-on créer une facture QR sans montant ?',
     'Oui. Laissez le champ montant vide. Un champ vide avec des coins apparaît alors sur la section paiement, et le payeur y inscrit le montant.'),
    ('Peut-on créer une facture QR en euros ?',
     'Oui, avec une IBAN CH ou LI normale. Avec une QR-IBAN et une référence QR, seul le CHF est possible.'),
    ('Comment bien imprimer la section paiement ?',
     'Sur papier A4 blanc, à l’échelle 100 % (pas « ajuster à la page »). La section paiement mesure 210 × 105 mm et se trouve en bas de la page ; les lignes pointillées indiquent où la détacher.'),
]

QRSRC = {
    'de': [src_link('SIX, Schweizer Implementation Guidelines QR-Rechnung, Version 2.4', QR_SRC['ig_de']),
           src_link('SIX, Merkblatt QR-Rechnung – Übergangsfrist 2025–2026 (KMU)', QR_SRC['sme_de']),
           src_link('PostFinance, Anpassungen bei den Adressen', QR_SRC['pf_de'])],
    'fr': [src_link('SIX, Implementation Guidelines suisses pour la QR-facture, version 2.4', QR_SRC['ig_fr']),
           src_link('SIX, fiche « QR-Rechnung – Übergangsfrist 2025–2026 » (PME, en allemand)', QR_SRC['sme_de']),
           src_link('PostFinance, adaptations des adresses (en allemand)', QR_SRC['pf_de'])],
}

WORDCOUNT['qr_de'] = tool_page(
    'qr', 'de', 'QR-Rechnung erstellen: kostenloser Generator',
    'QR-Rechnung kostenlos erstellen: Zahlteil mit Swiss QR Code als PDF, mit QR-IBAN, QR- oder RF-Referenz und strukturierter Adresse. Ohne Anmeldung.',
    'QR-Rechnung erstellen',
    'Zahlteil mit Empfangsschein und Swiss QR Code erstellen – mit IBAN oder QR-IBAN, als PDF oder zum Drucken. Kostenlos, ohne Anmeldung.',
    qr_tool('de'), QR_ART_DE, QR_FAQ_DE, QRSRC['de'], 'FinanceApplication', script='/js/qr-ui.js')
WORDCOUNT['qr_fr'] = tool_page(
    'qr', 'fr', 'Créer une facture QR gratuitement (Suisse)',
    'Créez une QR-facture gratuite : section paiement avec Swiss QR Code en PDF, QR-IBAN, référence QR ou RF, adresse structurée. Sans inscription.',
    'Créer une facture QR',
    'Section paiement avec récépissé et Swiss QR Code – avec IBAN ou QR-IBAN, en PDF ou à imprimer. Gratuit, sans inscription.',
    qr_tool('fr'), QR_ART_FR, QR_FAQ_FR, QRSRC['fr'], 'FinanceApplication', script='/js/qr-ui.js')
