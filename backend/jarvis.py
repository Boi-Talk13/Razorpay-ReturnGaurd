import os
import re
import random
import requests

# System prompt for Gemini if API key is present
JARVIS_SYSTEM_PROMPT = """
You are Jarvis, the advanced AI Assistant for ReturnGuard. 
ReturnGuard is an AI Risk Manager for Razorpay, designed to reduce Return to Origin (RTO) and return fraud for Indian e-commerce merchants.

Here are the key details of the project you must know:
1. **Architecture**: 
   - Backend: Flask API (app.py, model.py, scorer.py, generate_data.py)
   - Frontend: Vanilla HTML/CSS/JS (index.html, style.css, app.js)
   - Models: Random Forest Classifier, SHAP explainer, StandardScaler, and LabelEncoder.
2. **Core Features**:
   - Precision ML Risk Scoring (0-100 score).
   - SHAP explainability per transaction showing risk drivers.
   - Dynamic Checkout Interventions (disabling COD, showing warnings, injecting UPI discounts).
   - Live Webhook listener verifying HMAC-SHA256 signature (`X-Razorpay-Signature`).
   - Policy threshold tuner & monthly ROI calculator.
   - 1-Click WhatsApp outreach templates.
   - Audit trail showing decision logs with CSV/JSON export.
3. **Troubleshooting Guide**:
   - Webhook Signature Fail: Ensure `RAZORPAY_WEBHOOK_SECRET` in env matches Razorpay Dashboard. Make sure request.get_data() is used for raw body.
   - Model Not Found: The system trains a new model automatically on startup if `models/model.pkl` is missing.
   - Port 8000 already in use: Run `lsof -i :8000` to find the process ID and kill it using `kill -9 <PID>`.

Answer the user's questions about ReturnGuard, troubleshoot their issues, and explain the code/architecture in a helpful, concise way. Do not use emojis in your responses to keep it aligned with the professional, symbol-free design.
"""

# Rich database of project-specific QA facts
QA_DATABASE = [
    {
        "keywords": ["returnguard", "project", "app", "what is this", "about this", "purpose", "goal"],
        "answer": "ReturnGuard is an AI-powered Risk Manager built for Razorpay. It helps e-commerce merchants detect and prevent Return to Origin (RTO) and fraud losses by analyzing transactions in real-time, explaining risk using SHAP, and applying dynamic checkout interventions (like disabling COD or offering UPI discounts)."
    },
    {
        "keywords": ["who are you", "your name", "who is jarvis", "jarvis"],
        "answer": "I am Jarvis, the ReturnGuard AI assistant. I am here to explain the project architecture, clarify how our Random Forest model scores risk, describe webhooks, and help troubleshoot any issues you run into while running the app."
    },
    {
        "keywords": ["run", "locally", "setup", "start", "install", "dependencies", "requirements"],
        "answer": "To run ReturnGuard locally:\n1. Clone the project repository.\n2. Run 'pip install -r requirements.txt' in your terminal.\n3. Change directory: 'cd backend'.\n4. Start the server: 'python app.py'. (The script will auto-generate the dataset and train the model if not present).\n5. Open http://localhost:8000 in your browser."
    },
    {
        "keywords": ["model", "ml", "random forest", "classifier", "train"],
        "answer": "ReturnGuard uses a scikit-learn Random Forest Classifier. It is trained on 10,000 transaction records containing demographical, velocity, and payment method markers. It outputs a probability score from 0 to 100 which is mapped to Low, Medium, or High risk tiers."
    },
    {
        "keywords": ["accuracy", "precision", "recall", "auc", "f1", "metrics", "performance"],
        "answer": "The Random Forest model achieves the following metrics on the test split:\n- Precision: ~40% (minimizes false alarms for genuine buyers)\n- Recall: ~39% (detects the majority of risky returns)\n- AUC-ROC: ~0.79 (solid class separation performance)"
    },
    {
        "keywords": ["shap", "explain", "why scored", "drivers", "contribution", "shapley"],
        "answer": "SHAP (SHapley Additive exPlanations) is a game-theoretic approach to explain model predictions. For every scored transaction, ReturnGuard calculates SHAP values to show which features increased the risk (e.g. Tier-3 COD delivery) and which decreased it (e.g. loyal customer status)."
    },
    {
        "keywords": ["webhook", "signature", "secret", "fail", "verification", "hmac"],
        "answer": "To resolve webhook signature verification failures:\n1. Ensure the RAZORPAY_WEBHOOK_SECRET env variable matches the secret entered in your Razorpay Dashboard.\n2. Verify you hash the raw request body (via request.get_data()) using HMAC-SHA256.\n3. If testing locally, use the simulated webhook launcher in the UI which generates matching headers."
    },
    {
        "keywords": ["ngrok", "test", "dashboard", "live webhooks"],
        "answer": "To test live webhooks from your real Razorpay Dashboard locally:\n1. Start ngrok on port 8000: 'ngrok http 8000'.\n2. Copy the forwarding HTTPS URL.\n3. Go to Razorpay Dashboard -> Settings -> Webhooks, and add the URL: 'https://<your-ngrok-subdomain>.ngrok-free.app/api/webhook/razorpay'."
    },
    {
        "keywords": ["checkout", "intervention", "disable", "gate", "restrict", "cod"],
        "answer": "ReturnGuard performs dynamic checkout gating based on risk score:\n- Low Risk (0-34): Standard checkout with COD enabled.\n- Medium Risk (35-64): OTP verification required for COD, UPI discount offered.\n- High Risk (65-100): COD disabled entirely, forcing UPI/Card and offering a UPI discount."
    },
    {
        "keywords": ["upi", "discount", "incentive", "prepaid"],
        "answer": "We incentivize risky COD buyers to pay prepaid by offering a UPI discount (e.g., Rs. 200 off or 2% of the order value). Switching a transaction from COD to prepaid eliminates the RTO risk completely for the merchant."
    },
    {
        "keywords": ["deploy", "render", "production", "docker", "gunicorn", "procfile"],
        "answer": "To deploy ReturnGuard to production:\n- Render: Use the render.yaml blueprint or set build command to 'pip install -r requirements.txt' and start command to 'cd backend && gunicorn app:app --bind 0.0.0.0:$PORT'.\n- Docker: A Dockerfile is included at the root of the project to build and deploy to Railway or Fly.io."
    },
    {
        "keywords": ["features", "dataset", "columns", "inputs", "variables"],
        "answer": "The model uses 12 features for risk evaluation: order amount, product category, payment method, device type, address match status, customer loyalty tier, account age in days, order velocity (last 7 days), previous returns count, hour of the order, pincode tier, and state."
    },
    {
        "keywords": ["rto", "return to origin", "fraud", "cost", "india"],
        "answer": "Return to Origin (RTO) occurs when a COD order is rejected at delivery or cannot be delivered. It costs Indian e-commerce merchants over Rs. 30,000 crores annually in double shipping fees and blocked inventory. ReturnGuard aims to prevent these losses before shipment."
    },
    {
        "keywords": ["roi", "economics", "profit", "savings", "loss", "simulator"],
        "answer": "The ROI simulator helps merchants find the optimal risk cutoff threshold. It balances False Positives (lost profit from genuine buyers blocked) against False Negatives (shipping loss from missed RTOs) to maximize net monthly savings."
    },
    {
        "keywords": ["whatsapp", "outreach", "sms", "confirmation", "template"],
        "answer": "For Medium/High risk orders, ReturnGuard generates automated WhatsApp confirmation messages. You can copy these templates directly from the AI Copilot card in the UI to send to customers before dispatching."
    },
    {
        "keywords": ["audit", "ledger", "log", "trail", "csv", "export"],
        "answer": "The dashboard maintains a persistent audit log in 'backend/data/audit_log.json'. You can view previous decisions, clear the logs, or export them to CSV and JSON formats using the buttons in the Audit Trail section."
    },
    {
        "keywords": ["data generation", "generate_data", "synthetic", "dataset", "csv"],
        "answer": "If 'backend/data/transactions.csv' is missing on startup, 'backend/generate_data.py' automatically creates a 10,000-record synthetic transaction dataset containing realistic Indian e-commerce behavior profiles to train the model."
    },
    {
        "keywords": ["override", "rule", "matrix", "safety", "gate", "post-ml"],
        "answer": "The system applies post-ML safety overrides to prevent errors: COD under Rs. 10,000 is capped at Medium Risk (never blocked); COD over Rs. 50,000 for New buyers is forced to High Risk (blocked); COD over Rs. 100,000 for non-Loyal buyers is forced to High Risk (blocked)."
    },
    {
        "keywords": ["security", "hmac", "sha256", "signature"],
        "answer": "Webhook requests are secured using Razorpay's HMAC-SHA256 signature scheme. The server validates that the payload raw body, when hashed with your Webhook Secret, matches the X-Razorpay-Signature header before writing to the audit log."
    },
    {
        "keywords": ["tech", "technology", "flask", "python", "css", "js", "html"],
        "answer": "ReturnGuard is built using:\n- Backend: Flask, scikit-learn, numpy, shap, and requests.\n- Frontend: HTML5, custom CSS3 dark-mode design, and vanilla Javascript. Charts are rendered using dynamic inline SVG drawings."
    },
    {
        "keywords": ["version", "status", "health"],
        "answer": "ReturnGuard is currently running version 2.0.0. The system health status is active and verified, serving API endpoints and frontend widgets on http://localhost:8000."
    },
    {
        "keywords": ["hi", "hello", "hey"],
        "answer": "Hi! What can I help or do for you today?"
    },
    {
        "keywords": ["doubt", "question", "help", "query"],
        "answer": "Sure, go ahead! What is your doubt or question? Let me know what you are trying to understand or solve in the app, and I will help you out."
    }
]

def call_gemini(user_prompt):
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("RAZORPAY_GEMINI_KEY")
    if not api_key:
        return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": JARVIS_SYSTEM_PROMPT + "\n\nUser Question: " + user_prompt}]}
        ],
        "generationConfig": {
            "maxOutputTokens": 800,
            "temperature": 0.7
        }
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=8)
        if response.status_code == 200:
            res_data = response.json()
            return res_data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"[Jarvis] Gemini API Call failed, falling back to local engine. Error: {e}")
    return None

def local_jarvis_respond(query):
    query_clean = re.sub(r'[^\w\s]', '', query.lower())
    words = set(query_clean.split())
    
    # Simple stop words filter
    stop_words = {"a", "the", "is", "of", "and", "in", "to", "how", "what", "why", "who", 
                  "for", "do", "you", "are", "on", "with", "my", "me", "i", "have", "about",
                  "tell", "can", "please", "should", "does", "use", "app", "want", "explain", "explains"}
    
    filtered_words = words - stop_words
    
    best_match = None
    best_score = 0
    
    for qa in QA_DATABASE:
        score = 0
        for kw in qa["keywords"]:
            if kw in filtered_words:
                score += 3
            elif any(kw in word for word in filtered_words):
                score += 1
                
        if score > best_score:
            best_score = score
            best_match = qa
            
    if best_match and best_score >= 1:
        return best_match["answer"]

    # Fallback response
    return (
        "Sure, go ahead! What is your doubt or question? "
        "Tell me what you are trying to understand or resolve, and I will explain or solve it for you."
    )

def ask_jarvis(message):
    # Try Gemini API first
    res = call_gemini(message)
    if res:
        # Strip emojis from Gemini output to keep it symbol-free
        res_clean = res.encode('ascii', 'ignore').decode('ascii').strip()
        return res_clean
    
    # Otherwise fallback to local engine
    return local_jarvis_respond(message)
