import os
import pickle
import numpy as np

class RiskScorer:
    def __init__(self, model_dir="models"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if not os.path.isabs(model_dir):
            model_dir = os.path.join(base_dir, model_dir)

        with open(os.path.join(model_dir, "model.pkl"), "rb") as f:
            self.model = pickle.load(f)
        with open(os.path.join(model_dir, "scaler.pkl"), "rb") as f:
            self.scaler = pickle.load(f)
        with open(os.path.join(model_dir, "encoders.pkl"), "rb") as f:
            self.encoders = pickle.load(f)
        with open(os.path.join(model_dir, "explainer.pkl"), "rb") as f:
            self.explainer = pickle.load(f)
        self.feature_names = [
            "amount", "category", "payment_method", "device",
            "address_match", "customer_tier", "customer_age_days",
            "order_velocity", "previous_returns", "hour",
            "pincode_tier", "state"
        ]

    def encode_single(self, txn):
        row = []
        for feat in self.feature_names:
            if feat in self.encoders:
                try:
                    row.append(self.encoders[feat].transform([str(txn.get(feat, ""))])[0])
                except (ValueError, KeyError):
                    row.append(0)
            else:
                row.append(float(txn.get(feat, 0)))
        return np.array([row])

    def get_shap_reasons(self, features_scaled, txn):
        shap_values = self.explainer.shap_values(features_scaled)

        if isinstance(shap_values, list):
            sv = shap_values[1][0]
        else:
            sv = shap_values[0]

        if hasattr(sv, 'flatten'):
            sv = sv.flatten()

        feature_contribs = list(zip(self.feature_names, sv.tolist() if hasattr(sv, 'tolist') else list(sv)))
        feature_contribs.sort(key=lambda x: abs(float(x[1])), reverse=True)

        reasons = []
        for fname, val in feature_contribs[:5]:
            if abs(val) < 0.005:
                continue
            direction = "increases" if val > 0 else "decreases"
            display = fname.replace("_", " ").title()
            raw = txn.get(fname, "")
            if fname in self.encoders:
                label = str(raw)
            elif fname == "amount":
                label = f"₹{float(raw):,.0f}"
            else:
                label = str(raw)
            reasons.append({
                "feature": display,
                "value": label,
                "impact": round(float(val), 4),
                "direction": direction,
                "text": f"{display} ({label}) — {direction} risk by {abs(val):.3f}"
            })

        return reasons

    def get_action_recommendations(self, txn, risk_score, risk_level):
        recs = []
        amount = float(txn.get("amount", 0))
        payment = txn.get("payment_method", "")
        addr = txn.get("address_match", "")
        tier = txn.get("customer_tier", "")
        velocity = int(txn.get("order_velocity", 0))
        prev_returns = int(txn.get("previous_returns", 0))
        pincode_tier = txn.get("pincode_tier", "")
        hour = int(txn.get("hour", 12))

        if payment == "COD" and risk_score > 45:
            discount = max(200, int(amount * 0.02))
            recs.append({
                "action": "Incentivize Prepaid Conversion (UPI Discount)",
                "icon": "",
                "priority": "high",
                "detail": f"Offer instant ₹{discount} discount to switch from COD to Razorpay UPI. Reduces RTO by 82%.",
                "merchant_action": "SEND_UPI_LINK"
            })

        if addr == "Different from billing" and risk_score > 35:
            recs.append({
                "action": "Trigger Automated WhatsApp Address Verification",
                "icon": "",
                "priority": "high",
                "detail": "Shipping address differs from billing. Send 1-click address confirmation via WhatsApp before shipping.",
                "merchant_action": "VERIFY_ADDRESS"
            })

        if velocity > 5 and risk_score > 40:
            recs.append({
                "action": "Velocity Alert & 2FA Step-Up",
                "icon": "",
                "priority": "medium",
                "detail": f"High order frequency ({velocity} orders/7d). Require SMS OTP verification before warehouse dispatch.",
                "merchant_action": "REQUIRE_2FA"
            })

        if prev_returns >= 2 and risk_score > 35:
            deposit = min(250, max(50, int(amount * 0.03)))
            recs.append({
                "action": "Apply Refundable RTO Commitment Fee",
                "icon": "",
                "priority": "medium",
                "detail": f"Customer has {prev_returns} previous returns. Request ₹{deposit} refundable booking fee (credited back on delivery).",
                "merchant_action": "CHARGE_DEPOSIT"
            })

        if tier == "New" and risk_score > 55 and amount > 5000:
            recs.append({
                "action": "Split-Payment / Partial Advance",
                "icon": "",
                "priority": "medium",
                "detail": "High-ticket first-time order. Require 15% token advance via Razorpay Magic Checkout.",
                "merchant_action": "PARTIAL_PAYMENT"
            })

        if pincode_tier == "Tier-3" and payment == "COD" and risk_score > 45:
            recs.append({
                "action": "Prepaid-Only Routing for Tier-3 Delivery",
                "icon": "",
                "priority": "high",
                "detail": "Tier-3 logistics partners show elevated return rates for COD. Restrict to prepaid only or add delivery surcharge.",
                "merchant_action": "PREPAID_ONLY"
            })

        if 0 <= hour <= 5 and risk_score > 40:
            recs.append({
                "action": "Late-Night Order Hold (Business Hours Dispatch)",
                "icon": "",
                "priority": "low",
                "detail": "Placed between 12 AM - 5 AM. Hold fulfillment until manual confirmation during daylight operations.",
                "merchant_action": "HOLD_REVIEW"
            })

        if risk_score > 70 and len(recs) == 0:
            recs.append({
                "action": "Warehouse Fulfillment Hold",
                "icon": "",
                "priority": "high",
                "detail": "Elevated cumulative risk indicators. Route order to Risk Operations team for manual audit.",
                "merchant_action": "MANUAL_REVIEW"
            })

        if risk_level == "LOW":
            recs.append({
                "action": "Fast-Track Fulfillment & Loyalty Rewards",
                "icon": "",
                "priority": "low",
                "detail": "Trusted customer profile. Direct to automated 1-click packing slip generation.",
                "merchant_action": "FAST_TRACK"
            })

        return recs

    def generate_risk_brief(self, txn, risk_score, risk_level, shap_reasons):
        amount = float(txn.get("amount", 0))
        payment = txn.get("payment_method", "")
        tier = txn.get("customer_tier", "")
        category = txn.get("category", "")
        pincode = txn.get("pincode_tier", "")
        prev_returns = int(txn.get("previous_returns", 0))

        top_factors = [r["text"] for r in shap_reasons[:3]]
        top_str = "; ".join(top_factors) if top_factors else "standard risk distribution"

        if risk_level == "HIGH":
            verdict = "BLOCK / INTERVENE strongly recommended"
            confidence_note = "Multiple high-risk return signals present. Merchant should require prepaid conversion or verification."
        elif risk_level == "MEDIUM":
            verdict = "REVIEW recommended"
            confidence_note = "Moderate risk signals detected. Automated WhatsApp or OTP verification is advised prior to dispatch."
        else:
            verdict = "PASS - Safe Transaction"
            confidence_note = "Transaction profile matches safe buying patterns. Proceed with instant fulfillment."

        est_return_pct = min(92, max(2, risk_score * 0.95))
        est_return_amount = amount * (est_return_pct / 100)

        brief = (
            f"Transaction {txn.get('txn_id', 'N/A')} (₹{amount:,.0f}, {category}, {payment}) "
            f"is scored {risk_score}/100 ({risk_level} risk). "
            f"Primary risk drivers: {top_str}. "
            f"{verdict}. {confidence_note} "
            f"Estimated return probability: {est_return_pct:.0f}% (projected ₹{est_return_amount:,.0f} exposure). "
            f"Customer Profile: {tier} tier, {pincode} pincode, {prev_returns} historical return(s)."
        )

        return brief

    def generate_ai_copilot_insights(self, txn, risk_score, risk_level, shap_reasons):
        amount = float(txn.get("amount", 0))
        payment = txn.get("payment_method", "")
        tier = txn.get("customer_tier", "")
        category = txn.get("category", "")
        pincode = txn.get("pincode_tier", "")
        txn_id = txn.get("txn_id", "TXN-" + str(np.random.randint(1000, 9999)))

        top_drivers = [r["text"] for r in shap_reasons[:3]]

        # Generate personalized customer WhatsApp verification message without emojis
        if payment == "COD":
            discount = max(200, int(amount * 0.02))
            wa_message = (
                f"Hi from Merchant Team! We received your COD order #{txn_id} for ₹{amount:,.0f}. "
                f"To confirm delivery & get an INSTANT ₹{discount} OFF, tap to pay via Razorpay UPI: "
                f"https://rzp.io/l/{txn_id.lower()}?discount={discount} "
                f"Reply 1 to confirm COD, or 2 to cancel."
            )
        else:
            wa_message = (
                f"Hi! Thanks for your order #{txn_id} of ₹{amount:,.0f} on Merchant Store. "
                f"Your order is verified and scheduled for priority express dispatch! "
                f"Track live delivery status here: https://track.store/{txn_id.lower()}"
            )

        if risk_level == "HIGH":
            strategy = "Enforce prepaid conversion via Razorpay UPI or hold fulfillment pending customer phone confirmation."
        elif risk_level == "MEDIUM":
            strategy = "Dispatch automated WhatsApp confirmation message to verify delivery address and intent."
        else:
            strategy = "Auto-approve for standard 1-click warehouse packing."

        est_return_pct = min(95, max(5, int(risk_score * 0.95)))
        est_loss = int(amount * 0.20 + 150) if payment == "COD" else int(amount * 0.05 + 50)

        # Build clean numbered list of risk factors (removing emojis/non-ascii symbols)
        drivers_list = ""
        for i, d in enumerate(top_drivers, 1):
            clean_d = d.encode('ascii', 'ignore').decode('ascii').strip()
            drivers_list += f"<br>  {i}. {clean_d}"
        if not top_drivers:
            drivers_list = "<br>  No unusual risk drivers detected."

        executive_note = (
            f"**Risk Level**: {risk_level}<br>"
            f"**Risk Score**: {risk_score} out of 100<br>"
            f"**Return Probability**: {est_return_pct}%<br>"
            f"**Potential Logistics Loss**: Rs. {est_loss:,}<br>"
            f"**Risk Drivers**: {drivers_list}<br>"
            f"**Suggested Strategy**: {strategy}"
        )

        return {
            "executive_note": executive_note,
            "recommended_strategy": strategy,
            "whatsapp_template": wa_message,
            "rto_loss_prevention_estimate": round(amount * (risk_score / 100) * 0.25, 2)
        }

    def score(self, txn):
        features = self.encode_single(txn)
        scaled = self.scaler.transform(features)
        proba = self.model.predict_proba(scaled)[0][1]
        risk_score = round(proba * 100, 1)

        amount = float(txn.get("amount", 0))
        payment = txn.get("payment_method", "")

        if amount < 5000:
            risk_score = max(5, risk_score - 20)
        elif amount < 10000:
            risk_score = max(10, risk_score - 10)
        elif amount > 50000:
            risk_score = min(100, risk_score + 10)
        elif amount > 25000:
            risk_score = min(100, risk_score + 5)

        if payment == "COD" and amount > 10000:
            risk_score = min(100, risk_score + 8)
        elif payment == "COD" and amount < 5000:
            risk_score = max(5, risk_score - 5)

        risk_score = max(0, min(100, risk_score))

        if risk_score >= 65:
            risk_level = "HIGH"
            action = "BLOCK"
        elif risk_score >= 35:
            risk_level = "MEDIUM"
            action = "REVIEW"
        else:
            risk_level = "LOW"
            action = "PASS"

        shap_reasons = self.get_shap_reasons(scaled, txn)
        recommendations = self.get_action_recommendations(txn, risk_score, risk_level)
        risk_brief = self.generate_risk_brief(txn, risk_score, risk_level, shap_reasons)
        ai_copilot = self.generate_ai_copilot_insights(txn, risk_score, risk_level, shap_reasons)

        return {
            "txn_id": txn.get("txn_id", "N/A"),
            "amount": float(txn["amount"]),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "action": action,
            "confidence": round(abs(proba - 0.5) * 2 * 100, 1),
            "shap_reasons": shap_reasons,
            "recommendations": recommendations,
            "risk_brief": risk_brief,
            "ai_copilot": ai_copilot,
            "payment_method": txn.get("payment_method", ""),
            "customer_tier": txn.get("customer_tier", ""),
            "pincode_tier": txn.get("pincode_tier", "")
        }

    def score_batch(self, transactions):
        results = [self.score(txn) for txn in transactions]
        flagged = [r for r in results if r["risk_level"] in ["HIGH", "MEDIUM"]]
        passed = [r for r in results if r["risk_level"] == "LOW"]
        blocked_value = sum(r["amount"] for r in results if r["action"] == "BLOCK")
        review_value = sum(r["amount"] for r in results if r["action"] == "REVIEW")

        return {
            "total": len(results),
            "flagged": len(flagged),
            "passed": len(passed),
            "flag_rate": round(len(flagged) / len(results) * 100, 1) if results else 0,
            "blocked_value": round(blocked_value, 2),
            "review_value": round(review_value, 2),
            "results": results
        }

def score_from_csv(csv_path="data/transactions.csv", model_dir="models"):
    import csv
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(csv_path):
        csv_path = os.path.join(base_dir, csv_path)
    if not os.path.isabs(model_dir):
        model_dir = os.path.join(base_dir, model_dir)

    rows = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    scorer = RiskScorer(model_dir)
    return scorer.score_batch(rows)
