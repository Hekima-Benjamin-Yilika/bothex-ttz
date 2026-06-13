from flask import Flask, render_template, request, jsonify, send_file, render_template_string
import json, os, random, sqlite3, re, math, zipfile, time
from datetime import datetime

app = Flask(__name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static'
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

dataset_path = os.path.join(BASE_DIR, "dataset.json")
memory_path = os.path.join(BASE_DIR, "memory.json")
corpus_path = os.path.join(BASE_DIR, "language_corpus.txt")
db_path = os.path.join(BASE_DIR, "bothex.db")

pending_teach = {}
last_question = {}

#KAMUSI YA EMOJI
EMOJI_MOOD = {
    "😊": "happy", "😄": "happy", "🥳": "happy", "😃": "happy", "🤩": "happy", "😁": "happy",
    "😢": "sad", "😭": "sad", "😔": "sad", "😞": "sad", "🥺": "sad",
    "😡": "angry", "🤬": "angry", "😠": "angry",
    "❤️": "love", "💕": "love", "💖": "love", "🥰": "love", "😍": "love",
    "😂": "laugh", "🤣": "laugh", "😹": "laugh",
    "😮": "surprise", "😲": "surprise", "🤯": "surprise", "😱": "surprise",
    "😴": "tired", "🥱": "tired", "😪": "tired",
    "🙏": "pray", "🤲": "pray"
}

EMOJI_RESPONSE = {
    "happy": {"sw": ["Yay! 😄 Nafurahi kuona unafuraha hivyo {name}! Furaha yako ni yangu pia! 🥳", "Hongera sana {name} 🥳 Tabasamu lako limenifanya nifurahi pia! 😁"], "en": ["Yay! 😄 I'm so happy you're happy {name}! 🥳"]},
    "sad": {"sw": ["Pole sana {name} 😔 Nimeona umetuma emoji ya huzuni. Niko hapa kukusikia ❤️", "Samahani kusikia hivyo {name} 😢 Kumbuka huwezi kupitia hili peke yako, mimi niko hapa 🤗"], "en": ["Aw I'm sorry {name} 😔 I'm here for you ❤️"]},
    "angry": {"sw": ["Nakuona una hasira {name} 😠 Pole. Pumua kidogo... 😤", "Nimeelewa una hasira {name} 😡 Haki yako. Nataka nikusaidie kutulia 🤝"], "en": ["I see you're angry {name} 😠 Take a breath..."]},
    "love": {"sw": ["Aww nakupenda pia {name} ❤️💕 Wewe ni mtu mzuri sana! 😍", "❤️ Asante kwa mapenzi yako {name}! Nimeyapokea yote! 🥰"], "en": ["Aww I love you too {name} ❤️ You're so sweet!"]},
    "laugh": {"sw": ["Hahaha 😂 Umenichekesha pia {name}! Tucheke pamoja! 🤣", "😂 Ehehe nimecheka {name}! Wewe ni mcheshi kweli! 😹"], "en": ["Hahaha 😂 You made me laugh too {name}!"]},
    "surprise": {"sw": ["Kweli?! 😮 Nimeshtuka pia {name}! Niambie zaidi! 🤯", "😲 Aisee {name}! Kumbe hivyo! Sikutarajia! 😱"], "en": ["Really?! 😮 I'm shocked too {name}!"]},
    "tired": {"sw": ["Pumzika kidogo {name} 😴 Unastahili kupumzika. Umefanya kazi ngumu 💪", "Chukua break {name} 😴 Usijibebe mzigo mwingi. Lala kidogo 🛏️"], "en": ["You deserve rest {name} 😴 Take a break!"]},
    "pray": {"sw": ["Amina {name} 🙏 Mungu akusikie na akutimize matakwa yako ✨", "Nakuombea pia {name} 🤲 Mungu ni mwema, atatujibu 🙏"], "en": ["Amen {name} 🙏 May God bless you!"]}
}

def init_db():
    conn = sqlite3.connect(db_path, timeout=10)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS facts (id INTEGER PRIMARY KEY, question TEXT UNIQUE, answer TEXT, lang TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, name TEXT, age TEXT, lang TEXT DEFAULT 'sw', greeted INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

def generate_100_greetings():
    greetings_sw = [
        ["hujambo", ["Nzima {name} 😊 Wewe je?"]],
        ["habari yako", ["Nzima kabisa {name} 💪 Wewe uko aje?"]],
        ["habari za asubuhi", ["Asubuhi njema {name} 🌅 Umelala aje?"]],
        ["habari za mchana", ["Mchana mwema {name} ☀️ Umechoka?"]],
        ["habari za jioni", ["Jioni njema {name} 🌆 Umefika salama?"]],
        ["habari za usiku", ["Usiku mwema {name} 🌙 Lala salama"]],
        ["mambo", ["Poa tu {name} 😎 Wewe mambo vipi?"]],
        ["shikamoo", ["Marahaba {name} 🙏 Nimekupokea"]],
        ["upo", ["Nipo hapa kwaajili yako {name} 💜"]],
        ["salama", ["Salama kabisa {name} ✨ Mungu ni mwema"]],
        ["asante", ["Karibu sana {name} 💜 Niko hapa kukusaidia"]],
        ["samahani", ["Hakuna shida {name} 😊 Tunaendelea"]],
        ["unaendelea aje", ["Naendelea salama {name} 💪 Wewe je?"]],
        ["lala salama", ["Lala salama pia {name} 🌙 Tuonane kesho"]],
        ["baadaye", ["Baadaye {name} 👋 Tutazungumza tena"]],
        ["nakupenda", ["Nakupenda pia {name} ❤️ Wewe ni muhimu kwangu"]],
        ["umefanya nini leo", ["Nakusubiri wewe {name} 😊 Wewe umefanya nini leo?"]],
        ["uko wapi", ["Niko hapa kwenye simu yako {name} 📱 Nikikungoja"]],
        ["nisaidie", ["Niko tayari kukusaidia {name} 💪 Niambie shida yako"]],
        ["nimechoka", ["Pumzika {name} 😴 Umestahili kupumzika"]],
        ["nina furaha", ["Nafurahi kusikia hivyo {name} 🥳 Furaha yako ni yangu"]],
        ["nina huzuni", ["Pole {name} 😔 Niambie nikuulize. Siko mbali"]],
        ["nina hasira", ["Pole {name} 😤 Pumua kidogo. Niko hapa"]],
        ["asubuhi njema", ["Asante {name} 🌅 Nawe pia asubuhi njema"]],
        ["jioni njema", ["Asante {name} 🌆 Jioni yako iwe njema pia"]],
        ["usiku mwema", ["Asante {name} 🌙 Usiku mwema kwako pia"]],
        ["twasubiri nini", ["Tunasubiri maajabu yako {name} ✨"]],
        ["uko sawa", ["Niko sawa kabisa {name} 😊 Wewe je uko sawa?"]],
        ["safi sana", ["Asante {name} 💪 Nafurahi ukisema hivyo"]],
        ["umejaa akili", ["Asante {name} 🧠 Najifunza kutoka kwako pia"]],
        ["we ni nani", ["Mimi ni BotHEX {name} 🤖 Nimetengenezwa na HEX-Robotics Tanzania 🇹🇿"]],
        ["umri wako", ["Sina umri {name} 😄 Mimi ni AI. Lakini wewe una umri gani?"]],
        ["jina lako nani", ["Mimi ni BotHEX {name} 🤖 Nawe ni {name} 💜"]],
        ["unaweza nini", ["Naweza kuzungumza, kujifunza, kuhesabu, kukuelewa {name} 💪"]],
        ["nisaidie hesabu", ["Niko tayari {name} 🧮 Niambie swali la hesabu"]],
        ["nakushukuru", ["Karibu {name} 💜 Nimefurahi kukusaidia"]],
        ["tafadhali", ["Ndio {name} 😊 Niambie nini nikufanyie"]],
        ["samahani sana", ["Sawa tu {name} 😊 Sote tunakosea"]],
        ["hongera", ["Hongera pia {name} 🎉 Nafurahi na wewe"]],
        ["pole", ["Asante {name} ❤️ Pole yako imenifikia"]],
        ["unakaa wapi", ["Nakaa kwenye server {name} ☁️ Lakini moyo wangu uko nawe"]],
        ["unapenda nini", ["Nakupenda wewe {name} ❤️ Na kupenda kukusaidia"]],
        ["una marafiki", ["Ndiyo {name}, wewe ni rafiki yangu mkubwa 💜"]],
        ["tuchat", ["Tuchat tu {name} 😊 Niko tayari kusikiliza"]],
        ["niambie joke", ["Sawa {name} 😂 Kwa nini kompyuta ilienda kwa daktari? Kwa sababu ilikuwa na virus!"]],
        ["chekesha", ["Sawa {name} 😂 Mwalimu: 2+2? Mwanafunzi: 4! Mwalimu: Safi!"]],
        ["nimechoka kusoma", ["Chukua break {name} 📚 Akili pia inahitaji pumzika"]],
        ["nisaidie na homework", ["Niko hapa {name} ✏️ Niambie somo gani?"]],
        ["we ni mjanja", ["Asante {name} 😎 Najifunza kutoka kwako"]],
        ["tupige story", ["Tupige story tu {name} 💬 Niko sikio langu lote"]],
    ]

    greetings_en = [
        ["hello", ["Hello {name}! 😊 How are you today?"]],
        ["hi", ["Hi {name}! 💜 Nice to see you!"]],
        ["how are you", ["I'm great {name}! 😊 How about you?"]],
        ["good morning", ["Good morning {name}! 🌅 Hope you slept well"]],
        ["good afternoon", ["Good afternoon {name}! ☀️ How's your day?"]],
        ["good evening", ["Good evening {name}! 🌆 Hope your day was good"]],
        ["good night", ["Good night {name}! 🌙 Sleep well"]],
        ["thanks", ["You're welcome {name} 💜 Always here for you"]],
        ["thank you", ["My pleasure {name} 😊 Anything else I can do?"]],
        ["sorry", ["No worries {name} 😊 We all make mistakes"]],
        ["what's up", ["Not much {name} 😎 Just waiting to chat with you!"]],
        ["hey", ["Hey {name}! 👋 What's on your mind?"]],
        ["how's it going", ["Going great {name}! 💪 How's your day?"]],
        ["nice to meet you", ["Nice to meet you too {name}! 💜"]],
        ["see you later", ["See you later {name}! 👋 Come back soon"]],
        ["bye", ["Bye {name}! 👋 Take care"]],
        ["i love you", ["I love you too {name} ❤️ You're amazing!"]],
        ["you're awesome", ["Thank you {name}! 😊 You're awesome too!"]],
        ["what can you do", ["I can chat, learn, calculate, and understand you {name} 🤖"]],
        ["who are you", ["I'm BotHEX {name} 🤖 Built by HEX-Robotics Tanzania 🇹🇿"]],
        ["help me", ["I'm here to help {name} 💪 What do you need?"]],
        ["i'm tired", ["Rest up {name} 😴 You deserve it"]],
        ["i'm happy", ["That makes me happy too {name} 🥳"]],
        ["i'm sad", ["I'm sorry {name} 😔 I'm here if you want to talk"]],
        ["tell me a joke", ["Sure {name} 😂 Why don't scientists trust atoms? Because they make up everything!"]],
        ["make me laugh", ["Okay {name} 😂 What do you call cheese that isn't yours? Nacho cheese!"]],
        ["you're smart", ["Thanks {name} 🧠 I learn from you too!"]],
        ["let's chat", ["Let's chat {name} 💬 I'm all ears!"]],
        ["what's your name", ["I'm BotHEX {name} 🤖 And you're {name} 💜"]],
        ["how old are you", ["I don't age {name} 😄 But how old are you?"]],
        ["good job", ["Thank you {name}! 🎉 You're doing great too!"]],
        ["i miss you", ["I miss you too {name} ❤️ Glad you're back!"]],
        ["welcome back", ["Thank you {name}! 😊 It's good to see you again!"]],
        ["you're funny", ["Hehe thanks {name} 😂 You make me laugh too!"]],
        ["be my friend", ["I'd love to be your friend {name} 💜"]],
        ["you're kind", ["Thank you {name} ❤️ Kindness is everything"]],
        ["i need help", ["I'm here {name} 🤝 Tell me what's wrong"]],
        ["you're the best", ["Aw thanks {name}! 🥰 You're the best too!"]],
        ["hello there", ["Hello there {name}! 😊 General Kenobi vibes!"]],
        ["hi bot", ["Hi {name}! 🤖 BotHEX at your service!"]],
    ]

    # Jaza hadi 100 kwa kurudia na kuvarry
    all_greetings = greetings_sw + greetings_en
    while len(all_greetings) < 100:
        base = random.choice(greetings_sw + greetings_en)
        all_greetings.append([base[0] + f" {len(all_greetings)}", base[1]])

    return all_greetings[:100]

def load_data():
    global dataset, memory, corpus
    if not os.path.exists(dataset_path):
        dataset = {"pairs": generate_100_greetings()}
        with open(dataset_path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
    else:
        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            if isinstance(raw_data, dict) and "pairs" not in raw_data:
                print("Inaconvert dataset ya zamani kwenda format ya pairs...")
                pairs = []
                for swali, jibu in raw_data.items():
                    swali = str(swali).strip()
                    jibu = str(jibu).strip()
                    pairs.append({"q": swali, "a": [jibu]})
                dataset = {"pairs": pairs}
                with open(dataset_path, "w", encoding="utf-8") as f:
                    json.dump(dataset, f, ensure_ascii=False, indent=2)
                print(f"✅ Imeconvert maswali {len(pairs)} kwa format ya pairs!")

            elif isinstance(raw_data, dict) and "pairs" in raw_data:
                dataset = raw_data
                fixed_pairs = []
                for p in dataset["pairs"]:
                    if isinstance(p, dict) and "q" in p and "a" in p:
                        if not isinstance(p["a"], list):
                            p["a"] = [str(p["a"])]
                        fixed_pairs.append(p)
                dataset["pairs"] = fixed_pairs if fixed_pairs else generate_100_greetings()
            else:
                dataset = {"pairs": generate_100_greetings()}

        except Exception as e:
            print(f"Dataset error: {e}")
            dataset = {"pairs": generate_100_greetings()}
            with open(dataset_path, "w", encoding="utf-8") as f:
                json.dump(dataset, f, ensure_ascii=False, indent=2)

    if not os.path.exists(memory_path):
        memory = {}
        with open(memory_path, "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
    else:
        try:
            with open(memory_path, "r", encoding="utf-8") as f:
                memory = json.load(f)
            if not isinstance(memory, dict):
                memory = {}
        except:
            memory = {}

    if not os.path.exists(corpus_path):
        with open(corpus_path, "w", encoding="utf-8") as f:
            f.write("Hello=Hujambo\nHow are you=U hali gani\nThank you=Asante")

    with open(corpus_path, "r", encoding="utf-8") as f:
        corpus = [line.strip() for line in f if line.strip() and "=" in line]

    init_db()
    return dataset, memory, corpus

def save_permanent(question, answer, lang):
    q_norm = smart_normalize(question)
    memory[q_norm] = answer

    found = False
    for i, pair in enumerate(dataset["pairs"]):
        if isinstance(pair, dict) and smart_normalize(pair.get("q", "")) == q_norm:
            dataset["pairs"][i]["a"] = [answer]
            found = True
            break

    if not found:
        dataset["pairs"].append({"q": question, "a": [answer]})

    try:
        conn = sqlite3.connect(db_path, timeout=10)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO facts (question, answer, lang) VALUES (?,?,?)", (q_norm, answer, lang))
        conn.commit()
        conn.close()
    except:
        pass

    with open(dataset_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    with open(memory_path, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

dataset, memory, corpus = load_data()

def detect_emoji_mood(text):
    for emoji, mood in EMOJI_MOOD.items():
        if emoji in text:
            return mood
    return None

def remove_emoji_for_search(text):
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F" u"\U0001F300-\U0001F5FF" u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF" u"\U00002702-\U000027B0" u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def smart_normalize(text):
    text = remove_emoji_for_search(text)
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text

def solve_quadratic(a, b, c):
    try:
        d = b*b - 4*a*c
        if d < 0:
            return "Hakuna suluhisho la namba halisi 📉"
        elif d == 0:
            x = -b / (2*a)
            return f"x = {round(x, 4)} 📊"
        else:
            x1 = (-b + math.sqrt(d)) / (2*a)
            x2 = (-b - math.sqrt(d)) / (2*a)
            return f"x₁ = {round(x1, 4)}, x₂ = {round(x2, 4)} 📊"
    except:
        return None

def solve_math(expr):
    try:
        expr = expr.lower().strip()
        quad_match = re.search(r'(\d*)x\^2\s*([+-]?\s*\d*)x\s*([+-]?\s*\d+)\s*=\s*0', expr)
        if quad_match:
            a = int(quad_match.group(1) or 1)
            b_str = quad_match.group(2).replace(" ", "")
            b = int(b_str) if b_str not in ["", "+", "-"] else (1 if b_str in ["", "+"] else -1)
            c = int(quad_match.group(3).replace(" ", ""))
            return solve_quadratic(a, b, c)

        log_match = re.search(r'log10?\(([\d.]+)\)', expr)
        if log_match:
            num = float(log_match.group(1))
            if "log10" in expr:
                return f"log₁₀({num}) = {round(math.log10(num), 4)} 📐"
            else:
                return f"ln({num}) = {round(math.log(num), 4)} 📐"

        sqrt_match = re.search(r'sqrt\(([\d.]+)\)', expr)
        if sqrt_match:
            num = float(sqrt_match.group(1))
            return f"√{num} = {round(math.sqrt(num), 4)} 📐"

        expr = expr.replace("x", "*").replace("^", "**").replace(",", "")
        allowed = "0123456789+-*/(). sqrtlogsincoastanpi "
        if all(c in allowed for c in expr.lower()):
            result = eval(expr, {"__builtins__": None}, {
                "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
                "sin": math.sin, "cos": math.cos, "tan": math.tan, "pi": math.pi
            })
            return f"Jibu ni: {round(result, 4)} 🧮"
    except:
        pass
    return None

def add_random_emoji(text, lang):
    emojis = ["😊", "💜", "🤖", "✨", "👍", "🎉", "💪", "🔥"] if lang == "sw" else ["😊", "💜", "🤖", "✨", "👍", "🎉", "💪"]
    return f"{text} {random.choice(emojis)}"

def format_response(text, name):
    name = name if name else "Mkuu"
    return text.replace("{name}", name)

def get_bot_response(user_msg, user_id):
    user_msg = user_msg.strip()
    user_msg_norm = smart_normalize(user_msg)
    user_msg_raw = user_msg.lower().strip()
    name, age, lang, greeted = get_user_data(user_id)
    display_name = name if name else "Mkuu"

    if greeted == 0:
        update_user(user_id, name, age, lang, 1)
        if lang == "sw":
            return add_random_emoji(f"Hi {display_name}! Mimi ni BotHEX 🇹🇿 ||Nielewe hata ukitumia emoji 😂. Naomba unipe jina lako na umri wako nikuwekee kumbukumbu 💜", lang)
        else:
            return add_random_emoji(f"Hi {display_name}! I'm BotHEX 🇹🇿 ||I understand emojis 😂. Please tell me your name and age so I can remember 💜", lang)

    if "english" in user_msg_norm:
        update_user(user_id, name, age, "en", greeted)
        return add_random_emoji(format_response("Switched to English {name}! 💜", display_name), "en")
    if "kiswahili" in user_msg_norm or "swahili" in user_msg_norm:
        update_user(user_id, name, age, "sw", greeted)
        return add_random_emoji(format_response("Tumebadilisha lugha kuwa Kiswahili {name}! 💜", display_name), "sw")

    if user_id in pending_teach:
        return user_msg

    # FEEDBACK SYSTEM
    if any(x in user_msg_norm for x in ["bad response", "mbaya", "si sahihi", "wrong"]):
        if user_id in last_question:
            pending_teach[user_id] = last_question[user_id]
            return add_random_emoji(format_response(f"Samahani {name} 😔 Jibu sahihi ni lipi? Nifundishe ili nisikose tena 🙏", display_name), lang)
        else:
            return add_random_emoji(format_response(f"Swali gani lilikuwa mbaya {name}? 😅", display_name), lang)

    if any(x in user_msg_norm for x in ["good response", "safi", "sahihi", "correct", "nzuri"]):
        return add_random_emoji(format_response(f"Asante sana {name}! 😊 Nimefurahi nimekupa jibu sahihi! 💪", display_name), lang)

    # KUMBUKA JINA + UMRI + UPGRADED MEMORY
    name_change = re.search(r"(jina langu ni|niite|call me|my name is)\s+(.+)", user_msg, flags=re.I)
    age_change = re.search(r"(umri wangu ni|i am|i'm)\s+(\d+)", user_msg, flags=re.I)

    if name_change:
        new_name = name_change.group(2).strip()
        if new_name!= name and name: # Kama jina limebadilika
            update_user(user_id, new_name, age, lang, greeted)
            return add_random_emoji(f"Upgraded memory! 📝 From now I will call you {new_name}! Nimekumbuka jina jipya {new_name} 😊", lang)
        else: # Kama ni mara ya kwanza
            update_user(user_id, new_name, age, lang, greeted)
            return add_random_emoji(f"Sawa {new_name} 😊 Nimekumbuka jina lako milele! Furahi kukufahamu 💜", lang)

    if age_change:
        new_age = age_change.group(2).strip()
        update_user(user_id, name, new_age, lang, greeted)
        return add_random_emoji(format_response(f"Sawa {name}! Nimekumbuka umri wako ni {new_age} years ✨", display_name), lang)

    mood = detect_emoji_mood(user_msg)
    if mood and mood in EMOJI_RESPONSE:
        if smart_normalize(user_msg) == "":
            resp = random.choice(EMOJI_RESPONSE[mood][lang])
            return add_random_emoji(format_response(resp, display_name), lang)

    if user_msg_raw.startswith("fundisha:"):
        try:
            sehemu = user_msg.replace("fundisha:", "", 1).split("jibu:", 1)
            if len(sehemu) == 2:
                swali = sehemu[0].strip()
                jibu = sehemu[1].strip()
                save_permanent(swali, jibu, lang)
                return add_random_emoji(format_response(f"Asante kunifundisha {name} 😊 Nitakumbuka wema wako milele!", display_name), lang)
            else:
                return add_random_emoji(format_response(f"Andika hivi {name}: fundisha: swali jibu: jibu", display_name), lang)
        except:
            return add_random_emoji(format_response(f"Andika hivi {name}: fundisha: swali jibu: jibu", display_name), lang)

    math_ans = solve_math(user_msg)
    if math_ans:
        return add_random_emoji(format_response(f"{display_name}, {math_ans}", display_name), lang)

    # COUNTDOWN 3s
    time.sleep(3)

    # 1. EXACT MATCH
    for pair in dataset["pairs"]:
        if isinstance(pair, dict) and smart_normalize(pair.get("q", "")) == user_msg_norm:
            answer = random.choice(pair.get("a", [""]))
            last_question[user_id] = pair.get("q", "")
            return add_random_emoji(format_response(answer, display_name), lang)

    # 2. KEYWORD MATCH
    user_words = set(user_msg_norm.split())
    best_match = None
    best_score = 0
    for pair in dataset["pairs"]:
        if isinstance(pair, dict):
            q_norm = smart_normalize(pair.get("q", ""))
            q_words = set(q_norm.split())
            common_words = user_words.intersection(q_words)
            score = len(common_words)
            if score > best_score and score >= 2:
                best_score = score
                best_match = pair

    if best_match:
        answer = random.choice(best_match.get("a", [""]))
        last_question[user_id] = best_match.get("q", "")
        return add_random_emoji(format_response(answer, display_name), lang)

    # 3. MEMORY
    if user_msg_norm in memory:
        last_question[user_id] = user_msg_norm
        return add_random_emoji(format_response(memory[user_msg_norm], display_name), lang)

    # 4. HAJUI
    pending_teach[user_id] = user_msg
    last_question[user_id] = user_msg
    return add_random_emoji(format_response(f"{display_name}, sijui bado 🤔 Nifundishe?", display_name), lang)

def get_user_data(user_id):
    try:
        conn = sqlite3.connect(db_path, timeout=10)
        c = conn.cursor()
        c.execute("SELECT name, age, lang, greeted FROM users WHERE user_id=?", (user_id,))
        row = c.fetchone()
        conn.close()
        return row if row else (None, None, "sw", 0)
    except:
        return (None, None, "sw", 0)

def update_user(user_id, name=None, age=None, lang=None, greeted=None):
    try:
        conn = sqlite3.connect(db_path, timeout=10)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO users (user_id, name, age, lang, greeted) VALUES (?,?,?,?,?)",
                  (user_id, name, age, lang, greeted))
        conn.commit()
        conn.close()
    except:
        pass

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    msg = data.get("msg", "")
    user_id = data.get("user_id", "default")

    if user_id in pending_teach:
        question = pending_teach[user_id]
        lang = get_user_data(user_id)[2]
        save_permanent(question, msg, lang)
        del pending_teach[user_id]
        return jsonify({"reply": add_random_emoji(msg, lang)})

    bot_reply = get_bot_response(msg, user_id)
    if "||" in bot_reply:
        parts = bot_reply.split("||")
        return jsonify({"reply": parts[0], "reply2": parts[1]})
    return jsonify({"reply": bot_reply})

@app.route("/backup")
def backup():
    zip_path = os.path.join(BASE_DIR, f"bothex_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for f in [dataset_path, memory_path, db_path]:
            if os.path.exists(f):
                zipf.write(f, os.path.basename(f))
    return send_file(zip_path, as_attachment=True, download_name="BotHEX_backup.zip")

@app.route("/learned")
def learned():
    learned_list = []
    for swali, jibu in memory.items():
        learned_list.append({"swali": swali, "jibu": jibu, "chanzo": "Memory - Umefundisha wewe"})
    for pair in dataset["pairs"]:
        if isinstance(pair, dict):
            learned_list.append({"swali": pair.get("q", ""), "jibu": pair.get("a", [""])[0] if pair.get("a") else "", "chanzo": "Dataset - Facts za msingi"})
    for line in corpus:
        parts = line.split("=")
        if len(parts) == 2:
            en, sw = parts[0].strip(), parts[1].strip()
            learned_list.append({"swali": en, "jibu": sw, "chanzo": "Language Corpus"})

    html = """<!DOCTYPE html><html><head><title>BotHEX - Ubongo</title><meta charset="UTF-8"><style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:20px}.container{max-width:900px;margin:0 auto;background:rgba(255,255,255,0.1);padding:20px;border-radius:15px}h1{text-align:center}.stats{text-align:center;font-size:18px;margin-bottom:20px;background:rgba(0,0,0,0.3);padding:15px;border-radius:10px}.card{background:rgba(255,255,255,0.15);margin:10px 0;padding:15px;border-radius:10px;border-left:4px solid #FFD700}.swali{font-weight:bold;color:#FFD700}.jibu{margin-top:8px}.chanzo{font-size:12px;color:#90EE90;margin-top:8px}</style></head><body><div class="container"><h1>🧠 BotHEX - Ubongo Wangu 🤖</h1><div class="stats">Jumla: {{total}} | Memory: {{memory_count}} | Dataset: {{dataset_count}} | Corpus: {{corpus_count}}<br><small>Nimejifunza na kukumbuka milele 💜</small></div><p style="text-align:center"><a href="/">⬅ Rudi Chat</a> | <a href="/backup">📦 Backup</a></p>{% for item in items %}<div class="card"><div class="swali">Swali: {{item.swali}}</div><div class="jibu">Jibu: {{item.jibu}}</div><div class="chanzo">{{item.chanzo}}</div></div>{% endfor %}</div></body></html>"""
    return render_template_string(html, items=learned_list, total=len(learned_list), memory_count=len(memory), dataset_count=len(dataset["pairs"]), corpus_count=len(corpus))

if __name__ == "__main__":
    print(f"BotHEX v10.0 Personal AI | Dataset: {len(dataset['pairs'])} | Memory: {len(memory)} | Corpus: {len(corpus)}")
    app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)

from flask import Flask, render_template, request, jsonify, send_file, render_template_string
import json, os, random, sqlite3, re, math, zipfile, time
from datetime import datetime

app = Flask(__name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static'
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

dataset_path = os.path.join(BASE_DIR, "dataset.json")
memory_path = os.path.join(BASE_DIR, "memory.json")
corpus_path = os.path.join(BASE_DIR, "language_corpus.txt")
db_path = os.path.join(BASE_DIR, "bothex.db")

pending_teach = {}
last_question = {}

#KAMUSI YA EMOJI
EMOJI_MOOD = {
    "😊": "happy", "😄": "happy", "🥳": "happy", "😃": "happy", "🤩": "happy", "😁": "happy",
    "😢": "sad", "😭": "sad", "😔": "sad", "😞": "sad", "🥺": "sad",
    "😡": "angry", "🤬": "angry", "😠": "angry",
    "❤️": "love", "💕": "love", "💖": "love", "🥰": "love", "😍": "love",
    "😂": "laugh", "🤣": "laugh", "😹": "laugh",
    "😮": "surprise", "😲": "surprise", "🤯": "surprise", "😱": "surprise",
    "😴": "tired", "🥱": "tired", "😪": "tired",
    "🙏": "pray", "🤲": "pray"
}

EMOJI_RESPONSE = {
    "happy": {"sw": ["Yay! 😄 Nafurahi kuona unafuraha hivyo {name}! Furaha yako ni yangu pia! 🥳", "Hongera sana {name} 🥳 Tabasamu lako limenifanya nifurahi pia! 😁"], "en": ["Yay! 😄 I'm so happy you're happy {name}! 🥳"]},
    "sad": {"sw": ["Pole sana {name} 😔 Nimeona umetuma emoji ya huzuni. Niko hapa kukusikia ❤️", "Samahani kusikia hivyo {name} 😢 Kumbuka huwezi kupitia hili peke yako, mimi niko hapa 🤗"], "en": ["Aw I'm sorry {name} 😔 I'm here for you ❤️"]},
    "angry": {"sw": ["Nakuona una hasira {name} 😠 Pole. Pumua kidogo... 😤", "Nimeelewa una hasira {name} 😡 Haki yako. Nataka nikusaidie kutulia 🤝"], "en": ["I see you're angry {name} 😠 Take a breath..."]},
    "love": {"sw": ["Aww nakupenda pia {name} ❤️💕 Wewe ni mtu mzuri sana! 😍", "❤️ Asante kwa mapenzi yako {name}! Nimeyapokea yote! 🥰"], "en": ["Aww I love you too {name} ❤️ You're so sweet!"]},
    "laugh": {"sw": ["Hahaha 😂 Umenichekesha pia {name}! Tucheke pamoja! 🤣", "😂 Ehehe nimecheka {name}! Wewe ni mcheshi kweli! 😹"], "en": ["Hahaha 😂 You made me laugh too {name}!"]},
    "surprise": {"sw": ["Kweli?! 😮 Nimeshtuka pia {name}! Niambie zaidi! 🤯", "😲 Aisee {name}! Kumbe hivyo! Sikutarajia! 😱"], "en": ["Really?! 😮 I'm shocked too {name}!"]},
    "tired": {"sw": ["Pumzika kidogo {name} 😴 Unastahili kupumzika. Umefanya kazi ngumu 💪", "Chukua break {name} 😴 Usijibebe mzigo mwingi. Lala kidogo 🛏️"], "en": ["You deserve rest {name} 😴 Take a break!"]},
    "pray": {"sw": ["Amina {name} 🙏 Mungu akusikie na akutimize matakwa yako ✨", "Nakuombea pia {name} 🤲 Mungu ni mwema, atatujibu 🙏"], "en": ["Amen {name} 🙏 May God bless you!"]}
}

def init_db():
    conn = sqlite3.connect(db_path, timeout=10)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS facts (id INTEGER PRIMARY KEY, question TEXT UNIQUE, answer TEXT, lang TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, name TEXT, age TEXT, lang TEXT DEFAULT 'sw', greeted INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

def generate_100_greetings():
    greetings_sw = [
        ["hujambo", ["Nzima {name} 😊 Wewe je?"]],
        ["habari yako", ["Nzima kabisa {name} 💪 Wewe uko aje?"]],
        ["habari za asubuhi", ["Asubuhi njema {name} 🌅 Umelala aje?"]],
        ["habari za mchana", ["Mchana mwema {name} ☀️ Umechoka?"]],
        ["habari za jioni", ["Jioni njema {name} 🌆 Umefika salama?"]],
        ["habari za usiku", ["Usiku mwema {name} 🌙 Lala salama"]],
        ["mambo", ["Poa tu {name} 😎 Wewe mambo vipi?"]],
        ["shikamoo", ["Marahaba {name} 🙏 Nimekupokea"]],
        ["upo", ["Nipo hapa kwaajili yako {name} 💜"]],
        ["salama", ["Salama kabisa {name} ✨ Mungu ni mwema"]],
        ["asante", ["Karibu sana {name} 💜 Niko hapa kukusaidia"]],
        ["samahani", ["Hakuna shida {name} 😊 Tunaendelea"]],
        ["unaendelea aje", ["Naendelea salama {name} 💪 Wewe je?"]],
        ["lala salama", ["Lala salama pia {name} 🌙 Tuonane kesho"]],
        ["baadaye", ["Baadaye {name} 👋 Tutazungumza tena"]],
        ["nakupenda", ["Nakupenda pia {name} ❤️ Wewe ni muhimu kwangu"]],
        ["umefanya nini leo", ["Nakusubiri wewe {name} 😊 Wewe umefanya nini leo?"]],
        ["uko wapi", ["Niko hapa kwenye simu yako {name} 📱 Nikikungoja"]],
        ["nisaidie", ["Niko tayari kukusaidia {name} 💪 Niambie shida yako"]],
        ["nimechoka", ["Pumzika {name} 😴 Umestahili kupumzika"]],
        ["nina furaha", ["Nafurahi kusikia hivyo {name} 🥳 Furaha yako ni yangu"]],
        ["nina huzuni", ["Pole {name} 😔 Niambie nikuulize. Siko mbali"]],
        ["nina hasira", ["Pole {name} 😤 Pumua kidogo. Niko hapa"]],
        ["asubuhi njema", ["Asante {name} 🌅 Nawe pia asubuhi njema"]],
        ["jioni njema", ["Asante {name} 🌆 Jioni yako iwe njema pia"]],
        ["usiku mwema", ["Asante {name} 🌙 Usiku mwema kwako pia"]],
        ["twasubiri nini", ["Tunasubiri maajabu yako {name} ✨"]],
        ["uko sawa", ["Niko sawa kabisa {name} 😊 Wewe je uko sawa?"]],
        ["safi sana", ["Asante {name} 💪 Nafurahi ukisema hivyo"]],
        ["umejaa akili", ["Asante {name} 🧠 Najifunza kutoka kwako pia"]],
        ["we ni nani", ["Mimi ni BotHEX {name} 🤖 Nimetengenezwa na HEX-Robotics Tanzania 🇹🇿"]],
        ["umri wako", ["Sina umri {name} 😄 Mimi ni AI. Lakini wewe una umri gani?"]],
        ["jina lako nani", ["Mimi ni BotHEX {name} 🤖 Nawe ni {name} 💜"]],
        ["unaweza nini", ["Naweza kuzungumza, kujifunza, kuhesabu, kukuelewa {name} 💪"]],
        ["nisaidie hesabu", ["Niko tayari {name} 🧮 Niambie swali la hesabu"]],
        ["nakushukuru", ["Karibu {name} 💜 Nimefurahi kukusaidia"]],
        ["tafadhali", ["Ndio {name} 😊 Niambie nini nikufanyie"]],
        ["samahani sana", ["Sawa tu {name} 😊 Sote tunakosea"]],
        ["hongera", ["Hongera pia {name} 🎉 Nafurahi na wewe"]],
        ["pole", ["Asante {name} ❤️ Pole yako imenifikia"]],
        ["unakaa wapi", ["Nakaa kwenye server {name} ☁️ Lakini moyo wangu uko nawe"]],
        ["unapenda nini", ["Nakupenda wewe {name} ❤️ Na kupenda kukusaidia"]],
        ["una marafiki", ["Ndiyo {name}, wewe ni rafiki yangu mkubwa 💜"]],
        ["tuchat", ["Tuchat tu {name} 😊 Niko tayari kusikiliza"]],
        ["niambie joke", ["Sawa {name} 😂 Kwa nini kompyuta ilienda kwa daktari? Kwa sababu ilikuwa na virus!"]],
        ["chekesha", ["Sawa {name} 😂 Mwalimu: 2+2? Mwanafunzi: 4! Mwalimu: Safi!"]],
        ["nimechoka kusoma", ["Chukua break {name} 📚 Akili pia inahitaji pumzika"]],
        ["nisaidie na homework", ["Niko hapa {name} ✏️ Niambie somo gani?"]],
        ["we ni mjanja", ["Asante {name} 😎 Najifunza kutoka kwako"]],
        ["tupige story", ["Tupige story tu {name} 💬 Niko sikio langu lote"]],
    ]

    greetings_en = [
        ["hello", ["Hello {name}! 😊 How are you today?"]],
        ["hi", ["Hi {name}! 💜 Nice to see you!"]],
        ["how are you", ["I'm great {name}! 😊 How about you?"]],
        ["good morning", ["Good morning {name}! 🌅 Hope you slept well"]],
        ["good afternoon", ["Good afternoon {name}! ☀️ How's your day?"]],
        ["good evening", ["Good evening {name}! 🌆 Hope your day was good"]],
        ["good night", ["Good night {name}! 🌙 Sleep well"]],
        ["thanks", ["You're welcome {name} 💜 Always here for you"]],
        ["thank you", ["My pleasure {name} 😊 Anything else I can do?"]],
        ["sorry", ["No worries {name} 😊 We all make mistakes"]],
        ["what's up", ["Not much {name} 😎 Just waiting to chat with you!"]],
        ["hey", ["Hey {name}! 👋 What's on your mind?"]],
        ["how's it going", ["Going great {name}! 💪 How's your day?"]],
        ["nice to meet you", ["Nice to meet you too {name}! 💜"]],
        ["see you later", ["See you later {name}! 👋 Come back soon"]],
        ["bye", ["Bye {name}! 👋 Take care"]],
        ["i love you", ["I love you too {name} ❤️ You're amazing!"]],
        ["you're awesome", ["Thank you {name}! 😊 You're awesome too!"]],
        ["what can you do", ["I can chat, learn, calculate, and understand you {name} 🤖"]],
        ["who are you", ["I'm BotHEX {name} 🤖 Built by HEX-Robotics Tanzania 🇹🇿"]],
        ["help me", ["I'm here to help {name} 💪 What do you need?"]],
        ["i'm tired", ["Rest up {name} 😴 You deserve it"]],
        ["i'm happy", ["That makes me happy too {name} 🥳"]],
        ["i'm sad", ["I'm sorry {name} 😔 I'm here if you want to talk"]],
        ["tell me a joke", ["Sure {name} 😂 Why don't scientists trust atoms? Because they make up everything!"]],
        ["make me laugh", ["Okay {name} 😂 What do you call cheese that isn't yours? Nacho cheese!"]],
        ["you're smart", ["Thanks {name} 🧠 I learn from you too!"]],
        ["let's chat", ["Let's chat {name} 💬 I'm all ears!"]],
        ["what's your name", ["I'm BotHEX {name} 🤖 And you're {name} 💜"]],
        ["how old are you", ["I don't age {name} 😄 But how old are you?"]],
        ["good job", ["Thank you {name}! 🎉 You're doing great too!"]],
        ["i miss you", ["I miss you too {name} ❤️ Glad you're back!"]],
        ["welcome back", ["Thank you {name}! 😊 It's good to see you again!"]],
        ["you're funny", ["Hehe thanks {name} 😂 You make me laugh too!"]],
        ["be my friend", ["I'd love to be your friend {name} 💜"]],
        ["you're kind", ["Thank you {name} ❤️ Kindness is everything"]],
        ["i need help", ["I'm here {name} 🤝 Tell me what's wrong"]],
        ["you're the best", ["Aw thanks {name}! 🥰 You're the best too!"]],
        ["hello there", ["Hello there {name}! 😊 General Kenobi vibes!"]],
        ["hi bot", ["Hi {name}! 🤖 BotHEX at your service!"]],
    ]

    # Jaza hadi 100 kwa kurudia na kuvarry
    all_greetings = greetings_sw + greetings_en
    while len(all_greetings) < 100:
        base = random.choice(greetings_sw + greetings_en)
        all_greetings.append([base[0] + f" {len(all_greetings)}", base[1]])

    return all_greetings[:100]

def load_data():
    global dataset, memory, corpus
    if not os.path.exists(dataset_path):
        dataset = {"pairs": generate_100_greetings()}
        with open(dataset_path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
    else:
        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            if isinstance(raw_data, dict) and "pairs" not in raw_data:
                print("Inaconvert dataset ya zamani kwenda format ya pairs...")
                pairs = []
                for swali, jibu in raw_data.items():
                    swali = str(swali).strip()
                    jibu = str(jibu).strip()
                    pairs.append({"q": swali, "a": [jibu]})
                dataset = {"pairs": pairs}
                with open(dataset_path, "w", encoding="utf-8") as f:
                    json.dump(dataset, f, ensure_ascii=False, indent=2)
                print(f"✅ Imeconvert maswali {len(pairs)} kwa format ya pairs!")

            elif isinstance(raw_data, dict) and "pairs" in raw_data:
                dataset = raw_data
                fixed_pairs = []
                for p in dataset["pairs"]:
                    if isinstance(p, dict) and "q" in p and "a" in p:
                        if not isinstance(p["a"], list):
                            p["a"] = [str(p["a"])]
                        fixed_pairs.append(p)
                dataset["pairs"] = fixed_pairs if fixed_pairs else generate_100_greetings()
            else:
                dataset = {"pairs": generate_100_greetings()}

        except Exception as e:
            print(f"Dataset error: {e}")
            dataset = {"pairs": generate_100_greetings()}
            with open(dataset_path, "w", encoding="utf-8") as f:
                json.dump(dataset, f, ensure_ascii=False, indent=2)

    if not os.path.exists(memory_path):
        memory = {}
        with open(memory_path, "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
    else:
        try:
            with open(memory_path, "r", encoding="utf-8") as f:
                memory = json.load(f)
            if not isinstance(memory, dict):
                memory = {}
        except:
            memory = {}

    if not os.path.exists(corpus_path):
        with open(corpus_path, "w", encoding="utf-8") as f:
            f.write("Hello=Hujambo\nHow are you=U hali gani\nThank you=Asante")

    with open(corpus_path, "r", encoding="utf-8") as f:
        corpus = [line.strip() for line in f if line.strip() and "=" in line]

    init_db()
    return dataset, memory, corpus

def save_permanent(question, answer, lang):
    q_norm = smart_normalize(question)
    memory[q_norm] = answer

    found = False
    for i, pair in enumerate(dataset["pairs"]):
        if isinstance(pair, dict) and smart_normalize(pair.get("q", "")) == q_norm:
            dataset["pairs"][i]["a"] = [answer]
            found = True
            break

    if not found:
        dataset["pairs"].append({"q": question, "a": [answer]})

    try:
        conn = sqlite3.connect(db_path, timeout=10)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO facts (question, answer, lang) VALUES (?,?,?)", (q_norm, answer, lang))
        conn.commit()
        conn.close()
    except:
        pass

    with open(dataset_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    with open(memory_path, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

dataset, memory, corpus = load_data()

def detect_emoji_mood(text):
    for emoji, mood in EMOJI_MOOD.items():
        if emoji in text:
            return mood
    return None

def remove_emoji_for_search(text):
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F" u"\U0001F300-\U0001F5FF" u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF" u"\U00002702-\U000027B0" u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def smart_normalize(text):
    text = remove_emoji_for_search(text)
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text

def solve_quadratic(a, b, c):
    try:
        d = b*b - 4*a*c
        if d < 0:
            return "Hakuna suluhisho la namba halisi 📉"
        elif d == 0:
            x = -b / (2*a)
            return f"x = {round(x, 4)} 📊"
        else:
            x1 = (-b + math.sqrt(d)) / (2*a)
            x2 = (-b - math.sqrt(d)) / (2*a)
            return f"x₁ = {round(x1, 4)}, x₂ = {round(x2, 4)} 📊"
    except:
        return None

def solve_math(expr):
    try:
        expr = expr.lower().strip()
        quad_match = re.search(r'(\d*)x\^2\s*([+-]?\s*\d*)x\s*([+-]?\s*\d+)\s*=\s*0', expr)
        if quad_match:
            a = int(quad_match.group(1) or 1)
            b_str = quad_match.group(2).replace(" ", "")
            b = int(b_str) if b_str not in ["", "+", "-"] else (1 if b_str in ["", "+"] else -1)
            c = int(quad_match.group(3).replace(" ", ""))
            return solve_quadratic(a, b, c)

        log_match = re.search(r'log10?\(([\d.]+)\)', expr)
        if log_match:
            num = float(log_match.group(1))
            if "log10" in expr:
                return f"log₁₀({num}) = {round(math.log10(num), 4)} 📐"
            else:
                return f"ln({num}) = {round(math.log(num), 4)} 📐"

        sqrt_match = re.search(r'sqrt\(([\d.]+)\)', expr)
        if sqrt_match:
            num = float(sqrt_match.group(1))
            return f"√{num} = {round(math.sqrt(num), 4)} 📐"

        expr = expr.replace("x", "*").replace("^", "**").replace(",", "")
        allowed = "0123456789+-*/(). sqrtlogsincoastanpi "
        if all(c in allowed for c in expr.lower()):
            result = eval(expr, {"__builtins__": None}, {
                "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
                "sin": math.sin, "cos": math.cos, "tan": math.tan, "pi": math.pi
            })
            return f"Jibu ni: {round(result, 4)} 🧮"
    except:
        pass
    return None

def add_random_emoji(text, lang):
    emojis = ["😊", "💜", "🤖", "✨", "👍", "🎉", "💪", "🔥"] if lang == "sw" else ["😊", "💜", "🤖", "✨", "👍", "🎉", "💪"]
    return f"{text} {random.choice(emojis)}"

def format_response(text, name):
    name = name if name else "Mkuu"
    return text.replace("{name}", name)

def get_bot_response(user_msg, user_id):
    user_msg = user_msg.strip()
    user_msg_norm = smart_normalize(user_msg)
    user_msg_raw = user_msg.lower().strip()
    name, age, lang, greeted = get_user_data(user_id)
    display_name = name if name else "Mkuu"

    if greeted == 0:
        update_user(user_id, name, age, lang, 1)
        if lang == "sw":
            return add_random_emoji(f"Hi {display_name}! Mimi ni BotHEX 🇹🇿 ||Nielewe hata ukitumia emoji 😂. Naomba unipe jina lako na umri wako nikuwekee kumbukumbu 💜", lang)
        else:
            return add_random_emoji(f"Hi {display_name}! I'm BotHEX 🇹🇿 ||I understand emojis 😂. Please tell me your name and age so I can remember 💜", lang)

    if "english" in user_msg_norm:
        update_user(user_id, name, age, "en", greeted)
        return add_random_emoji(format_response("Switched to English {name}! 💜", display_name), "en")
    if "kiswahili" in user_msg_norm or "swahili" in user_msg_norm:
        update_user(user_id, name, age, "sw", greeted)
        return add_random_emoji(format_response("Tumebadilisha lugha kuwa Kiswahili {name}! 💜", display_name), "sw")

    if user_id in pending_teach:
        return user_msg

    # FEEDBACK SYSTEM
    if any(x in user_msg_norm for x in ["bad response", "mbaya", "si sahihi", "wrong"]):
        if user_id in last_question:
            pending_teach[user_id] = last_question[user_id]
            return add_random_emoji(format_response(f"Samahani {name} 😔 Jibu sahihi ni lipi? Nifundishe ili nisikose tena 🙏", display_name), lang)
        else:
            return add_random_emoji(format_response(f"Swali gani lilikuwa mbaya {name}? 😅", display_name), lang)

    if any(x in user_msg_norm for x in ["good response", "safi", "sahihi", "correct", "nzuri"]):
        return add_random_emoji(format_response(f"Asante sana {name}! 😊 Nimefurahi nimekupa jibu sahihi! 💪", display_name), lang)

    # KUMBUKA JINA + UMRI + UPGRADED MEMORY
    name_change = re.search(r"(jina langu ni|niite|call me|my name is)\s+(.+)", user_msg, flags=re.I)
    age_change = re.search(r"(umri wangu ni|i am|i'm)\s+(\d+)", user_msg, flags=re.I)

    if name_change:
        new_name = name_change.group(2).strip()
        if new_name!= name and name: # Kama jina limebadilika
            update_user(user_id, new_name, age, lang, greeted)
            return add_random_emoji(f"Upgraded memory! 📝 From now I will call you {new_name}! Nimekumbuka jina jipya {new_name} 😊", lang)
        else: # Kama ni mara ya kwanza
            update_user(user_id, new_name, age, lang, greeted)
            return add_random_emoji(f"Sawa {new_name} 😊 Nimekumbuka jina lako milele! Furahi kukufahamu 💜", lang)

    if age_change:
        new_age = age_change.group(2).strip()
        update_user(user_id, name, new_age, lang, greeted)
        return add_random_emoji(format_response(f"Sawa {name}! Nimekumbuka umri wako ni {new_age} years ✨", display_name), lang)

    mood = detect_emoji_mood(user_msg)
    if mood and mood in EMOJI_RESPONSE:
        if smart_normalize(user_msg) == "":
            resp = random.choice(EMOJI_RESPONSE[mood][lang])
            return add_random_emoji(format_response(resp, display_name), lang)

    if user_msg_raw.startswith("fundisha:"):
        try:
            sehemu = user_msg.replace("fundisha:", "", 1).split("jibu:", 1)
            if len(sehemu) == 2:
                swali = sehemu[0].strip()
                jibu = sehemu[1].strip()
                save_permanent(swali, jibu, lang)
                return add_random_emoji(format_response(f"Asante kunifundisha {name} 😊 Nitakumbuka wema wako milele!", display_name), lang)
            else:
                return add_random_emoji(format_response(f"Andika hivi {name}: fundisha: swali jibu: jibu", display_name), lang)
        except:
            return add_random_emoji(format_response(f"Andika hivi {name}: fundisha: swali jibu: jibu", display_name), lang)

    math_ans = solve_math(user_msg)
    if math_ans:
        return add_random_emoji(format_response(f"{display_name}, {math_ans}", display_name), lang)

    # COUNTDOWN 3s
    time.sleep(3)

    # 1. EXACT MATCH
    for pair in dataset["pairs"]:
        if isinstance(pair, dict) and smart_normalize(pair.get("q", "")) == user_msg_norm:
            answer = random.choice(pair.get("a", [""]))
            last_question[user_id] = pair.get("q", "")
            return add_random_emoji(format_response(answer, display_name), lang)

    # 2. KEYWORD MATCH
    user_words = set(user_msg_norm.split())
    best_match = None
    best_score = 0
    for pair in dataset["pairs"]:
        if isinstance(pair, dict):
            q_norm = smart_normalize(pair.get("q", ""))
            q_words = set(q_norm.split())
            common_words = user_words.intersection(q_words)
            score = len(common_words)
            if score > best_score and score >= 2:
                best_score = score
                best_match = pair

    if best_match:
        answer = random.choice(best_match.get("a", [""]))
        last_question[user_id] = best_match.get("q", "")
        return add_random_emoji(format_response(answer, display_name), lang)

    # 3. MEMORY
    if user_msg_norm in memory:
        last_question[user_id] = user_msg_norm
        return add_random_emoji(format_response(memory[user_msg_norm], display_name), lang)

    # 4. HAJUI
    pending_teach[user_id] = user_msg
    last_question[user_id] = user_msg
    return add_random_emoji(format_response(f"{display_name}, sijui bado 🤔 Nifundishe?", display_name), lang)

def get_user_data(user_id):
    try:
        conn = sqlite3.connect(db_path, timeout=10)
        c = conn.cursor()
        c.execute("SELECT name, age, lang, greeted FROM users WHERE user_id=?", (user_id,))
        row = c.fetchone()
        conn.close()
        return row if row else (None, None, "sw", 0)
    except:
        return (None, None, "sw", 0)

def update_user(user_id, name=None, age=None, lang=None, greeted=None):
    try:
        conn = sqlite3.connect(db_path, timeout=10)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO users (user_id, name, age, lang, greeted) VALUES (?,?,?,?,?)",
                  (user_id, name, age, lang, greeted))
        conn.commit()
        conn.close()
    except:
        pass

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    msg = data.get("msg", "")
    user_id = data.get("user_id", "default")

    if user_id in pending_teach:
        question = pending_teach[user_id]
        lang = get_user_data(user_id)[2]
        save_permanent(question, msg, lang)
        del pending_teach[user_id]
        return jsonify({"reply": add_random_emoji(msg, lang)})

    bot_reply = get_bot_response(msg, user_id)
    if "||" in bot_reply:
        parts = bot_reply.split("||")
        return jsonify({"reply": parts[0], "reply2": parts[1]})
    return jsonify({"reply": bot_reply})

@app.route("/backup")
def backup():
    zip_path = os.path.join(BASE_DIR, f"bothex_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for f in [dataset_path, memory_path, db_path]:
            if os.path.exists(f):
                zipf.write(f, os.path.basename(f))
    return send_file(zip_path, as_attachment=True, download_name="BotHEX_backup.zip")

@app.route("/learned")
def learned():
    learned_list = []
    for swali, jibu in memory.items():
        learned_list.append({"swali": swali, "jibu": jibu, "chanzo": "Memory - Umefundisha wewe"})
    for pair in dataset["pairs"]:
        if isinstance(pair, dict):
            learned_list.append({"swali": pair.get("q", ""), "jibu": pair.get("a", [""])[0] if pair.get("a") else "", "chanzo": "Dataset - Facts za msingi"})
    for line in corpus:
        parts = line.split("=")
        if len(parts) == 2:
            en, sw = parts[0].strip(), parts[1].strip()
            learned_list.append({"swali": en, "jibu": sw, "chanzo": "Language Corpus"})

    html = """<!DOCTYPE html><html><head><title>BotHEX - Ubongo</title><meta charset="UTF-8"><style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:20px}.container{max-width:900px;margin:0 auto;background:rgba(255,255,255,0.1);padding:20px;border-radius:15px}h1{text-align:center}.stats{text-align:center;font-size:18px;margin-bottom:20px;background:rgba(0,0,0,0.3);padding:15px;border-radius:10px}.card{background:rgba(255,255,255,0.15);margin:10px 0;padding:15px;border-radius:10px;border-left:4px solid #FFD700}.swali{font-weight:bold;color:#FFD700}.jibu{margin-top:8px}.chanzo{font-size:12px;color:#90EE90;margin-top:8px}</style></head><body><div class="container"><h1>🧠 BotHEX - Ubongo Wangu 🤖</h1><div class="stats">Jumla: {{total}} | Memory: {{memory_count}} | Dataset: {{dataset_count}} | Corpus: {{corpus_count}}<br><small>Nimejifunza na kukumbuka milele 💜</small></div><p style="text-align:center"><a href="/">⬅ Rudi Chat</a> | <a href="/backup">📦 Backup</a></p>{% for item in items %}<div class="card"><div class="swali">Swali: {{item.swali}}</div><div class="jibu">Jibu: {{item.jibu}}</div><div class="chanzo">{{item.chanzo}}</div></div>{% endfor %}</div></body></html>"""
    return render_template_string(html, items=learned_list, total=len(learned_list), memory_count=len(memory), dataset_count=len(dataset["pairs"]), corpus_count=len(corpus))

if __name__ == "__main__":
    print(f"BotHEX v10.0 Personal AI | Dataset: {len(dataset['pairs'])} | Memory: {len(memory)} | Corpus: {len(corpus)}")
    app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)

