# app.py
# Run locally:
#   pip install streamlit
#   streamlit run app.py
#
# requirements.txt for deployment:
#   streamlit

import random
import re
from collections import Counter

import streamlit as st

st.set_page_config(
    page_title="German A1 Sentence Builder",
    page_icon="🇩🇪",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    .main {
        background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%);
    }
    .hero {
        background: rgba(255,255,255,0.92);
        border: 1px solid #e5e7eb;
        border-radius: 28px;
        padding: 34px;
        margin-bottom: 22px;
        box-shadow: 0 16px 38px rgba(15, 23, 42, 0.08);
        position: relative;
        overflow: hidden;
    }
    .hero:before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 6px;
        background: linear-gradient(90deg, #2563eb, #22c55e, #f59e0b);
    }
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: #eff6ff;
        color: #1e40af;
        border: 1px solid #bfdbfe;
        border-radius: 999px;
        padding: 7px 12px;
        font-weight: 800;
        margin-bottom: 14px;
    }
    .hero h1 {
        font-size: 3rem;
        line-height: 1.05;
        letter-spacing: -0.04em;
        margin: 0 0 14px 0;
        color: #111827;
    }
    .hero p {
        color: #4b5563;
        font-size: 1.07rem;
        max-width: 980px;
    }
    .metric-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 20px;
        padding: 18px;
        box-shadow: 0 10px 24px rgba(15,23,42,0.05);
        min-height: 110px;
    }
    .metric-card strong {
        display: block;
        font-size: 1.8rem;
        color: #111827;
    }
    .metric-card span {
        color: #6b7280;
        font-weight: 600;
    }
    .rule-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 20px;
        padding: 18px;
        box-shadow: 0 8px 20px rgba(15,23,42,0.04);
        height: 100%;
        color: #111827 !important;
    }
    .rule-card h3 {
        color: #111827 !important;
        font-size: 1.05rem;
        margin-bottom: 8px;
    }
    .rule-card p, .rule-card b, .rule-card strong {
        color: #111827 !important;
    }
    .formula {
        background: #eff6ff;
        color: #1e3a8a !important;
        border: 1px solid #bfdbfe;
        border-radius: 999px;
        padding: 4px 10px;
        font-weight: 800;
        display: inline-block;
        margin: 4px 0;
        white-space: normal;
    }
    .stMarkdown, .stText, .stCaption {
        color: inherit;
    }
    
    .exercise-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 22px;
        padding: 20px;
        box-shadow: 0 10px 24px rgba(15,23,42,0.05);
        margin-bottom: 16px;
    }
    .topic-pill {
        display: inline-block;
        background: #f3f4f6;
        color: #4b5563;
        border-radius: 999px;
        padding: 4px 10px;
        font-size: 0.82rem;
        font-weight: 800;
    }
    .answer-box {
        background: #ecfdf5;
        border: 1px solid #bbf7d0;
        color: #14532d;
        border-radius: 14px;
        padding: 12px;
        font-weight: 800;
        margin-top: 10px;
    }
    .wrong-box {
        background: #fef2f2;
        border: 1px solid #fecaca;
        color: #991b1b;
        border-radius: 14px;
        padding: 12px;
        font-weight: 800;
        margin-top: 10px;
    }
    .info-box {
        background: #fffbeb;
        border: 1px solid #fde68a;
        color: #78350f;
        border-radius: 16px;
        padding: 14px;
        margin: 12px 0;
    }
    div[data-testid="stButton"] button {
        border-radius: 999px;
        font-weight: 800;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def normalize(text: str) -> str:
    text = text.strip().lower()
    text = text.replace("ä", "a").replace("ö", "o").replace("ü", "u").replace("ß", "ss")
    text = re.sub(r"[.!?]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def deterministic_shuffle(words, seed_text):
    rng = random.Random(seed_text)
    shuffled = words[:]
    rng.shuffle(shuffled)
    if shuffled == words and len(words) > 1:
        shuffled = shuffled[::-1]
    return shuffled


def init_state():
    defaults = {
        "correct": 0,
        "tried": 0,
        "answered_keys": set(),
        "current_order": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def record_result(key, is_correct):
    if key not in st.session_state.answered_keys:
        st.session_state.tried += 1
        if is_correct:
            st.session_state.correct += 1
        st.session_state.answered_keys.add(key)


BASE_SENTENCES = [
    ("Ich heiße Pradum.", "My name is Pradum.", "introduction"),
    ("Ich komme aus Indien.", "I come from India.", "introduction"),
    ("Ich wohne in Berlin.", "I live in Berlin.", "introduction"),
    ("Ich bin Student.", "I am a student.", "introduction"),
    ("Ich lerne Deutsch.", "I am learning German.", "learning"),
    ("Wir lernen heute Deutsch.", "We are learning German today.", "learning"),
    ("Du sprichst gut Englisch.", "You speak English well.", "language"),
    ("Bitte sprechen Sie langsam.", "Please speak slowly.", "communication"),
    ("Kannst du das wiederholen?", "Can you repeat that?", "communication"),
    ("Ich habe eine Frage.", "I have a question.", "communication"),
    ("Meine Mutter wohnt in Indien.", "My mother lives in India.", "family"),
    ("Mein Vater arbeitet viel.", "My father works a lot.", "family"),
    ("Meine Schwester studiert Medizin.", "My sister studies medicine.", "family"),
    ("Mein Bruder spielt Fußball.", "My brother plays football.", "family"),
    ("Wir haben zwei Kinder.", "We have two children.", "family"),
    ("Ich trinke Wasser.", "I drink water.", "food"),
    ("Du isst Brot.", "You eat bread.", "food"),
    ("Er trinkt Kaffee.", "He drinks coffee.", "food"),
    ("Sie isst einen Apfel.", "She eats an apple.", "food"),
    ("Wir essen heute Pizza.", "We are eating pizza today.", "food"),
    ("Ich möchte einen Tee.", "I would like a tea.", "food"),
    ("Das Essen schmeckt gut.", "The food tastes good.", "food"),
    ("Ich gehe zur Schule.", "I go to school.", "school"),
    ("Du machst die Hausaufgaben.", "You do the homework.", "school"),
    ("Er liest ein Buch.", "He reads a book.", "school"),
    ("Sie schreibt einen Satz.", "She writes a sentence.", "school"),
    ("Wir haben morgen Unterricht.", "We have class tomorrow.", "school"),
    ("Ich verstehe die Frage.", "I understand the question.", "school"),
    ("Ich arbeite im Büro.", "I work in the office.", "work"),
    ("Du hast heute frei.", "You are free today.", "work"),
    ("Er schreibt eine E-Mail.", "He writes an email.", "work"),
    ("Sie hat einen Termin.", "She has an appointment.", "work"),
    ("Wir beginnen um neun Uhr.", "We start at nine o'clock.", "work"),
    ("Ich mache eine Pause.", "I take a break.", "work"),
    ("Ich fahre mit dem Bus.", "I travel by bus.", "travel"),
    ("Du nimmst die Bahn.", "You take the train.", "travel"),
    ("Er fährt nach München.", "He travels to Munich.", "travel"),
    ("Sie geht zum Bahnhof.", "She goes to the train station.", "travel"),
    ("Wir reisen am Samstag.", "We travel on Saturday.", "travel"),
    ("Ich kaufe ein Ticket.", "I buy a ticket.", "travel"),
    ("Ich stehe um sieben Uhr auf.", "I get up at seven o'clock.", "daily routine"),
    ("Du duschst am Morgen.", "You shower in the morning.", "daily routine"),
    ("Er frühstückt um acht Uhr.", "He has breakfast at eight o'clock.", "daily routine"),
    ("Sie geht zur Arbeit.", "She goes to work.", "daily routine"),
    ("Wir essen am Abend.", "We eat in the evening.", "daily routine"),
    ("Ich schlafe um elf Uhr.", "I sleep at eleven o'clock.", "daily routine"),
    ("Ich kaufe Milch.", "I buy milk.", "shopping"),
    ("Du bezahlst mit Karte.", "You pay by card.", "shopping"),
    ("Er sucht eine Jacke.", "He is looking for a jacket.", "shopping"),
    ("Sie braucht neue Schuhe.", "She needs new shoes.", "shopping"),
    ("Wir gehen in den Supermarkt.", "We go to the supermarket.", "shopping"),
    ("Wie viel kostet das?", "How much does that cost?", "shopping"),
    ("Ich bin krank.", "I am sick.", "health"),
    ("Du hast Fieber.", "You have a fever.", "health"),
    ("Er geht zum Arzt.", "He goes to the doctor.", "health"),
    ("Sie braucht Medizin.", "She needs medicine.", "health"),
    ("Ich brauche einen Termin.", "I need an appointment.", "health"),
    ("Ich spiele gern Fußball.", "I like playing football.", "hobbies"),
    ("Du hörst gern Musik.", "You like listening to music.", "hobbies"),
    ("Er liest gern Bücher.", "He likes reading books.", "hobbies"),
    ("Sie tanzt am Abend.", "She dances in the evening.", "hobbies"),
    ("Wir kochen zusammen.", "We cook together.", "hobbies"),
    ("Ich wohne in einer Wohnung.", "I live in an apartment.", "home"),
    ("Du hast ein Zimmer.", "You have a room.", "home"),
    ("Er öffnet das Fenster.", "He opens the window.", "home"),
    ("Sie schließt die Tür.", "She closes the door.", "home"),
    ("Wir sitzen im Wohnzimmer.", "We are sitting in the living room.", "home"),
    ("Wie heißt du?", "What is your name?", "question"),
    ("Wo wohnst du?", "Where do you live?", "question"),
    ("Woher kommst du?", "Where do you come from?", "question"),
    ("Was machst du heute?", "What are you doing today?", "question"),
    ("Wann kommst du nach Hause?", "When are you coming home?", "question"),
    ("Warum lernst du Deutsch?", "Why are you learning German?", "question"),
    ("Ich komme nicht aus Deutschland.", "I do not come from Germany.", "negation"),
    ("Du hast keine Zeit.", "You have no time.", "negation"),
    ("Er trinkt keinen Kaffee.", "He drinks no coffee.", "negation"),
    ("Sie isst kein Fleisch.", "She eats no meat.", "negation"),
    ("Wir gehen heute nicht ins Kino.", "We are not going to the cinema today.", "negation"),
    ("Ich möchte Deutsch lernen.", "I would like to learn German.", "modal verbs"),
    ("Du kannst gut kochen.", "You can cook well.", "modal verbs"),
    ("Er muss heute arbeiten.", "He must work today.", "modal verbs"),
    ("Sie kann morgen kommen.", "She can come tomorrow.", "modal verbs"),
    ("Wir wollen ins Kino gehen.", "We want to go to the cinema.", "modal verbs"),
    ("Heute regnet es.", "It is raining today.", "weather"),
    ("Morgen scheint die Sonne.", "The sun shines tomorrow.", "weather"),
    ("Es ist sehr kalt.", "It is very cold.", "weather"),
    ("Im Sommer ist es warm.", "In summer it is warm.", "weather"),
    ("Das Wetter ist schön.", "The weather is nice.", "weather"),
    ("Ich habe einen Hund.", "I have a dog.", "animals"),
    ("Du hast eine Katze.", "You have a cat.", "animals"),
    ("Der Hund schläft im Garten.", "The dog sleeps in the garden.", "animals"),
    ("Die Katze sitzt auf dem Sofa.", "The cat sits on the sofa.", "animals"),
    ("Ich mag Tiere.", "I like animals.", "animals"),
    ("Ich bin glücklich.", "I am happy.", "feelings"),
    ("Du bist traurig.", "You are sad.", "feelings"),
    ("Er ist nervös.", "He is nervous.", "feelings"),
    ("Sie ist sehr müde.", "She is very tired.", "feelings"),
    ("Ich habe Hunger.", "I am hungry.", "feelings"),
    ("Der Tisch ist braun.", "The table is brown.", "colors"),
    ("Die Blume ist rot.", "The flower is red.", "colors"),
    ("Das Auto ist schwarz.", "The car is black.", "colors"),
    ("Meine Tasche ist blau.", "My bag is blue.", "colors"),
    ("Sein Hemd ist weiß.", "His shirt is white.", "colors"),
    ("Ich habe heute einen Termin.", "I have an appointment today.", "time"),
    ("Du kommst um acht Uhr.", "You come at eight o'clock.", "time"),
    ("Er geht am Montag arbeiten.", "He goes to work on Monday.", "time"),
    ("Sie lernt am Abend Deutsch.", "She learns German in the evening.", "time"),
    ("Heute ist Freitag.", "Today is Friday.", "time"),
    ("Ich bin im Restaurant.", "I am in the restaurant.", "restaurant"),
    ("Du bestellst eine Suppe.", "You order a soup.", "restaurant"),
    ("Er nimmt einen Salat.", "He takes a salad.", "restaurant"),
    ("Sie bezahlt die Rechnung.", "She pays the bill.", "restaurant"),
    ("Kann ich bitte bezahlen?", "Can I pay, please?", "restaurant"),
]

EXTRA_SENTENCES = [
    ("Ich brauche heute Hilfe.", "I need help today.", "communication"),
    ("Kannst du bitte langsam sprechen?", "Can you please speak slowly?", "communication"),
    ("Ich lerne neue Wörter.", "I am learning new words.", "learning"),
    ("Der Satz ist sehr einfach.", "The sentence is very easy.", "learning"),
    ("Wir wiederholen die Grammatik.", "We repeat the grammar.", "learning"),
    ("Ich wohne seit Januar hier.", "I have lived here since January.", "home"),
    ("Die Wohnung hat zwei Zimmer.", "The apartment has two rooms.", "home"),
    ("Mein Zimmer ist sehr hell.", "My room is very bright.", "home"),
    ("Die Küche ist neben dem Bad.", "The kitchen is next to the bathroom.", "home"),
    ("Ich räume mein Zimmer auf.", "I tidy up my room.", "home"),
    ("Ich fahre morgen nach Potsdam.", "I am travelling to Potsdam tomorrow.", "travel"),
    ("Der Zug fährt um zehn Uhr.", "The train leaves at ten o'clock.", "travel"),
    ("Ich warte am Bahnhof.", "I wait at the train station.", "travel"),
    ("Wir steigen in den Bus ein.", "We get on the bus.", "travel"),
    ("Wo kann ich ein Ticket kaufen?", "Where can I buy a ticket?", "travel"),
    ("Ich kaufe heute Gemüse.", "I am buying vegetables today.", "shopping"),
    ("Die Tomaten sind sehr frisch.", "The tomatoes are very fresh.", "shopping"),
    ("Ich brauche noch Brot.", "I still need bread.", "shopping"),
    ("Der Supermarkt schließt um acht.", "The supermarket closes at eight.", "shopping"),
    ("Ich bezahle lieber bar.", "I prefer to pay cash.", "shopping"),
    ("Ich bestelle eine Pizza.", "I order a pizza.", "restaurant"),
    ("Die Rechnung kommt sofort.", "The bill comes immediately.", "restaurant"),
    ("Wir reservieren einen Tisch.", "We reserve a table.", "restaurant"),
    ("Das Wasser ist ohne Gas.", "The water is still.", "restaurant"),
    ("Ich esse gern Suppe.", "I like eating soup.", "restaurant"),
    ("Meine Mutter ruft mich an.", "My mother calls me.", "family"),
    ("Mein Bruder besucht mich morgen.", "My brother visits me tomorrow.", "family"),
    ("Die Kinder spielen im Garten.", "The children play in the garden.", "family"),
    ("Meine Eltern kommen am Sonntag.", "My parents come on Sunday.", "family"),
    ("Wir feiern zusammen Geburtstag.", "We celebrate birthday together.", "family"),
    ("Ich habe heute Kopfschmerzen.", "I have a headache today.", "health"),
    ("Der Arzt gibt mir Medizin.", "The doctor gives me medicine.", "health"),
    ("Ich muss viel schlafen.", "I must sleep a lot.", "health"),
    ("Die Apotheke öffnet um neun.", "The pharmacy opens at nine.", "health"),
    ("Mir geht es besser.", "I feel better.", "health"),
    ("Ich arbeite von neun bis fünf.", "I work from nine to five.", "work"),
    ("Die Kollegin erklärt das Problem.", "The colleague explains the problem.", "work"),
    ("Wir haben heute ein Meeting.", "We have a meeting today.", "work"),
    ("Ich schreibe den Bericht.", "I write the report.", "work"),
    ("Der Computer funktioniert nicht.", "The computer does not work.", "work"),
    ("Am Montag lerne ich Deutsch.", "On Monday I learn German.", "time"),
    ("Im Mai beginnt mein Kurs.", "My course begins in May.", "time"),
    ("Die Stunde dauert fünfundvierzig Minuten.", "The lesson lasts forty-five minutes.", "time"),
    ("Heute Abend habe ich Zeit.", "This evening I have time.", "time"),
    ("Morgen früh gehe ich laufen.", "Tomorrow morning I go running.", "time"),
    ("Es ist heute sehr warm.", "It is very warm today.", "weather"),
    ("Im Herbst regnet es oft.", "In autumn it often rains.", "weather"),
    ("Der Wind ist stark.", "The wind is strong.", "weather"),
    ("Ich nehme einen Regenschirm mit.", "I take an umbrella with me.", "weather"),
    ("Bei schönem Wetter gehen wir raus.", "In nice weather we go outside.", "weather"),
]

ARTICLE_PAIRS = [
    ("Mann", "der"), ("Frau", "die"), ("Kind", "das"), ("Tisch", "der"), ("Lampe", "die"), ("Buch", "das"),
    ("Wohnung", "die"), ("Computer", "der"), ("Auto", "das"), ("Schule", "die"), ("Lehrer", "der"), ("Lehrerin", "die"),
    ("Mädchen", "das"), ("Brötchen", "das"), ("Montag", "der"), ("Sommer", "der"), ("Information", "die"), ("Freiheit", "die"),
    ("Essen", "das"), ("Arbeit", "die"), ("Hund", "der"), ("Katze", "die"), ("Pferd", "das"), ("Bahnhof", "der"),
    ("Abend", "der"), ("Adresse", "die"), ("Alter", "das"), ("Apfel", "der"), ("Apotheke", "die"), ("Arzt", "der"),
    ("Ärztin", "die"), ("Aufgabe", "die"), ("Auge", "das"), ("Ausgang", "der"), ("Baby", "das"), ("Bäckerei", "die"),
    ("Bad", "das"), ("Banane", "die"), ("Bank", "die"), ("Bett", "das"), ("Bier", "das"), ("Bild", "das"),
    ("Birne", "die"), ("Bleistift", "der"), ("Blume", "die"), ("Bus", "der"), ("Café", "das"), ("Chef", "der"),
    ("Chefin", "die"), ("Deutsch", "das"), ("Dorf", "das"), ("Drucker", "der"), ("Dusche", "die"), ("Ei", "das"),
    ("E-Mail", "die"), ("Ende", "das"), ("Entschuldigung", "die"), ("Erklärung", "die"), ("Familie", "die"), ("Fahrrad", "das"),
    ("Fahrer", "der"), ("Fahrerin", "die"), ("Fenster", "das"), ("Fernseher", "der"), ("Film", "der"), ("Firma", "die"),
    ("Fisch", "der"), ("Flasche", "die"), ("Flughafen", "der"), ("Foto", "das"), ("Frage", "die"), ("Frühstück", "das"),
    ("Fuß", "der"), ("Garten", "der"), ("Geburtstag", "der"), ("Geld", "das"), ("Gemüse", "das"), ("Geschäft", "das"),
    ("Geschenk", "das"), ("Getränk", "das"), ("Glas", "das"), ("Grammatik", "die"), ("Gruppe", "die"), ("Haar", "das"),
    ("Hand", "die"), ("Handy", "das"), ("Haus", "das"), ("Hausaufgabe", "die"), ("Heft", "das"), ("Hemd", "das"),
    ("Hilfe", "die"), ("Hobby", "das"), ("Hotel", "das"), ("Hunger", "der"), ("Jacke", "die"), ("Jahr", "das"),
    ("Kaffee", "der"), ("Karte", "die"), ("Käse", "der"), ("Kasse", "die"), ("Kellner", "der"), ("Kellnerin", "die"),
    ("Kino", "das"), ("Kleid", "das"), ("Koffer", "der"), ("Kollege", "der"), ("Kollegin", "die"), ("Kopf", "der"),
    ("Krankheit", "die"), ("Küche", "die"), ("Kuchen", "der"), ("Kurs", "der"), ("Laden", "der"), ("Land", "das"),
    ("Leben", "das"), ("Leute", "die"), ("Lied", "das"), ("Markt", "der"), ("Maschine", "die"), ("Meer", "das"),
    ("Minute", "die"), ("Mittag", "der"), ("Morgen", "der"), ("Musik", "die"), ("Nachbar", "der"), ("Nachbarin", "die"),
    ("Nachricht", "die"), ("Name", "der"), ("Nase", "die"), ("Nacht", "die"), ("Nummer", "die"), ("Obst", "das"),
    ("Ohr", "das"), ("Orange", "die"), ("Papier", "das"), ("Park", "der"), ("Pause", "die"), ("Plan", "der"),
    ("Platz", "der"), ("Polizei", "die"), ("Problem", "das"), ("Rechnung", "die"), ("Regen", "der"), ("Reise", "die"),
    ("Restaurant", "das"), ("Rezept", "das"), ("Saft", "der"), ("Salat", "der"), ("Salz", "das"), ("Satz", "der"),
    ("Schlüssel", "der"), ("Schnee", "der"), ("Schrank", "der"), ("Schuh", "der"), ("Schwester", "die"), ("Sohn", "der"),
    ("Sonne", "die"), ("Spiel", "das"), ("Sprache", "die"), ("Stadt", "die"), ("Stift", "der"), ("Straße", "die"),
    ("Student", "der"), ("Studentin", "die"), ("Stunde", "die"), ("Supermarkt", "der"), ("Tasche", "die"), ("Taxi", "das"),
    ("Tee", "der"), ("Teil", "der"), ("Telefon", "das"), ("Termin", "der"), ("Ticket", "das"), ("Tochter", "die"),
    ("Toilette", "die"), ("Tomate", "die"), ("Tür", "die"), ("Uhr", "die"), ("Universität", "die"), ("Vater", "der"),
    ("Verkäufer", "der"), ("Verkäuferin", "die"), ("Vogel", "der"), ("Wand", "die"), ("Wasser", "das"), ("Weg", "der"),
    ("Wetter", "das"), ("Woche", "die"), ("Wochenende", "das"), ("Wort", "das"), ("Zeit", "die"), ("Zeitung", "die"),
    ("Zug", "der"), ("Zimmer", "das"), ("Zucker", "der"), ("Zwiebel", "die"), ("Anmeldung", "die"), ("Ankunft", "die"),
    ("Anruf", "der"), ("Anzug", "der"), ("Apartment", "das"), ("App", "die"), ("Arm", "der"), ("Artikel", "der"),
    ("Aufzug", "der"), ("Ausweis", "der"), ("Bahn", "die"), ("Balkon", "der"), ("Bauch", "der"), ("Beispiel", "das"),
    ("Beruf", "der"), ("Besuch", "der"), ("Bibliothek", "die"), ("Brief", "der"), ("Brille", "die"), ("Bruder", "der"),
    ("Büro", "das"), ("Butter", "die"), ("Cent", "der"), ("Chance", "die"), ("Datum", "das"), ("Dialog", "der"),
    ("Ding", "das"), ("Durst", "der"), ("Einladung", "die"), ("Eintritt", "der"), ("Eltern", "die"), ("Ergebnis", "das"),
    ("Fahrkarte", "die"), ("Farbe", "die"), ("Fehler", "der"), ("Feier", "die"), ("Fleisch", "das"), ("Flug", "der"),
    ("Formular", "das"), ("Freund", "der"), ("Freundin", "die"), ("Führerschein", "der"), ("Gabel", "die"), ("Garage", "die"),
    ("Gebäude", "das"), ("Gebühr", "die"), ("Gegenteil", "das"), ("Gepäck", "das"), ("Gerät", "das"), ("Geschichte", "die"),
    ("Gespräch", "das"), ("Gesundheit", "die"), ("Gewicht", "das"), ("Haltestelle", "die"), ("Hauptbahnhof", "der"), ("Haut", "die"),
    ("Heizung", "die"), ("Hose", "die"), ("Idee", "die"), ("Insel", "die"), ("Internet", "das"), ("Januar", "der"),
    ("Juli", "der"), ("Junge", "der"), ("Kamera", "die"), ("Kartoffel", "die"), ("Kaufhaus", "das"), ("Keller", "der"),
    ("Kilometer", "der"), ("Klasse", "die"), ("Klavier", "das"), ("Kneipe", "die"), ("Konto", "das"), ("Körper", "der"),
    ("Krankenhaus", "das"), ("Kugelschreiber", "der"), ("Kultur", "die"), ("Kunde", "der"), ("Kundin", "die"), ("Lage", "die"),
    ("Leitung", "die"), ("Licht", "das"), ("Liste", "die"), ("Lösung", "die"), ("Luft", "die"), ("Mahlzeit", "die"),
    ("Mai", "der"), ("Mannschaft", "die"), ("Mantel", "der"), ("Medikament", "das"), ("Messer", "das"), ("Miete", "die"),
    ("Milch", "die"), ("Moment", "der"), ("Monat", "der"), ("Museum", "das"), ("Mutter", "die"), ("Nudeln", "die"),
    ("Öl", "das"), ("Onkel", "der"), ("Opa", "der"), ("Oma", "die"), ("Ordnung", "die"), ("Paket", "das"),
    ("Pass", "der"), ("Pfeffer", "der"), ("Pizza", "die"), ("Post", "die"), ("Prüfung", "die"), ("Radio", "das"),
    ("Rathaus", "das"), ("Raum", "der"), ("Regal", "das"), ("Reis", "der"), ("Rezeption", "die"), ("Rücken", "der"),
    ("Sache", "die"), ("Schalter", "der"), ("Schiff", "das"), ("Schokolade", "die"), ("Schwimmbad", "das"), ("See", "der"),
    ("Seife", "die"), ("Sekunde", "die"), ("Sessel", "der"), ("Sicherheit", "die"), ("Situation", "die"), ("Sofa", "das"),
    ("Sport", "der"), ("Station", "die"), ("Stock", "der"), ("Straßenbahn", "die"), ("Stuhl", "der"), ("Team", "das"),
    ("Theater", "das"), ("Thema", "das"), ("Tipp", "der"), ("Treppe", "die"), ("Übung", "die"), ("U-Bahn", "die"),
    ("Urlaub", "der"), ("Verbindung", "die"), ("Verein", "der"), ("Versicherung", "die"), ("Vertrag", "der"), ("Video", "das"),
    ("Vormittag", "der"), ("Wagen", "der"), ("Wäsche", "die"), ("Wein", "der"), ("Werkstatt", "die"), ("Wohnzimmer", "das"),
    ("Zahl", "die"), ("Zentrum", "das"), ("Ziel", "das"), ("Zitrone", "die"), ("Zugticket", "das"), ("Zukunft", "die"),
    ("Ahnung", "die"), ("Anfang", "der"), ("Angst", "die"), ("April", "der"), ("August", "der"), ("Ausbildung", "die"),
    ("Ausflug", "der"), ("Auskunft", "die"), ("Badezimmer", "das"), ("Berg", "der"), ("Bestellung", "die"), ("Bewerbung", "die"),
    ("Blatt", "das"), ("Blut", "das"), ("Brot", "das"), ("Bundesland", "das"), ("Dezember", "der"), ("Donnerstag", "der"),
    ("Erdbeere", "die"), ("Februar", "der"), ("Feiertag", "der"), ("Flur", "der"), ("Freitag", "der"), ("Fundbüro", "das"),
    ("Fußball", "der"), ("Geldautomat", "der"), ("Gericht", "das"), ("Größe", "die"), ("Gutschein", "der"), ("Handschuh", "der"),
    ("Hauptstadt", "die"), ("Herbst", "der"), ("Himmel", "der"), ("Hochschule", "die"), ("Jahreszeit", "die"), ("Joghurt", "der"),
    ("Kalender", "der"), ("Kauf", "der"), ("Kilo", "das"), ("Kiosk", "der"), ("Konzert", "das"), ("Krawatte", "die"),
    ("Kreditkarte", "die"), ("Kreis", "der"), ("Kühlschrank", "der"), ("Löffel", "der"), ("Lokal", "das"), ("Lust", "die"),
    ("März", "der"), ("Maus", "die"), ("Metzgerei", "die"), ("Mikrowelle", "die"), ("Mittwoch", "der"), ("Möbel", "die"),
    ("Nachmittag", "der"), ("Norden", "der"), ("November", "der"), ("Oktober", "der"), ("Panne", "die"), ("Parkschein", "der"),
    ("Pullover", "der"), ("Quittung", "die"), ("Regenjacke", "die"), ("Reiseführer", "der"), ("Reparatur", "die"), ("Reservierung", "die"),
    ("Samstag", "der"), ("Schlafzimmer", "das"), ("Sonntag", "der"), ("Süden", "der"), ("Telefonnummer", "die"), ("Temperatur", "die"),
    ("Toast", "der"), ("Training", "das"), ("Traube", "die"), ("Umgebung", "die"), ("Unterricht", "der"), ("Vase", "die"),
    ("Verspätung", "die"), ("Viertel", "das"), ("Visum", "das"), ("Vorname", "der"), ("Wald", "der"), ("Wecker", "der"),
    ("Winter", "der"), ("Wurst", "die"), ("Zahnarzt", "der"), ("Zahnärztin", "die"), ("Zeugnis", "das"), ("Zugang", "der"),
    ("Zusammenfassung", "die"), ("Abfahrt", "die"), ("Akku", "der"), ("Angebot", "das"), ("Anleitung", "die"), ("Arbeitsplatz", "der"),
    ("Aufenthalt", "der"), ("Bahnsteig", "der"), ("Bein", "das"), ("Bereich", "der"), ("Bescheinigung", "die"), ("Betrag", "der"),
    ("Briefmarke", "die"), ("Brücke", "die"), ("Bürste", "die"), ("Dame", "die"), ("Dauer", "die"), ("Decke", "die"),
    ("Display", "das"), ("Dose", "die"), ("Ecke", "die"), ("Eingang", "der"), ("Einkauf", "der"), ("Eis", "das"),
    ("Empfehlung", "die"), ("Erfahrung", "die"), ("Fabrik", "die"), ("Fach", "das"), ("Fähigkeit", "die"), ("Fahrt", "die"),
    ("Fahrradweg", "der"), ("Fernbedienung", "die"), ("Fieber", "das"), ("Fitnessstudio", "das"), ("Flugzeug", "das"), ("Frisör", "der"),
    ("Frisörin", "die"), ("Frühling", "der"), ("Fund", "der"), ("Gast", "der"), ("Gehalt", "das"), ("Gitarre", "die"),
    ("Grenze", "die"), ("Handtuch", "das"), ("Hochzeit", "die"), ("Hut", "der"), ("Inhalt", "der"), ("Interesse", "das"),
    ("Kamm", "der"), ("Kapitel", "das"), ("Kassenbon", "der"), ("Kennwort", "das"), ("Kirche", "die"), ("Kleidung", "die"),
    ("Kopfhörer", "der"), ("Krankenversicherung", "die"), ("Kreuzung", "die"), ("Kursbuch", "das"), ("Ladekabel", "das"), ("Laptop", "der"),
    ("Lebensmittel", "die"), ("Lernkarte", "die"), ("Lieblingsfarbe", "die"), ("Linie", "die"), ("Magen", "der"), ("Meldung", "die"),
    ("Messe", "die"), ("Nachname", "der"), ("Notiz", "die"), ("Notizbuch", "das"), ("Öffnungszeit", "die"), ("Ort", "der"),
    ("Pflanze", "die"), ("Portemonnaie", "das"), ("Programm", "das"), ("Prospekt", "der"), ("Punkt", "der"), ("Rad", "das"),
    ("Regel", "die"), ("Reinigung", "die"), ("Richtung", "die"), ("Rolltreppe", "die"), ("Rucksack", "der"), ("Schere", "die"),
    ("Schild", "das"), ("Schlange", "die"), ("Schnitzel", "das"), ("Schüssel", "die"), ("Service", "der"), ("Sitzplatz", "der"),
    ("Socke", "die"), ("Sonnenbrille", "die"), ("Spaziergang", "der"), ("Steckdose", "die"), ("Steuer", "die"), ("Stockwerk", "das"),
    ("Störung", "die"), ("Strand", "der"), ("Studentenwohnheim", "das"), ("Tablet", "das"), ("Teller", "der"), ("Text", "der"),
    ("Tourist", "der"), ("Touristin", "die"), ("Tüte", "die"), ("Übernachtung", "die"), ("Unfall", "der"), ("Unterschied", "der"),
    ("Verabredung", "die"), ("Verkehr", "der"), ("Vorschlag", "der"), ("Vorstellung", "die"), ("Wartezimmer", "das"), ("Waschmaschine", "die"),
    ("Wasserflasche", "die"), ("Website", "die"), ("Welt", "die"), ("Wörterbuch", "das"), ("Zeile", "die"), ("Zettel", "der"),
]


def build_jumble_sentences():
    sentences = BASE_SENTENCES[:]
    while len(sentences) < 300:
        sentences.extend(EXTRA_SENTENCES)
    return sentences[:300]


def build_writing_sentences():
    base = [(en, de, topic) for de, en, topic in BASE_SENTENCES]
    extra = [(en, de, topic) for de, en, topic in EXTRA_SENTENCES]
    while len(base) < 300:
        base.extend(extra)
    return base[:300]


def build_articles():
    articles = ARTICLE_PAIRS[:]
    while len(articles) < 500:
        articles.extend(ARTICLE_PAIRS)
    return articles[:500]


JUMBLE_SENTENCES = build_jumble_sentences()
WRITING_SENTENCES = build_writing_sentences()
ARTICLE_DRILL = build_articles()
TOTAL_EXERCISES = len(JUMBLE_SENTENCES) + len(WRITING_SENTENCES) + len(ARTICLE_DRILL)


def render_hero():
    st.markdown(
        f"""
        <div class="hero">
            <div class="badge">● German A1 Interactive Workbook</div>
            <h1>German A1 Sentence Builder</h1>
            <p>
                A shareable practice site for German A1 learners. It trains sentence order,
                translation, articles, negation, questions, modal verbs, daily life vocabulary,
                shopping, travel, work, family, food, and simple communication.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    cards = [
        (len(JUMBLE_SENTENCES), "German word-order drills"),
        (len(WRITING_SENTENCES), "English-to-German writing drills"),
        (len(ARTICLE_DRILL), "der, die, das article drills"),
        ("A1", "simple exam-friendly German"),
    ]
    for col, (number, label) in zip([col1, col2, col3, col4], cards):
        col.markdown(
            f"""
            <div class="metric-card">
                <strong>{number}</strong>
                <span>{label}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_rules():
    st.subheader("Before You Start: A1 Tricks That Actually Help")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
            <div class="rule-card">
                <h3>Basic word order</h3>
                <span class="formula">Position 1 + Verb + Subject + Rest</span>
                <p><b>Ich wohne in Berlin.</b></p>
                <p><b>Heute wohne ich in Berlin.</b></p>
                <p>The verb usually stays in position 2.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
            <div class="rule-card">
                <h3>Yes/No questions</h3>
                <span class="formula">Verb + Subject + Rest?</span>
                <p><b>Kommst du aus Indien?</b></p>
                <p>Start with the verb when the answer is yes or no.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """
            <div class="rule-card">
                <h3>W-questions</h3>
                <span class="formula">Question word + Verb + Subject</span>
                <p><b>Wo wohnst du?</b></p>
                <p><b>Was machst du heute?</b></p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    c4, c5, c6 = st.columns(3)
    with c4:
        st.markdown(
            """
            <div class="rule-card">
                <h3>Modal verbs</h3>
                <span class="formula">Modal verb second + main verb at end</span>
                <p><b>Ich möchte Kaffee trinken.</b></p>
                <p><b>Wir können Deutsch lernen.</b></p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c5:
        st.markdown(
            """
            <div class="rule-card">
                <h3>Negation</h3>
                <p><b>nicht</b> negates verbs or adjectives.</p>
                <p><b>Ich komme nicht.</b></p>
                <p><b>kein/keine</b> negates nouns.</p>
                <p><b>Ich habe keinen Hund.</b></p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c6:
        st.markdown(
            """
            <div class="rule-card">
                <h3>Time before place</h3>
                <span class="formula">Time + Manner + Place</span>
                <p><b>Ich gehe heute mit Ali in die Schule.</b></p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.subheader("der, die, das: practical tricks")
    a, b, c = st.columns(3)
    with a:
        st.markdown(
            """
            <div class="rule-card">
                <h3>Usually der</h3>
                <p>Male people/jobs: <b>der Mann, der Lehrer</b></p>
                <p>Days/months/seasons: <b>der Montag, der Januar, der Sommer</b></p>
                <p>Many -er endings: <b>der Computer, der Drucker</b></p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with b:
        st.markdown(
            """
            <div class="rule-card">
                <h3>Usually die</h3>
                <p>Female people/jobs: <b>die Frau, die Lehrerin</b></p>
                <p>All plurals: <b>die Kinder, die Bücher</b></p>
                <p>-ung, -heit, -keit, -schaft, -tion: <b>die Wohnung, die Information</b></p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c:
        st.markdown(
            """
            <div class="rule-card">
                <h3>Usually das</h3>
                <p>-chen and -lein: <b>das Mädchen, das Brötchen</b></p>
                <p>Infinitive nouns: <b>das Essen, das Lernen</b></p>
                <p>Many young beings: <b>das Kind, das Baby</b></p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="info-box">
            <b>Important:</b> These are tricks, not perfect rules. Learn every noun with its article:
            <b>der Tisch</b>, <b>die Lampe</b>, <b>das Buch</b>. Never learn only the noun.
        </div>
        """,
        unsafe_allow_html=True,
    )


def filter_items(items, topic_index, search_text):
    selected_topic = st.session_state.get(topic_index, "All topics")
    query = search_text.strip().lower()
    filtered = []
    for item in items:
        haystack = " ".join(str(x) for x in item).lower()
        topic = item[-1] if len(item) == 3 else "article"
        if selected_topic != "All topics" and topic != selected_topic:
            continue
        if query and query not in haystack:
            continue
        filtered.append(item)
    return filtered


def render_progress():
    correct = st.session_state.correct
    tried = st.session_state.tried
    accuracy = round((correct / tried) * 100) if tried else 0
    progress = tried / TOTAL_EXERCISES if TOTAL_EXERCISES else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total exercises", TOTAL_EXERCISES)
    c2.metric("Tried", tried)
    c3.metric("Correct", correct)
    c4.metric("Accuracy", f"{accuracy}%")
    st.progress(progress)


def render_jumbled_exercises(items):
    st.subheader("Part 1: German Word-Order Practice")
    st.caption("Click words in the correct order. Then check your answer.")

    for idx, (de, en, topic) in enumerate(items, start=1):
        global_index = JUMBLE_SENTENCES.index((de, en, topic)) if (de, en, topic) in JUMBLE_SENTENCES else idx
        exercise_key = f"jumble-{global_index}-{de}"
        answer_key = f"order-{exercise_key}"
        if answer_key not in st.session_state:
            st.session_state[answer_key] = []

        words = re.sub(r"[.!?]", "", de).split()
        shuffled_words = deterministic_shuffle(words, de)

        with st.container(border=True):
            left, right = st.columns([4, 1])
            left.markdown(f"**{idx}. Arrange the words**")
            right.markdown(f"<span class='topic-pill'>{topic}</span>", unsafe_allow_html=True)
            st.write(f"English meaning: {en}")

            selected = st.session_state[answer_key]
            st.markdown("**Your sentence:** " + (" ".join(selected) if selected else "_Click words below_"))

            cols = st.columns(min(5, max(1, len(shuffled_words))))
            for i, word in enumerate(shuffled_words):
                used_count = selected.count(word)
                total_word_count = words.count(word)
                disabled = used_count >= total_word_count
                if cols[i % len(cols)].button(word, key=f"{exercise_key}-word-{i}", disabled=disabled):
                    st.session_state[answer_key].append(word)
                    st.rerun()

            c1, c2, c3 = st.columns([1, 1, 4])
            if c1.button("Check", key=f"check-{exercise_key}"):
                attempt = " ".join(st.session_state[answer_key])
                is_correct = normalize(attempt) == normalize(de)
                record_result(exercise_key, is_correct)
                if is_correct:
                    st.success("Correct")
                else:
                    st.error("Not correct yet")
                    st.markdown(f"<div class='wrong-box'>Your answer: {attempt or 'empty'}</div>", unsafe_allow_html=True)
            if c2.button("Clear", key=f"clear-{exercise_key}"):
                st.session_state[answer_key] = []
                st.rerun()
            with st.expander("Show answer"):
                st.markdown(f"<div class='answer-box'>{de}</div>", unsafe_allow_html=True)


def render_writing_exercises(items):
    st.subheader("Part 2: English to German Writing Practice")
    st.caption("Write the German sentence yourself. Then check or reveal the answer.")

    for idx, (en, de, topic) in enumerate(items, start=1):
        exercise_key = f"writing-{idx}-{de}"
        with st.container(border=True):
            left, right = st.columns([4, 1])
            left.markdown(f"**{idx}. Translate into German**")
            right.markdown(f"<span class='topic-pill'>{topic}</span>", unsafe_allow_html=True)
            st.write(f"English: {en}")
            user_answer = st.text_input("Your German sentence", key=f"input-{exercise_key}", label_visibility="collapsed")
            c1, c2 = st.columns([1, 5])
            if c1.button("Check", key=f"check-{exercise_key}"):
                is_correct = normalize(user_answer) == normalize(de)
                record_result(exercise_key, is_correct)
                if is_correct:
                    st.success("Correct")
                else:
                    st.error("Not correct yet")
            with st.expander("Show answer"):
                st.markdown(f"<div class='answer-box'>{de}</div>", unsafe_allow_html=True)


def render_article_drill(items):
    st.subheader("Part 3: der, die, das Article Drill")
    st.caption("Choose the correct article. Learn the noun together with the article.")

    for idx, (noun, article) in enumerate(items, start=1):
        exercise_key = f"article-{idx}-{noun}"
        with st.container(border=True):
            st.markdown(f"**{idx}. {noun}**")
            c1, c2, c3, c4 = st.columns([1, 1, 1, 5])
            for col, choice in zip([c1, c2, c3], ["der", "die", "das"]):
                if col.button(choice, key=f"{exercise_key}-{choice}"):
                    is_correct = choice == article
                    record_result(exercise_key, is_correct)
                    if is_correct:
                        st.success(f"Correct: {article} {noun}")
                    else:
                        st.error("Not correct")
            with st.expander("Show answer"):
                st.markdown(f"<div class='answer-box'>{article} {noun}</div>", unsafe_allow_html=True)


def main():
    init_state()
    render_hero()

    with st.sidebar:
        st.title("Practice Menu")
        page = st.radio(
            "Choose section",
            [
                "Rules and tricks",
                "Jumbled German sentences",
                "English to German writing",
                "Article mini-drill",
            ],
        )
        st.divider()
        st.subheader("Filter")
        all_topics = sorted(set(topic for _, _, topic in JUMBLE_SENTENCES + [(de, en, topic) for en, de, topic in WRITING_SENTENCES]))
        st.selectbox("Topic", ["All topics"] + all_topics, key="topic_filter")
        search_text = st.text_input("Search", placeholder="family, food, question...")
        max_questions = st.slider("Questions shown", 5, 100, 20, 5)
        st.divider()
        if st.button("Reset progress"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    render_progress()

    if page == "Rules and tricks":
        render_rules()
    elif page == "Jumbled German sentences":
        filtered = filter_items(JUMBLE_SENTENCES, "topic_filter", search_text)[:max_questions]
        render_jumbled_exercises(filtered)
    elif page == "English to German writing":
        filtered = filter_items(WRITING_SENTENCES, "topic_filter", search_text)[:max_questions]
        render_writing_exercises(filtered)
    else:
        article_search = search_text.strip().lower()
        filtered_articles = [item for item in ARTICLE_DRILL if not article_search or article_search in item[0].lower()]
        render_article_drill(filtered_articles[:max_questions])


if __name__ == "__main__":
    main()
