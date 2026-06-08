"""
Orion Signals — Main Entry Point
----------------------------------
Login page + routing σε Entry ή Pro dashboard.

Τρέξε:
    python -m streamlit run app.py
"""

import streamlit as st
from auth import login, is_pro

st.set_page_config(
    page_title="Orion Signals",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=Inter:wght@300;400;500&display=swap');

#MainMenu, footer, header, .stDeployButton { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

.stApp {
    background: #080810;
    font-family: 'Inter', sans-serif;
}

.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background-image:
        radial-gradient(1px 1px at 10% 20%, rgba(255,255,255,0.4) 0%, transparent 100%),
        radial-gradient(1px 1px at 30% 60%, rgba(255,255,255,0.3) 0%, transparent 100%),
        radial-gradient(1px 1px at 50% 10%, rgba(255,255,255,0.5) 0%, transparent 100%),
        radial-gradient(1px 1px at 70% 80%, rgba(255,255,255,0.3) 0%, transparent 100%),
        radial-gradient(2px 2px at 60% 70%, rgba(124,58,237,0.6) 0%, transparent 100%),
        radial-gradient(2px 2px at 25% 35%, rgba(124,58,237,0.4) 0%, transparent 100%);
    pointer-events: none;
    z-index: 0;
}

.stApp::after {
    content: '';
    position: fixed;
    top: -200px;
    left: 50%;
    transform: translateX(-50%);
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(124,58,237,0.15) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
}

.logo-container {
    text-align: center;
    margin-bottom: 2rem;
}

.logo-icon {
    font-size: 3.5rem;
    display: block;
    filter: drop-shadow(0 0 20px rgba(124,58,237,0.8));
}

.logo-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.8rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.02em;
    margin: 0;
    line-height: 1;
}

.logo-title span { color: #7C3AED; }

.logo-tagline {
    font-size: 0.85rem;
    color: rgba(255,255,255,0.35);
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-top: 0.5rem;
}

.stTextInput > div > div > input {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(124,58,237,0.3) !important;
    border-radius: 10px !important;
    color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
    padding: 0.75rem 1rem !important;
    font-size: 0.95rem !important;
    transition: all 0.2s !important;
}

.stTextInput > div > div > input:focus {
    border-color: rgba(124,58,237,0.8) !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.15) !important;
}

.stTextInput > div > div > input::placeholder {
    color: rgba(255,255,255,0.2) !important;
}

.stTextInput label {
    color: rgba(255,255,255,0.5) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}

.stButton > button {
    background: linear-gradient(135deg, #7C3AED, #5B21B6) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    width: 100% !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 20px rgba(124,58,237,0.4) !important;
    margin-top: 0.5rem !important;
}

.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 30px rgba(124,58,237,0.6) !important;
}

.footer {
    text-align: center;
    margin-top: 2rem;
    color: rgba(255,255,255,0.15);
    font-size: 0.72rem;
}
</style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.logged_in and st.session_state.user:
    user = st.session_state.user
    if is_pro(user):
        from pro_app import show_pro_dashboard
        show_pro_dashboard(user)
    else:
        from entry_app import show_entry_dashboard
        show_entry_dashboard(user)
    st.stop()

st.markdown("""
<div class="logo-container">
    <span class="logo-icon">🎯</span>
    <h1 class="logo-title">Orion <span>Signals</span></h1>
    <p class="logo-tagline">See through the noise</p>
</div>
""", unsafe_allow_html=True)

email = st.text_input("Email", placeholder="you@example.com")
password = st.text_input("Password", type="password", placeholder="••••••••")

if st.button("Σύνδεση →"):
    if not email or not password:
        st.error("Συμπλήρωσε email και password.")
    else:
        user = login(email, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.user = user
            st.rerun()
        else:
            st.error("❌ Λάθος email ή password.")

st.markdown("""
<div class="footer">
    © 2026 Orion Signals · Educational tool · Not financial advice
</div>
""", unsafe_allow_html=True)

