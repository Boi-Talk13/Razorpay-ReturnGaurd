const API_BASE = "";

// ============ THEME TOGGLE ============
(function() {
    const toggleBtn = document.getElementById("theme-toggle");
    if (!toggleBtn) return;

    const sunIcon = toggleBtn.querySelector(".sun-icon");
    const moonIcon = toggleBtn.querySelector(".moon-icon");

    const savedTheme = localStorage.getItem("theme") || "dark";
    if (savedTheme === "light") {
        document.body.classList.add("light-mode");
        sunIcon.classList.add("hidden");
        moonIcon.classList.remove("hidden");
    }

    toggleBtn.addEventListener("click", () => {
        const isLight = document.body.classList.toggle("light-mode");
        localStorage.setItem("theme", isLight ? "light" : "dark");
        if (isLight) {
            sunIcon.classList.add("hidden");
            moonIcon.classList.remove("hidden");
        } else {
            sunIcon.classList.remove("hidden");
            moonIcon.classList.add("hidden");
        }
        if (typeof drawCurveChart === "function" && thresholdCurve && thresholdCurve.length) {
            drawCurveChart(thresholdCurve);
        }
    });
})();

// ============ HELPERS ============

function animateValue(el, target, decimals = 1, suffix = "") {
    if (!el) return;
    const duration = 1200, start = performance.now();
    function tick(now) {
        const p = Math.min((now - start) / duration, 1);
        const e = 1 - Math.pow(1 - p, 3);
        el.textContent = (target * e).toFixed(decimals) + suffix;
        if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
}

function animateCurrency(el, target) {
    if (!el) return;
    const duration = 1200, start = performance.now();
    function tick(now) {
        const p = Math.min((now - start) / duration, 1);
        const e = 1 - Math.pow(1 - p, 3);
        el.textContent = "₹" + Math.round(target * e).toLocaleString("en-IN");
        if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
}

function animateInt(el, target) {
    if (!el) return;
    const duration = 900, start = performance.now();
    function tick(now) {
        const p = Math.min((now - start) / duration, 1);
        el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3)));
        if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
}

function formatName(name) {
    return name.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

// ============ DATETIME DEFAULT = NOW ============

(function () {
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    const el = document.getElementById("order_time");
    if (el) el.value = now.toISOString().slice(0, 16);

    const webhookUrlEl = document.getElementById("live-webhook-url");
    if (webhookUrlEl) {
        webhookUrlEl.textContent = window.location.origin + "/api/webhook/razorpay";
    }
})();

// ============ PINCODE LOOKUP ============

let derivedTier = "Tier-2";
const METRO_PREFIXES = ["110", "400", "600", "700", "560", "500", "411", "380"];
const TIER1_CITIES = ["Jaipur","Lucknow","Surat","Nagpur","Indore","Bhopal","Visakhapatnam","Coimbatore","Kochi","Ernakulam","Chandigarh","Noida","Gurugram","Thane","Bhubaneswar","Patna","Vadodara","Ludhiana","Agra","Nashik","Faridabad","Rajkot","Varanasi","Mysuru","Madurai","Guwahati","Vijayawada","Aurangabad","Thiruvananthapuram","Trivandrum","Kozhikode","Calicut","Kanpur","Pune"];

function classifyTier(pin, district, postOffices) {
    if (METRO_PREFIXES.includes(pin.slice(0, 3))) return "Metro";
    if (district && TIER1_CITIES.some(c => district.toLowerCase().includes(c.toLowerCase()))) return "Tier-1";
    if (postOffices && postOffices.every(po => po.BranchType === "BO")) return "Tier-3";
    return "Tier-2";
}

const pinInput = document.getElementById("pincode");
const pinMeta = document.getElementById("pin-meta");
const pinState = document.getElementById("pin_state");
const pinDistrict = document.getElementById("pin_district");

if (pinInput) {
    pinInput.addEventListener("input", async () => {
        const pin = pinInput.value.trim();
        if (!/^\d{6}$/.test(pin)) {
            pinState.value = ""; pinDistrict.value = "";
            pinMeta.innerHTML = ""; derivedTier = "Tier-2"; return;
        }
        pinMeta.innerHTML = `<span class="pin-loading">Looking up...</span>`;
        try {
            const res = await fetch(`${API_BASE}/api/pincode/${pin}`);
            const data = await res.json();
            if (data[0].Status === "Success" && data[0].PostOffice && data[0].PostOffice.length > 0) {
                const offices = data[0].PostOffice;
                pinState.value = offices[0].State;
                pinDistrict.value = offices[0].District;
                derivedTier = classifyTier(pin, offices[0].District, offices);
                pinMeta.innerHTML = `<span class="pin-tier-chip tier-${derivedTier.toLowerCase().replace("-", "")}">${derivedTier}</span><span class="pin-offices">${offices.length} offices</span>`;
            } else {
                pinState.value = ""; pinDistrict.value = "";
                derivedTier = "Tier-2";
                pinMeta.innerHTML = `<span class="pin-error">Invalid pincode</span>`;
            }
        } catch {
            derivedTier = METRO_PREFIXES.includes(pin.slice(0, 3)) ? "Metro" : "Tier-2";
            pinMeta.innerHTML = `<span class="pin-error">Offline — tier estimated</span>`;
        }
    });
}

// ============ LOAD METRICS ============

let thresholdCurve = [];

async function loadMetrics() {
    try {
        const res = await fetch(`${API_BASE}/api/metrics`);
        const data = await res.json();

        animateValue(document.getElementById("precision"), data.precision * 100, 1, "%");
        animateValue(document.getElementById("recall"), data.recall * 100, 1, "%");
        animateValue(document.getElementById("f1"), data.f1_score * 100, 1, "%");
        animateValue(document.getElementById("auc"), data.auc_roc, 3);

        setTimeout(() => {
            document.getElementById("precision-bar").style.width = (data.precision * 100) + "%";
            document.getElementById("recall-bar").style.width = (data.recall * 100) + "%";
            document.getElementById("f1-bar").style.width = (data.f1_score * 100) + "%";
            document.getElementById("auc-bar").style.width = (data.auc_roc * 100) + "%";
        }, 100);

        animateCurrency(document.getElementById("fp-cost"), data.false_positive_cost);
        animateCurrency(document.getElementById("fn-cost"), data.false_negative_cost);

        animateInt(document.getElementById("tn"), data.confusion_matrix.true_negatives);
        animateInt(document.getElementById("fp"), data.confusion_matrix.false_positives);
        animateInt(document.getElementById("fn"), data.confusion_matrix.false_negatives);
        animateInt(document.getElementById("tp"), data.confusion_matrix.true_positives);

        const featContainer = document.getElementById("feature-bars");
        featContainer.innerHTML = data.feature_importance.map(({feature, importance}) => `
            <div class="feat-row">
                <span class="feat-name">${formatName(feature)}</span>
                <div class="feat-bar-track">
                    <div class="feat-bar-fill" style="width: ${importance * 100}%"></div>
                </div>
                <span class="feat-pct">${(importance * 100).toFixed(1)}%</span>
            </div>
        `).join("");

        thresholdCurve = data.threshold_curve || [];
        drawCurveChart(thresholdCurve);
        updateThreshold(0.5);
    } catch (err) {
        console.error("Failed to load metrics:", err);
    }
}

// ============ THRESHOLD TUNER & ROI SIMULATOR ============

function drawCurveChart(curve) {
    const svg = document.getElementById("curve-chart");
    if (!curve || !curve.length || !svg) return;

    const w = 520, h = 280, pad = 44;
    const cw = w - pad * 2, ch = h - pad * 2;

    const maxFP = Math.max(...curve.map(d => d.fp_cost)) || 1;
    const maxFN = Math.max(...curve.map(d => d.fn_cost)) || 1;

    function x(t) { return pad + ((t - 0.1) / 0.8) * cw; }
    function yPct(v) { return pad + ch - Math.max(0, Math.min(1, v)) * ch; }
    function yFP(v) { return pad + ch - (v / maxFP) * ch; }
    function yFN(v) { return pad + ch - (v / maxFN) * ch; }

    function makePath(pts) {
        return pts.map((p, i) => `${i === 0 ? "M" : "L"} ${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(" ");
    }

    const pPath = makePath(curve.map(d => [x(d.threshold), yPct(d.precision)]));
    const rPath = makePath(curve.map(d => [x(d.threshold), yPct(d.recall)]));
    const fpPath = makePath(curve.map(d => [x(d.threshold), yFP(d.fp_cost)]));
    const fnPath = makePath(curve.map(d => [x(d.threshold), yFN(d.fn_cost)]));

    let gridLines = "";
    for (let i = 0; i <= 4; i++) {
        const v = i * 0.25;
        const yy = yPct(v);
        gridLines += `<line x1="${pad}" y1="${yy.toFixed(1)}" x2="${pad + cw}" y2="${yy.toFixed(1)}" stroke="var(--border)" stroke-width="1"/>`;
        gridLines += `<text x="${(pad - 8).toFixed(1)}" y="${(yy + 4).toFixed(1)}" fill="var(--muted)" font-size="9" text-anchor="end">${(v * 100).toFixed(0)}%</text>`;
    }

    let xLabels = "";
    curve.forEach(d => {
        xLabels += `<text x="${x(d.threshold).toFixed(1)}" y="${(pad + ch + 18).toFixed(1)}" fill="var(--muted)" font-size="9" text-anchor="middle">${d.threshold.toFixed(1)}</text>`;
    });

    let dots = "";
    curve.forEach(d => {
        dots += `<circle cx="${x(d.threshold).toFixed(1)}" cy="${yPct(d.precision).toFixed(1)}" r="4" fill="var(--indigo)"/>`;
        dots += `<circle cx="${x(d.threshold).toFixed(1)}" cy="${yPct(d.recall).toFixed(1)}" r="4" fill="var(--green)"/>`;
        dots += `<circle cx="${x(d.threshold).toFixed(1)}" cy="${yFP(d.fp_cost).toFixed(1)}" r="4" fill="var(--amber)"/>`;
        dots += `<circle cx="${x(d.threshold).toFixed(1)}" cy="${yFN(d.fn_cost).toFixed(1)}" r="4" fill="var(--red)"/>`;
    });

    svg.innerHTML = `
        <line x1="${pad}" y1="${pad}" x2="${pad}" y2="${pad + ch}" stroke="var(--border-hi)" stroke-width="1.5"/>
        <line x1="${pad}" y1="${pad + ch}" x2="${pad + cw}" y2="${pad + ch}" stroke="var(--border-hi)" stroke-width="1.5"/>
        ${gridLines}
        ${xLabels}
        <text x="${(pad - 28).toFixed(1)}" y="${(pad + ch / 2).toFixed(1)}" fill="var(--muted)" font-size="9" text-anchor="middle" transform="rotate(-90 ${(pad - 28).toFixed(1)} ${(pad + ch / 2).toFixed(1)})">Score / Cost</text>
        <text x="${(pad + cw / 2).toFixed(1)}" y="${(pad + ch + 32).toFixed(1)}" fill="var(--muted)" font-size="9" text-anchor="middle">Threshold</text>
        <path d="${pPath}" fill="none" stroke="var(--indigo)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="${rPath}" fill="none" stroke="var(--green)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="${fpPath}" fill="none" stroke="var(--amber)" stroke-width="2" stroke-dasharray="5,3" stroke-linecap="round"/>
        <path d="${fnPath}" fill="none" stroke="var(--red)" stroke-width="2" stroke-dasharray="5,3" stroke-linecap="round"/>
        ${dots}
    `;
}


function updateThreshold(val) {
    const t = parseFloat(val);
    const sliderValEl = document.getElementById("threshold-value");
    if (sliderValEl) sliderValEl.textContent = t.toFixed(2);

    const row = thresholdCurve.find(d => Math.abs(d.threshold - t) < 0.05) || thresholdCurve[4];
    if (row) {
        document.getElementById("t-precision").textContent = (row.precision * 100).toFixed(1) + "%";
        document.getElementById("t-recall").textContent = (row.recall * 100).toFixed(1) + "%";
        document.getElementById("t-fp-cost").textContent = "₹" + Math.round(row.fp_cost).toLocaleString("en-IN");
        document.getElementById("t-fn-cost").textContent = "₹" + Math.round(row.fn_cost).toLocaleString("en-IN");
    }
    updatePolicySim(row);
    drawCurveChart(thresholdCurve);
}

function updatePolicySim(row) {
    if (!row) return;
    const orders = parseFloat(document.getElementById("sim-orders").value) || 10000;
    const aov = parseFloat(document.getElementById("sim-aov").value) || 5000;

    const baseReturnRate = 0.22;
    const totalReturns = orders * baseReturnRate;
    const returnsCaught = totalReturns * row.recall;
    const fpOrders = orders * (1 - baseReturnRate) * (1 - (row.true_negatives / (row.true_negatives + row.false_positives || 1)));

    const saved = returnsCaught * (aov * 0.25); // ~25% RTO cost avoided
    const lost = fpOrders * (aov * 0.10);  // 10% lost margin from friction
    const net = saved - lost;

    document.getElementById("sim-saved").textContent = "+₹" + Math.round(saved).toLocaleString("en-IN");
    document.getElementById("sim-lost").textContent = "-₹" + Math.round(lost).toLocaleString("en-IN");
    const netEl = document.getElementById("sim-net");
    netEl.textContent = (net >= 0 ? "+₹" : "-₹") + Math.round(Math.abs(net)).toLocaleString("en-IN");
    netEl.className = "p-net " + (net >= 0 ? "positive" : "negative");
}

const slider = document.getElementById("threshold-slider");
if (slider) {
    slider.addEventListener("input", e => updateThreshold(e.target.value));
}
const simOrders = document.getElementById("sim-orders");
const simAov = document.getElementById("sim-aov");
if (simOrders) simOrders.addEventListener("input", () => updateThreshold(slider ? slider.value : 0.5));
if (simAov) simAov.addEventListener("input", () => updateThreshold(slider ? slider.value : 0.5));

// ============ 1-CLICK QUICK PRESETS ============

function loadPresetData(scenario) {
    document.getElementById("amount").value = scenario.amount;
    document.getElementById("category").value = scenario.category;
    document.getElementById("payment_method").value = scenario.payment_method;
    document.getElementById("device").value = scenario.device;
    document.getElementById("address_match").value = scenario.address_match;
    document.getElementById("customer_tier").value = scenario.customer_tier;
    document.getElementById("customer_age_days").value = scenario.customer_age_days;
    document.getElementById("order_velocity").value = scenario.order_velocity;
    document.getElementById("previous_returns").value = scenario.previous_returns;
    document.getElementById("pincode").value = scenario.pincode;
    document.getElementById("pin_state").value = scenario.state;
    document.getElementById("pin_district").value = scenario.pincode_tier;
    derivedTier = scenario.pincode_tier;

    // Trigger score form submit
    document.getElementById("score-form").dispatchEvent(new Event("submit"));
}

document.getElementById("preset-cod-electronics")?.addEventListener("click", () => {
    loadPresetData({
        amount: 16500, category: "Electronics", payment_method: "COD", device: "Mobile",
        address_match: "Different from billing", customer_tier: "New", customer_age_days: 4,
        order_velocity: 9, previous_returns: 3, pincode: "800001", pincode_tier: "Tier-3", state: "Bihar"
    });
});

document.getElementById("preset-midnight-spree")?.addEventListener("click", () => {
    loadPresetData({
        amount: 9200, category: "Clothing", payment_method: "COD", device: "Desktop",
        address_match: "Different from billing", customer_tier: "New", customer_age_days: 12,
        order_velocity: 11, previous_returns: 2, pincode: "201301", pincode_tier: "Tier-2", state: "Uttar Pradesh"
    });
});

document.getElementById("preset-loyal-metro")?.addEventListener("click", () => {
    loadPresetData({
        amount: 4500, category: "Home & Kitchen", payment_method: "UPI", device: "Mobile",
        address_match: "Same as billing", customer_tier: "Loyal", customer_age_days: 520,
        order_velocity: 1, previous_returns: 0, pincode: "560001", pincode_tier: "Metro", state: "Karnataka"
    });
});

document.getElementById("preset-tier3-mismatch")?.addEventListener("click", () => {
    loadPresetData({
        amount: 3400, category: "Beauty", payment_method: "COD", device: "Mobile",
        address_match: "Different from billing", customer_tier: "Returning", customer_age_days: 110,
        order_velocity: 4, previous_returns: 2, pincode: "302001", pincode_tier: "Tier-3", state: "Rajasthan"
    });
});

// ============ SCORE TRANSACTION FORM ============

document.getElementById("score-form")?.addEventListener("submit", async e => {
    e.preventDefault();
    const btn = document.getElementById("analyze-btn");
    btn.classList.add("loading");

    const orderTimeVal = document.getElementById("order_time").value;
    const hour = orderTimeVal ? new Date(orderTimeVal).getHours() : 14;

    const txn = {
        amount: parseFloat(document.getElementById("amount").value) || 5000,
        category: document.getElementById("category").value,
        payment_method: document.getElementById("payment_method").value,
        device: document.getElementById("device").value,
        address_match: document.getElementById("address_match").value,
        customer_tier: document.getElementById("customer_tier").value,
        customer_age_days: document.getElementById("customer_age_days").value,
        order_velocity: document.getElementById("order_velocity").value,
        previous_returns: document.getElementById("previous_returns").value,
        hour: hour,
        pincode_tier: derivedTier,
        state: document.getElementById("pin_state").value || "Karnataka"
    };

    try {
        const res = await fetch(`${API_BASE}/api/score`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(txn)
        });
        const data = await res.json();
        setTimeout(() => { btn.classList.remove("loading"); showResult(data); }, 300);
    } catch (err) {
        console.error("Scoring failed:", err);
        btn.classList.remove("loading");
    }
});

function showResult(data) {
    document.getElementById("result-idle").classList.add("hidden");
    const live = document.getElementById("result-live");
    live.classList.remove("hidden");

    // Gauge
    const arc = document.getElementById("gauge-arc");
    const totalLen = 252;
    const offset = totalLen - (data.risk_score / 100) * totalLen;
    const colors = { LOW: "#34d399", MEDIUM: "#fbbf24", HIGH: "#fb7185" };
    arc.style.stroke = colors[data.risk_level] || "#6366f1";
    arc.style.transition = "none";
    arc.style.strokeDashoffset = totalLen;
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            arc.style.transition = "stroke-dashoffset 1s cubic-bezier(0.4,0,0.2,1), stroke 0.5s";
            arc.style.strokeDashoffset = offset;
        });
    });

    animateInt(document.getElementById("result-score"), data.risk_score);

    const levelEl = document.getElementById("result-level");
    levelEl.textContent = data.risk_level + " RISK";
    levelEl.className = "tag " + data.risk_level;

    document.getElementById("result-action").textContent = "→ " + data.action;
    document.getElementById("result-confidence").textContent = data.confidence + "%";
    setTimeout(() => { document.getElementById("conf-fill").style.width = data.confidence + "%"; }, 200);

    // AI Copilot & WhatsApp Box
    if (data.ai_copilot) {
        document.getElementById("copilot-note").innerHTML = data.ai_copilot.executive_note.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        document.getElementById("copilot-roi").textContent = "₹" + Math.round(data.ai_copilot.rto_loss_prevention_estimate).toLocaleString("en-IN") + " Saved";
        document.getElementById("wa-bubble").textContent = data.ai_copilot.whatsapp_template;
    }

    // SHAP bars
    const shapContainer = document.getElementById("shap-bars");
    const maxImpact = Math.max(...(data.shap_reasons || []).map(r => Math.abs(r.impact)), 0.01);
    shapContainer.innerHTML = (data.shap_reasons || []).slice(0, 6).map(r => {
        const pct = Math.min(100, (Math.abs(r.impact) / maxImpact) * 50);
        const isPos = r.direction === "increases";
        return `
            <div class="shap-row">
                <span class="shap-feature">${r.feature}</span>
                <span class="shap-value">${r.value}</span>
                <div class="shap-bar-track">
                    <div class="shap-bar-center"></div>
                    <div class="shap-bar-fill ${isPos ? "positive" : "negative"}" style="width: ${pct}%"></div>
                </div>
                <span class="shap-impact ${isPos ? "pos" : "neg"}">${isPos ? "+" : "-"}${Math.abs(r.impact).toFixed(3)}</span>
            </div>
        `;
    }).join("");

    // Recommendations
    const recsContainer = document.getElementById("recs-list");
    recsContainer.innerHTML = (data.recommendations || []).map(r => `
        <div class="rec-card">
            <div class="rec-head">
                <span class="rec-icon">${r.icon}</span>
                <span class="rec-action">${r.action}</span>
                <span class="rec-priority ${r.priority}">${r.priority}</span>
            </div>
            <p class="rec-detail">${r.detail}</p>
            <button class="rec-btn" onclick="handleMerchantAction('${r.merchant_action}', '${data.txn_id}')">
                Apply Action ${r.icon}
            </button>
        </div>
    `).join("");

    if (window.innerWidth < 960) live.scrollIntoView({ behavior: "smooth", block: "nearest" });
    loadAuditLog();
}

// 1-Click Copy WhatsApp
document.getElementById("btn-copy-wa")?.addEventListener("click", () => {
    const text = document.getElementById("wa-bubble").textContent;
    navigator.clipboard.writeText(text).then(() => {
        const btn = document.getElementById("btn-copy-wa");
        btn.textContent = "Copied! ✓";
        setTimeout(() => btn.textContent = "Copy Message", 2000);
    });
});

// Copy Webhook URL
document.getElementById("copy-endpoint-btn")?.addEventListener("click", () => {
    const url = document.getElementById("live-webhook-url").textContent;
    navigator.clipboard.writeText(url).then(() => {
        const btn = document.getElementById("copy-endpoint-btn");
        btn.textContent = "Copied! ✓";
        setTimeout(() => btn.textContent = "Copy URL", 2000);
    });
});

function handleMerchantAction(action, txnId) {
    alert(`⚡ Razorpay Action "${action}" Triggered for Order ${txnId}!\n\nPayload sent to Razorpay Rules Engine to adjust checkout constraints or dispatch WhatsApp verification.`);
}

// ============ WEBHOOK SIMULATOR ============

document.getElementById("simulate-webhook")?.addEventListener("click", async () => {
    const btn = document.getElementById("simulate-webhook");
    btn.textContent = "Processing...";
    btn.style.pointerEvents = "none";

    try {
        const res = await fetch(`${API_BASE}/api/webhook/simulate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ event_type: "payment.authorized" })
        });
        const data = await res.json();
        showWebhookResult(data);
    } catch (err) {
        console.error("Webhook simulation failed:", err);
    }

    btn.innerHTML = `Fire Simulated Webhook <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`;
    btn.style.pointerEvents = "auto";
});

function showWebhookResult(data) {
    document.getElementById("webhook-result").classList.remove("hidden");

    const r = data.risk_assessment;
    const payload = data.webhook_payload || {};
    const paymentEntity = payload.payload?.payment?.entity || {};
    const amtINR = Number(paymentEntity.amount || r.amount * 100) / 100;
    const method = (paymentEntity.method || r.payment_method || "UPI").toUpperCase();
    const txnId = paymentEntity.id || r.txn_id || "WH-XXXXX";
    const eventType = payload.event || "payment.authorized";
    const riskLevel = r.risk_level;
    const riskScore = r.risk_score;
    const action = r.action;

    // ── Story Flow ──
    document.getElementById("wh-s1-detail").textContent =
        `${method} • ₹${amtINR.toLocaleString("en-IN")} • ${eventType}`;
    document.getElementById("wh-s2-detail").textContent =
        `Score: ${riskScore} → ${riskLevel} RISK`;
    document.getElementById("wh-s3-icon").textContent =
        riskLevel === "HIGH" ? "🚫" : riskLevel === "MEDIUM" ? "⚠️" : "✅";
    document.getElementById("wh-s3-detail").textContent =
        action === "BLOCK_COD" ? "COD Blocked — Switch to Prepaid" :
        action === "MANUAL_REVIEW" ? "Flagged for manual audit" :
        action === "PASS" ? "Fast-Track fulfillment approved" :
        `Action: ${action}`;

    // ── Info Cards ──
    document.getElementById("wh-card-amount").textContent = `₹${amtINR.toLocaleString("en-IN")}`;
    document.getElementById("wh-card-method").textContent = method;
    document.getElementById("wh-card-txn").textContent = txnId;
    document.getElementById("wh-card-event").textContent = eventType;

    // ── Risk Circle ──
    const circle = document.getElementById("wh-risk-circle");
    circle.className = `wh-risk-score-circle ${riskLevel}`;
    document.getElementById("wh-risk-score-val").textContent = riskScore;

    const levelLabel = document.getElementById("wh-risk-level-label");
    levelLabel.textContent = `${riskLevel} RISK`;
    levelLabel.className = `wh-risk-level ${riskLevel}`;
    document.getElementById("wh-risk-action-tag").textContent = `→ Action: ${action}`;

    // ── Notes Injected ──
    const notesGrid = document.getElementById("wh-notes-grid");
    const notes = {
        "risk_level": riskLevel,
        "risk_score": riskScore,
        "returnguard_verdict": action === "PASS" ? "PASS" : "BLOCK",
        "recommended_action": action
    };
    notesGrid.innerHTML = Object.entries(notes).map(([k, v]) =>
        `<div class="wh-note-tag"><span class="wh-note-key">${k}:</span><span class="wh-note-val">"${v}"</span></div>`
    ).join("");

    // ── Merchant Interventions ──
    const assessmentEl = document.getElementById("wh-assessment");
    if (r.recommendations?.length) {
        assessmentEl.innerHTML = `
            <div style="font-size:0.72rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.07em;margin-bottom:0.75rem;">
                Injected Merchant Interventions
            </div>
            ${r.recommendations.slice(0, 2).map(rec => `
                <div class="rec-card" style="margin-bottom:0.5rem">
                    <div class="rec-head">
                        <span class="rec-icon">${rec.icon}</span>
                        <span class="rec-action">${rec.action}</span>
                        <span class="rec-priority ${rec.priority}">${rec.priority.toUpperCase()}</span>
                    </div>
                    <p class="rec-detail">${rec.detail}</p>
                </div>
            `).join("")}
        `;
    } else {
        assessmentEl.innerHTML = "";
    }

    loadAuditLog();

    // Scroll to result
    document.getElementById("webhook-result").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// ============ CHECKOUT SIMULATOR ============

let ckDerivedTier = "Tier-2";
const ckPinInput = document.getElementById("ck-pincode");
const ckPinMeta = document.getElementById("ck-pin-meta");
const ckState = document.getElementById("ck-state");
const ckDistrict = document.getElementById("ck-district");

if (ckPinInput) {
    ckPinInput.addEventListener("input", async () => {
        const pin = ckPinInput.value.trim();
        if (!/^\d{6}$/.test(pin)) {
            if (ckState) ckState.value = "";
            if (ckDistrict) ckDistrict.value = "";
            ckPinMeta.innerHTML = "";
            ckDerivedTier = "Tier-2";
            return;
        }
        ckPinMeta.innerHTML = `<span class="pin-loading">Looking up...</span>`;
        try {
            const res = await fetch(`${API_BASE}/api/pincode/${pin}`);
            const data = await res.json();
            if (data[0].Status === "Success" && data[0].PostOffice && data[0].PostOffice.length > 0) {
                const offices = data[0].PostOffice;
                const state = offices[0].State;
                const district = offices[0].District;
                if (ckState) ckState.value = state;
                if (ckDistrict) ckDistrict.value = district;
                ckDerivedTier = classifyTier(pin, district, offices);
                const tierClass = ckDerivedTier.toLowerCase().replace("-", "");
                ckPinMeta.innerHTML = `<span class="pin-tier-chip tier-${tierClass}">${ckDerivedTier}</span><span class="pin-offices">📍 ${district}, ${state} &bull; ${offices.length} post offices</span>`;
            } else {
                if (ckState) ckState.value = "";
                if (ckDistrict) ckDistrict.value = "";
                ckDerivedTier = "Tier-2";
                ckPinMeta.innerHTML = `<span class="pin-error">Invalid pincode</span>`;
            }
        } catch {
            ckDerivedTier = METRO_PREFIXES.includes(pin.slice(0, 3)) ? "Metro" : "Tier-2";
            ckPinMeta.innerHTML = `<span class="pin-error">Offline — tier estimated</span>`;
        }
    });
}



async function runCheckoutSimulation(customPaymentMethod = null) {
    const tier = document.getElementById("ck-tier").value;
    const paymentMethod = customPaymentMethod || document.getElementById("ck-payment").value;

    const payload = {
        amount: parseFloat(document.getElementById("ck-amount").value) || 12000,
        payment_method: paymentMethod,
        customer_tier: tier,
        address_match: document.getElementById("ck-address").value,
        pincode_tier: ckDerivedTier,
        category: "Electronics",
        device: "Mobile",
        state: ckState.value || "Karnataka"
    };

    try {
        const res = await fetch(`${API_BASE}/api/checkout/simulate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        showCheckoutPreview(data);
    } catch (err) {
        console.error("Checkout simulation failed:", err);
    }
}

document.getElementById("run-checkout")?.addEventListener("click", () => runCheckoutSimulation());
document.getElementById("ck-payment")?.addEventListener("change", (e) => runCheckoutSimulation(e.target.value));

let currentCheckoutData = null;

function showCheckoutPreview(data) {
    currentCheckoutData = data;
    document.getElementById("checkout-preview").classList.remove("hidden");
    const ui = data.checkout_ui;
    const r = data.risk_result;
    const txn = data.transaction;
    const isPrepaid = txn.payment_method !== "COD";

    document.getElementById("ck-amount-display").textContent = "₹" + Number(txn.amount).toLocaleString("en-IN");

    const badge = document.getElementById("ck-risk-badge");
    if (isPrepaid) {
        badge.textContent = "PREPAID VERIFIED (LOW RISK)";
        badge.className = "ck-risk-badge LOW";
    } else {
        badge.textContent = r.risk_level + " RISK (COD)";
        badge.className = "ck-risk-badge " + r.risk_level;
    }

    document.getElementById("ck-message").textContent = ui.ui_message;

    const methods = document.getElementById("ck-methods");
    methods.innerHTML = `
        <div class="ck-method ${txn.payment_method === 'UPI' ? 'selected' : ''}" onclick="selectPhonePayment('UPI')">
            <div class="ck-method-info">
                <span class="ck-method-icon">⚡</span>
                <span class="ck-method-name">Razorpay UPI ${txn.payment_method === 'UPI' ? '✓' : ''}</span>
            </div>
            <span class="ck-method-status ok">Instant (₹200 Off)</span>
        </div>
        <div class="ck-method ${txn.payment_method === 'Credit Card' ? 'selected' : ''}" onclick="selectPhonePayment('Credit Card')">
            <div class="ck-method-info">
                <span class="ck-method-icon">💳</span>
                <span class="ck-method-name">Cards (Visa/Mastercard) ${txn.payment_method === 'Credit Card' ? '✓' : ''}</span>
            </div>
            <span class="ck-method-status ok">Instant</span>
        </div>
        <div class="ck-method ${!ui.cod_enabled ? 'disabled' : ''} ${txn.payment_method === 'COD' ? 'selected' : ''}" onclick="${ui.cod_enabled ? "selectPhonePayment('COD')" : "alert('COD is disabled due to high return risk for this order. Please use UPI for instant approval & ₹200 off.')"}">
            <div class="ck-method-info">
                <span class="ck-method-icon">💵</span>
                <span class="ck-method-name">Cash on Delivery</span>
            </div>
            <span class="ck-method-status ${ui.cod_enabled ? 'ok' : 'blocked'}">${ui.cod_message}</span>
        </div>
    `;

    const discount = document.getElementById("ck-discount");
    if (ui.discount_offer && txn.payment_method === "UPI") {
        discount.innerHTML = `<span class="ck-discount-offer">🎉 Razorpay UPI Discount: ₹${ui.discount_offer.amount} off applied!</span>`;
    } else if (!ui.cod_enabled && txn.payment_method === "COD") {
        discount.innerHTML = `<span class="ck-discount-offer" style="background: rgba(251,113,133,0.15); border-color: rgba(251,113,133,0.3); color: #fda4af;">⚠️ COD is restricted. Switch to UPI to get ₹200 OFF!</span>`;
    } else {
        discount.innerHTML = "";
    }

    // Reset overlay
    const overlay = document.getElementById("ck-pay-overlay");
    overlay.classList.add("hidden");
    const spinner = overlay.querySelector(".ck-pay-spinner");
    spinner.className = "ck-pay-spinner";
    const status = document.getElementById("ck-pay-status");
    status.className = "ck-pay-status";
    status.textContent = "Processing...";

    loadAuditLog();
}

window.selectPhonePayment = function(method) {
    document.getElementById("ck-payment").value = method;
    runCheckoutSimulation(method);
};

// PAY NOW BUTTON ON PHONE MOCKUP
document.getElementById("ck-pay-btn")?.addEventListener("click", () => {
    const overlay = document.getElementById("ck-pay-overlay");
    const spinner = overlay.querySelector(".ck-pay-spinner");
    const status = document.getElementById("ck-pay-status");

    overlay.classList.remove("hidden");
    spinner.className = "ck-pay-spinner";
    status.className = "ck-pay-status";
    status.textContent = "Processing with Razorpay...";

    const currentMethod = currentCheckoutData ? currentCheckoutData.transaction.payment_method : "UPI";
    const isCod = currentMethod === "COD";
    const codEnabled = currentCheckoutData ? currentCheckoutData.checkout_ui.cod_enabled : true;

    if (isCod && !codEnabled) {
        // High risk COD blocked
        setTimeout(() => {
            spinner.className = "ck-pay-spinner failed";
            status.className = "ck-pay-status failed";
            status.textContent = "COD Restricted\nHigh return probability detected.\nTap 'Razorpay UPI' above for ₹200 off!";
        }, 1200);
    } else if (isCod && currentCheckoutData?.risk_result?.risk_level === "MEDIUM") {
        // Medium risk COD requires OTP
        setTimeout(() => { status.textContent = "Sending WhatsApp OTP..."; }, 800);
        setTimeout(() => { status.textContent = "OTP Verified ✓"; }, 2000);
        setTimeout(() => {
            spinner.className = "ck-pay-spinner success";
            status.className = "ck-pay-status success";
            status.textContent = "COD Order Verified!\nScheduled for Dispatch.";
        }, 3200);
    } else {
        // Prepaid (UPI / Card) instant pass
        setTimeout(() => {
            spinner.className = "ck-pay-spinner success";
            status.className = "ck-pay-status success";
            status.textContent = `Payment Successful! ✓\nPaid via ${currentMethod}\nReturnGuard Risk Cleared.`;
        }, 1200);
    }
});

// ============ OFFICIAL RAZORPAY CHECKOUT MODAL ============

const rzpModal = document.getElementById("rzp-modal");
const rzpModalClose = document.getElementById("rzp-modal-close");

function closeRazorpayModal() {
    if (rzpModal) rzpModal.classList.add("hidden");
    const procOverlay = document.getElementById("modal-processing");
    if (procOverlay) {
        procOverlay.classList.add("hidden");
        procOverlay.style.display = "none";
    }
    // Reset pipeline for next open
    if (typeof resetPipelineSteps === "function") {
        try { resetPipelineSteps(); } catch(_) {}
    }
}

rzpModalClose?.addEventListener("click", closeRazorpayModal);

rzpModal?.addEventListener("click", (e) => {
    if (e.target === rzpModal) closeRazorpayModal();
});

document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && rzpModal && !rzpModal.classList.contains("hidden")) {
        closeRazorpayModal();
    }
});

document.getElementById("launch-real-rzp")?.addEventListener("click", async () => {
    const amt = parseFloat(document.getElementById("ck-amount").value) || 12000;
    const tier = document.getElementById("ck-tier").value;
    const addr = document.getElementById("ck-address").value;
    
    // Evaluate current order parameters
    const payload = {
        amount: amt,
        payment_method: "COD",
        customer_tier: tier,
        address_match: addr,
        pincode_tier: ckDerivedTier,
        category: "Electronics",
        device: "Mobile",
        state: ckState.value || "Karnataka"
    };

    let isCodBlocked = false;
    try {
        const res = await fetch(`${API_BASE}/api/checkout/simulate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        isCodBlocked = !data.checkout_ui.cod_enabled;
    } catch (e) {
        isCodBlocked = false;
    }

    // Reset processing state BEFORE showing modal
    const procOverlay = document.getElementById("modal-processing");
    if (procOverlay) {
        procOverlay.classList.add("hidden");
        procOverlay.style.display = "none";
    }
    const spinner = document.getElementById("modal-spinner");
    if (spinner) spinner.className = "rzp-spinner";

    // Open Modal
    rzpModal.classList.remove("hidden");
    document.getElementById("modal-amount").textContent = "₹" + amt.toLocaleString("en-IN");
    document.getElementById("modal-pay-amt").textContent = "₹" + amt.toLocaleString("en-IN");

    const riskPill = document.getElementById("modal-risk-pill");
    const codOpt = document.getElementById("opt-cod");
    const codBadge = document.getElementById("modal-cod-badge");
    const codDesc = document.getElementById("modal-cod-desc");
    const discountBox = document.getElementById("modal-discount-box");

    if (isCodBlocked) {
        if (riskPill) {
            riskPill.textContent = "⚠️ High Return Risk (COD Gated)";
            riskPill.className = "rzp-risk-pill high-risk";
        }
        if (codOpt) codOpt.classList.add("disabled");
        if (codBadge) {
            codBadge.textContent = "Disabled (Risk)";
            codBadge.className = "rzp-opt-badge blocked";
        }
        if (codDesc) codDesc.textContent = "Disabled due to high return probability";
        if (discountBox) discountBox.classList.remove("hidden");
    } else {
        if (riskPill) {
            riskPill.textContent = "🛡️ ReturnGuard AI Verified";
            riskPill.className = "rzp-risk-pill";
        }
        if (codOpt) codOpt.classList.remove("disabled");
        if (codBadge) {
            codBadge.textContent = "Available";
            codBadge.className = "rzp-opt-badge green";
        }
        if (codDesc) codDesc.textContent = "Pay upon physical delivery";
        if (discountBox) discountBox.classList.remove("hidden");
    }
});

// Modal payment option selection
document.querySelectorAll(".rzp-method-option").forEach(opt => {
    opt.addEventListener("click", () => {
        if (opt.classList.contains("disabled")) return;
        document.querySelectorAll(".rzp-method-option").forEach(o => o.classList.remove("active"));
        opt.classList.add("active");
        opt.querySelector("input").checked = true;
    });
});

// ---- Pipeline Trace Helpers ----
function pipelineStepActive(n) {
    const ind = document.getElementById(`step-${n}-icon`);
    const step = document.getElementById(`step-${n}`);
    if (!ind || !step) return;
    step.classList.add("active");
    ind.className = "rzp-step-indicator";
    ind.innerHTML = `<div class="rzp-step-spinner"></div>`;
}

function pipelineStepDone(n, detail) {
    const ind = document.getElementById(`step-${n}-icon`);
    const step = document.getElementById(`step-${n}`);
    const det = document.getElementById(`step-${n}-detail`);
    const conn = document.getElementById(`conn-${n}`);
    if (ind) { ind.className = "rzp-step-indicator done"; ind.innerHTML = ""; }
    if (step) { step.classList.remove("active"); step.classList.add("done"); }
    if (det && detail) det.textContent = detail;
    if (conn) conn.classList.add("done");
}

function pipelineStepFailed(n, detail) {
    const ind = document.getElementById(`step-${n}-icon`);
    const step = document.getElementById(`step-${n}`);
    const det = document.getElementById(`step-${n}-detail`);
    const conn = document.getElementById(`conn-${n - 1}`);
    if (ind) { ind.className = "rzp-step-indicator failed-ind"; ind.innerHTML = ""; }
    if (step) { step.classList.remove("active"); step.classList.add("failed"); }
    if (det && detail) det.textContent = detail;
    if (conn) conn.classList.add("failed");
}

function resetPipelineSteps() {
    [1,2,3,4].forEach(n => {
        const ind = document.getElementById(`step-${n}-icon`);
        const step = document.getElementById(`step-${n}`);
        const det = document.getElementById(`step-${n}-detail`);
        const conn = document.getElementById(`conn-${n}`);
        if (step) step.className = "rzp-step";
        if (ind) { ind.className = n === 1 ? "rzp-step-indicator" : "rzp-step-indicator waiting"; ind.innerHTML = n === 1 ? `<div class="rzp-step-spinner"></div>` : `<span class="rzp-step-num">${n}</span>`; }
        if (conn) conn.className = "rzp-step-connector";
    });
    document.getElementById("step-1-detail").textContent = "Validating cart & shipping address";
    document.getElementById("step-2-detail").textContent = "Scoring 12 risk signals via ML model";
    document.getElementById("step-3-detail").textContent = "Razorpay encrypting transaction";
    document.getElementById("step-4-detail").textContent = "Awaiting issuer acknowledgement";
    document.getElementById("pipeline-failure-card")?.classList.add("hidden");
    document.getElementById("pipeline-success-card")?.classList.add("hidden");
    document.getElementById("pipeline-icon").textContent = "⏳";
    document.getElementById("pipeline-title").textContent = "Processing Transaction";
    document.getElementById("pipeline-sub").textContent = "Authenticating with Razorpay gateway...";
}

// Modal Pay Button Action — Full Pipeline Trace
document.getElementById("modal-pay-btn")?.addEventListener("click", async () => {
    const procOverlay = document.getElementById("modal-processing");
    if (!procOverlay) return;

    // Show overlay with pipeline
    procOverlay.classList.remove("hidden");
    procOverlay.style.display = "flex";
    resetPipelineSteps();

    const activeOpt = document.querySelector(".rzp-method-option.active");
    const selectedMethod = activeOpt ? activeOpt.id : "opt-upi";
    const isCodSelected = selectedMethod === "opt-cod";
    const isCodDisabled = activeOpt && activeOpt.classList.contains("disabled");
    const amt = parseFloat(document.getElementById("ck-amount")?.value || document.getElementById("modal-amount")?.textContent?.replace(/[^\d]/g, "") || 12000);
    const tier = document.getElementById("ck-tier")?.value || "New";
    const discount = Math.max(200, Math.round(amt * 0.02));

    // STEP 1 — Order Submitted
    pipelineStepActive(1);
    await new Promise(r => setTimeout(r, 700));
    pipelineStepDone(1, "Cart validated · Address confirmed");

    // STEP 2 — Risk Engine
    pipelineStepActive(2);
    await new Promise(r => setTimeout(r, 900));

    // If COD is blocked → fail at step 2
    if (isCodSelected && isCodDisabled) {
        // Fetch real failure reasons from backend
        let failureReasons = [
            `High-value COD order (₹${amt.toLocaleString("en-IN")}) — RTO loss risk`,
            `Customer tier: ${tier} — unverified payment history`,
            `COD blocked by ReturnGuard AI Risk Policy`
        ];
        try {
            const addr = document.getElementById("ck-address")?.value || "Different from billing";
            const res = await fetch(`${API_BASE}/api/checkout/simulate`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ amount: amt, payment_method: "COD", customer_tier: tier, address_match: addr, pincode_tier: ckDerivedTier || "Tier-2" })
            });
            const d = await res.json();
            if (d.risk_result?.reasons?.length) {
                failureReasons = d.risk_result.reasons.slice(0, 3).map(r => r.text || r);
            }
            if (d.risk_result?.shap_reasons?.length) {
                failureReasons = d.risk_result.shap_reasons.slice(0, 3).map(r => r.text);
            }
        } catch(_) {}

        pipelineStepFailed(2, `BLOCKED — Risk Score too high for COD`);

        // Update header
        document.getElementById("pipeline-icon").textContent = "🚫";
        document.getElementById("pipeline-title").textContent = "COD Blocked by Risk Engine";
        document.getElementById("pipeline-sub").textContent = "ReturnGuard AI intercepted this transaction";

        // Show failure card with reasons
        await new Promise(r => setTimeout(r, 300));
        const failCard = document.getElementById("pipeline-failure-card");
        const reasonsList = document.getElementById("pipeline-failure-reasons");
        const discLabel = document.getElementById("pipeline-discount-label");
        if (reasonsList) {
            reasonsList.innerHTML = failureReasons.map(r => `<li>${r}</li>`).join("");
        }
        if (discLabel) discLabel.textContent = `₹${discount}`;
        if (failCard) failCard.classList.remove("hidden");
        return;
    }

    // Risk passed
    const methodLabel = selectedMethod === "opt-upi" ? "UPI" : selectedMethod === "opt-card" ? "Card" : "NetBanking";
    pipelineStepDone(2, `VERIFIED — Prepaid ${methodLabel} · Zero RTO risk`);

    // STEP 3 — Gateway Auth
    pipelineStepActive(3);
    await new Promise(r => setTimeout(r, 800));
    pipelineStepDone(3, "TLS 1.3 · 256-bit AES · Token generated");

    // STEP 4 — Bank Confirmation
    pipelineStepActive(4);
    await new Promise(r => setTimeout(r, 900));
    pipelineStepDone(4, selectedMethod === "opt-upi" ? "UPI debit confirmed by NPCI" : "Issuer approved · Auth code received");

    // Show success
    document.getElementById("pipeline-icon").textContent = "✅";
    document.getElementById("pipeline-title").textContent = "Payment Confirmed!";
    document.getElementById("pipeline-sub").textContent = "Transaction settled with Razorpay";

    const payId = `pay_rzp_${Math.random().toString(36).substring(2, 9)}`;
    document.getElementById("pipeline-pay-id").textContent = payId;
    document.getElementById("pipeline-success-card")?.classList.remove("hidden");

    await new Promise(r => setTimeout(r, 2200));
    closeRazorpayModal();
    loadAuditLog();
});

// "Switch to UPI" inside failure card
document.getElementById("pipeline-switch-upi")?.addEventListener("click", () => {
    closeRazorpayModal();
    // Switch to UPI in the checkout form and re-open modal
    const ckPayment = document.getElementById("ck-payment");
    if (ckPayment) ckPayment.value = "UPI";
    document.getElementById("launch-real-rzp")?.click();
});

// ============ BATCH SCORING ============

let batchData = null;

document.getElementById("run-batch-btn")?.addEventListener("click", async () => {
    const btn = document.getElementById("run-batch-btn");
    btn.textContent = "Scoring 10,000 Records...";
    btn.style.pointerEvents = "none";

    try {
        const res = await fetch(`${API_BASE}/api/score-batch`);
        batchData = await res.json();
        showBatchResults(batchData);
    } catch (err) {
        console.error("Batch scoring failed:", err);
    }

    btn.innerHTML = `Run Batch Analysis <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polygon points="5 3 19 12 5 21 5 3"/></svg>`;
    btn.style.pointerEvents = "auto";
});

function showBatchResults(data) {
    document.getElementById("batch-results").classList.remove("hidden");
    animateInt(document.getElementById("b-total"), data.total);
    animateInt(document.getElementById("b-flagged"), data.flagged);
    animateInt(document.getElementById("b-passed"), data.passed);
    document.getElementById("b-blocked").textContent = "₹" + Math.round(data.blocked_value).toLocaleString("en-IN");
    document.getElementById("b-review").textContent = "₹" + Math.round(data.review_value).toLocaleString("en-IN");

    const sorted = [...data.results].sort((a, b) => b.risk_score - a.risk_score);
    const tbody = document.getElementById("batch-tbody");
    tbody.innerHTML = sorted.slice(0, 100).map(r => {
        const topReason = r.shap_reasons && r.shap_reasons.length ? r.shap_reasons[0].text : "—";
        return `<tr>
            <td>${r.txn_id}</td><td>₹${Number(r.amount).toLocaleString("en-IN")}</td>
            <td><span class="score-pill ${r.risk_level}">${r.risk_score}</span></td>
            <td><span class="score-pill ${r.risk_level}">${r.risk_level}</span></td>
            <td><span class="action-mini ${r.action}">${r.action}</span></td>
            <td class="reason-cell">${topReason}</td>
        </tr>`;
    }).join("");
    loadAuditLog();
}

document.getElementById("download-csv")?.addEventListener("click", () => {
    if (!batchData) return;
    const headers = ["txn_id", "amount", "risk_score", "risk_level", "action", "top_shap_factor"];
    const rows = batchData.results.map(r => [
        r.txn_id, r.amount, r.risk_score, r.risk_level, r.action,
        r.shap_reasons && r.shap_reasons.length ? r.shap_reasons[0].text.replace(/,/g, " ") : ""
    ]);
    const csv = [headers.join(","), ...rows.map(r => r.join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "returnguard_batch_scores.csv"; a.click();
    URL.revokeObjectURL(url);
});

// ============ AUDIT LOG ============

async function loadAuditLog() {
    try {
        const res = await fetch(`${API_BASE}/api/audit-log`);
        const data = await res.json();
        const list = document.getElementById("audit-list");
        if (!data.decisions || !data.decisions.length) {
            list.innerHTML = `<div class="audit-empty">No decisions logged yet. Test a scenario or score a transaction above.</div>`;
            return;
        }
        list.innerHTML = data.decisions.slice(0, 30).map(d => {
            const time = new Date(d.timestamp).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
            const badge = d.type === "batch" ? "BATCH" : d.type === "razorpay_webhook" ? "RZP" : d.type === "simulated_webhook" ? "WH" : d.risk_level || "TXN";
            const badgeClass = d.risk_level || "BATCH";
            return `
                <div class="audit-item">
                    <div class="audit-badge ${badgeClass}">${badge}</div>
                    <div class="audit-main">
                        <div class="audit-title">${d.txn_id} — ₹${Number(d.amount).toLocaleString("en-IN")} <span class="audit-action-tag">${d.action}</span></div>
                        <div class="audit-reasons">${(d.reasons || []).join(" · ")}</div>
                    </div>
                    <span class="audit-time">${time}</span>
                </div>
            `;
        }).join("");
    } catch (err) {
        console.error("Audit log failed:", err);
    }
}

document.getElementById("clear-audit-btn")?.addEventListener("click", async () => {
    if (!confirm("Are you sure you want to clear the audit log?")) return;
    try {
        await fetch(`${API_BASE}/api/audit-log/clear`, { method: "POST" });
        loadAuditLog();
    } catch (e) {
        console.error("Clear log failed:", e);
    }
});

// ============ SCROLL REVEAL ============

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = "1";
            entry.target.style.transform = "translateY(0)";
        }
    });
}, { threshold: 0.1 });

document.querySelectorAll(".m-card, .chart-card, .cost-card, .step-card").forEach(el => {
    el.style.opacity = "0";
    el.style.transform = "translateY(16px)";
    el.style.transition = "opacity 0.6s ease, transform 0.6s ease";
    observer.observe(el);
});

// Redraw chart when tuner section scrolls into view
const tunerSection = document.getElementById("tuner");
if (tunerSection) {
    const chartRedrawObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && thresholdCurve.length) {
                drawCurveChart(thresholdCurve);
            }
        });
    }, { threshold: 0.2 });
    chartRedrawObserver.observe(tunerSection);
}

// ============ INIT ============

loadMetrics();
loadAuditLog();

// ============ JARVIS AI CHATBOT ============
(function() {
    const bubble = document.getElementById("jarvis-bubble");
    const windowEl = document.getElementById("jarvis-window");
    const closeBtn = document.getElementById("jarvis-close");
    const form = document.getElementById("jarvis-form");
    const input = document.getElementById("jarvis-input");
    const messages = document.getElementById("jarvis-messages");

    if (!bubble || !windowEl || !closeBtn || !form || !input || !messages) return;

    bubble.addEventListener("click", () => {
        windowEl.classList.toggle("hidden");
        const tooltip = document.getElementById("jarvis-tooltip");
        if (!windowEl.classList.contains("hidden")) {
            input.focus();
            messages.scrollTop = messages.scrollHeight;
            if (tooltip) tooltip.classList.add("hidden");
        } else {
            if (tooltip) tooltip.classList.remove("hidden");
        }
    });

    closeBtn.addEventListener("click", () => {
        windowEl.classList.add("hidden");
        const tooltip = document.getElementById("jarvis-tooltip");
        if (tooltip) tooltip.classList.remove("hidden");
    });

    function appendMessage(text, sender) {
        const msg = document.createElement("div");
        msg.className = "msg " + sender;
        msg.textContent = text;
        messages.appendChild(msg);
        messages.scrollTop = messages.scrollHeight;
        return msg;
    }

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (!text) return;

        input.value = "";
        appendMessage(text, "user");

        // Append typing placeholder
        const typingMsg = appendMessage("Thinking...", "bot typing");
        typingMsg.classList.add("typing");

        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text })
            });
            const data = await res.json();
            
            // Remove typing class and update content
            typingMsg.classList.remove("typing");
            typingMsg.textContent = data.response || "Sorry, I encountered an issue processing that query.";
        } catch (error) {
            typingMsg.classList.remove("typing");
            typingMsg.textContent = "Offline. Please ensure the backend is running.";
        }
        messages.scrollTop = messages.scrollHeight;
    });
})();

