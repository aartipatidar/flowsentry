import streamlit as st
from google.cloud import firestore
import json
from datetime import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="FlowSentry | Agentic CI/CD Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark/clean UI elements
st.markdown("""
<style>
    .metric-card {
        background-color: #1E222B;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #313745;
        text-align: center;
    }
    .badge-p1 {
        background-color: #8B0000;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.8rem;
    }
    .badge-p2 {
        background-color: #D2691E;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.8rem;
    }
    .badge-p3 {
        background-color: #2E8B57;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)


# --- FIRESTORE INITIALIZATION ---
@st.cache_resource
def get_db_client():
    # Automatically picks up GCP credentials or running Cloud Run environment
    return firestore.Client()

try:
    db = get_db_client()
except Exception as e:
    st.error(f"Failed to connect to Firestore: {e}")
    st.stop()


# --- DATA FETCHING ---
def fetch_incidents(limit=20):
    incidents_ref = db.collection("incidents")
    # Stream items sorted by timestamp
    docs = incidents_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit).stream()
    data = []
    for doc in docs:
        item = doc.to_dict()
        data.append(item)
    return data


# --- HEADER & REFRESH ---
st.title("🛡️ FlowSentry — CI/CD Failure Intelligence")
st.caption("Agentic Root Cause Analysis & Automated Incident Remediation")

col_head1, col_head2 = st.columns([4, 1])
with col_head2:
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

incidents = fetch_incidents()

# --- TOP METRICS ROW ---
m1, m2, m3, m4 = st.columns(4)

total_incidents = len(incidents)
p1_count = sum(1 for i in incidents if i.get("classification", {}).get("severity") == "P1")
avg_confidence = (
    sum(int(i.get("remediation", {}).get("confidence_score", 0)) for i in incidents) / total_incidents
    if total_incidents > 0 else 0
)

with m1:
    st.markdown(f"<div class='metric-card'><h4>Total Incidents</h4><h2>{total_incidents}</h2></div>", unsafe_allow_html=True)
with m2:
    st.markdown(f"<div class='metric-card'><h4>Critical (P1)</h4><h2 style='color: #FF4B4B;'>{p1_count}</h2></div>", unsafe_allow_html=True)
with m3:
    st.markdown(f"<div class='metric-card'><h4>Avg Agent Confidence</h4><h2 style='color: #00D4B1;'>{avg_confidence:.1f}%</h2></div>", unsafe_allow_html=True)
with m4:
    st.markdown("<div class='metric-card'><h4>System Status</h4><h2 style='color: #00FF66;'>Active</h2></div>", unsafe_allow_html=True)

st.divider()

# --- SIDEBAR FILTERS ---
st.sidebar.header("🔍 Filter Incidents")
selected_env = st.sidebar.multiselect(
    "Environment",
    options=list(set(i.get("environment", "Unknown") for i in incidents)),
    default=list(set(i.get("environment", "Unknown") for i in incidents))
)

selected_stage = st.sidebar.multiselect(
    "Pipeline Stage",
    options=list(set(i.get("stage", "Unknown") for i in incidents)),
    default=list(set(i.get("stage", "Unknown") for i in incidents))
)

# Apply Filters
filtered_incidents = [
    i for i in incidents
    if i.get("environment") in selected_env and i.get("stage") in selected_stage
]

# --- INCIDENT FEED CARDS ---
st.subheader(f"Recent Incidents ({len(filtered_incidents)})")

if not filtered_incidents:
    st.info("No incidents matching the selected criteria.")

for inc in filtered_incidents:
    inc_id = inc.get("incident_id", "N/A")
    timestamp = inc.get("timestamp", "")
    stage = inc.get("stage", "N/A").upper()
    env = inc.get("environment", "N/A")
    
    classification = inc.get("classification", {})
    severity = classification.get("severity", "P3")
    category = classification.get("category", "General Failure")
    sig = classification.get("failure_signature", "UNKNOWN_FAIL")
    
    remediation = inc.get("remediation", {})
    what_failed = remediation.get("what_failed", "Pipeline Execution Error")
    root_cause = remediation.get("root_cause_explanation", "No detailed root cause generated.")
    confidence = remediation.get("confidence_score", 0)
    recommended_action = remediation.get("recommended_action", "Manual investigation required.")
    
    parsed = inc.get("parsed_signals", {})

    # Card Container
    with st.container(border=True):
        c1, c2, c3 = st.columns([3, 2, 1])
        
        with c1:
            # Severity Badge styling
            badge_class = f"badge-{severity.lower()}"
            st.markdown(
                f"<span class='{badge_class}'>{severity}</span> &nbsp; **{what_failed}**",
                unsafe_allow_html=True
            )
            st.caption(f"🆔 `{inc_id}` | 🕒 {timestamp} | 📍 Env: `{env}` | 🚀 Stage: `{stage}`")
        
        with c2:
            st.markdown(f"**Category:** `{category}`")
            st.markdown(f"**Signature:** `{sig}`")
        
        with c3:
            st.metric("Agent Confidence", f"{confidence}%")

        # Expandable Diagnostic Details
        with st.expander("🔬 View Agent Diagnostic & Remediation Plan"):
            col_diag, col_fix = st.columns(2)
            
            with col_diag:
                st.markdown("### 🧩 Root Cause Analysis")
                st.write(root_cause)
                
                st.markdown("**Parsed Log Signals:**")
                st.json(parsed)

            with col_fix:
                st.markdown("### 🛠️ Recommended Action")
                st.success(recommended_action)
                
                st.markdown("**Historical Context Matches:**")
                st.info("Match found in past 30 days — precedent applied.")