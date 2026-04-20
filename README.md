# 🏦 FD Advisor AI - Multilingual Fixed Deposit Assistant
live link: https://fd-advisor-ai-chatbot-x7t8.vercel.app

[![Made with Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Built with LangGraph](https://img.shields.io/badge/Built%20with-LangGraph-1e3a5f.svg)](https://langchain.com/langgraph)
[![Powered by Groq](https://img.shields.io/badge/Powered%20by-Groq-ff6b6b.svg)](https://groq.com)
[![Deployed on Render](https://img.shields.io/badge/Deployed%20on-Render-46C3B9.svg)](https://render.com)
[![Deployed on Vercel](https://img.shields.io/badge/Deployed%20on-Vercel-000000.svg)](https://vercel.com)

> **A multilingual AI assistant that explains Fixed Deposit jargon in plain terms and guides users through booking an FD — Built for Blostem Hackathon 2026**

---

## 🌐 Live Demo

| Service | URL |
|---------|-----|
| **Frontend Chat Interface** | [https://fd-advisor-ai-chatbot-x7t8.vercel.app](https://fd-advisor-ai-chatbot-x7t8.vercel.app) |
| **Backend API** | [https://fd-advisor-ai-chatbot-1.onrender.com](https://fd-advisor-ai-chatbot-1.onrender.com) |
| **Health Check** | [https://fd-advisor-ai-chatbot-1.onrender.com/api/health](https://fd-advisor-ai-chatbot-1.onrender.com/api/health) |
| **GitHub Repository** | [https://github.com/Soumyo321/FD-Advisor-AI-Chatbot](https://github.com/Soumyo321/FD-Advisor-AI-Chatbot) |

---

## 🎯 The Problem

A user in **Gorakhpur** sees this offer:

> **Suryoday Small Finance Bank — 8.50% p.a. — 12M tenor**

And has **no idea** what to do. What does "p.a." mean? What is "tenor"? Is their money safe? How do they book it?

**FD Advisor AI solves this** — a warm, multilingual chatbot that speaks Hindi, English, Bengali, and Telugu, explains financial jargon simply, and guides users through booking an FD step-by-step.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🌐 **Multilingual** | Hindi, English, Bengali, Telugu — auto-detects and responds in user's language |
| 📖 **Jargon Simplification** | Explains "p.a.", "tenor", "maturity", "TDS", "DICGC" in plain terms |
| 📝 **FD Booking Flow** | 8-step guided process: Amount → Duration → Senior Citizen → Bank Selection → FD Type → Calculation → Documents → Confirmation |
| 🧮 **Smart Calculations** | Quarterly compounding, TDS deduction (10% if interest > ₹40,000/year) |
| 🔢 **Regional Number Parsing** | Understands "50 hazar", "1.5 lakh", "pachas hazaar", "2 crore" |
| 🛡️ **DICGC Safety** | Automatically adds ₹5 lakh government guarantee note for Small Finance Banks |
| 💬 **Handles Off-Topic** | Answers any question while gently relating to financial wellness |
| 😊 **Empathetic Design** | Handles angry, frustrated, or confused users with warmth |

---

## 🗣️ Try These Prompts

### Start Booking
| Prompt | What Happens |
|--------|--------------|
| `how can i book my fd` | AI starts booking flow |
| `मुझे FD खोलनी है` | Hindi - starts booking |
| `book fd` | Quick start |

### During Booking Flow
| AI Asks | You Type |
|---------|----------|
| How much to invest? | `50000` or `50 hazar` or `1 lakh` |
| For how long? | `1 year` or `12 months` or `2 saal` |
| Senior citizen? | `yes` / `no` / `haan` / `nahi` |
| Which bank? | `Suryoday` / `Unity` / `SBI` |
| FD type? | `cumulative` or `non-cumulative` |

### Complete Flow ExampleUser: how can i book my fd
AI: How much would you like to invest?
User: 50000
AI: For how many months?
User: 1 year
AI: Are you a senior citizen?
User: no
AI: Here are top banks... Which one?
User: Suryoday
AI: Cumulative or non-cumulative?
User: cumulative
AI: ✅ Maturity amount: ₹54,250 | Interest: ₹4,250 | TDS: ₹0

text

---

## 🗣️ Language Support Examples

| Language | Example Prompt |
|----------|----------------|
| **Hindi** | `भाई ये FD क्या होता है? 8.50% सालाना मतलब कितना पैसा मिलेगा?` |
| **Hinglish** | `Bhai 50 hazar lagane se 1 saal mein kitna banega?` |
| **Bengali** | `আমি ৫০ হাজার টাকা FD করতে চাই, কত টাকা পাবো?` |
| **Telugu** | `నేను 50,000 FD చేయాలనుకుంటున్నాను, ఎంత వడ్డీ వస్తుంది?` |
| **English** | `What is the difference between cumulative and non-cumulative FD?` |

---

## 🧠 Jargon Simplified

| Term | Plain Explanation |
|------|-------------------|
| **p.a.** | Per annum = per year = साल में कितना interest मिलेगा |
| **Tenor / Tenure** | कितने time के लिए FD रखना है |
| **Maturity** | FD खतम होने पर पैसा + interest वापस |
| **TDS** | Tax cut — अगर साल का interest ₹40,000 से ज़्यादा हो तो 10% कटेगा |
| **DICGC** | Government guarantee — ₹5 लाख तक सुरक्षित, bank बंद हुआ तो भी |
| **Cumulative FD** | सब पैसा end में मिलता है |
| **Non-Cumulative** | Interest monthly/quarterly मिलता रहता है |

---

## 🔢 Regional Number Parsing

| You Type | Understood As |
|----------|---------------|
| `50 hazar` | ₹50,000 |
| `1.5 lakh` | ₹1,50,000 |
| `2 crore` | ₹2,00,00,000 |
| `pachas hazaar` | ₹50,000 |
| `सवा लाख` | ₹1,25,000 |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python, FastAPI, LangGraph |
| **LLM** | Groq (Llama 3.3 70B) |
| **Frontend** | Next.js, TypeScript |
| **State Management** | LangGraph State Machine |
| **Deployment** | Render (Backend) + Vercel (Frontend) |

---

## 📁 Project Structure
FD-Advisor-AI-Chatbot/
├── backend/
│ ├── api_server.py # FastAPI server
│ ├── chatbot_groq_langgraph.py # LangGraph state machine + FD logic
│ ├── requirements.txt # Python dependencies
│ └── .gitignore
├── frontend/
│ └── my-app/
│ ├── app/
│ │ └── page.tsx # Chat interface
│ ├── package.json
│ └── next.config.js
└── README.md

text

---

## 🚀 How It Works

### Booking Flow State Machine
Step 1: Amount → User types "50000"
Step 2: Duration → User types "1 year"
Step 3: Senior → User types "no"
Step 4: Bank → AI shows top 3 banks, user selects
Step 5: FD Type → User chooses cumulative/non-cumulative
Step 6: Calculation → AI shows maturity + interest + TDS
Step 7: Documents → AI lists PAN, Aadhaar requirements
Step 8: Confirm → Booking complete

text

### Language Detection

The assistant automatically detects language from:
- **Devanagari script** → Hindi
- **Bengali script** → Bengali  
- **Tamil script** → Tamil
- **Hinglish keywords** → Hinglish
- **English** → Default

---

## 📋 Track Information

**Hackathon Track:** Track 01 - Multilingual Chat Interface

**Problem Statement:** A user in Gorakhpur sees "Suryoday Small Finance Bank — 8.50% p.a. — 12M tenor" and has no idea what to do. Build a multilingual chat interface that explains FD jargon in plain terms and guides users through booking.

---

## 👨‍💻 Author

**Soumyodip Bhattacharya (Soumyo321)**  
[GitHub](https://github.com/Soumyo321)

---

## 📄 License

MIT License - Free for anyone to use, modify, and distribute.

---

## 🙏 Acknowledgments

- **Blostem** for organizing the hackathon
- **Groq** for providing LLM API access
- **LangChain/LangGraph** for state management framework
- **Render** for free backend hosting
- **Vercel** for free frontend hosting

---

## ⭐ Support

If you find this project useful, please give it a star on GitHub!

---

## 📞 Contact

For questions or feedback, please open an issue on GitHub.

---

**Made with ❤️ for Blostem Hackathon 2026**
