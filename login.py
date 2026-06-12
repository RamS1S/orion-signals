"""
Orion Signals — Login Page
Μόνο Sign In.
"""
import streamlit as st
from auth import login
from styles import inject_logo

def show_login():
    inject_logo(tagline=True)

    email    = st.text_input("Email",    placeholder="your@email.com", key="si_email")
    password = st.text_input("Password", type="password", placeholder="enter your password", key="si_pass")

    if st.button("Sign In →", key="signin_btn"):
        if not email or not password:
            st.error("Please fill in all fields.")
        else:
            user = login(email, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.rerun()
            else:
                st.error("❌ Wrong email or password.")

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2,1,2])
    with col2:
        if st.button("Sign Up", key="goto_register"):
            st.session_state.active_page = "register"
            st.rerun()

    st.markdown("""
    <div class="login-footer">
        © 2026 Orion Signals · Educational tool · Not financial advice
    </div>
    """, unsafe_allow_html=True)
