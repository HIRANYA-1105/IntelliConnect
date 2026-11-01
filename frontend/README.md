# IntelliConnect — frontend

Frontend-only demo for **IntelliConnect: An AI/ML-Powered Conversational Support System for Telecom Customer Service**. No backend or build step — plain HTML/CSS/JS, so it runs directly in VS Code.

## Run it in VS Code

1. Open the `intelliconnect` folder in VS Code (`File → Open Folder…`).
2. Install the **Live Server** extension (by Ritwick Dey) if you don't have it — search it in the Extensions panel.
3. Right-click `index.html` → **Open with Live Server**.
4. The app opens in your browser at something like `http://127.0.0.1:5500`.

(No `npm install` needed — there's nothing to build.)

## What's inside

- `index.html` — login / signup screen
- `dashboard.html` — the chat + AI-insight screen shown after login
- `css/style.css` — all styling (one shared stylesheet, design tokens at the top)
- `js/auth.js` — signup/login logic (stores accounts in the browser's `localStorage` — this is a frontend demo, not a real user database)
- `js/dashboard.js` — chat simulation: keyword-based intent detection and an escalation-risk score, standing in for the real NLU/predictive models

## Where your ML models plug in

Right now `detectIntent()` and `scoreEscalation()` in `js/dashboard.js` use simple keyword rules so the UI is fully demoable without a backend. When your actual model is ready:

- Replace `detectIntent(text)` with a call to your intent-classification API (should return an intent label + confidence).
- Replace `scoreEscalation(text, turnCount)` with a call to your escalation-prediction model.
- Replace the `localStorage`-based auth in `js/auth.js` with real API calls to your backend once one exists.

## Design notes

- Palette: deep signal-navy (`#131B34`) with a teal-cyan "signal" accent (`#2DD8C7`) and a coral accent (`#FF6B4A`) reserved for escalation/risk states.
- Typography: Sora for headings, Inter for body text (loaded from Google Fonts).
- Logo: a chat bubble merged with a signal arc — conversational AI + telecom connectivity in one mark.
- The insight panel on the dashboard (intent, confidence, escalation-risk meter) is the visual centerpiece — it's what makes this different from a generic chat UI and ties directly back to the project's problem statement.
