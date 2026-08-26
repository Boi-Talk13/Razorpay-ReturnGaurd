import csv
import random
import os
from datetime import datetime, timedelta

random.seed(42)

CATEGORIES = ["Electronics", "Clothing", "Home & Kitchen", "Beauty", "Sports", "Books", "Toys"]
PAYMENT_METHODS = ["UPI", "Credit Card", "Debit Card", "Net Banking", "COD", "Wallet"]
DEVICES = ["Mobile", "Desktop", "Tablet"]
ADDRESSES = ["Same as billing", "Different from billing"]
CUSTOMER_TIERS = ["New", "Returning", "Loyal"]
PINCODE_TIERS = ["Metro", "Tier-1", "Tier-2", "Tier-3"]
STATES = [
    "Karnataka", "Maharashtra", "Tamil Nadu", "Delhi", "Telangana",
    "Gujarat", "Rajasthan", "West Bengal", "Uttar Pradesh", "Kerala",
    "Punjab", "Madhya Pradesh", "Bihar", "Odisha", "Assam"
]

def weighted_choice(items, weights):
    return random.choices(items, weights=weights, k=1)[0]

def generate_transaction(txn_id):
    base_date = datetime(2025, 6, 1)
    order_date = base_date + timedelta(days=random.randint(0, 90))
    hour = weighted_choice(
        list(range(24)),
        [1, 1, 1, 1, 1, 2, 3, 5, 8, 10, 12, 13, 14, 13, 12, 11, 10, 9, 8, 6, 4, 3, 2, 1]
    )
    order_date = order_date.replace(hour=hour)

    amount = round(random.lognormvariate(7.5, 1.2), 2)
    amount = max(99, min(99999, amount))

    if amount < 500:
        category = weighted_choice(CATEGORIES, [10, 30, 20, 15, 10, 10, 5])
    elif amount < 3000:
        category = weighted_choice(CATEGORIES, [25, 25, 20, 10, 10, 5, 5])
    else:
        category = weighted_choice(CATEGORIES, [40, 15, 15, 5, 10, 5, 10])

    payment_method = weighted_choice(PAYMENT_METHODS, [30, 20, 15, 10, 20, 5])
    device = weighted_choice(DEVICES, [60, 30, 10])
    pincode_tier = weighted_choice(PINCODE_TIERS, [30, 25, 25, 20])
    state = random.choice(STATES)

    if pincode_tier == "Metro":
        address_match = weighted_choice(ADDRESSES, [75, 25])
    elif pincode_tier == "Tier-3":
        address_match = weighted_choice(ADDRESSES, [55, 45])
    else:
        address_match = weighted_choice(ADDRESSES, [65, 35])

    customer_tier = weighted_choice(CUSTOMER_TIERS, [25, 40, 35])
    customer_age_days = random.randint(0, 2000)

    if customer_tier == "New":
        customer_age_days = random.randint(0, 90)
    elif customer_tier == "Returning":
        customer_age_days = random.randint(30, 800)
    else:
        customer_age_days = random.randint(180, 2000)

    order_velocity = random.randint(1, 15)
    previous_returns = random.randint(0, 5)

    if customer_tier == "Loyal":
        previous_returns = weighted_choice([0, 0, 0, 1, 1, 2], [40, 25, 15, 10, 7, 3])
    elif customer_tier == "New":
        previous_returns = 0
    else:
        previous_returns = weighted_choice([0, 0, 1, 1, 2, 3], [30, 25, 20, 15, 7, 3])

    risk_score = 0
    if amount > 15000: risk_score += 22
    elif amount > 8000: risk_score += 14
    elif amount > 3000: risk_score += 7

    if payment_method == "COD": risk_score += 18
    elif payment_method == "Wallet": risk_score += 5

    if address_match == "Different from billing": risk_score += 14
    if customer_tier == "New": risk_score += 16
    elif customer_tier == "Returning": risk_score += 5

    if customer_age_days < 30: risk_score += 12
    elif customer_age_days < 90: risk_score += 5

    if order_velocity > 8: risk_score += 14
    elif order_velocity > 5: risk_score += 8

    if previous_returns > 2: risk_score += 20
    elif previous_returns > 0: risk_score += 8

    if 0 <= hour <= 5: risk_score += 10
    elif 22 <= hour <= 23: risk_score += 5

    if pincode_tier == "Tier-3": risk_score += 8
    elif pincode_tier == "Tier-2": risk_score += 3

    if device == "Mobile": risk_score += 2

    risk_score += random.randint(-8, 8)
    risk_score = max(0, min(100, risk_score))

    if risk_score > 70:
        returned = 1 if random.random() < 0.75 else 0
    elif risk_score > 50:
        returned = 1 if random.random() < 0.35 else 0
    elif risk_score > 30:
        returned = 1 if random.random() < 0.08 else 0
    else:
        returned = 1 if random.random() < 0.02 else 0

    return {
        "txn_id": f"TXN-{txn_id:05d}",
        "order_date": order_date.strftime("%Y-%m-%d %H:%M"),
        "amount": amount,
        "category": category,
        "payment_method": payment_method,
        "device": device,
        "address_match": address_match,
        "customer_tier": customer_tier,
        "customer_age_days": customer_age_days,
        "order_velocity": order_velocity,
        "previous_returns": previous_returns,
        "hour": hour,
        "pincode_tier": pincode_tier,
        "state": state,
        "returned": returned
    }

def generate_dataset(n=10000, output_path="data/transactions.csv"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    transactions = [generate_transaction(i) for i in range(1, n + 1)]

    fieldnames = [
        "txn_id", "order_date", "amount", "category", "payment_method", "device",
        "address_match", "customer_tier", "customer_age_days",
        "order_velocity", "previous_returns", "hour",
        "pincode_tier", "state", "returned"
    ]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(transactions)

    returned_count = sum(1 for t in transactions if t["returned"] == 1)
    print(f"Generated {n} transactions: {returned_count} returned ({returned_count/n*100:.1f}%), {n - returned_count} not returned ({(n-returned_count)/n*100:.1f}%)")
    return output_path

if __name__ == "__main__":
    generate_dataset(10000, "data/transactions.csv")
