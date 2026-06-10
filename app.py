"""
Orion Signals — Main Entry Point
Full flow: Login → Dashboard / Register → Quiz → Disclaimer → Dashboard
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
    background: #020408;
    font-family: 'Inter', sans-serif;
    color: #E2E8F0;
}

.block-container {
    position: relative;
    z-index: 10;
    padding-top: 0 !important;
    max-width: 520px !important;
}

.star-canvas {
    position: fixed; top: 0; left: 0;
    width: 100%; height: 100%;
    pointer-events: none; z-index: 0;
}

.orion-svg {
    position: fixed; top: 0; left: 0;
    width: 100%; height: 100%;
    pointer-events: none; z-index: 1; opacity: 0.55;
}

.stApp::after {
    content: '';
    position: fixed; bottom: -100px; right: 20%;
    width: 500px; height: 500px;
    background: radial-gradient(ellipse, rgba(124,58,237,0.07) 0%, transparent 70%);
    pointer-events: none; z-index: 0;
}

.top-bar {
    position: fixed; top: 0; left: 0; right: 0;
    height: 52px;
    display: flex; align-items: center;
    padding: 0 2rem;
    background: rgba(2,4,8,0.85);
    border-bottom: 1px solid rgba(124,58,237,0.15);
    backdrop-filter: blur(12px);
    z-index: 100;
}
.top-logo {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem; font-weight: 800;
    color: #fff; letter-spacing: -0.02em;
}
.top-logo span { color: #7C3AED; }
.top-spacer { height: 72px; }

.logo-wrap {
    text-align: center; margin-bottom: 1.5rem;
}
.logo-icon {
    font-size: 2.8rem; display: block;
    filter: drop-shadow(0 0 25px rgba(124,58,237,0.9));
    margin-bottom: 0.2rem;
}
.logo-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.4rem; font-weight: 800;
    color: #fff; letter-spacing: -0.03em;
    margin: 0; line-height: 1;
}
.logo-title span { color: #7C3AED; }
.logo-tagline {
    font-size: 0.7rem;
    color: rgba(255,255,255,0.25);
    letter-spacing: 0.28em; text-transform: uppercase;
    margin-top: 0.35rem;
}

.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.03) !important;
    border-radius: 10px !important;
    padding: 3px !important; gap: 3px !important;
    border: 1px solid rgba(124,58,237,0.15) !important;
    margin-bottom: 1.2rem !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: rgba(255,255,255,0.35) !important;
    border-radius: 7px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important; font-size: 0.82rem !important;
    letter-spacing: 0.06em !important;
    padding: 0.45rem 1.2rem !important;
    border: none !important; transition: all 0.2s !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(124,58,237,0.28) !important;
    color: #ffffff !important; border: none !important;
}

.stTextInput > div > div > input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(124,58,237,0.22) !important;
    border-radius: 8px !important; color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.82rem !important;
    padding: 0.5rem 0.85rem !important;
    transition: all 0.2s !important; height: 36px !important;
}
.stTextInput > div > div > input:focus {
    border-color: rgba(124,58,237,0.65) !important;
    box-shadow: 0 0 0 2px rgba(124,58,237,0.1) !important;
}
.stTextInput > div > div > input::placeholder {
    color: rgba(255,255,255,0.15) !important;
    font-size: 0.72rem !important; font-style: italic !important;
}
.stTextInput label {
    color: rgba(255,255,255,0.4) !important;
    font-size: 0.7rem !important; font-weight: 500 !important;
    letter-spacing: 0.12em !important; text-transform: uppercase !important;
    margin-bottom: 2px !important;
}

.stButton > button {
    background: linear-gradient(135deg, #7C3AED 0%, #4F1D96 100%) !important;
    color: white !important; border: none !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important; font-size: 0.85rem !important;
    letter-spacing: 0.08em !important; width: 100% !important;
    padding: 0.6rem !important; margin-top: 0.2rem !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 18px rgba(124,58,237,0.32) !important;
    height: 40px !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 24px rgba(124,58,237,0.52) !important;
}

.phone-note {
    font-size: 0.68rem; color: rgba(255,255,255,0.25);
    margin-top: -0.3rem; margin-bottom: 0.3rem;
    padding-left: 0.2rem;
}

.login-footer {
    text-align: center; margin-top: 1.2rem;
    color: rgba(255,255,255,0.12);
    font-size: 0.65rem; letter-spacing: 0.05em;
}

@keyframes twinkle { 0%,100%{opacity:0.2} 50%{opacity:0.9} }
</style>

<canvas class="star-canvas" id="starCanvas"></canvas>

<svg class="orion-svg" viewBox="0 0 1440 900" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <filter id="glow"><feGaussianBlur stdDeviation="3" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <filter id="bglow"><feGaussianBlur stdDeviation="6" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <circle cx="60"   cy="90"  r="0.8" fill="white" opacity="0.35" style="animation:twinkle 3.1s infinite 0.2s"/>
  <circle cx="140"  cy="220" r="0.6" fill="white" opacity="0.28"/>
  <circle cx="210"  cy="55"  r="1.0" fill="white" opacity="0.45" style="animation:twinkle 2.4s infinite 0.7s"/>
  <circle cx="310"  cy="170" r="0.7" fill="white" opacity="0.32" style="animation:twinkle 3.8s infinite 1.4s"/>
  <circle cx="380"  cy="320" r="0.9" fill="white" opacity="0.38" style="animation:twinkle 2.9s infinite 0.4s"/>
  <circle cx="100"  cy="450" r="0.9" fill="white" opacity="0.38" style="animation:twinkle 3.7s infinite 1.6s"/>
  <circle cx="190"  cy="520" r="0.6" fill="white" opacity="0.25"/>
  <circle cx="270"  cy="420" r="1.0" fill="white" opacity="0.43" style="animation:twinkle 2.6s infinite 0.8s"/>
  <circle cx="50"   cy="750" r="0.9" fill="white" opacity="0.37" style="animation:twinkle 3.6s infinite 1.3s"/>
  <circle cx="160"  cy="820" r="0.6" fill="white" opacity="0.25" style="animation:twinkle 4.1s infinite 2.0s"/>
  <circle cx="1300" cy="100" r="0.8" fill="white" opacity="0.35" style="animation:twinkle 3.2s infinite 0.4s"/>
  <circle cx="1380" cy="250" r="0.6" fill="white" opacity="0.28"/>
  <circle cx="1420" cy="50"  r="1.0" fill="white" opacity="0.45" style="animation:twinkle 2.6s infinite 1.2s"/>
  <circle cx="1350" cy="400" r="0.7" fill="white" opacity="0.32"/>
  <circle cx="1400" cy="550" r="0.9" fill="white" opacity="0.38" style="animation:twinkle 3.8s infinite 0.6s"/>
  <circle cx="1390" cy="750" r="1.0" fill="white" opacity="0.42"/>
  <line x1="1050" y1="260" x2="990"  y2="420" stroke="rgba(167,139,250,0.18)" stroke-width="0.8"/>
  <line x1="1140" y1="280" x2="1030" y2="420" stroke="rgba(167,139,250,0.18)" stroke-width="0.8"/>
  <line x1="990"  y1="420" x2="1030" y2="418" stroke="rgba(167,139,250,0.25)" stroke-width="1"/>
  <line x1="1030" y1="418" x2="1068" y2="414" stroke="rgba(167,139,250,0.25)" stroke-width="1"/>
  <line x1="990"  y1="420" x2="950"  y2="565" stroke="rgba(167,139,250,0.15)" stroke-width="0.8"/>
  <line x1="1068" y1="414" x2="1105" y2="560" stroke="rgba(167,139,250,0.15)" stroke-width="0.8"/>
  <line x1="1050" y1="260" x2="1095" y2="165" stroke="rgba(167,139,250,0.12)" stroke-width="0.8"/>
  <line x1="1140" y1="280" x2="1095" y2="165" stroke="rgba(167,139,250,0.12)" stroke-width="0.8"/>
  <line x1="1030" y1="418" x2="1022" y2="500" stroke="rgba(167,139,250,0.2)"  stroke-width="0.8"/>
  <circle cx="1050" cy="260" r="4"  fill="#FCA5A5" opacity="0.92" filter="url(#glow)" style="animation:twinkle 2.5s infinite"/>
  <circle cx="1050" cy="260" r="1.5" fill="#fff"/>
  <circle cx="1140" cy="280" r="3"  fill="#BFDBFE" opacity="0.9" filter="url(#glow)" style="animation:twinkle 3s infinite 0.5s"/>
  <circle cx="1140" cy="280" r="1.2" fill="#fff"/>
  <circle cx="990"  cy="420" r="2.5" fill="#C4B5FD" opacity="0.95" style="animation:twinkle 2.8s infinite 0.3s"/>
  <circle cx="990"  cy="420" r="1" fill="#fff"/>
  <circle cx="1030" cy="418" r="3.2" fill="#DDD6FE" opacity="0.98" filter="url(#glow)" style="animation:twinkle 2s infinite 0.8s"/>
  <circle cx="1030" cy="418" r="1.3" fill="#fff"/>
  <circle cx="1068" cy="414" r="2.5" fill="#C4B5FD" opacity="0.95" style="animation:twinkle 3.2s infinite 1.3s"/>
  <circle cx="1068" cy="414" r="1" fill="#fff"/>
  <circle cx="1018" cy="500" r="16" fill="rgba(124,58,237,0.07)"/>
  <circle cx="1018" cy="500" r="2.5" fill="#A78BFA" opacity="0.65" filter="url(#glow)"/>
  <circle cx="1018" cy="500" r="1" fill="white" opacity="0.8"/>
  <circle cx="1105" cy="560" r="5"  fill="#93C5FD" opacity="0.92" filter="url(#bglow)" style="animation:twinkle 1.8s infinite"/>
  <circle cx="1105" cy="560" r="2" fill="#fff"/>
  <circle cx="950"  cy="565" r="3.5" fill="#C4B5FD" opacity="0.88" filter="url(#glow)" style="animation:twinkle 2.2s infinite 1s"/>
  <circle cx="950"  cy="565" r="1.4" fill="#fff"/>
</svg>

<script>
(function(){
    function init(){
        const c=document.getElementById('starCanvas');
        if(!c){setTimeout(init,200);return;}
        const ctx=c.getContext('2d');
        function resize(){c.width=window.innerWidth;c.height=window.innerHeight;}
        resize();window.addEventListener('resize',resize);
        const stars=Array.from({length:220},()=>({
            x:Math.random(),y:Math.random(),
            r:Math.random()*1.1+0.15,
            base:Math.random()*0.4+0.08,
            speed:Math.random()*0.008+0.002,
            phase:Math.random()*Math.PI*2,
        }));
        let t=0;
        function draw(){
            t+=0.016;
            ctx.clearRect(0,0,c.width,c.height);
            stars.forEach(s=>{
                const op=s.base+Math.sin(t*s.speed*60+s.phase)*0.14;
                ctx.beginPath();
                ctx.arc(s.x*c.width,s.y*c.height,s.r,0,Math.PI*2);
                ctx.fillStyle=`rgba(255,255,255,${Math.max(0,op)})`;
                ctx.fill();
            });
            requestAnimationFrame(draw);
        }
        draw();
    }
    setTimeout(init,400);
})();
</script>

<div class="top-bar">
    <div class="top-logo">🎯 Orion <span>Signals</span></div>
</div>
<div class="top-spacer"></div>
""", unsafe_allow_html=True)

# ── SESSION STATE ──
for key, val in {
    "logged_in": False,
    "user": None,
    "show_quiz": False,
    "show_disclaimer": False,
    "quiz_completed": False,
    "disclaimer_accepted": False,
    "pending_user": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── URL PARAMS → default tab ──
params = st.query_params
default_tab = params.get("tab", "signin")

# ── ROUTING ──

# 1. Logged in → Dashboard
if st.session_state.logged_in and st.session_state.user:
    user = st.session_state.user
    if is_pro(user):
        from pro_app import show_pro_dashboard
        show_pro_dashboard(user)
    else:
        from entry_app import show_entry_dashboard
        show_entry_dashboard(user)
    st.stop()

# 2. Quiz flow
if st.session_state.show_quiz and not st.session_state.quiz_completed:
    from quiz import show_quiz
    st.markdown("""
    <div class="logo-wrap">
        <span class="logo-icon">🎯</span>
        <h1 class="logo-title">Orion <span>Signals</span></h1>
    </div>
    """, unsafe_allow_html=True)
    if show_quiz():
        st.session_state.quiz_completed = True
        st.session_state.show_disclaimer = True
        st.rerun()
    st.stop()

# 3. Disclaimer flow
if st.session_state.show_disclaimer and not st.session_state.disclaimer_accepted:
    from disclaimer import show_disclaimer
    st.markdown("""
    <div class="logo-wrap">
        <span class="logo-icon">🎯</span>
        <h1 class="logo-title">Orion <span>Signals</span></h1>
    </div>
    """, unsafe_allow_html=True)
    if show_disclaimer():
        st.session_state.disclaimer_accepted = True
        # Login με pending user
        if st.session_state.pending_user:
            st.session_state.logged_in = True
            st.session_state.user = st.session_state.pending_user
        st.rerun()
    st.stop()

# ── LOGIN PAGE ──
st.markdown("""
<div class="logo-wrap">
    <span class="logo-icon">🎯</span>
    <h1 class="logo-title">Orion <span>Signals</span></h1>
    <p class="logo-tagline">See through the noise</p>
</div>
""", unsafe_allow_html=True)

# Default tab βάσει URL param
tab_index = 1 if default_tab == "signup" else 0
tab_in, tab_up = st.tabs(["Sign In", "Sign Up"])

# ── SIGN IN ──
with tab_in:
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

# ── SIGN UP ──
with tab_up:
    su_username = st.text_input("Username",       placeholder="e.g. trader_john",         key="su_username")
    su_name     = st.text_input("Full Name",      placeholder="e.g. John Doe",            key="su_name")
    su_email    = st.text_input("Email",          placeholder="your@email.com",            key="su_email")
    su_phone    = st.text_input("Phone Number",   placeholder="+30 69X XXX XXXX",         key="su_phone")
    st.markdown('<div class="phone-note">Used for account verification and Telegram alerts</div>',
                unsafe_allow_html=True)
    su_pass     = st.text_input("Password",       type="password", placeholder="min. 8 characters", key="su_pass")
    su_confirm  = st.text_input("Confirm Password", type="password", placeholder="repeat password",  key="su_confirm")

    if st.button("Create Account →", key="signup_btn"):
        if not all([su_username, su_name, su_email, su_phone, su_pass, su_confirm]):
            st.error("Please fill in all fields.")
        elif su_pass != su_confirm:
            st.error("❌ Passwords do not match.")
        elif len(su_pass) < 8:
            st.error("❌ Password must be at least 8 characters.")
        else:
            # Αποθήκευση pending user (αργότερα θα γίνει database)
            st.session_state.pending_user = {
                "email": su_email,
                "name": su_name,
                "username": su_username,
                "plan": "entry",  # default
            }
            st.session_state.show_quiz = True
            st.rerun()

st.markdown("""
<div class="login-footer">
    © 2026 Orion Signals · Educational tool · Not financial advice
</div>
""", unsafe_allow_html=True)
