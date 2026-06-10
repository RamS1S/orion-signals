"""
Orion Signals — Login Page
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
}

/* ── TOP BAR ── */
.top-bar {
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 52px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 2rem;
    background: rgba(2,4,8,0.85);
    border-bottom: 1px solid rgba(124,58,237,0.15);
    backdrop-filter: blur(12px);
    z-index: 100;
}

.top-logo {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem;
    font-weight: 800;
    color: #fff;
    letter-spacing: -0.02em;
}

.top-logo span { color: #7C3AED; }

.lang-btn {
    background: rgba(124,58,237,0.15);
    border: 1px solid rgba(124,58,237,0.3);
    color: rgba(255,255,255,0.7);
    padding: 0.3rem 0.9rem;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    cursor: pointer;
    transition: all 0.2s;
    text-transform: uppercase;
}

.lang-btn:hover {
    background: rgba(124,58,237,0.3);
    color: #fff;
}

/* Spacer for fixed top bar */
.top-spacer { height: 70px; }

/* ── STARS CANVAS ── */
.star-canvas {
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    pointer-events: none;
    z-index: 0;
}

/* ── ORION SVG ── */
.orion-svg {
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    pointer-events: none;
    z-index: 1;
}

/* Purple nebula glow */
.stApp::after {
    content: '';
    position: fixed;
    bottom: -100px;
    right: 20%;
    width: 500px;
    height: 500px;
    background: radial-gradient(ellipse, rgba(124,58,237,0.07) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
}

/* ── LOGO CENTER ── */
.logo-wrap {
    text-align: center;
    margin-bottom: 1.5rem;
    animation: fadeInDown 0.9s ease;
}

.logo-icon {
    font-size: 2.8rem;
    display: block;
    filter: drop-shadow(0 0 25px rgba(124,58,237,0.9));
    margin-bottom: 0.2rem;
}

.logo-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.4rem;
    font-weight: 800;
    color: #fff;
    letter-spacing: -0.03em;
    margin: 0;
    line-height: 1;
    text-shadow: 0 0 40px rgba(124,58,237,0.4);
}

.logo-title span { color: #7C3AED; }

.logo-tagline {
    font-size: 0.7rem;
    color: rgba(255,255,255,0.25);
    letter-spacing: 0.28em;
    text-transform: uppercase;
    margin-top: 0.35rem;
}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.03) !important;
    border-radius: 10px !important;
    padding: 3px !important;
    gap: 3px !important;
    border: 1px solid rgba(124,58,237,0.15) !important;
    margin-bottom: 1.2rem !important;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: rgba(255,255,255,0.35) !important;
    border-radius: 7px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.06em !important;
    padding: 0.45rem 1.2rem !important;
    border: none !important;
    transition: all 0.2s !important;
}

.stTabs [aria-selected="true"] {
    background: rgba(124,58,237,0.28) !important;
    color: #ffffff !important;
    border: none !important;
}

/* ── INPUTS ── */
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(124,58,237,0.22) !important;
    border-radius: 8px !important;
    color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.82rem !important;
    padding: 0.5rem 0.85rem !important;
    transition: all 0.2s !important;
    height: 36px !important;
}

.stTextInput > div > div > input:focus {
    border-color: rgba(124,58,237,0.65) !important;
    box-shadow: 0 0 0 2px rgba(124,58,237,0.1) !important;
    background: rgba(124,58,237,0.04) !important;
}

.stTextInput > div > div > input::placeholder {
    color: rgba(255,255,255,0.15) !important;
    font-size: 0.75rem !important;
    font-style: italic !important;
}

.stTextInput label {
    color: rgba(255,255,255,0.4) !important;
    font-size: 0.7rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    margin-bottom: 2px !important;
}

/* ── BUTTON ── */
.stButton > button {
    background: linear-gradient(135deg, #7C3AED 0%, #4F1D96 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.08em !important;
    width: 100% !important;
    padding: 0.6rem !important;
    margin-top: 0.2rem !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 18px rgba(124,58,237,0.32) !important;
    height: 40px !important;
}

.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 24px rgba(124,58,237,0.52) !important;
}

/* ── DIVIDER ── */
.or-divider {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    margin: 0.9rem 0 0.7rem;
    color: rgba(255,255,255,0.18);
    font-size: 0.7rem;
    letter-spacing: 0.1em;
}
.or-divider::before, .or-divider::after {
    content: '';
    flex: 1;
    height: 1px;
    background: rgba(255,255,255,0.07);
}

/* ── FOOTER ── */
.login-footer {
    text-align: center;
    margin-top: 1.2rem;
    color: rgba(255,255,255,0.12);
    font-size: 0.65rem;
    letter-spacing: 0.05em;
}

@keyframes fadeInDown {
    from { opacity: 0; transform: translateY(-14px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(14px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes twinkle {
    0%, 100% { opacity: 0.2; }
    50%       { opacity: 1; }
}
</style>

<!-- ══ STAR CANVAS + ORION ══ -->
<canvas class="star-canvas" id="starCanvas"></canvas>

<svg class="orion-svg" viewBox="0 0 1440 900" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <filter id="glow"><feGaussianBlur stdDeviation="3" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <filter id="bglow"><feGaussianBlur stdDeviation="6" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>

  <!-- Background scatter stars (all over) -->
  <circle cx="60"   cy="90"  r="0.8" fill="white" opacity="0.35" style="animation:twinkle 3.1s infinite 0.2s"/>
  <circle cx="140"  cy="220" r="0.6" fill="white" opacity="0.28"/>
  <circle cx="210"  cy="55"  r="1.0" fill="white" opacity="0.45" style="animation:twinkle 2.4s infinite 0.7s"/>
  <circle cx="310"  cy="170" r="0.7" fill="white" opacity="0.32" style="animation:twinkle 3.8s infinite 1.4s"/>
  <circle cx="380"  cy="320" r="0.9" fill="white" opacity="0.38" style="animation:twinkle 2.9s infinite 0.4s"/>
  <circle cx="460"  cy="80"  r="0.6" fill="white" opacity="0.25"/>
  <circle cx="520"  cy="250" r="1.1" fill="white" opacity="0.48" style="animation:twinkle 2.1s infinite 1.8s"/>
  <circle cx="590"  cy="40"  r="0.8" fill="white" opacity="0.35" style="animation:twinkle 4.0s infinite 0.9s"/>
  <circle cx="650"  cy="180" r="0.7" fill="white" opacity="0.30"/>
  <circle cx="720"  cy="290" r="0.9" fill="white" opacity="0.40" style="animation:twinkle 3.3s infinite 2.1s"/>
  <circle cx="780"  cy="60"  r="0.6" fill="white" opacity="0.27" style="animation:twinkle 2.7s infinite 0.6s"/>
  <circle cx="830"  cy="380" r="1.0" fill="white" opacity="0.42"/>
  <circle cx="890"  cy="120" r="0.8" fill="white" opacity="0.36" style="animation:twinkle 3.5s infinite 1.1s"/>
  <circle cx="960"  cy="200" r="0.7" fill="white" opacity="0.30" style="animation:twinkle 2.3s infinite 0.3s"/>
  <circle cx="100"  cy="450" r="0.9" fill="white" opacity="0.38" style="animation:twinkle 3.7s infinite 1.6s"/>
  <circle cx="190"  cy="520" r="0.6" fill="white" opacity="0.25"/>
  <circle cx="270"  cy="420" r="1.0" fill="white" opacity="0.43" style="animation:twinkle 2.6s infinite 0.8s"/>
  <circle cx="350"  cy="600" r="0.8" fill="white" opacity="0.35" style="animation:twinkle 3.9s infinite 2.3s"/>
  <circle cx="430"  cy="480" r="0.7" fill="white" opacity="0.30"/>
  <circle cx="500"  cy="680" r="0.9" fill="white" opacity="0.38" style="animation:twinkle 2.8s infinite 1.0s"/>
  <circle cx="570"  cy="550" r="1.1" fill="white" opacity="0.46" style="animation:twinkle 2.2s infinite 0.5s"/>
  <circle cx="640"  cy="720" r="0.6" fill="white" opacity="0.27"/>
  <circle cx="700"  cy="600" r="0.8" fill="white" opacity="0.35" style="animation:twinkle 3.4s infinite 1.7s"/>
  <circle cx="760"  cy="800" r="0.7" fill="white" opacity="0.30" style="animation:twinkle 2.5s infinite 0.2s"/>
  <circle cx="820"  cy="650" r="1.0" fill="white" opacity="0.42"/>
  <circle cx="50"   cy="750" r="0.9" fill="white" opacity="0.37" style="animation:twinkle 3.6s infinite 1.3s"/>
  <circle cx="160"  cy="820" r="0.6" fill="white" opacity="0.25" style="animation:twinkle 4.1s infinite 2.0s"/>
  <circle cx="280"  cy="760" r="1.0" fill="white" opacity="0.43"/>
  <circle cx="450"  cy="850" r="0.8" fill="white" opacity="0.35" style="animation:twinkle 2.9s infinite 0.7s"/>

  <!-- Right side scattered -->
  <circle cx="1300" cy="100" r="0.8" fill="white" opacity="0.35" style="animation:twinkle 3.2s infinite 0.4s"/>
  <circle cx="1380" cy="250" r="0.6" fill="white" opacity="0.28"/>
  <circle cx="1420" cy="50"  r="1.0" fill="white" opacity="0.45" style="animation:twinkle 2.6s infinite 1.2s"/>
  <circle cx="1350" cy="400" r="0.7" fill="white" opacity="0.32"/>
  <circle cx="1400" cy="550" r="0.9" fill="white" opacity="0.38" style="animation:twinkle 3.8s infinite 0.6s"/>
  <circle cx="1320" cy="650" r="0.6" fill="white" opacity="0.25" style="animation:twinkle 2.3s infinite 1.9s"/>
  <circle cx="1390" cy="750" r="1.0" fill="white" opacity="0.42"/>
  <circle cx="1340" cy="850" r="0.8" fill="white" opacity="0.35" style="animation:twinkle 3.5s infinite 0.8s"/>

  <!-- ══ ORION CONSTELLATION (right side) ══ -->
  <!-- Lines -->
  <line x1="1050" y1="260" x2="990"  y2="420" stroke="rgba(167,139,250,0.18)" stroke-width="0.8"/>
  <line x1="1140" y1="280" x2="1030" y2="420" stroke="rgba(167,139,250,0.18)" stroke-width="0.8"/>
  <line x1="990"  y1="420" x2="1030" y2="418" stroke="rgba(167,139,250,0.25)" stroke-width="1"/>
  <line x1="1030" y1="418" x2="1068" y2="414" stroke="rgba(167,139,250,0.25)" stroke-width="1"/>
  <line x1="990"  y1="420" x2="950"  y2="565" stroke="rgba(167,139,250,0.15)" stroke-width="0.8"/>
  <line x1="1068" y1="414" x2="1105" y2="560" stroke="rgba(167,139,250,0.15)" stroke-width="0.8"/>
  <line x1="1050" y1="260" x2="1095" y2="165" stroke="rgba(167,139,250,0.12)" stroke-width="0.8"/>
  <line x1="1140" y1="280" x2="1095" y2="165" stroke="rgba(167,139,250,0.12)" stroke-width="0.8"/>
  <line x1="1140" y1="280" x2="1240" y2="340" stroke="rgba(167,139,250,0.1)"  stroke-width="0.8"/>
  <line x1="1030" y1="418" x2="1022" y2="500" stroke="rgba(167,139,250,0.2)"  stroke-width="0.8"/>

  <!-- Head stars -->
  <circle cx="1088" cy="158" r="1.4" fill="white" opacity="0.55" style="animation:twinkle 4s infinite 1s"/>
  <circle cx="1105" cy="150" r="0.9" fill="white" opacity="0.38"/>
  <circle cx="1072" cy="168" r="1.1" fill="white" opacity="0.45" style="animation:twinkle 3s infinite 2s"/>

  <!-- BETELGEUSE - left shoulder, red -->
  <circle cx="1050" cy="260" r="10" fill="rgba(239,68,68,0.15)" filter="url(#bglow)"/>
  <circle cx="1050" cy="260" r="4"  fill="#FCA5A5" opacity="0.92" filter="url(#glow)" style="animation:twinkle 2.5s infinite"/>
  <circle cx="1050" cy="260" r="1.5" fill="#fff"/>

  <!-- BELLATRIX - right shoulder, blue-white -->
  <circle cx="1140" cy="280" r="7" fill="rgba(147,197,253,0.18)" filter="url(#bglow)"/>
  <circle cx="1140" cy="280" r="3"  fill="#BFDBFE" opacity="0.9" filter="url(#glow)" style="animation:twinkle 3s infinite 0.5s"/>
  <circle cx="1140" cy="280" r="1.2" fill="#fff"/>

  <!-- BELT - ALNITAK -->
  <circle cx="990"  cy="420" r="5" fill="rgba(167,139,250,0.2)" filter="url(#glow)"/>
  <circle cx="990"  cy="420" r="2.5" fill="#C4B5FD" opacity="0.95" style="animation:twinkle 2.8s infinite 0.3s"/>
  <circle cx="990"  cy="420" r="1" fill="#fff"/>

  <!-- BELT - ALNILAM (brightest) -->
  <circle cx="1030" cy="418" r="8" fill="rgba(167,139,250,0.22)" filter="url(#bglow)"/>
  <circle cx="1030" cy="418" r="3.2" fill="#DDD6FE" opacity="0.98" filter="url(#glow)" style="animation:twinkle 2s infinite 0.8s"/>
  <circle cx="1030" cy="418" r="1.3" fill="#fff"/>

  <!-- BELT - MINTAKA -->
  <circle cx="1068" cy="414" r="5" fill="rgba(167,139,250,0.18)" filter="url(#glow)"/>
  <circle cx="1068" cy="414" r="2.5" fill="#C4B5FD" opacity="0.95" style="animation:twinkle 3.2s infinite 1.3s"/>
  <circle cx="1068" cy="414" r="1" fill="#fff"/>

  <!-- SWORD (Nebula) -->
  <circle cx="1022" cy="472" r="1.7" fill="white" opacity="0.48" style="animation:twinkle 3s infinite 0.6s"/>
  <circle cx="1018" cy="500" r="16" fill="rgba(124,58,237,0.07)"/>
  <circle cx="1018" cy="500" r="2.5" fill="#A78BFA" opacity="0.65" filter="url(#glow)"/>
  <circle cx="1018" cy="500" r="1" fill="white" opacity="0.8"/>
  <circle cx="1020" cy="528" r="1.4" fill="white" opacity="0.4" style="animation:twinkle 4s infinite 1.5s"/>

  <!-- RIGEL - right foot, blue-white bright -->
  <circle cx="1105" cy="560" r="14" fill="rgba(147,197,253,0.12)" filter="url(#bglow)"/>
  <circle cx="1105" cy="560" r="5"  fill="#93C5FD" opacity="0.92" filter="url(#bglow)" style="animation:twinkle 1.8s infinite"/>
  <circle cx="1105" cy="560" r="2" fill="#fff"/>

  <!-- SAIPH - left foot -->
  <circle cx="950"  cy="565" r="9" fill="rgba(167,139,250,0.14)" filter="url(#glow)"/>
  <circle cx="950"  cy="565" r="3.5" fill="#C4B5FD" opacity="0.88" filter="url(#glow)" style="animation:twinkle 2.2s infinite 1s"/>
  <circle cx="950"  cy="565" r="1.4" fill="#fff"/>

  <!-- Arm star -->
  <circle cx="1240" cy="340" r="1.8" fill="white" opacity="0.48" style="animation:twinkle 3s infinite 0.7s"/>
  <circle cx="1270" cy="360" r="1.2" fill="white" opacity="0.35"/>

  <!-- Label -->
  <text x="1060" y="620" fill="rgba(167,139,250,0.25)" font-size="9"
        font-family="Inter,sans-serif" letter-spacing="4" text-anchor="middle">ORION</text>
</svg>

<!-- Starfield JS -->
<script>
(function() {
    function init() {
        const c = document.getElementById('starCanvas');
        if (!c) { setTimeout(init, 200); return; }
        const ctx = c.getContext('2d');
        function resize() { c.width = window.innerWidth; c.height = window.innerHeight; }
        resize();
        window.addEventListener('resize', resize);
        const stars = Array.from({length: 220}, () => ({
            x: Math.random(), y: Math.random(),
            r: Math.random() * 1.1 + 0.15,
            base: Math.random() * 0.45 + 0.08,
            speed: Math.random() * 0.008 + 0.002,
            phase: Math.random() * Math.PI * 2,
        }));
        function draw(t) {
            ctx.clearRect(0, 0, c.width, c.height);
            stars.forEach(s => {
                const op = s.base + Math.sin(t * s.speed * 1000 + s.phase) * 0.12;
                ctx.beginPath();
                ctx.arc(s.x * c.width, s.y * c.height, s.r, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(255,255,255,${Math.max(0, op)})`;
                ctx.fill();
            });
            requestAnimationFrame(draw);
        }
        requestAnimationFrame(draw);
    }
    setTimeout(init, 400);
})();
</script>

<!-- TOP BAR HTML -->
<div class="top-bar">
    <div class="top-logo">🎯 Orion <span>Signals</span></div>
    <div id="lang-display" class="lang-btn">🌐 EN / ΕΛ</div>
</div>
<div class="top-spacer"></div>
""", unsafe_allow_html=True)

# ── SESSION STATE ──
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "lang" not in st.session_state:
    st.session_state.lang = "EN"

# ── ROUTING ──
if st.session_state.logged_in and st.session_state.user:
    user = st.session_state.user
    if is_pro(user):
        from pro_app import show_pro_dashboard
        show_pro_dashboard(user)
    else:
        from entry_app import show_entry_dashboard
        show_entry_dashboard(user)
    st.stop()

# ── TRANSLATIONS ──
T = {
    "EN": {
        "tagline": "See through the noise",
        "signin": "Sign In", "signup": "Sign Up",
        "email": "Email", "email_ph": "your@email.com",
        "pass": "Password", "pass_ph": "enter password",
        "name": "Full Name", "name_ph": "John Doe",
        "confirm": "Confirm Password", "confirm_ph": "repeat password",
        "signin_btn": "Sign In →", "signup_btn": "Create Account →",
        "wrong": "❌ Wrong email or password.",
        "fill": "Please fill in all fields.",
        "coming": "ℹ️ Registration coming soon. Use demo accounts.",
        "footer": "© 2026 Orion Signals · Educational tool · Not financial advice",
        "demo": "Demo accounts",
        "lang_switch": "🌐 Ελληνικά",
    },
    "EL": {
        "tagline": "Δες μέσα από τον θόρυβο",
        "signin": "Σύνδεση", "signup": "Εγγραφή",
        "email": "Email", "email_ph": "το@email.σου",
        "pass": "Κωδικός", "pass_ph": "εισάγετε κωδικό",
        "name": "Ονοματεπώνυμο", "name_ph": "Γιάννης Παπαδόπουλος",
        "confirm": "Επιβεβαίωση", "confirm_ph": "επαναλάβετε κωδικό",
        "signin_btn": "Σύνδεση →", "signup_btn": "Δημιουργία Λογαριασμού →",
        "wrong": "❌ Λάθος email ή κωδικός.",
        "fill": "Συμπλήρωσε όλα τα πεδία.",
        "coming": "ℹ️ Η εγγραφή έρχεται σύντομα.",
        "footer": "© 2026 Orion Signals · Εκπαιδευτικό εργαλείο · Όχι επενδυτική συμβουλή",
        "demo": "Demo λογαριασμοί",
        "lang_switch": "🌐 English",
    }
}

lang = st.session_state.lang
t = T[lang]

# ── LANGUAGE BUTTON (top right via Streamlit) ──
col_spacer, col_lang = st.columns([5, 1])
with col_lang:
    if st.button(t["lang_switch"], key="lang_btn"):
        st.session_state.lang = "EL" if lang == "EN" else "EN"
        st.rerun()

# ── LOGO ──
st.markdown(f"""
<div class="logo-wrap">
    <span class="logo-icon">🎯</span>
    <h1 class="logo-title">Orion <span>Signals</span></h1>
    <p class="logo-tagline">{t['tagline']}</p>
</div>
""", unsafe_allow_html=True)

# ── TABS ──
tab_in, tab_up = st.tabs([t["signin"], t["signup"]])

with tab_in:
    email    = st.text_input(t["email"],   placeholder=t["email_ph"],   key="si_email")
    password = st.text_input(t["pass"],    type="password", placeholder=t["pass_ph"], key="si_pass")

    if st.button(t["signin_btn"], key="signin_btn"):
        if not email or not password:
            st.error(t["fill"])
        else:
            user = login(email, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.rerun()
            else:
                st.error(t["wrong"])

    st.markdown(f"""
    <div class="or-divider">{t['demo']}</div>
    <div style="font-size:0.72rem;color:rgba(255,255,255,0.22);text-align:center;line-height:2.2;">
        <span style="background:rgba(124,58,237,0.2);color:#A78BFA;border:1px solid rgba(124,58,237,0.3);
              padding:2px 8px;border-radius:10px;font-size:0.68rem;">⚡ Pro</span>
        &nbsp; pro@orion.com &nbsp;/&nbsp; pro123<br>
        <span style="background:rgba(255,255,255,0.06);color:rgba(255,255,255,0.45);
              border:1px solid rgba(255,255,255,0.1);padding:2px 8px;border-radius:10px;font-size:0.68rem;">Entry</span>
        &nbsp; entry@orion.com &nbsp;/&nbsp; entry123
    </div>
    """, unsafe_allow_html=True)

with tab_up:
    su_name    = st.text_input(t["name"],    placeholder=t["name_ph"],    key="su_name")
    su_email   = st.text_input(t["email"],   placeholder=t["email_ph"],   key="su_email")
    su_pass    = st.text_input(t["pass"],    type="password", placeholder=t["pass_ph"],    key="su_pass")
    su_confirm = st.text_input(t["confirm"], type="password", placeholder=t["confirm_ph"], key="su_confirm")

    if st.button(t["signup_btn"], key="signup_btn"):
        st.info(t["coming"])

st.markdown(f'<div class="login-footer">{t["footer"]}</div>', unsafe_allow_html=True)
