"""
Orion Signals — Router
Κάνει μόνο routing — τίποτα άλλο.
"""
import streamlit as st
from auth import login, is_admin, is_pro, is_entry, is_crypto, is_combined, has_active_subscription
from styles import inject_background

# Wide layout για admin, centered για τους υπόλοιπους
_is_admin = st.session_state.get("user", {}) and st.session_state.get("user", {}).get("role") == "admin"

st.set_page_config(
    page_title="Orion Signals",
    page_icon="🎯",
    layout="wide" if _is_admin else "centered",
    initial_sidebar_state="collapsed",
)

inject_background()

# ── SESSION STATE ──
defaults = {
    "logged_in":           False,
    "user":                None,
    "active_page":         "login",
    "quiz_completed":      False,
    "disclaimer_accepted": False,
    "pricing_done":        False,
    "pending_user":        None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── ROUTING ──

# 1. Logged in
if st.session_state.logged_in and st.session_state.user:
    user = st.session_state.user

    # Admin → admin panel
    if is_admin(user):
        from admin_app import show_admin_dashboard
        show_admin_dashboard(user)
        st.stop()

    # Inactive subscription → show message
    if not has_active_subscription(user):
        from styles import inject_logo
        inject_logo()
        st.error("⚠️ Your subscription is inactive.")
        st.markdown("""
        <div style="text-align:center;margin-top:1rem;font-size:0.85rem;color:rgba(255,255,255,0.5);">
            Please contact support to reactivate your account.
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚪 Logout"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
        st.stop()

    # Route to correct dashboard
    plan = user.get("plan", "entry")
    if plan == "pro":
        from pro_app import show_pro_dashboard
        show_pro_dashboard(user)
    elif plan == "crypto_entry":
        from crypto_entry_app import show_crypto_entry_dashboard
        show_crypto_entry_dashboard(user)
    elif plan == "crypto_pro":
        from crypto_pro_app import show_crypto_pro_dashboard
        show_crypto_pro_dashboard(user)
    elif plan == "combined":
        from combined_app import show_combined_dashboard
        show_combined_dashboard(user)
    else:
        from entry_app import show_entry_dashboard
        show_entry_dashboard(user)
    st.stop()

# 2. Quiz
if st.session_state.active_page == "quiz":
    from quiz import show_quiz
    from styles import inject_logo
    inject_logo()
    if show_quiz():
        st.session_state.quiz_completed = True
        st.session_state.active_page = "disclaimer"
        st.rerun()
    st.stop()

# 3. Disclaimer
if st.session_state.active_page == "disclaimer":
    from disclaimer import show_disclaimer
    from styles import inject_logo
    inject_logo()
    if show_disclaimer():
        st.session_state.disclaimer_accepted = True
        st.session_state.active_page = "pricing"
        st.rerun()
    st.stop()

# 4. Pricing
if st.session_state.active_page == "pricing":
    from pricing import show_pricing
    show_pricing()
    st.stop()

# 5. Register
if st.session_state.active_page == "register":
    from register import show_register
    show_register()
    st.stop()

# 6. Login (default)
from login import show_login
show_login()
