"""
Orion Signals — Disclaimer Module
-----------------------------------
Εμφανίζεται μετά το Sign Up και πριν το Dashboard.
Χωρίς database — session based.
"""

import streamlit as st
from datetime import datetime

DISCLAIMER_VERSION = "1.0"
DISCLAIMER_DATE = "2026-06-10"


def show_disclaimer():
    """
    Εμφανίζει τον disclaimer.
    Επιστρέφει True αν ο χρήστης αποδέχτηκε όλα.
    """

    st.markdown("""
    <style>
    .disclaimer-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .disclaimer-title {
        font-family: 'Syne', sans-serif;
        font-size: 1.6rem;
        font-weight: 800;
        color: #fff;
        margin-bottom: 0.5rem;
    }
    .disclaimer-subtitle {
        font-size: 0.85rem;
        color: rgba(255,255,255,0.4);
        letter-spacing: 0.05em;
    }
    .disclaimer-box {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(124,58,237,0.2);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        font-size: 0.85rem;
        color: rgba(255,255,255,0.6);
        line-height: 1.8;
        max-height: 220px;
        overflow-y: auto;
    }
    .disclaimer-box h4 {
        color: #A78BFA;
        font-size: 0.82rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
        margin-top: 1rem;
    }
    .disclaimer-box h4:first-child { margin-top: 0; }
    .disclaimer-box strong { color: rgba(255,255,255,0.8); }
    .version-badge {
        display: inline-block;
        background: rgba(124,58,237,0.15);
        border: 1px solid rgba(124,58,237,0.25);
        color: rgba(167,139,250,0.7);
        font-size: 0.68rem;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        margin-bottom: 1rem;
        letter-spacing: 0.08em;
    }
    .checks-section {
        margin-bottom: 1.5rem;
    }
    .checks-title {
        font-size: 0.75rem;
        color: rgba(255,255,255,0.35);
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 0.75rem;
    }
    /* Checkbox styling */
    .stCheckbox > label {
        color: rgba(255,255,255,0.65) !important;
        font-size: 0.83rem !important;
        line-height: 1.5 !important;
    }
    .stCheckbox > label > div[data-testid="stMarkdownContainer"] p {
        color: rgba(255,255,255,0.65) !important;
        font-size: 0.83rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown(f"""
    <div class="disclaimer-header">
        <div class="disclaimer-title">⚖️ Terms & Disclaimer</div>
        <div class="disclaimer-subtitle">Please read carefully before continuing</div>
    </div>
    <div class="version-badge">Version {DISCLAIMER_VERSION} · {DISCLAIMER_DATE}</div>
    """, unsafe_allow_html=True)

    # Disclaimer text box
    st.markdown("""
    <div class="disclaimer-box">
        <h4>1. Educational Tool Only</h4>
        Orion Signals is an <strong>educational and analytical tool</strong>.
        It does not provide investment advice, financial recommendations,
        or trading signals of any kind. All information displayed is for
        informational and educational purposes only.

        <h4>2. No Financial Advice</h4>
        Nothing on this platform constitutes financial, investment, legal,
        or tax advice. <strong>All trading decisions are made solely by you.</strong>
        Orion Signals and its creators bear no responsibility for any financial
        losses incurred as a result of using this platform.

        <h4>3. Risk of Loss</h4>
        Trading stocks, options, cryptocurrencies and other financial instruments
        involves <strong>significant risk of loss</strong>, including the possible
        loss of all capital invested. Past performance and backtested results
        do not guarantee future results.

        <h4>4. No Guarantee of Accuracy</h4>
        Technical analysis has inherent limitations. Signal scores, win rates,
        and indicators displayed are based on historical data and mathematical
        models. They may be inaccurate, incomplete, or delayed.
        <strong>Always conduct your own research.</strong>

        <h4>5. Your Responsibility</h4>
        You acknowledge that you are solely responsible for your trading decisions,
        risk management, and financial outcomes. You agree to use this platform
        at your own risk.

        <h4>6. Privacy & Data</h4>
        By creating an account, you agree to our Privacy Policy. We collect
        only the data necessary to provide the service. We do not sell your
        personal data to third parties.

        <h4>7. Restricted Jurisdictions</h4>
        This platform is not intended for use in jurisdictions where such tools
        are prohibited or restricted by law. It is your responsibility to ensure
        compliance with local regulations.
    </div>
    """, unsafe_allow_html=True)

    # Checkboxes
    st.markdown('<div class="checks-title">I confirm that:</div>', unsafe_allow_html=True)

    c1 = st.checkbox("I am 18 years of age or older")
    c2 = st.checkbox("I understand that Orion Signals is an **educational tool**, not a financial advisor")
    c3 = st.checkbox("I understand that trading involves **significant risk of loss**, including loss of all capital")
    c4 = st.checkbox("I acknowledge that **all trading decisions are mine alone** — Orion Signals bears no responsibility for my outcomes")
    c5 = st.checkbox("I understand that past performance and backtested results **do not guarantee future results**")
    c6 = st.checkbox("I confirm that using this platform is **legal in my jurisdiction**")
    c7 = st.checkbox("I have read and agree to the **Terms of Service** and **Privacy Policy**")

    all_checked = all([c1, c2, c3, c4, c5, c6, c7])

    st.markdown("<br>", unsafe_allow_html=True)

    if all_checked:
        if st.button("I Agree — Continue to Dashboard →", key="disclaimer_agree"):
            # Αποθήκευση στο session state
            st.session_state.disclaimer_accepted = True
            st.session_state.disclaimer_version = DISCLAIMER_VERSION
            st.session_state.disclaimer_timestamp = datetime.now().isoformat()
            return True
    else:
        st.button("Please check all boxes above to continue",
                  disabled=True, key="disclaimer_disabled")
        remaining = 7 - sum([c1, c2, c3, c4, c5, c6, c7])
        if remaining > 0:
            st.caption(f"⚠️ {remaining} confirmation{'s' if remaining > 1 else ''} remaining")

    return False
