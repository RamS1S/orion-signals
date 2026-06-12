"""
Orion Signals — Register Page
Μόνο Sign Up.
"""
import streamlit as st
from styles import inject_logo

def show_register():
    inject_logo()

    st.markdown("""
    <div style="text-align:center;margin-bottom:1.2rem;">
        <span style="font-family:'Syne',sans-serif;font-size:1rem;font-weight:700;color:#fff;">
            Create your account
        </span>
    </div>
    """, unsafe_allow_html=True)

    username = st.text_input("Username",         placeholder="e.g. trader_john",    key="su_username")
    name     = st.text_input("Full Name",         placeholder="e.g. John Doe",       key="su_name")
    email    = st.text_input("Email",             placeholder="your@email.com",       key="su_email")
    phone    = st.text_input("Phone Number",      placeholder="+30 69X XXX XXXX",    key="su_phone")
    st.markdown('<div class="phone-note">Used for account verification and Telegram alerts</div>',
                unsafe_allow_html=True)
    password = st.text_input("Password",          type="password",
                              placeholder="min. 8 characters",   key="su_pass")
    confirm  = st.text_input("Confirm Password",  type="password",
                              placeholder="repeat password",      key="su_confirm")

    if st.button("Create Account →", key="signup_btn"):
        # Validation
        if not all([username, name, email, phone, password, confirm]):
            st.error("Please fill in all fields.")
        elif password != confirm:
            st.error("❌ Passwords do not match.")
        elif len(password) < 8:
            st.error("❌ Password must be at least 8 characters.")
        else:
            # Αποθήκευση pending user
            st.session_state.pending_user = {
                "email":    email,
                "name":     name,
                "username": username,
                "phone":    phone,
                "plan":     "entry",
            }
            st.session_state.active_page = "quiz"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2,1,2])
    with col2:
        if st.button("Sign In", key="goto_login"):
            st.session_state.active_page = "login"
            st.rerun()

    st.markdown("""
    <div class="login-footer">
        © 2026 Orion Signals · Educational tool · Not financial advice
    </div>
    """, unsafe_allow_html=True)
