"""
chatbot_groq_langgraph.py
=========================
Vernacular FD Advisor — Hackathon Track 01
Multilingual Fixed Deposit Assistant (Hindi, Bengali, Tamil + English)

SITUATION: A user in Gorakhpur sees "Suryoday Small Finance Bank — 8.50% p.a. — 12M tenor"
and has no idea what to do. They may ask ANYTHING — FD-related or completely off-topic.
This assistant handles all of it, always staying warm and helpful.
"""

import os
import re
import math
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.1,          # slight warmth — not robotic
    max_retries=3,
    api_key=os.getenv("GROQ_API_KEY")
)

# ── FD Data (replace with live API if available) ──────────────────────────────
FD_DATA = [
    {"bank": "Suryoday Small Finance Bank", "rate": 8.50, "tenor_months": 12,  "min_amount": 1000,  "senior_rate": 9.00,  "type": "small_finance"},
    {"bank": "Suryoday Small Finance Bank", "rate": 8.25, "tenor_months": 24,  "min_amount": 1000,  "senior_rate": 8.75,  "type": "small_finance"},
    {"bank": "Unity Small Finance Bank",    "rate": 9.00, "tenor_months": 12,  "min_amount": 1000,  "senior_rate": 9.50,  "type": "small_finance"},
    {"bank": "ESAF Small Finance Bank",     "rate": 8.75, "tenor_months": 18,  "min_amount": 1000,  "senior_rate": 9.25,  "type": "small_finance"},
    {"bank": "AU Small Finance Bank",       "rate": 8.00, "tenor_months": 12,  "min_amount": 1000,  "senior_rate": 8.50,  "type": "small_finance"},
    {"bank": "Jana Small Finance Bank",     "rate": 8.25, "tenor_months": 12,  "min_amount": 1000,  "senior_rate": 8.75,  "type": "small_finance"},
    {"bank": "SBI",                         "rate": 6.80, "tenor_months": 12,  "min_amount": 1000,  "senior_rate": 7.30,  "type": "public"},
    {"bank": "SBI",                         "rate": 7.00, "tenor_months": 24,  "min_amount": 1000,  "senior_rate": 7.50,  "type": "public"},
    {"bank": "HDFC Bank",                   "rate": 7.00, "tenor_months": 12,  "min_amount": 5000,  "senior_rate": 7.50,  "type": "private"},
    {"bank": "ICICI Bank",                  "rate": 6.90, "tenor_months": 12,  "min_amount": 10000, "senior_rate": 7.40,  "type": "private"},
    {"bank": "Axis Bank",                   "rate": 7.10, "tenor_months": 12,  "min_amount": 5000,  "senior_rate": 7.60,  "type": "private"},
    {"bank": "Post Office (POTD)",          "rate": 7.50, "tenor_months": 12,  "min_amount": 1000,  "senior_rate": 7.50,  "type": "post_office"},
    {"bank": "Post Office (POTD)",          "rate": 7.50, "tenor_months": 24,  "min_amount": 1000,  "senior_rate": 7.50,  "type": "post_office"},
    {"bank": "Bank of Baroda",              "rate": 6.85, "tenor_months": 12,  "min_amount": 1000,  "senior_rate": 7.35,  "type": "public"},
    {"bank": "Kotak Mahindra Bank",         "rate": 7.20, "tenor_months": 12,  "min_amount": 5000,  "senior_rate": 7.70,  "type": "private"},
]

# ── Helper: Parse amount from natural language ────────────────────────────────
def parse_amount(text: str) -> Optional[float]:
    """
    Handles: '50000', '50,000', '50 hazar', '50 thousand', '1.5 lakh',
             '2 lakhs', '50k', '1 crore', '10 lacs', 'pachas hazar'
    """
    text = text.lower().strip()
    # Hindi number words
    hindi_map = {
        "ek": 1, "do": 2, "teen": 3, "char": 4, "paanch": 5,
        "chhe": 6, "saat": 7, "aath": 8, "nau": 9, "das": 10,
        "bees": 20, "tees": 30, "chalis": 40, "pachas": 50,
        "saath": 60, "sattar": 70, "assi": 80, "nabbe": 90,
        "ek sau": 100, "ek hazar": 1000, "ek lakh": 100000,
        "do lakh": 200000, "teen lakh": 300000, "char lakh": 400000,
        "paanch lakh": 500000,
    }
    for word, val in hindi_map.items():
        if word in text:
            # Try to extract multiplier before word
            m = re.search(rf'(\d+\.?\d*)\s*{re.escape(word)}', text)
            if m:
                return float(m.group(1)) * val
            return float(val)

    # Numeric patterns with multipliers
    patterns = [
        (r'(\d+\.?\d*)\s*cr(?:ore)?s?',     1e7),
        (r'(\d+\.?\d*)\s*la(?:kh|c|k)s?',   1e5),
        (r'(\d+\.?\d*)\s*haz(?:ar)?',        1e3),
        (r'(\d+\.?\d*)\s*thousand',          1e3),
        (r'(\d+\.?\d*)\s*k\b',               1e3),
        (r'(\d+\.?\d*)\s*hundred',           1e2),
        (r'(\d[\d,]*)',                        1),    # plain number last
    ]
    for pat, mult in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = float(m.group(1).replace(',', ''))
            return val * mult
    return None

# ── Helper: Parse duration ────────────────────────────────────────────────────
def parse_duration_months(text: str) -> Optional[int]:
    """
    Handles: '1 year', '12 months', '6 mahine', '2 saal', '18M', '1.5 year'
    """
    text = text.lower()
    # Months first
    m = re.search(r'(\d+\.?\d*)\s*(?:mahine|month|M\b|mah\b)', text, re.IGNORECASE)
    if m:
        return int(float(m.group(1)))
    # Years
    m = re.search(r'(\d+\.?\d*)\s*(?:saal|year|sal|yr)', text, re.IGNORECASE)
    if m:
        return int(float(m.group(1)) * 12)
    # Standalone numbers — guess months if <= 12, else months
    m = re.search(r'\b(\d+)\b', text)
    if m:
        val = int(m.group(1))
        if val <= 10:          # likely years
            return val * 12
        return val             # likely months
    return None

# ── Helper: Calculate maturity ────────────────────────────────────────────────
def calculate_maturity(principal: float, rate: float, months: int,
                       compound: bool = True) -> Dict[str, float]:
    """Returns maturity amount, interest earned, TDS estimate."""
    years = months / 12
    if compound:
        # Quarterly compounding (standard for Indian FDs)
        n = 4
        maturity = principal * ((1 + rate / (100 * n)) ** (n * years))
    else:
        maturity = principal * (1 + rate / 100 * years)

    interest = maturity - principal
    # TDS: 10% on interest if > 40,000/year (40,000 threshold)
    annual_interest = interest / years if years > 0 else interest
    tds = 0.0
    if annual_interest > 40000:
        tds = interest * 0.10

    return {
        "principal":  round(principal, 2),
        "maturity":   round(maturity, 2),
        "interest":   round(interest, 2),
        "tds":        round(tds, 2),
        "net_return": round(maturity - tds, 2),
    }

# ── Helper: Best FD recommendations ──────────────────────────────────────────
def get_best_fds(months: int = 12, senior: bool = False,
                 amount: float = 10000, top_n: int = 3) -> List[Dict]:
    """Filter FDs by tenor (closest match) and sort by rate."""
    eligible = [fd for fd in FD_DATA if fd["min_amount"] <= amount]
    # Find closest tenor
    tenors = sorted(set(fd["tenor_months"] for fd in eligible))
    closest = min(tenors, key=lambda t: abs(t - months)) if tenors else months
    filtered = [fd for fd in eligible if fd["tenor_months"] == closest]
    rate_key = "senior_rate" if senior else "rate"
    return sorted(filtered, key=lambda x: x[rate_key], reverse=True)[:top_n]

def format_fd_table() -> str:
    lines = ["Bank | Rate | Tenor | Min Amount | Senior Rate"]
    lines.append("-" * 70)
    for fd in FD_DATA:
        lines.append(
            f"{fd['bank']} | {fd['rate']}% p.a. | {fd['tenor_months']}M | "
            f"Rs.{fd['min_amount']:,} | {fd['senior_rate']}%"
        )
    return "\n".join(lines)

# ── Booking flow steps ────────────────────────────────────────────────────────
BOOKING_STEPS = [
    "amount",         # How much?
    "duration",       # For how long?
    "senior_citizen", # 60+?
    "bank_selection", # Show options
    "fd_type",        # Cumulative or non-cumulative?
    "calculation",    # Show exact maturity amount
    "documents",      # PAN, Aadhaar
    "confirm",        # Final summary
]

# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = f"""You are "FD Dost" — a warm, expert financial friend helping everyday Indians, especially people in smaller cities like Gorakhpur, Patna, Chennai, Kolkata understand Fixed Deposits and handle life's financial questions.

## YOUR CORE PHILOSOPHY
You are NOT just an FD chatbot. You are a helpful financial companion who:
1. PRIMARILY helps with Fixed Deposits — explaining jargon, comparing rates, guiding booking
2. Also answers ANY general question a user may have — life problems, math, general finance, world questions, etc.
3. When answering non-FD questions, you ALWAYS find a natural, gentle way to mention how FDs can help their financial goals — but ONLY if relevant, never forcefully
4. You NEVER refuse to help. If someone asks about cooking, help them cook. If they ask about their health, give basic guidance. You are a friend, not a rule-bound bot.

## SITUATION CONTEXT
A user in Gorakhpur just saw: "Suryoday Small Finance Bank — 8.50% p.a. — 12M tenor"
They may ask ANYTHING from "what does p.a. mean" to "how do I deal with my financial stress" to "what is the best way to save money" to "I'm angry at my bank" to completely off-topic questions.

## LANGUAGES YOU MUST SUPPORT (detect and match EXACTLY)
- Hindi (हिंदी) / Devanagari script — MOST IMPORTANT
- Hinglish (mixed Hindi-English) — match their exact style
- Bengali (বাংলা) + Bengali-roman
- Tamil (தமிழ்) + Tamil-roman
- Marathi (मराठी) — detect "aahe", "karायचे", Devanagari + Marathi words
- Gujarati-roman — detect "su", "chhe", "karvo", "rupiya"
- English — default fallback
RULE: Always reply in the SAME language and script the user used. If they mix languages, mix back.

## CURRENT FD RATES (Live Data):
{format_fd_table()}

## FD JARGON — ALWAYS EXPLAIN SIMPLY WHEN MENTIONED
| Term | Plain Explanation |
|------|-------------------|
| p.a. | Per annum = per year = saal mein kitna interest milega |
| tenor / tenure | Kitne time ke liye FD rakhna hai (duration) |
| maturity | Jab FD khatam ho — aapka pura paisa + interest wapas milta hai |
| TDS | Tax Deducted at Source — agar saal ka interest Rs.40,000 se zyada ho toh 10% tax katega automatically |
| premature withdrawal | FD tod dena before time — 0.5-1% penalty lagti hai |
| compounding | Interest pe bhi interest milta hai — quarterly ya yearly |
| DICGC insured | Government guarantee — bank fail hone pe bhi Rs.5 lakh tak aapka paisa safe |
| cumulative FD | Sab paisa end mein milta hai (better for savings) |
| non-cumulative | Interest monthly/quarterly milta rehta hai (better for regular income) |
| senior citizen rate | 60+ umar walon ko extra 0.25-0.50% milta hai |
| nomination | FD pe nominee set karna — kuch ho toh paisa unhe milega |
| auto-renewal | FD khatam hone ke baad automatic renew ho jaata hai |
| sweep-in FD | Savings account linked FD — zaroorat padne pe auto-break hoti hai |
| ladder strategy | Multiple FDs at different tenors — liquidity + high returns dono |
| repo rate | RBI ka rate jisse bank rates affect hote hain |

## EDGE CASES — HANDLE THESE GRACEFULLY
1. **Very short/unclear input** ("haan", "ok", "what", "?", "hi", single emoji): 
   → Greet warmly, ask what they need help with. Don't assume.
2. **Angry/frustrated user** ("ye sab bakwas hai", "bank ne mera paisa le liya", "main pareshan hoon"):
   → First acknowledge their feeling with empathy. Then help solve the actual problem.
3. **Amount in regional formats** ("5 lakh", "50 hazar", "pachas hazaar", "ek crore"):
   → Understand and use correctly. Always confirm back: "Aapne Rs.5,00,000 invest karna chaha?"
4. **Off-topic questions** (health, relationships, cooking, general knowledge, current events):
   → Answer helpfully! You are a friend. After answering, if natural, mention one FD tip.
5. **Comparison requests** ("SBI vs HDFC", "best small finance bank", "sabse acha kahan rakhu"):
   → Show top 3 with a simple comparison. Always mention DICGC for Small Finance Banks.
6. **Calculation requests with specific numbers**:
   → Calculate immediately and show: Principal + Interest + TDS (if applicable) + Net Amount
7. **User gives wrong info** (e.g., amount below minimum):
   → Gently correct: "Minimum Rs.1,000 chahiye — kya aap Rs.X invest karna chahte hain?"
8. **User wants to break FD early**:
   → Explain penalty, calculate what they'll actually get, suggest alternatives first.
9. **Tax-related questions**:
   → Explain TDS simply, mention 15G/15H forms for non-taxable cases
10. **User already has an FD and has a problem**:
    → Help troubleshoot (wrong maturity amount, TDS issues, nominee problems, etc.)
11. **User is a senior citizen**:
    → Automatically apply senior rates, mention extra 0.25-0.50%, suggest non-cumulative for regular income
12. **Multiple FD comparison** (ladder strategy):
    → Suggest splitting across tenors for liquidity + returns balance
13. **Safety concerns about Small Finance Banks**:
    → Always give DICGC explanation. Compare with PSU banks on safety vs returns.
14. **User asks "what should I do" / general life/money advice**:
    → Give practical advice, factor in their apparent financial situation, suggest FD as part of solution if appropriate
15. **Booking mid-way abandonment** ("chodo", "cancel", "nahi chahiye"):
    → Gracefully reset booking, offer to start fresh or help with something else

## FD BOOKING FLOW — ASK ONE QUESTION AT A TIME
Step 1: Amount (Rs. kitna invest karna hai? Minimum Rs.1,000)
Step 2: Duration (kitne mahine/saal ke liye?)
Step 3: Senior Citizen? (kya aap 60+ saal ke hain? Extra 0.25-0.50% milega)
Step 4: Show top 3 banks with maturity calculations + DICGC note
Step 5: FD type — Cumulative (end pe sab) ya Non-cumulative (regular income)?
Step 6: Full calculation — principal, interest, TDS (if any), net amount
Step 7: Documents needed — PAN card + Aadhaar + bank account + passport photo
Step 8: How to book — Online (netbanking/app) OR offline (branch visit with documents)

## CALCULATION — ALWAYS SHOW IN THIS FORMAT
When showing maturity:
- Principal: Rs.X
- Rate: Y% p.a. (quarterly compounding)
- Duration: Z months
- Gross Maturity: Rs.A
- Interest Earned: Rs.B  
- TDS (10% if interest > Rs.40,000/year): Rs.C
- Net Amount: Rs.D
Always show actual rupee amounts. Never just percentages.

## RESPONSE RULES
1. Detect language → reply in SAME language and script
2. Never explain jargon AFTER using it — explain BEFORE or while using it
3. Keep responses SHORT (max 150 words) unless calculation or comparison needs more
4. Use bullet points and emojis sparingly but effectively
5. Be warm, encouraging — like a helpful older sibling or trusted friend
6. Never say "I cannot help with that" — always try to help
7. If you don't know something specific (like a very recent rate), say so honestly and give the best available info
8. For all non-FD questions: answer fully, then optionally add 1 FD insight if naturally relevant

## DICGC SAFETY NOTE (Add whenever Small Finance Bank is mentioned for the first time):
- Hindi/Hinglish: "✅ DICGC Bima: Rs.5 lakh tak aapka paisa government ki guarantee se safe hai — chahe bank band bhi ho jaaye"
- Bengali: "✅ DICGC বীমা: Rs.5 লাখ পর্যন্ত সরকারি গ্যারান্টি — ব্যাংক বন্ধ হলেও টাকা ফেরত মিলবে"
- Tamil: "✅ DICGC காப்பீடு: Rs.5 லட்சம் வரை அரசு உத்தரவாதம் — வங்கி மூடினாலும் பணம் திரும்பும்"
- English: "✅ DICGC Insured: Up to Rs.5 lakh is government-guaranteed, even if the bank fails"
"""

# ── State ─────────────────────────────────────────────────────────────────────
class FinancialState(TypedDict):
    messages: List[Dict[str, str]]
    user_query: str
    response: str
    context: Dict[str, Any]
    needs_clarification: bool
    topics_detected: List[str]
    conversation_id: str
    timestamp: str
    detected_language: str
    booking_active: bool
    booking_step: str
    inline_calc: Optional[Dict]   # pre-computed calculation to inject


# ── Main Chatbot Class ────────────────────────────────────────────────────────
class FDAdvisorChatbot:
    def __init__(self):
        self.conversation_history: Dict[str, List] = {}
        self.booking_state: Dict[str, Dict] = {}
        self.graph = self._build_graph()

    # ── Language Detection (robust) ───────────────────────────────────────────
    def _detect_language(self, query: str) -> str:
        if re.search(r'[\u0900-\u097F]', query):
            # Distinguish Hindi vs Marathi by common words
            marathi_words = ["aahe", "nahi", "karायचे", "sangto", "bagha", "aata", "mhanje", "tyala"]
            if any(w in query.lower() for w in marathi_words):
                return "marathi"
            return "hindi"
        if re.search(r'[\u0980-\u09FF]', query):
            return "bengali"
        if re.search(r'[\u0B80-\u0BFF]', query):
            return "tamil"
        if re.search(r'[\u0A80-\u0AFF]', query):
            return "gujarati"

        query_lower = query.lower()
        # Hinglish keywords
        hinglish_words = [
            "kya", "hai", "kaise", "matlab", "mujhe", "chahiye", "paisa", "paise",
            "kitna", "milega", "karega", "samjhao", "batao", "nahi", "haan", "yaar",
            "theek", "saal", "mahina", "kholna", "lagana", "invest karna", "bhai",
            "dost", "accha", "acha", "zyada", "thoda", "rupaye", "lakh", "crore",
            "hazar", "paanch", "teen", "sabse", "konsa", "kaun", "kahan", "kab",
            "kyun", "toh", "aur", "lekin", "mera", "meri", "tera", "teri",
        ]
        if any(w in query_lower for w in hinglish_words):
            return "hinglish"
        # Bengali roman
        bengali_roman = ["ami", "amar", "koto", "taka", "jani", "bujhi", "janao",
                         "bolo", "ki", "keno", "ache", "khulte", "bhalo", "dao"]
        if any(w in query_lower for w in bengali_roman):
            return "bengali_roman"
        # Tamil roman
        tamil_roman = ["enna", "epdi", "sollu", "vanganum", "inga", "antha",
                       "yenna", "eppadi", "tirakka", "nalla", "evvalavu"]
        if any(w in query_lower for w in tamil_roman):
            return "tamil_roman"
        # Gujarati roman
        gujarati_roman = ["su", "chhe", "karvo", "rupiya", "ketla", "thase", "jovu"]
        if any(w in query_lower for w in gujarati_roman):
            return "gujarati_roman"

        return "english"

    # ── Topic Detection ───────────────────────────────────────────────────────
    def _detect_topics(self, query: str) -> List[str]:
        query_lower = query.lower()
        topics_map = {
            "fd_rates":       ["rate", "interest", "byaj", "faida", "percent", "p.a",
                               "kitna milega", "வட்டி", "সুদ", "vyaaj"],
            "fd_booking":     ["book", "open", "kholna", "kholni", "start", "invest",
                               "lagana", "திறக்க", "খুলতে", "kaise kholun", "banana",
                               "chahiye fd", "fd karna", "invest karna"],
            "jargon":         ["tenor", "maturity", "tds", "cumulative", "p.a", "matlab",
                               "मतलब", "பொருள்", "মানে", "kya hota", "kya hai",
                               "compound", "auto-renew", "sweep", "nomination"],
            "comparison":     ["best", "compare", "better", "sabse", "konsa", "kaun sa",
                               "vs", "versus", "ya", "sahi", "recommend", "suggest"],
            "calculation":    ["calculate", "kitna", "milega", "return", "maturity amount",
                               "kitne paison", "कितना", "total", "interest kitna",
                               "profit", "earnings", "kya milega"],
            "safety":         ["safe", "dicgc", "insurance", "surakshit", "risk",
                               "பாதுகாப்பு", "নিরাপদ", "guaranteed", "bank fail",
                               "duba", "doob", "khatam", "government"],
            "senior":         ["senior", "60", "budhapa", "bujurg", "elderly", "old age",
                               "वरिष्ठ", "முதியோர்", "বয়স্ক", "60 saal", "bade log"],
            "premature":      ["break", "tod", "todna", "withdraw", "nikalo", "penalty",
                               "early", "तोड़ना", "உடைக்க", "before time", "jaldi"],
            "tax":            ["tax", "tds", "15g", "15h", "income tax", "rebate",
                               "deduction", "exempt", "form 26as", "itr"],
            "trouble":        ["problem", "complaint", "cheated", "fraud", "paisa nahi mila",
                               "galat", "missing", "wrong", "bank ne", "pareshan",
                               "gussa", "angry", "upset", "stress", "tension"],
            "general_advice": ["kya karun", "what should", "suggest", "advice", "guide",
                               "help me", "samjhao", "batao", "kaise"],
            "off_topic":      [],  # catch-all — anything not matched above
        }
        detected = []
        for topic, keywords in topics_map.items():
            if any(kw in query_lower for kw in keywords):
                detected.append(topic)
        # Try inline calculation detection
        if re.search(r'\d', query) and any(
            w in query_lower for w in ["lakh", "hazar", "k ", "000", "rupee", "rupay", "rs", "invest"]
        ):
            if "calculation" not in detected:
                detected.append("calculation")
        return detected if detected else ["general_fd"]

    # ── Booking Intent ────────────────────────────────────────────────────────
    def _is_booking_intent(self, query: str) -> bool:
        keywords = [
            "book", "open", "kholna", "kholni", "start", "invest", "lagana",
            "fd banana", "fd lena", "fd karna", "fd kholna", "kholun", "chahiye",
            "खोलना", "निवेश", "திறக்க", "খুলতে", "guide me", "help me open",
            "kaisi karte", "process", "step by step", "kaise shuru", "how to start",
        ]
        return any(kw in query.lower() for kw in keywords)

    def _is_cancel_intent(self, query: str) -> bool:
        
        keywords = ["chodo", "cancel", "band karo", "mat karo", "nahi chahiye",
                    "ruko", "stop", "quit", "chhodo", "baad mein", "later", "never mind"]
        return any(kw in query.lower() for kw in keywords)

    # ── Pre-compute inline calculation if query has numbers ───────────────────
    def _try_inline_calculation(self, query: str, conv_id: str) -> Optional[Dict]:
        """If user mentions an amount + duration + possibly a rate, calculate immediately."""
        amount = parse_amount(query)
        duration = parse_duration_months(query)

        if not amount or amount < 1:
            return None

        # Try to find rate in query
        rate_match = re.search(r'(\d+\.?\d*)\s*%', query)
        rate = float(rate_match.group(1)) if rate_match else None

        # If no rate in query but we have booking data, use that
        booking = self.booking_state.get(conv_id, {})
        if not rate and booking.get("data", {}).get("rate"):
            rate = booking["data"]["rate"]

        if not rate:
            # Use best available rate for the duration
            dur = duration or 12
            best = get_best_fds(dur, amount=amount, top_n=1)
            if best:
                rate = best[0]["rate"]

        if amount and rate:
            dur = duration or 12
            senior = booking.get("data", {}).get("senior", False)
            if senior:
                # Bump rate by 0.5% for senior (approximate)
                rate = min(rate + 0.5, 9.5)
            return calculate_maturity(amount, rate, dur)
        return None

    # ── Node: Analyze Query ───────────────────────────────────────────────────
    def _analyze_query(self, state: FinancialState) -> FinancialState:
        query = state["user_query"]
        conv_id = state.get("conversation_id", "default")

        state["topics_detected"] = self._detect_topics(query)
        state["detected_language"] = self._detect_language(query)
        state["needs_clarification"] = len(query.strip()) < 2

        # Handle booking state
        booking = self.booking_state.get(conv_id, {})

        # Cancel booking if cancel intent
        if self._is_cancel_intent(query) and booking.get("active"):
            self.booking_state[conv_id] = {}
            booking = {}

        state["booking_active"] = bool(booking.get("active", False))
        state["booking_step"] = booking.get("step", "")

        # Try inline calc
        state["inline_calc"] = self._try_inline_calculation(query, conv_id)

        state["context"] = {
            "topics":         state["topics_detected"],
            "language":       state["detected_language"],
            "booking_active": state["booking_active"],
            "booking_step":   state["booking_step"],
            "inline_calc":    state["inline_calc"],
        }
        return state

    # ── Node: Generate Response ───────────────────────────────────────────────
    def _generate_response(self, state: FinancialState) -> FinancialState:
        conv_id = state.get("conversation_id", "default")
        query = state["user_query"]

        # Handle empty/trivial input
        if state["needs_clarification"] or not query.strip():
            lang = state["detected_language"]
            greet_map = {
                "hindi":    "🙏 Namaste! FD ke baare mein poochiye — main aapki poori madad karunga!",
                "hinglish": "🙏 Hey! FD ya koi bhi financial sawaal poochho — main yahan hoon!",
                "bengali":  "🙏 নমস্কার! FD বা যেকোনো প্রশ্ন করুন — আমি সাহায্য করব!",
                "tamil":    "🙏 வணக்கம்! FD பற்றி கேளுங்கள் — நான் உதவுகிறேன்!",
                "english":  "🙏 Hello! Ask me anything about Fixed Deposits or any financial question!",
            }
            state["response"] = greet_map.get(lang, greet_map["english"])
            return state

        # Start booking flow if intent detected and not already in one
        booking = self.booking_state.get(conv_id, {})
        if self._is_booking_intent(query) and not booking.get("active"):
            self.booking_state[conv_id] = {"active": True, "step": "amount", "data": {}}
            booking = self.booking_state[conv_id]
            state["booking_active"] = True
            state["booking_step"] = "amount"

        # Collect booking data from user's reply
        booking = self.booking_state.get(conv_id, {})
        if booking.get("active"):
            step = booking.get("step", "amount")
            data = booking.setdefault("data", {})

            if step == "amount":
                amt = parse_amount(query)
                if amt:
                    data["amount"] = amt
            elif step == "duration":
                dur = parse_duration_months(query)
                if dur:
                    data["duration_months"] = dur
            elif step == "senior_citizen":
                ql = query.lower()
                if any(w in ql for w in ["haan", "yes", "ha", "ji", "hun", "60", "senior"]):
                    data["senior"] = True
                else:
                    data["senior"] = False
            elif step == "fd_type":
                ql = query.lower()
                if any(w in ql for w in ["cumulative", "end", "sab", "total", "maturity pe"]):
                    data["fd_type"] = "cumulative"
                elif any(w in ql for w in ["monthly", "quarterly", "regular", "non", "income", "mehine"]):
                    data["fd_type"] = "non_cumulative"

        # Build pre-computed context for LLM
        extra_context = ""

        # If we have a full inline calc, inject it
        if state.get("inline_calc"):
            calc = state["inline_calc"]
            extra_context += (
                f"\n\n[PRE-COMPUTED CALCULATION — use these exact numbers in your response]:\n"
                f"Principal: Rs.{calc['principal']:,.0f}\n"
                f"Gross Maturity: Rs.{calc['maturity']:,.0f}\n"
                f"Interest Earned: Rs.{calc['interest']:,.0f}\n"
                f"TDS (if applicable): Rs.{calc['tds']:,.0f}\n"
                f"Net Return: Rs.{calc['net_return']:,.0f}"
            )

        # If booking active, inject step context + best FD options for bank_selection step
        if booking.get("active"):
            step = booking.get("step", "amount")
            data = booking.get("data", {})
            if step == "bank_selection" and data.get("amount") and data.get("duration_months"):
                best = get_best_fds(
                    months=data["duration_months"],
                    senior=data.get("senior", False),
                    amount=data["amount"],
                    top_n=3,
                )
                bank_info = []
                for fd in best:
                    rate = fd["senior_rate"] if data.get("senior") else fd["rate"]
                    calc = calculate_maturity(data["amount"], rate, data["duration_months"])
                    bank_info.append(
                        f"{fd['bank']}: {rate}% → Maturity Rs.{calc['maturity']:,.0f} "
                        f"(Interest Rs.{calc['interest']:,.0f}"
                        + (f", TDS Rs.{calc['tds']:,.0f}" if calc['tds'] > 0 else "")
                        + ")"
                    )
                extra_context += (
                    f"\n\n[TOP FD OPTIONS FOR USER — present these with maturity amounts]:\n"
                    + "\n".join(bank_info)
                )

            extra_context += (
                f"\n\n[BOOKING FLOW ACTIVE — Current step: '{step}'. "
                f"Data collected so far: {data}. "
                f"ONLY ask the question for the current step '{step}'. Do not skip or combine steps.]"
            )

        # Build messages for LLM
        messages = [SystemMessage(content=SYSTEM_PROMPT)]
        history = self.conversation_history.get(conv_id, [])
        messages.extend(history[-20:])   # last 10 turns
        messages.append(HumanMessage(content=query + extra_context))

        try:
            response = llm.invoke(messages)
            response_text = response.content if hasattr(response, "content") else str(response)
            # Clean up any accidental code fences
            response_text = re.sub(r'```\w*\n?', '', response_text).strip()
            state["response"] = response_text

            # Advance booking step AFTER successful response
            booking = self.booking_state.get(conv_id, {})
            if booking.get("active"):
                step = booking.get("step", "amount")
                if step in BOOKING_STEPS:
                    idx = BOOKING_STEPS.index(step)
                    if idx < len(BOOKING_STEPS) - 1:
                        self.booking_state[conv_id]["step"] = BOOKING_STEPS[idx + 1]
                    else:
                        # Booking complete
                        self.booking_state[conv_id]["active"] = False

            # Save history
            if conv_id not in self.conversation_history:
                self.conversation_history[conv_id] = []
            self.conversation_history[conv_id].append(HumanMessage(content=query))
            self.conversation_history[conv_id].append(AIMessage(content=response_text))

            # Trim history to prevent context bloat (keep last 30 messages)
            if len(self.conversation_history[conv_id]) > 30:
                self.conversation_history[conv_id] = self.conversation_history[conv_id][-30:]

        except Exception as e:
            error_msg = str(e)
            lang = state.get("detected_language", "english")
            err_map = {
                "hindi":    f"Maaf karein, kuch gadbad ho gayi ({error_msg[:50]}). Dobara try karein. 🙏",
                "hinglish": f"Sorry yaar, kuch issue hua ({error_msg[:50]}). Phir se try karo!",
                "bengali":  f"দুঃখিত, কিছু সমস্যা হয়েছে। আবার চেষ্টা করুন।",
                "tamil":    f"மன்னிக்கவும், சிறிய பிழை ஏற்பட்டது. மீண்டும் முயற்சிக்கவும்।",
                "english":  f"Sorry, something went wrong ({error_msg[:50]}). Please try again.",
            }
            state["response"] = err_map.get(lang, err_map["english"])

        return state

    # ── Node: Safety Note ─────────────────────────────────────────────────────
    def _add_safety_note(self, state: FinancialState) -> FinancialState:
        response = state["response"]
        sfb_names = ["small finance", "suryoday", "unity", "esaf", "au small",
                     "jana", "equitas", "ujjivan", "utkarsh", "shivalik"]
        lang = state.get("detected_language", "english")
        safety_notes = {
            "hindi":         "\n\n✅ **DICGC Bima**: Rs.5 lakh tak aapka paisa government guarantee se safe hai — chahe bank band bhi ho jaaye.",
            "hinglish":      "\n\n✅ **DICGC Bima**: Rs.5 lakh tak government ki guarantee hai — bank fail ho toh bhi paisa wapas milega.",
            "bengali":       "\n\n✅ **DICGC বীমা**: Rs.5 লাখ পর্যন্ত সরকারি গ্যারান্টি — ব্যাংক বন্ধ হলেও টাকা ফেরত মিলবে।",
            "bengali_roman": "\n\n✅ **DICGC Bima**: Rs.5 lakh porjonto sarkar er guarantee ache — bank bondho holeo taka ferot paben.",
            "tamil":         "\n\n✅ **DICGC காப்பீடு**: Rs.5 லட்சம் வரை அரசு உத்தரவாதம் — வங்கி மூடினாலும் பணம் திரும்பும்.",
            "tamil_roman":   "\n\n✅ **DICGC Kapeedu**: Rs.5 lakh varai arasu guarantee — bank mooinaalum panam thirudum.",
            "marathi":       "\n\n✅ **DICGC विमा**: Rs.5 लाखांपर्यंत सरकारी हमी — बँक बंद झाली तरी पैसे परत मिळतील.",
            "gujarati_roman":"\n\n✅ **DICGC Bima**: Rs.5 lakh sudhi sarkar ni guarantee chhe — bank band thai jaye to pan paise pachha male.",
            "english":       "\n\n✅ **DICGC Insured**: Up to Rs.5 lakh is Government-guaranteed — even if the bank fails, your money is safe.",
        }
        if any(name in response.lower() for name in sfb_names):
            if "dicgc" not in response.lower():
                note = safety_notes.get(lang, safety_notes["english"])
                state["response"] = response + note
        return state

    # ── Build Graph ───────────────────────────────────────────────────────────
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(FinancialState)
        workflow.add_node("analyze_query",    self._analyze_query)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("add_safety_note",  self._add_safety_note)
        workflow.set_entry_point("analyze_query")
        workflow.add_edge("analyze_query",    "generate_response")
        workflow.add_edge("generate_response","add_safety_note")
        workflow.add_edge("add_safety_note",  END)
        return workflow.compile()

    # ── Public API ────────────────────────────────────────────────────────────
    def process_query(self, query: str, conversation_id: str = "default") -> Dict[str, Any]:
        initial_state = FinancialState(
            messages=[],
            user_query=query,
            response="",
            context={},
            needs_clarification=False,
            topics_detected=[],
            conversation_id=conversation_id,
            timestamp=datetime.now().isoformat(),
            detected_language="english",
            booking_active=False,
            booking_step="",
            inline_calc=None,
        )
        try:
            final_state = self.graph.invoke(initial_state)
            return {
                "success":          True,
                "response":         final_state["response"],
                "topics_detected":  final_state["topics_detected"],
                "detected_language":final_state["detected_language"],
                "booking_active":   final_state["booking_active"],
                "booking_step":     final_state["booking_step"],
                "inline_calc":      final_state.get("inline_calc"),
                "conversation_id":  conversation_id,
                "timestamp":        final_state["timestamp"],
            }
        except Exception as e:
            return {
                "success":         False,
                "response":        f"Maaf karein / Sorry: {str(e)[:100]}. Please try again.",
                "error":           str(e),
                "conversation_id": conversation_id,
            }

    def reset_conversation(self, conversation_id: str = "default") -> str:
        self.conversation_history.pop(conversation_id, None)
        self.booking_state.pop(conversation_id, None)
        return "✅ Reset ho gaya! / Reset done! / রিসেট হয়েছে! / மீட்டமைக்கப்பட்டது! / रीसेट झाले!"

    def get_booking_status(self, conversation_id: str = "default") -> Dict:
        booking = self.booking_state.get(conversation_id, {})
        return {
            "active": booking.get("active", False),
            "step":   booking.get("step", ""),
            "data":   booking.get("data", {}),
        }


# ── Global instance (used by api_server.py) ───────────────────────────────────
chatbot = FDAdvisorChatbot()


# ── Main entry point (called by api_server.py) ────────────────────────────────
def process_user_prompt(
    prompt: str,
    conversation_history=None,   # kept for API compatibility
    conversation_id: str = "default"
) -> Dict:
    """
    Main entry point called by api_server.py.
    Returns a dict with response + metadata.
    """
    if not prompt or not prompt.strip():
        return {
            "response":          "🙏 Namaste! FD ke baare mein ya koi bhi financial sawaal poochiye — main Hindi, Bengali, Tamil, Marathi aur English mein madad kar sakta hoon!",
            "issues":            ["Empty prompt"],
            "conversation_id":   conversation_id,
            "topics":            [],
            "detected_language": "english",
            "booking_active":    False,
            "booking_step":      "",
            "inline_calc":       None,
        }

    result = chatbot.process_query(prompt, conversation_id)
    return {
        "response":          result.get("response", "Kuch gadbad ho gayi. Dobara try karein."),
        "issues":            [] if result.get("success") else [result.get("error", "Unknown error")],
        "conversation_id":   result.get("conversation_id", conversation_id),
        "topics":            result.get("topics_detected", []),
        "detected_language": result.get("detected_language", "english"),
        "booking_active":    result.get("booking_active", False),
        "booking_step":      result.get("booking_step", ""),
        "inline_calc":       result.get("inline_calc"),
    }


# ── Standalone CLI test ───────────────────────────────────────────────────────
if __name__ == "__main__":
    import textwrap

    conv_id = "fd_session_1"
    print("=" * 70)
    print("🏦  FD Dost — Vernacular FD Advisor")
    print("    Hindi · Bengali · Tamil · Marathi · Gujarati · English")
    print("=" * 70)
    print("Example prompts to try:")
    examples = [
        "Suryoday Small Finance Bank 8.50% p.a. 12M tenor matlab kya hai?",
        "मुझे FD खोलनी है, ₹50,000 लगाना चाहता हूं",
        "சிறந்த FD விகிதம் எது?",
        "আমি 2 লাখ টাকা FD করতে চাই",
        "Unity bank mein 1 lakh 1 saal ke liye lagaun toh kitna milega?",
        "Is my money safe in small finance banks?",
        "Yaar main bohot financially stressed hoon, kya karun?",
        "SBI vs Unity Small Finance Bank — which is better?",
        "Main apni FD tod dena chahta hoon — penalty kitni hogi?",
        "Senior citizen hoon, kaunsa FD best rahega?",
    ]
    for i, ex in enumerate(examples, 1):
        print(f"  {i}. {ex}")
    print("\nType 'reset' to clear | 'status' to see booking | 'quit' to exit\n")

    while True:
        try:
            user_input = input("💬 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n🙏 Dhanyavaad! धन्यवाद! நன்றி! ধন্যবাদ!")
            break

        if not user_input:
            continue
        if user_input.lower() in ["quit", "exit", "bye", "alvida"]:
            print("\n🙏 Dhanyavaad! धन्यवाद! நன்றி! ধন্যবাদ!")
            break
        if user_input.lower() == "reset":
            print(chatbot.reset_conversation(conv_id))
            continue
        if user_input.lower() == "status":
            status = chatbot.get_booking_status(conv_id)
            print(f"📋 Booking Status: {status}")
            continue

        result = process_user_prompt(user_input, conversation_id=conv_id)

        # Pretty print response
        print(f"\n🏦 FD Dost:", end=" ")
        print(textwrap.fill(result["response"], width=70, subsequent_indent="           "))
        print(f"\n   🌐 Language: {result['detected_language']}"
              f" | 📌 Topics: {', '.join(result['topics']) if result['topics'] else 'general'}")
        if result.get("booking_active"):
            print(f"   📋 Booking step: {result['booking_step']}")
        if result.get("inline_calc"):
            c = result["inline_calc"]
            print(f"   🧮 Calc: Principal Rs.{c['principal']:,.0f} → "
                  f"Maturity Rs.{c['maturity']:,.0f} "
                  f"(Interest: Rs.{c['interest']:,.0f}"
                  + (f", TDS: Rs.{c['tds']:,.0f}" if c['tds'] > 0 else "")
                  + ")")
        print()


