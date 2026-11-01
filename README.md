# IntelliConnect — backend

Flask REST API implementing the 6 AI/ML features for **IntelliConnect: An
AI/ML-Powered Conversational Support System for Telecom Customer Service**.

Tested end-to-end on the ML/data logic before handing off (intent
classifier, escalation model, recommender, and bill anomaly explainer were
all run and verified to produce sensible output). `flask_cors`,
`flask_sqlalchemy`, `langdetect`, `deep_translator`, `speech_recognition`
and `pydub` need to be installed via `pip` on your machine before the full
server starts — see below.

---

## 1. Setup (VS Code)

```bash
# from inside the intelliconnect-backend folder
python -m venv venv

# activate it
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
```

**ffmpeg** (needed only for the voice feature, to convert uploaded audio to
WAV before speech recognition):
- macOS: `brew install ffmpeg`
- Windows: download from ffmpeg.org and add it to PATH
- Linux: `sudo apt install ffmpeg`

If you skip ffmpeg, everything else still works — only `/api/voice/transcribe`
will return a friendly error instead of a transcript.

### Run it

```bash
python app.py
```

Server starts at `http://127.0.0.1:5000`. Visiting that URL in a browser
shows a JSON list of all endpoints (so you know it's alive, no more blank
pages).

### Load demo data (optional but recommended)

```bash
python seed_data.py
```

Creates two demo accounts with bill/usage history so you can test the
billing and recommendation endpoints immediately:
- `ananya@example.com` / `password123` — has a billing anomaly in her latest bill
- `karthik@example.com` / `password123` — a newer, lighter-usage customer

---

## 2. What each feature uses, and why

| # | Feature | Approach | Why this approach |
|---|---------|----------|--------------------|
| 1 | Proactive network issue detection | Rolling count of independent outage reports per pincode within a time window (`ml/network_monitor.py`) | Transparent and immediately trustworthy for a support system — an area-level threshold rule is standard practice before investing in a full anomaly-detection model over historical report-rate baselines |
| 2 | Predictive churn/escalation | **Logistic Regression** over 5 engineered features (`ml/escalation.py`) | Linear model chosen *specifically* so its coefficients double as feature attributions — this is what makes feature 6 (explainable escalation) honest rather than a black box. A Random Forest would likely score similarly but is harder to explain to a non-technical evaluator |
| 3 | Bill anomaly explainer | Z-score of current bill vs. the customer's own trailing average, plus rule-based root-cause attribution across charge components (`ml/bill_anomaly.py`) | "Why was I charged this" needs a reasoning trail a customer can verify, not a probability — statistics + rules are the right tool here, not a classifier |
| 4 | Multilingual + code-mixed support | Unicode-range + romanized-keyword heuristics for code-mix detection, `langdetect` as fallback, `deep-translator` (Google Translate) for actual translation (`services/language.py`) | Off-the-shelf language detectors handle "Tenglish" (Telugu written in Latin script mixed with English) badly — a lightweight custom layer catches that case before falling back to a general detector |
| 5 | Voice + visual troubleshooting | Voice: Google Web Speech API via `SpeechRecognition`. Visual: dominant-hue extraction from an uploaded device photo mapped to standard router-light color conventions (`services/voice.py`, `services/visual.py`) | Both need to work end-to-end for a demo without training custom models from scratch; the visual diagnosis function is written so a CNN classifier can be dropped in later without changing the API contract |
| 6 | Personalized recommendation | **k-Nearest Neighbours** over a synthetic usage/plan-choice profile set, combined with a rule-based "are you near your data limit" check (`ml/recommender.py`) | KNN gives a genuine "customers like you chose this" collaborative-filtering flavor even with a small dataset, and needs no training step, which keeps it fast and simple to reason about |
| — | *Bonus:* agent handoff summary | Extractive summary built from the conversation + the escalation model's own top feature contributions (`ml/handoff_summary.py`) | Explainability shouldn't stop at the customer — when a human agent takes over, they get a 5-line brief instead of re-reading the whole chat. Fires automatically whenever risk is "high" |

### About the datasets

- **Intent classifier** (`data/intents_dataset.py`): ~85 hand-written labeled
  examples across 6 intents (billing, network, plan_change, sim, cancel,
  general), including Telugu-English code-mixed phrasing. This is a
  starter dataset for a prototype — accuracy will improve a lot with more
  real examples. To add more, just append `("your example text", "intent_key")`
  tuples to the list; the model retrains automatically at server startup.
- **Escalation model** (`ml/escalation.py`): trained on 400 *synthetically
  generated* rows (`_generate_synthetic_dataset()`), built from a known
  rule (low sentiment + repeat contact + complaint history + low tenure →
  higher escalation probability) plus random noise, so the model has to
  actually learn the pattern rather than memorize it. This stands in for
  real historical support-ticket outcomes, which you don't have yet as a
  student project — swap in a real labeled dataset (ticket → did it
  escalate, yes/no) later without changing any code outside this function.
- **Recommender** (`ml/recommender.py`): 150 synthetic customer profiles
  (usage level × price sensitivity → plan chosen), used only to give the
  KNN something to vote over. Replace with real anonymized usage/plan
  history when available.

Both synthetic datasets are clearly marked as such in code comments — this
is normal, expected practice for an academic ML prototype where historical
production data doesn't exist yet.

---

## 3. API endpoints

### Auth
```
POST /api/auth/signup   { name, email, password, phone, plan?, pincode? }
POST /api/auth/login    { email, password }
```

### Chat (the core pipeline — runs all 6 features together)
```
POST /api/chat
{ "user_id": 1, "thread_id": "optional-existing-thread", "message": "my bill is too high this month" }
```
Returns: detected language, translated text, intent + confidence +
distribution, escalation risk score + level + explanation, a proactive
network alert (if your area has recent reports), a bill anomaly
explanation (if intent is billing), a plan recommendation (if intent is
plan_change), and an agent handoff summary (if risk is high).

### Network
```
POST /api/network/report        { pincode, issue_type? }
GET  /api/network/status/<pincode>
```

### Billing
```
POST /api/bill/explain          { user_id }
GET  /api/bills/<user_id>
```

### Voice & visual (multipart/form-data)
```
POST /api/voice/transcribe      form field: audio  (wav/mp3/m4a/webm)
POST /api/visual/diagnose       form field: image  (jpg/png)
```

### Recommendation
```
GET /api/recommend/<user_id>
```

---

## 4. Connecting the frontend

The frontend built earlier (`intelliconnect` folder, login + chat UI) uses
`localStorage` for everything, so it runs standalone with no backend. To
wire it up to this API instead:

- In `js/auth.js`, replace the `localStorage`-based signup/login with
  `fetch("http://127.0.0.1:5000/api/auth/signup", { method: "POST", ... })`
  and store the returned `user.id` (instead of just the email) as the
  session.
- In `js/dashboard.js`, replace `detectIntent()` / `scoreEscalation()` /
  `botReplyFor()` with a single call to `POST /api/chat` and render the
  fields it returns directly into the insight panel.

Ask me if you'd like this wiring done for you — it's a small, mechanical
change once the backend is running.
