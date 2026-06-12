"""
Orion Signals — Combined Dashboard
🌐 Combined €150/μήνα
"""
import streamlit as st

def show_combined_dashboard(user):
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=Inter:wght@300;400;500&display=swap');
    #MainMenu,footer,.stDeployButton{display:none!important}
    [data-testid="stToolbar"]{display:none!important}
    .stApp{background:#080810;font-family:'Inter',sans-serif;color:#E2E8F0}
    [data-testid="stSidebar"]{background:#0D0D1A!important;border-right:1px solid rgba(124,58,237,0.15)!important}
    [data-testid="stSidebar"] *{color:#E2E8F0!important}
    .orion-header{display:flex;align-items:center;justify-content:space-between;
        padding:1rem 0 1.5rem;border-bottom:1px solid rgba(0,200,83,0.2);margin-bottom:1.5rem}
    .orion-logo{font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:800;color:#fff}
    .orion-logo span{color:#7C3AED}
    .plan-badge{background:rgba(0,200,83,0.15);color:#00C853;
        border:1px solid rgba(0,200,83,0.3);padding:0.25rem 0.75rem;
        border-radius:20px;font-size:0.75rem;font-weight:600;letter-spacing:0.08em}
    .coming-card{background:rgba(255,255,255,0.02);border:1px solid rgba(0,200,83,0.15);
        border-radius:16px;padding:3rem;text-align:center;margin:2rem 0}
    .stButton>button{background:linear-gradient(135deg,#7C3AED,#5B21B6)!important;
        color:white!important;border:none!important;border-radius:8px!important;
        font-family:'Syne',sans-serif!important;font-weight:700!important}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="orion-header">
        <div class="orion-logo">🎯 Orion <span>Signals</span></div>
        <span class="plan-badge">🌐 Combined</span>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(f"**👤 {user['name']}**")
        st.markdown(f"*{user['email']}*")
        st.markdown("---")
        if st.button("🚪 Logout"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    st.markdown("""
    <div class="coming-card">
        <div style="font-size:3rem;margin-bottom:1rem;">🌐</div>
        <div style="font-family:'Syne',sans-serif;font-size:1.8rem;font-weight:800;color:#fff;margin-bottom:0.5rem;">
            Combined Dashboard
        </div>
        <div style="color:rgba(255,255,255,0.5);font-size:0.9rem;max-width:500px;margin:0 auto;line-height:1.7;">
            Stocks Pro + Crypto Pro in one unified dashboard.<br>
            Cross-market signals · Unified portfolio tracker<br>
            All indicators · All alerts · Priority support
        </div>
        <div style="margin-top:2rem;background:rgba(0,200,83,0.08);border:1px solid rgba(0,200,83,0.2);
                    border-radius:10px;padding:0.75rem 1.5rem;display:inline-block;">
            <span style="color:#00C853;font-size:0.85rem;font-weight:600;">
                🔨 Under Development — Coming Soon
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.caption("⚠️ Educational tool only. Not financial advice.")
