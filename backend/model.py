import csv
import json
import os
import pickle
import numpy as np
import shap
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score
)

def load_data(path="data/transactions.csv"):
    rows = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def encode_features(rows):
    encoders = {}
    for col in ["category", "payment_method", "device", "address_match", "customer_tier", "pincode_tier", "state"]:
        le = LabelEncoder()
        le.fit([r[col] for r in rows])
        encoders[col] = le

    features = []
    for r in rows:
        features.append([
            float(r["amount"]),
            encoders["category"].transform([r["category"]])[0],
            encoders["payment_method"].transform([r["payment_method"]])[0],
            encoders["device"].transform([r["device"]])[0],
            encoders["address_match"].transform([r["address_match"]])[0],
            encoders["customer_tier"].transform([r["customer_tier"]])[0],
            int(r["customer_age_days"]),
            int(r["order_velocity"]),
            int(r["previous_returns"]),
            int(r["hour"]),
            encoders["pincode_tier"].transform([r["pincode_tier"]])[0],
            encoders["state"].transform([r["state"]])[0],
        ])

    labels = [int(r["returned"]) for r in rows]
    return np.array(features), np.array(labels), encoders

FEATURE_NAMES = [
    "amount", "category", "payment_method", "device",
    "address_match", "customer_tier", "customer_age_days",
    "order_velocity", "previous_returns", "hour",
    "pincode_tier", "state"
]

def train_and_evaluate(data_path="data/transactions.csv", model_dir="models"):
    rows = load_data(data_path)
    X, y, encoders = encode_features(rows)

    X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
        X, y, np.arange(len(y)), test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_split=10,
        min_samples_leaf=4,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1
    )
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)
    y_proba = model.predict_proba(X_test_scaled)[:, 1]

    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)

    tn, fp, fn, tp = cm.ravel()
    avg_amount = np.mean([float(r["amount"]) for r in rows])

    explainer = shap.TreeExplainer(model)

    threshold_curve = []
    for t in [round(0.1 * i, 1) for i in range(1, 10)]:
        y_pred_t = (y_proba >= t).astype(int)
        p_t = precision_score(y_test, y_pred_t, zero_division=0)
        r_t = recall_score(y_test, y_pred_t, zero_division=0)
        cm_t = confusion_matrix(y_test, y_pred_t)
        tn_t, fp_t, fn_t, tp_t = cm_t.ravel()
        threshold_curve.append({
            "threshold": t,
            "precision": round(p_t, 4),
            "recall": round(r_t, 4),
            "true_negatives": int(tn_t),
            "false_positives": int(fp_t),
            "false_negatives": int(fn_t),
            "true_positives": int(tp_t),
            "fp_cost": round(fp_t * avg_amount, 2),
            "fn_cost": round(fn_t * avg_amount, 2)
        })

    importances = model.feature_importances_
    feature_importance = sorted(
        zip(FEATURE_NAMES, importances),
        key=lambda x: x[1], reverse=True
    )

    metrics = {
        "total_transactions": len(rows),
        "return_rate": round(y.mean() * 100, 2),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "auc_roc": round(auc, 4),
        "confusion_matrix": {
            "true_negatives": int(tn), "false_positives": int(fp),
            "false_negatives": int(fn), "true_positives": int(tp)
        },
        "false_positive_cost": round(fp * avg_amount, 2),
        "false_negative_cost": round(fn * avg_amount, 2),
        "avg_transaction_amount": round(avg_amount, 2),
        "total_test_samples": len(y_test),
        "total_returned_in_test": int(y_test.sum()),
        "threshold_curve": threshold_curve,
        "feature_importance": [{"feature": f, "importance": round(float(i), 4)} for f, i in feature_importance],
        "classification_report": classification_report(y_test, y_pred, output_dict=True)
    }

    os.makedirs(model_dir, exist_ok=True)
    with open(os.path.join(model_dir, "model.pkl"), "wb") as f:
        pickle.dump(model, f)
    with open(os.path.join(model_dir, "scaler.pkl"), "wb") as f:
        pickle.dump(scaler, f)
    with open(os.path.join(model_dir, "encoders.pkl"), "wb") as f:
        pickle.dump(encoders, f)
    with open(os.path.join(model_dir, "explainer.pkl"), "wb") as f:
        pickle.dump(explainer, f)
    with open(os.path.join(model_dir, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\n{'='*55}")
    print(f"  MODEL TRAINING RESULTS  ({len(rows):,} transactions)")
    print(f"{'='*55}")
    print(f"  Return rate:     {y.mean()*100:.1f}%")
    print(f"  Precision:       {precision:.4f}")
    print(f"  Recall:          {recall:.4f}")
    print(f"  F1 Score:        {f1:.4f}")
    print(f"  AUC-ROC:         {auc:.4f}")
    print(f"\n  Confusion Matrix:")
    print(f"    TN: {tn}  FP: {fp}")
    print(f"    FN: {fn}  TP: {tp}")
    print(f"\n  FP Cost:  Rs.{fp * avg_amount:,.2f}")
    print(f"  FN Cost:  Rs.{fn * avg_amount:,.2f}")
    print(f"\n  Top Features:")
    for fname, imp in feature_importance[:5]:
        print(f"    {fname}: {imp:.4f}")
    print(f"{'='*55}\n")

    return metrics

if __name__ == "__main__":
    train_and_evaluate()
