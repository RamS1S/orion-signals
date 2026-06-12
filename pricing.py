"""
Orion Signals — Pricing Page
Εμφανίζεται μετά το disclaimer.
Ο χρήστης επιλέγει πλάνο και πηγαίνει στο dashboard.
"""
import streamlit as st
from styles import inject_logo

def show_pricing():
    inject_logo()

    st.markdown("""
    <style>
    .pricing-title {
        text-align: center;
        font-family: 'Syne', sans-serif;
        font-size: 1.4rem; font-weight: 800;
        color: #fff; margin-bottom: 0.3rem;
    }
    .pricing-sub {
        text-align: center;
        font-size: 0.82rem; color: rgba(255,255,255,0.4);
        margin-bottom: 2rem;
    }
    .plan-card {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px; padding: 1.5rem;
        transition: all 0.2s; margin-bottom: 0.75rem;
    }
    .plan-card.featured {
        border-color: rgba(124,58,237,0.5);
        background: rgba(124,58,237,0.06);
    }
    .plan-name {
        font-family: 'Syne', sans-serif;
        font-size: 1rem; font-weight: 800; color: #fff;
        margin-bottom: 0.2rem;
    }
    .plan-price {
        font-family: 'Syne', sans-serif;
        font-size: 1.8rem; font-weight: 800; color: #fff;
    }
    .plan-price span { font-size: 0.85rem; color: rgba(255,255,255,0.4); font-weight: 400; }
    .plan-desc { font-size: 0.78rem; color: rgba(255,255,255,0.45); margin: 0.5rem 0 1rem; line-height: 1.5; }
    .plan-features { font-size: 0.78rem; color: rgba(255,255,255,0.55); line-height: 2; }
    .feat-check { color: #00C853; }
    .feat-cross { color: rgba(255,255,255,0.2); }
    .popular-badge {
        display: inline-block;
        background: #7C3AED; color: #fff;
        font-size: 0.65rem; font-weight: 700;
        letter-spacing: 0.1em; text-transform: uppercase;
        padding: 0.15rem 0.6rem; border-radius: 10px;
        margin-left: 0.5rem; vertical-align: middle;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="pricing-title">Choose your plan</div>
    <div class="pricing-sub">Start with Entry and upgrade anytime</div>
    """, unsafe_allow_html=True)

    # ── PLAN 1: ENTRY ──
    with st.container():
        st.markdown("""
        <div class="plan-card">
            <div class="plan-name">Entry</div>
            <div class="plan-price">€29 <span>/ month</span></div>
            <div class="plan-desc">For traders who are learning the system.</div>
            <div class="plan-features">
                <span class="feat-check">✓</span> Stock scanner — top 10 daily<br>
                <span class="feat-check">✓</span> 13 technical indicators<br>
                <span class="feat-check">✓</span> Backtesting — 1 year<br>
                <span class="feat-check">✓</span> Portfolio tracker (max 5)<br>
                <span class="feat-check">✓</span> Telegram daily summary<br>
                <span class="feat-cross">–</span> ATR / SL / Target<br>
                <span class="feat-cross">–</span> Crypto scanner
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start with Entry →", key="pick_entry"):
            st.session_state.pending_user["plan"] = "entry"
            st.session_state.logged_in = True
            st.session_state.user = st.session_state.pending_user
            st.session_state.active_page = "login"
            st.rerun()

    # ── PLAN 2: PRO ──
    with st.container():
        st.markdown("""
        <div class="plan-card featured">
            <div class="plan-name">Pro <span class="popular-badge">Most Popular</span></div>
            <div class="plan-price">€79 <span>/ month</span></div>
            <div class="plan-desc">For serious traders who want every edge.</div>
            <div class="plan-features">
                <span class="feat-check">✓</span> Everything in Entry +<br>
                <span class="feat-check">✓</span> ATR / Entry / Stop Loss / Target<br>
                <span class="feat-check">✓</span> Fuel Gauge (exhaustion detector)<br>
                <span class="feat-check">✓</span> Earnings filter<br>
                <span class="feat-check">✓</span> Backtesting — 10 years<br>
                <span class="feat-check">✓</span> Unlimited portfolio<br>
                <span class="feat-check">✓</span> Telegram real-time alerts
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Get Pro →", key="pick_pro"):
            st.session_state.pending_user["plan"] = "pro"
            st.session_state.logged_in = True
            st.session_state.user = st.session_state.pending_user
            st.session_state.active_page = "login"
            st.rerun()

    # ── PLAN 3: CRYPTO ──
    with st.container():
        st.markdown("""
        <div class="plan-card">
            <div class="plan-name">Crypto</div>
            <div class="plan-price">€49 <span>/ month</span></div>
            <div class="plan-desc">For crypto-only traders.</div>
            <div class="plan-features">
                <span class="feat-check">✓</span> Crypto scanner (BTC, ETH + altcoins)<br>
                <span class="feat-check">✓</span> Fear & Greed Index<br>
                <span class="feat-check">✓</span> Funding Rate monitor<br>
                <span class="feat-check">✓</span> Exchange Inflow/Outflow<br>
                <span class="feat-check">✓</span> ATR / SL / Target<br>
                <span class="feat-check">✓</span> Telegram real-time alerts<br>
                <span class="feat-cross">–</span> Stock scanner
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Get Crypto →", key="pick_crypto"):
            st.session_state.pending_user["plan"] = "crypto"
            st.session_state.logged_in = True
            st.session_state.user = st.session_state.pending_user
            st.session_state.active_page = "login"
            st.rerun()

    # ── PLAN 4: COMBINED ──
    with st.container():
        st.markdown("""
        <div class="plan-card">
            <div class="plan-name">Pro + Crypto</div>
            <div class="plan-price">€150 <span>/ month</span></div>
            <div class="plan-desc">Everything — stocks and crypto combined.</div>
            <div class="plan-features">
                <span class="feat-check">✓</span> Everything in Pro +<br>
                <span class="feat-check">✓</span> Everything in Crypto +<br>
                <span class="feat-check">✓</span> Cross-market signals<br>
                <span class="feat-check">✓</span> Unified portfolio tracker<br>
                <span class="feat-check">✓</span> Priority support
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Get Pro + Crypto →", key="pick_combined"):
            st.session_state.pending_user["plan"] = "combined"
            st.session_state.logged_in = True
            st.session_state.user = st.session_state.pending_user
            st.session_state.active_page = "login"
            st.rerun()

    st.markdown("""
    <div class="login-footer">
        © 2026 Orion Signals · Educational tool · Not financial advice
    </div>
    """, unsafe_allow_html=True)
