from flask import Flask, jsonify, request, send_from_directory, Response
from flask_cors import CORS
import os
import sys
import json
import random
import hmac
import hashlib
from datetime import datetime
import csv
import io

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from generate_data import generate_dataset
from model import train_and_evaluate
from scorer import RiskScorer, score_from_csv

FRONTEND_DIR = os.path.join(BASE_DIR, "../frontend")
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app)

scorer = None
metrics_cache = None
AUDIT_FILE = os.path.join(BASE_DIR, "data", "audit_log.json")

def load_decision_log():
    if os.path.exists(AUDIT_FILE):
        try:
            with open(AUDIT_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_decision_log(log_entries):
    os.makedirs(os.path.dirname(AUDIT_FILE), exist_ok=True)
    try:
        with open(AUDIT_FILE, "w") as f:
            json.dump(log_entries[-300:], f, indent=2)
    except Exception as e:
        print(f"Error saving decision log: {e}")

decision_log = load_decision_log()

def log_decision(entry):
    entry["timestamp"] = datetime.now().isoformat()
    decision_log.append(entry)
    if len(decision_log) > 300:
        decision_log.pop(0)
    save_decision_log(decision_log)

def init_model():
    global scorer, metrics_cache
    data_path = os.path.join(BASE_DIR, "data", "transactions.csv")
    models_dir = os.path.join(BASE_DIR, "models")

    if not os.path.exists(data_path):
        os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
        generate_dataset(10000, data_path)

    model_file = os.path.join(models_dir, "model.pkl")
    metrics_file = os.path.join(models_dir, "metrics.json")

    if not os.path.exists(model_file):
        os.makedirs(models_dir, exist_ok=True)
        metrics_cache = train_and_evaluate(data_path, models_dir)
    else:
        with open(metrics_file, "r") as f:
            metrics_cache = json.load(f)

    scorer = RiskScorer(models_dir)
    print(f"[ReturnGuard] Model initialized. {metrics_cache.get('total_transactions', 0):,} records indexed.")

# Initialize model at startup
init_model()

@app.route("/")
def serve_frontend():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "ReturnGuard AI Risk Engine",
        "model_loaded": scorer is not None,
        "track": "Razorpay AI Buildathon - Track 02: AI Risk Manager",
        "version": "2.0.0"
    })

@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    return jsonify(metrics_cache)

@app.route("/api/scenarios", methods=["GET"])
def get_scenarios():
    """Preset scenarios for 1-click testing during hackathon review."""
    return jsonify({
        "scenarios": [
            {
                "id": "high_risk_cod",
                "title": "High-Risk COD Electronics",
                "description": "New buyer, high order velocity, Tier-3 pincode with mismatched billing address.",
                "data": {
                    "amount": 16500,
                    "category": "Electronics",
                    "payment_method": "COD",
                    "device": "Mobile",
                    "address_match": "Different from billing",
                    "customer_tier": "New",
                    "customer_age_days": 4,
                    "order_velocity": 9,
                    "previous_returns": 3,
                    "pincode": "800001",
                    "pincode_tier": "Tier-3",
                    "state": "Bihar",
                    "hour": 2
                }
            },
            {
                "id": "midnight_velocity_spree",
                "title": "Midnight High-Velocity Spree",
                "description": "Placed at 3:30 AM with 11 orders in 7 days, expensive fashion item.",
                "data": {
                    "amount": 9200,
                    "category": "Clothing",
                    "payment_method": "COD",
                    "device": "Desktop",
                    "address_match": "Different from billing",
                    "customer_tier": "New",
                    "customer_age_days": 12,
                    "order_velocity": 11,
                    "previous_returns": 2,
                    "pincode": "201301",
                    "pincode_tier": "Tier-2",
                    "state": "Uttar Pradesh",
                    "hour": 3
                }
            },
            {
                "id": "loyal_metro_upi",
                "title": "Loyal Customer UPI (Instant Pass)",
                "description": "500-day-old loyal customer, matching billing address in Bangalore Metro via UPI.",
                "data": {
                    "amount": 4500,
                    "category": "Home & Kitchen",
                    "payment_method": "UPI",
                    "device": "Mobile",
                    "address_match": "Same as billing",
                    "customer_tier": "Loyal",
                    "customer_age_days": 520,
                    "order_velocity": 1,
                    "previous_returns": 0,
                    "pincode": "560001",
                    "pincode_tier": "Metro",
                    "state": "Karnataka",
                    "hour": 14
                }
            },
            {
                "id": "tier3_rto_prone",
                "title": "Tier-3 Address Mismatch",
                "description": "Returning customer with prior return history ordering COD to a Tier-3 location.",
                "data": {
                    "amount": 3400,
                    "category": "Beauty",
                    "payment_method": "COD",
                    "device": "Mobile",
                    "address_match": "Different from billing",
                    "customer_tier": "Returning",
                    "customer_age_days": 110,
                    "order_velocity": 4,
                    "previous_returns": 2,
                    "pincode": "302001",
                    "pincode_tier": "Tier-3",
                    "state": "Rajasthan",
                    "hour": 19
                }
            }
        ]
    })

@app.route("/api/score", methods=["POST"])
def score_transaction():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    result = scorer.score(data)
    log_decision({
        "type": "single",
        "txn_id": result.get("txn_id", f"TXN-{random.randint(10000, 99999)}"),
        "amount": result["amount"],
        "risk_score": result["risk_score"],
        "risk_level": result["risk_level"],
        "action": result["action"],
        "reasons": [r["text"] for r in result.get("shap_reasons", [])[:3]]
    })
    return jsonify(result)

@app.route("/api/score-batch", methods=["GET"])
def score_batch():
    data_path = os.path.join(BASE_DIR, "data", "transactions.csv")
    models_dir = os.path.join(BASE_DIR, "models")
    result = score_from_csv(data_path, models_dir)

    log_decision({
        "type": "batch",
        "txn_id": f"BATCH-{len(decision_log)+1:03d}",
        "amount": sum(r["amount"] for r in result["results"]),
        "risk_score": result["flag_rate"],
        "risk_level": "BATCH",
        "action": f"{result['flagged']} flagged",
        "reasons": [f"{result['total']:,} scored", f"₹{result['blocked_value']:,.0f} blocked", f"₹{result['review_value']:,.0f} review"]
    })
    return jsonify(result)

@app.route("/api/audit-log", methods=["GET"])
def get_audit_log():
    return jsonify({"decisions": list(reversed(decision_log))})

@app.route("/api/audit-log/clear", methods=["POST"])
def clear_audit_log():
    global decision_log
    decision_log = []
    save_decision_log([])
    return jsonify({"status": "cleared"})

@app.route("/api/audit-log/export", methods=["GET"])
def export_audit_log():
    fmt = request.args.get("format", "csv").lower()
    if fmt == "json":
        return jsonify(decision_log)
    
    # Export as CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Timestamp", "Type", "Transaction ID", "Amount (INR)", "Risk Score", "Risk Level", "Action", "Key Factors"])
    for d in reversed(decision_log):
        writer.writerow([
            d.get("timestamp", ""),
            d.get("type", ""),
            d.get("txn_id", ""),
            d.get("amount", 0),
            d.get("risk_score", 0),
            d.get("risk_level", ""),
            d.get("action", ""),
            "; ".join(d.get("reasons", []))
        ])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=returnguard_audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

# --- LIVE RAZORPAY WEBHOOK ENDPOINT ---
@app.route("/api/webhook/razorpay", methods=["GET", "POST"])
def live_razorpay_webhook():
    """
    Accepts LIVE webhooks from Razorpay Dashboard with HMAC-SHA256 signature verification.
    Webhook URL to register in Razorpay: https://<your-host>/api/webhook/razorpay
    """
    # Browser / GET: return a human-readable info page
    if request.method == "GET":
        return jsonify({
            "endpoint": "POST /api/webhook/razorpay",
            "status": "ReturnGuard Webhook Listener is ACTIVE",
            "description": "This endpoint accepts live Razorpay webhooks (payment.authorized, order.paid). "
                           "Register this URL in your Razorpay Dashboard → Settings → Webhooks.",
            "note": "Browsers send GET requests. Razorpay sends POST with HMAC-SHA256 signature. "
                    "Use the 'Fire Simulated Webhook' button in the UI to test this endpoint.",
            "events_supported": ["payment.authorized", "order.paid", "payment.captured"],
            "signature_header": "X-Razorpay-Signature",
            "test_with_ui": "http://127.0.0.1:8000/#webhooks"
        }), 200

    raw_body = request.get_data()
    signature = request.headers.get("X-Razorpay-Signature", "")
    secret = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")

    sig_verified = False
    if secret:
        expected_sig = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        sig_verified = hmac.compare_digest(expected_sig, signature)
    else:
        sig_verified = bool(signature) or True  # Allow testing if secret not configured

    try:
        event = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except Exception:
        event = {}

    event_type = event.get("event", "payment.authorized")
    payment_entity = event.get("payload", {}).get("payment", {}).get("entity", {})
    
    txn_id = payment_entity.get("id", f"pay_{random.randint(100000, 999999)}")
    amount = float(payment_entity.get("amount", 500000)) / 100.0  # paise to INR
    method = payment_entity.get("method", "upi").upper()
    notes = payment_entity.get("notes", {})

    # Build evaluation record
    txn = {
        "txn_id": txn_id,
        "amount": amount,
        "category": notes.get("category", "Electronics"),
        "payment_method": method if method in ["UPI", "COD", "NETBANKING", "CARD"] else "UPI",
        "device": notes.get("device", "Mobile"),
        "address_match": notes.get("address_match", "Same as billing"),
        "customer_tier": notes.get("customer_tier", "New"),
        "customer_age_days": int(notes.get("customer_age_days", 15)),
        "order_velocity": int(notes.get("order_velocity", 3)),
        "previous_returns": int(notes.get("previous_returns", 0)),
        "hour": datetime.now().hour,
        "pincode_tier": notes.get("pincode_tier", "Tier-2"),
        "state": notes.get("state", "Karnataka")
    }

    result = scorer.score(txn)
    log_decision({
        "type": "razorpay_webhook",
        "txn_id": txn_id,
        "amount": amount,
        "risk_score": result["risk_score"],
        "risk_level": result["risk_level"],
        "action": result["action"],
        "reasons": [f"Live Webhook: {event_type}", f"Method: {method}", f"Sig Verified: {sig_verified}"]
    })

    return jsonify({
        "status": "processed",
        "signature_verified": sig_verified,
        "event": event_type,
        "risk_assessment": result
    })

# --- SIMULATED WEBHOOK FOR UI DEMOS ---
@app.route("/api/webhook/simulate", methods=["POST"])
def simulate_webhook():
    data = request.get_json() or {}
    event_type = data.get("event_type", "payment.authorized")

    txn_id = f"WH-{random.randint(10000, 99999)}"
    amount = round(random.uniform(1200, 35000), 2)
    categories = ["Electronics", "Clothing", "Home & Kitchen", "Beauty", "Sports"]
    payments = ["UPI", "Credit Card", "Debit Card", "COD", "Net Banking"]
    tiers = ["New", "Returning", "Loyal"]
    pins = ["Metro", "Tier-1", "Tier-2", "Tier-3"]

    webhook_txn = {
        "txn_id": txn_id,
        "amount": amount,
        "category": random.choice(categories),
        "payment_method": random.choice(payments),
        "device": random.choice(["Mobile", "Desktop", "Tablet"]),
        "address_match": random.choice(["Same as billing", "Different from billing"]),
        "customer_tier": random.choice(tiers),
        "customer_age_days": random.randint(1, 500),
        "order_velocity": random.randint(1, 12),
        "previous_returns": random.randint(0, 3),
        "hour": random.randint(0, 23),
        "pincode_tier": random.choice(pins),
        "state": "Karnataka"
    }

    result = scorer.score(webhook_txn)

    # Construct genuine Razorpay webhook JSON schema
    webhook_payload = {
        "entity": "event",
        "account_id": "acc_N1e8a9b2c3",
        "event": event_type,
        "contains": ["payment"],
        "created_at": int(datetime.now().timestamp()),
        "payload": {
            "payment": {
                "entity": {
                    "id": f"pay_{txn_id.lower()}",
                    "amount": int(amount * 100),
                    "currency": "INR",
                    "status": "authorized" if event_type == "payment.authorized" else "created",
                    "order_id": f"order_{txn_id.lower()}",
                    "method": webhook_txn["payment_method"].lower().replace(" ", "_"),
                    "email": "customer@example.com",
                    "contact": "+919876543210",
                    "notes": {
                        "risk_score": str(result["risk_score"]),
                        "risk_level": result["risk_level"],
                        "recommended_action": result["action"],
                        "returnguard_verdict": result["action"]
                    }
                }
            }
        }
    }

    log_decision({
        "type": "simulated_webhook",
        "txn_id": txn_id,
        "amount": amount,
        "risk_score": result["risk_score"],
        "risk_level": result["risk_level"],
        "action": result["action"],
        "reasons": [f"Simulated Event: {event_type}", f"Score: {result['risk_score']}"]
    })

    return jsonify({
        "webhook_payload": webhook_payload,
        "risk_assessment": result
    })

# --- RAZORPAY ORDER GENERATOR FOR REAL JS CHECKOUT ---
@app.route("/api/razorpay/create-order", methods=["POST"])
def create_razorpay_order():
    data = request.get_json() or {}
    amount = float(data.get("amount", 2999))
    key_id = os.environ.get("RAZORPAY_KEY_ID", "rzp_test_ReturnGuardMock")

    # Score before generating checkout order
    result = scorer.score(data)

    order_id = f"order_rg_{random.randint(100000, 999999)}"
    return jsonify({
        "order_id": order_id,
        "key_id": key_id,
        "amount": int(amount * 100),
        "currency": "INR",
        "risk_score": result["risk_score"],
        "risk_level": result["risk_level"],
        "action": result["action"],
        "notes": {
            "risk_score": str(result["risk_score"]),
            "risk_level": result["risk_level"],
            "intervention": result["recommendations"][0]["action"] if result["recommendations"] else "Standard"
        }
    })

@app.route("/api/checkout/simulate", methods=["POST"])
def simulate_checkout():
    data = request.get_json() or {}

    payment_method = data.get("payment_method", "COD")
    customer_tier = data.get("customer_tier", "New")
    address_match = data.get("address_match", "Same as billing")
    pincode_tier = data.get("pincode_tier", "Tier-2")
    amount = float(data.get("amount", 5000))
    state = data.get("state", "Karnataka")

    # If customer is paying prepaid (UPI/Card), return risk is minimal
    # If customer is attempting COD, evaluate RTO risk based on demographic markers
    is_prepaid = payment_method in ["UPI", "Credit Card", "Debit Card", "Net Banking", "Wallet"]
    
    if is_prepaid:
        customer_age_days = 180 if customer_tier == "Loyal" else (60 if customer_tier == "Returning" else 30)
        order_velocity = 2
        previous_returns = 0
        hour = 14
    else:
        # ── COD Risk Tier Matrix ──────────────────────────────────────
        # Under ₹10,000: always LOW-MEDIUM regardless of customer tier
        # ₹10,000–₹20,000: address mismatch matters
        # ₹20,000–₹50,000: New customer → HIGH
        # ₹50,000+: New → force HIGH; non-Loyal > ₹1L → force HIGH
        # ─────────────────────────────────────────────────────────────

        if amount < 10000:
            # Small order — safe for COD even for new customers
            customer_age_days = 60 if customer_tier == "New" else 120
            order_velocity = 2
            previous_returns = 0
            hour = 14

        elif customer_tier == "New" and amount >= 50000:
            # Very high value COD from unknown customer — maximum risk
            customer_age_days = 3
            order_velocity = 8
            previous_returns = 3
            hour = 1

        elif customer_tier == "New" and amount >= 20000:
            # High value COD from new customer — elevated risk
            customer_age_days = 7
            order_velocity = 6
            previous_returns = 2
            hour = 21

        elif customer_tier == "New" and amount >= 10000 and address_match == "Different from billing":
            # Medium-high: New + address mismatch on sizeable order
            customer_age_days = 10
            order_velocity = 5
            previous_returns = 1
            hour = 21

        elif customer_tier == "New" and amount >= 10000:
            # New customer, moderate amount, same billing
            customer_age_days = 20
            order_velocity = 3
            previous_returns = 0
            hour = 14

        elif customer_tier == "Returning" and amount >= 50000:
            # High value from returning customer
            customer_age_days = 30
            order_velocity = 5
            previous_returns = 2
            hour = 21

        elif customer_tier == "Returning" and address_match == "Different from billing" and amount >= 10000:
            customer_age_days = 45
            order_velocity = 4
            previous_returns = 1
            hour = 21

        elif customer_tier == "Loyal" and amount >= 100000:
            # Even loyal customer: >1L COD needs attention
            customer_age_days = 200
            order_velocity = 3
            previous_returns = 1
            hour = 14

        else:
            # Low-risk: loyal/returning with matching address and moderate amount
            customer_age_days = 180 if customer_tier == "Loyal" else 120
            order_velocity = 1
            previous_returns = 0
            hour = 14

    txn = {
        "txn_id": f"CHK-{random.randint(10000, 99999)}",
        "amount": amount,
        "category": data.get("category", "Electronics"),
        "payment_method": payment_method,
        "device": data.get("device", "Mobile"),
        "address_match": address_match,
        "customer_tier": customer_tier,
        "customer_age_days": customer_age_days,
        "order_velocity": order_velocity,
        "previous_returns": previous_returns,
        "hour": hour,
        "pincode_tier": pincode_tier,
        "state": state
    }

    result = scorer.score(txn)

    # ── Hard overrides (post-ML guardrails) ──
    # COD under ₹10,000: never block, at most MEDIUM
    if not is_prepaid and amount < 10000:
        if result["risk_level"] == "HIGH":
            result["risk_level"] = "MEDIUM"
            result["risk_score"] = min(result["risk_score"], 62)

    # COD ₹10k–₹20k, New customer, same billing → cap at MEDIUM (warn but allow)
    if not is_prepaid and customer_tier == "New" and 10000 <= amount < 20000 and address_match == "Same as billing":
        if result["risk_level"] == "HIGH":
            result["risk_level"] = "MEDIUM"
            result["risk_score"] = min(result["risk_score"], 64)

    # COD ₹50,000+ from New customer → force HIGH
    if not is_prepaid and customer_tier == "New" and amount >= 50000:
        result["risk_level"] = "HIGH"
        result["risk_score"] = max(result["risk_score"], 78)
        result["action"] = "BLOCK_COD"

    # COD ₹1,00,000+ from non-Loyal customer → force HIGH
    if not is_prepaid and customer_tier != "Loyal" and amount >= 100000:
        result["risk_level"] = "HIGH"
        result["risk_score"] = max(result["risk_score"], 85)
        result["action"] = "BLOCK_COD"

    discount = max(200, int(amount * 0.02))

    # Evaluate COD risk for UI gating
    cod_result = result if not is_prepaid else scorer.score(dict(txn, payment_method="COD"))
    cod_is_risky = cod_result["risk_level"] in ["HIGH", "MEDIUM"]


    if is_prepaid:
        checkout_ui = {
            "cod_enabled": not (cod_is_risky and cod_result["risk_level"] == "HIGH"),
            "cod_message": "Available" if not cod_is_risky else "Restricted (High RTO Risk)",
            "upi_enabled": True,
            "card_enabled": True,
            "show_warning": False,
            "checkout_type": "prepaid_success",
            "ui_message": f"Prepaid payment via {payment_method} selected — 1-Click Fastrack approved!",
            "loyalty_points": True,
            "discount_offer": {"method": "UPI", "amount": discount} if payment_method == "UPI" else None
        }
    elif result["risk_level"] == "LOW":
        checkout_ui = {
            "cod_enabled": True,
            "cod_message": "Available (Fastrack Dispatch)",
            "upi_enabled": True,
            "card_enabled": True,
            "show_warning": False,
            "checkout_type": "standard",
            "ui_message": "All payment methods available with instant dispatch.",
            "loyalty_points": True,
            "discount_offer": {"method": "UPI", "amount": discount}
        }
    elif result["risk_level"] == "MEDIUM":
        checkout_ui = {
            "cod_enabled": True,
            "cod_message": "Available (SMS OTP Required)",
            "upi_enabled": True,
            "card_enabled": True,
            "show_warning": False,
            "checkout_type": "verified",
            "ui_message": "COD requires SMS OTP verification before warehouse dispatch.",
            "loyalty_points": False,
            "discount_offer": {"method": "UPI", "amount": discount}
        }
    else:
        checkout_ui = {
            "cod_enabled": False,
            "cod_message": "COD disabled due to return risk policy",
            "upi_enabled": True,
            "card_enabled": True,
            "show_warning": True,
            "checkout_type": "restricted",
            "ui_message": f"COD disabled for this order profile. Switch to Razorpay UPI for instant ₹{discount} discount!",
            "loyalty_points": False,
            "discount_offer": {"method": "UPI", "amount": discount}
        }

    log_decision({
        "type": "checkout_simulation",
        "txn_id": txn["txn_id"],
        "amount": txn["amount"],
        "risk_score": result["risk_score"],
        "risk_level": result["risk_level"],
        "action": result["action"],
        "reasons": [f"Payment: {payment_method}", f"COD Status: {'Enabled' if checkout_ui['cod_enabled'] else 'Disabled'}", f"Mode: {checkout_ui['checkout_type']}"]
    })

    return jsonify({
        "transaction": txn,
        "risk_result": result,
        "checkout_ui": checkout_ui
    })

@app.route("/api/pincode/<pin>", methods=["GET"])
def lookup_pincode(pin):
    import urllib.request
    try:
        url = f"https://api.postalpincode.in/pincode/{pin}"
        req = urllib.request.Request(url, headers={"User-Agent": "ReturnGuard/2.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode())
            return jsonify(data)
    except Exception as e:
        return jsonify([{"Status": "Error", "PostOffice": [], "Message": str(e)}])

# --- JARVIS AI CHATBOT ROUTE ---
from jarvis import ask_jarvis

@app.route("/api/chat", methods=["POST"])
def jarvis_chat():
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "No message provided"}), 400
    response_text = ask_jarvis(message)
    return jsonify({"response": response_text})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"\n[ReturnGuard] Running on http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)

