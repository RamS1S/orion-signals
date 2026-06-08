"""
Orion Signals — Main Entry Point
Login page με Sign In / Sign Up + γλώσσα + αστερισμός Ωρίωνα
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

/* ── STARFIELD ── */
.star-canvas {
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    pointer-events: none;
    z-index: 0;
}

/* Orion constellation SVG overlay */
.orion-svg {
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    pointer-events: none;
    z-index: 1;
    opacity: 0.6;
}

/* Nebula glow */
.stApp::after {
    content: '';
    position: fixed;
    bottom: -100px;
    left: 50%;
    transform: translateX(-50%);
    width: 800px;
    height: 400px;
    background: radial-gradient(ellipse, rgba(124,58,237,0.08) 0%, rgba(59,130,246,0.05) 40%, transparent 70%);
    pointer-events: none;
    z-index: 0;
}

/* Main content above stars */
.block-container {
    position: relative;
    z-index: 10;
}

/* Logo */
.logo-wrap {
    text-align: center;
    margin-bottom: 1.8rem;
    animation: fadeInDown 0.9s ease;
}

.logo-icon {
    font-size: 3rem;
    display: block;
    filter: drop-shadow(0 0 25px rgba(124,58,237,0.9));
    margin-bottom: 0.3rem;
}

.logo-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.6rem;
    font-weight: 800;
    color: #fff;
    letter-spacing: -0.03em;
    margin: 0;
    line-height: 1;
    text-shadow: 0 0 40px rgba(124,58,237,0.4);
}

.logo-title span { color: #7C3AED; }

.logo-tagline {
    font-size: 0.78rem;
    color: rgba(255,255,255,0.3);
    letter-spacing: 0.25em;
    text-transform: uppercase;
    margin-top: 0.4rem;
}

/* Language toggle */
.lang-toggle {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 0.5rem;
}

/* Card */
.login-card {
    background: rgba(8,8,20,0.7);
    border: 1px solid rgba(124,58,237,0.25);
    border-radius: 16px;
    padding: 2rem;
    backdrop-filter: blur(20px);
    animation: fadeInUp 0.9s ease 0.15s both;
}

/* Tabs override */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.03) !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid rgba(124,58,237,0.15) !important;
    margin-bottom: 1.5rem !important;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: rgba(255,255,255,0.4) !important;
    border-radius: 7px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.05em !important;
    padding: 0.5rem 1.5rem !important;
    border: none !important;
    transition: all 0.2s !important;
}

.stTabs [aria-selected="true"] {
    background: rgba(124,58,237,0.3) !important;
    color: #ffffff !important;
    border: none !important;
}

/* Inputs */
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(124,58,237,0.25) !important;
    border-radius: 8px !important;
    color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.85rem !important;
    padding: 0.6rem 0.9rem !important;
    transition: all 0.2s !important;
}

.stTextInput > div > div > input:focus {
    border-color: rgba(124,58,237,0.7) !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.12) !important;
    background: rgba(124,58,237,0.04) !important;
}

.stTextInput > div > div > input::placeholder {
    color: rgba(255,255,255,0.18) !important;
    font-size: 0.8rem !important;
}

.stTextInput label {
    color: rgba(255,255,255,0.45) !important;
    font-size: 0.75rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}

/* Button */
.stButton > button {
    background: linear-gradient(135deg, #7C3AED 0%, #4F1D96 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.08em !important;
    width: 100% !important;
    padding: 0.65rem !important;
    margin-top: 0.3rem !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 20px rgba(124,58,237,0.35) !important;
}

.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 28px rgba(124,58,237,0.55) !important;
}

/* Divider */
.or-divider {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin: 1rem 0;
    color: rgba(255,255,255,0.2);
    font-size: 0.75rem;
    letter-spacing: 0.1em;
}
.or-divider::before, .or-divider::after {
    content: '';
    flex: 1;
    height: 1px;
    background: rgba(255,255,255,0.08);
}

/* Footer */
.login-footer {
    text-align: center;
    margin-top: 1.5rem;
    color: rgba(255,255,255,0.15);
    font-size: 0.7rem;
    letter-spacing: 0.05em;
    animation: fadeIn 1.2s ease 0.4s both;
}

/* Constellation label */
.constellation-label {
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    color: rgba(255,255,255,0.15);
    font-size: 0.65rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    z-index: 5;
}

@keyframes fadeInDown {
    from { opacity: 0; transform: translateY(-16px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
}
@keyframes twinkle {
    0%, 100% { opacity: 0.3; }
    50%       { opacity: 1; }
}
@keyframes pulse-star {
    0%, 100% { r: 2; opacity: 0.8; }
    50%       { r: 3; opacity: 1; }
}
</style>

<!-- Orion Constellation SVG -->
<svg class="orion-svg" viewBox="0 0 1440 900" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="starGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="1"/>
      <stop offset="100%" stop-color="#7C3AED" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="brightStar" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="1"/>
      <stop offset="60%" stop-color="#A78BFA" stop-opacity="0.3"/>
      <stop offset="100%" stop-color="#7C3AED" stop-opacity="0"/>
    </radialGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
      <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="brightGlow">
      <feGaussianBlur stdDeviation="5" result="coloredBlur"/>
      <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>

  <!-- Random background stars -->
  <circle cx="50" cy="80" r="0.8" fill="white" opacity="0.4" style="animation: twinkle 3s infinite 0.2s"/>
  <circle cx="120" cy="200" r="0.6" fill="white" opacity="0.3" style="animation: twinkle 4s infinite 1s"/>
  <circle cx="200" cy="50" r="1" fill="white" opacity="0.5" style="animation: twinkle 2.5s infinite 0.5s"/>
  <circle cx="350" cy="150" r="0.7" fill="white" opacity="0.35" style="animation: twinkle 3.5s infinite 1.5s"/>
  <circle cx="500" cy="30" r="0.9" fill="white" opacity="0.45" style="animation: twinkle 2s infinite 0.8s"/>
  <circle cx="650" cy="100" r="0.6" fill="white" opacity="0.3"/>
  <circle cx="750" cy="50" r="1.1" fill="white" opacity="0.5" style="animation: twinkle 3s infinite 2s"/>
  <circle cx="900" cy="120" r="0.8" fill="white" opacity="0.4" style="animation: twinkle 4s infinite 0.3s"/>
  <circle cx="1050" cy="60" r="0.7" fill="white" opacity="0.35"/>
  <circle cx="1200" cy="180" r="0.9" fill="white" opacity="0.45" style="animation: twinkle 2.8s infinite 1.2s"/>
  <circle cx="1350" cy="80" r="0.6" fill="white" opacity="0.3" style="animation: twinkle 3.2s infinite 0.7s"/>
  <circle cx="80" cy="400" r="0.8" fill="white" opacity="0.35"/>
  <circle cx="180" cy="500" r="1" fill="white" opacity="0.4" style="animation: twinkle 3.8s infinite 1.8s"/>
  <circle cx="300" cy="350" r="0.7" fill="white" opacity="0.3"/>
  <circle cx="420" cy="450" r="0.9" fill="white" opacity="0.45" style="animation: twinkle 2.5s infinite 0.4s"/>
  <circle cx="1100" cy="300" r="0.8" fill="white" opacity="0.4"/>
  <circle cx="1280" cy="420" r="1" fill="white" opacity="0.5" style="animation: twinkle 3s infinite 1.6s"/>
  <circle cx="1380" cy="350" r="0.7" fill="white" opacity="0.3" style="animation: twinkle 4s infinite 0.9s"/>
  <circle cx="60" cy="700" r="0.9" fill="white" opacity="0.4" style="animation: twinkle 2.8s infinite 2.2s"/>
  <circle cx="200" cy="750" r="0.6" fill="white" opacity="0.3"/>
  <circle cx="400" cy="800" r="0.8" fill="white" opacity="0.35" style="animation: twinkle 3.5s infinite 1.1s"/>
  <circle cx="600" cy="820" r="1" fill="white" opacity="0.45"/>
  <circle cx="800" cy="780" r="0.7" fill="white" opacity="0.3" style="animation: twinkle 2.5s infinite 0.6s"/>
  <circle cx="1000" cy="850" r="0.9" fill="white" opacity="0.4" style="animation: twinkle 3s infinite 1.9s"/>
  <circle cx="1200" cy="760" r="0.8" fill="white" opacity="0.35"/>
  <circle cx="1400" cy="800" r="1.1" fill="white" opacity="0.5" style="animation: twinkle 4s infinite 0.1s"/>

  <!-- ═══ ORION CONSTELLATION ═══ -->
  <!-- Positioned right side of screen -->

  <!-- Constellation lines (subtle) -->
  <!-- Betelgeuse to Belt -->
  <line x1="1050" y1="280" x2="980" y2="430" stroke="rgba(167,139,250,0.15)" stroke-width="0.8"/>
  <!-- Bellatrix to Belt -->
  <line x1="1150" y1="300" x2="1020" y2="430" stroke="rgba(167,139,250,0.15)" stroke-width="0.8"/>
  <!-- Belt stars -->
  <line x1="980" y1="430" x2="1020" y2="430" stroke="rgba(167,139,250,0.2)" stroke-width="0.8"/>
  <line x1="1020" y1="430" x2="1060" y2="425" stroke="rgba(167,139,250,0.2)" stroke-width="0.8"/>
  <!-- Belt to feet -->
  <line x1="980" y1="430" x2="940" y2="580" stroke="rgba(167,139,250,0.15)" stroke-width="0.8"/>
  <line x1="1060" y1="425" x2="1100" y2="575" stroke="rgba(167,139,250,0.15)" stroke-width="0.8"/>
  <!-- Shoulders to head -->
  <line x1="1050" y1="280" x2="1100" y2="180" stroke="rgba(167,139,250,0.12)" stroke-width="0.8"/>
  <line x1="1150" y1="300" x2="1100" y2="180" stroke="rgba(167,139,250,0.12)" stroke-width="0.8"/>
  <!-- Arm -->
  <line x1="1150" y1="300" x2="1250" y2="360" stroke="rgba(167,139,250,0.1)" stroke-width="0.8"/>
  <!-- Sword (below belt) -->
  <line x1="1020" y1="430" x2="1010" y2="510" stroke="rgba(167,139,250,0.18)" stroke-width="0.8"/>

  <!-- BETELGEUSE (left shoulder - reddish, bright) -->
  <circle cx="1050" cy="280" r="12" fill="radial-gradient(circle, rgba(239,68,68,0.3), transparent)" opacity="0.4"/>
  <circle cx="1050" cy="280" r="4" fill="#FCA5A5" opacity="0.9" filter="url(#brightGlow)"
          style="animation: twinkle 2.5s infinite 0s"/>
  <circle cx="1050" cy="280" r="1.5" fill="#ffffff"/>

  <!-- BELLATRIX (right shoulder - blue-white) -->
  <circle cx="1150" cy="300" r="8" fill="rgba(147,197,253,0.2)" opacity="0.5"/>
  <circle cx="1150" cy="300" r="3" fill="#BFDBFE" opacity="0.9" filter="url(#glow)"
          style="animation: twinkle 3s infinite 0.5s"/>
  <circle cx="1150" cy="300" r="1.2" fill="#ffffff"/>

  <!-- HEAD (small cluster) -->
  <circle cx="1095" cy="175" r="1.5" fill="white" opacity="0.6" style="animation: twinkle 4s infinite 1s"/>
  <circle cx="1110" cy="168" r="1" fill="white" opacity="0.4"/>
  <circle cx="1080" cy="182" r="1.2" fill="white" opacity="0.5" style="animation: twinkle 3s infinite 2s"/>

  <!-- BELT - ALNITAK (left) -->
  <circle cx="980" cy="432" r="6" fill="rgba(167,139,250,0.2)" opacity="0.6"/>
  <circle cx="980" cy="432" r="2.5" fill="#C4B5FD" opacity="0.95" filter="url(#glow)"
          style="animation: twinkle 2.8s infinite 0.3s"/>
  <circle cx="980" cy="432" r="1" fill="#ffffff"/>

  <!-- BELT - ALNILAM (middle) -->
  <circle cx="1022" cy="428" r="7" fill="rgba(167,139,250,0.25)" opacity="0.6"/>
  <circle cx="1022" cy="428" r="3" fill="#DDD6FE" opacity="0.95" filter="url(#brightGlow)"
          style="animation: twinkle 2s infinite 0.8s"/>
  <circle cx="1022" cy="428" r="1.2" fill="#ffffff"/>

  <!-- BELT - MINTAKA (right) -->
  <circle cx="1062" cy="424" r="6" fill="rgba(167,139,250,0.2)" opacity="0.6"/>
  <circle cx="1062" cy="424" r="2.5" fill="#C4B5FD" opacity="0.95" filter="url(#glow)"
          style="animation: twinkle 3.2s infinite 1.3s"/>
  <circle cx="1062" cy="424" r="1" fill="#ffffff"/>

  <!-- SWORD (Orion Nebula area) -->
  <circle cx="1012" cy="480" r="1.8" fill="white" opacity="0.5" style="animation: twinkle 3s infinite 0.6s"/>
  <circle cx="1015" cy="510" r="14" fill="rgba(124,58,237,0.08)" opacity="0.8"/>
  <circle cx="1015" cy="510" r="2.5" fill="#A78BFA" opacity="0.6" filter="url(#glow)"/>
  <circle cx="1015" cy="510" r="1" fill="white" opacity="0.8"/>
  <circle cx="1018" cy="540" r="1.5" fill="white" opacity="0.4" style="animation: twinkle 4s infinite 1.5s"/>

  <!-- RIGEL (right foot - blue-white, very bright) -->
  <circle cx="1100" cy="580" r="15" fill="rgba(147,197,253,0.1)" opacity="0.6"/>
  <circle cx="1100" cy="580" r="5" fill="#93C5FD" opacity="0.9" filter="url(#brightGlow)"
          style="animation: twinkle 1.8s infinite 0s"/>
  <circle cx="1100" cy="580" r="2" fill="#ffffff"/>

  <!-- SAIPH (left foot) -->
  <circle cx="940" cy="582" r="10" fill="rgba(167,139,250,0.15)" opacity="0.5"/>
  <circle cx="940" cy="582" r="3.5" fill="#C4B5FD" opacity="0.85" filter="url(#glow)"
          style="animation: twinkle 2.2s infinite 1s"/>
  <circle cx="940" cy="582" r="1.5" fill="#ffffff"/>

  <!-- ARM extended star -->
  <circle cx="1250" cy="362" r="2" fill="white" opacity="0.5" style="animation: twinkle 3s infinite 0.7s"/>
  <circle cx="1280" cy="380" r="1.5" fill="white" opacity="0.4"/>

  <!-- Constellation label -->
  <text x="1060" y="650" fill="rgba(167,139,250,0.3)" font-size="10"
        font-family="Inter, sans-serif" letter-spacing="3" text-anchor="middle">ORION</text>
</svg>

<script>
// Starfield canvas
const canvas = document.createElement('canvas');
canvas.className = 'star-canvas';
document.body.appendChild(canvas);
const ctx = canvas.getContext('2d');

function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}
resize();
window.addEventListener('resize', resize);

const stars = Array.from({length: 180}, () => ({
    x: Math.random() * window.innerWidth,
    y: Math.random() * window.innerHeight,
    r: Math.random() * 1.2 + 0.2,
    opacity: Math.random() * 0.5 + 0.1,
    speed: Math.random() * 0.01 + 0.003,
    phase: Math.random() * Math.PI * 2,
}));

function drawStars(t) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    stars.forEach(s => {
        const op = s.opacity + Math.sin(t * s.speed + s.phase) * 0.15;
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255,255,255,${Math.max(0, op)})`;
        ctx.fill();
    });
    requestAnimationFrame(drawStars);
}
requestAnimationFrame(drawStars);
</script>
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
        "signin": "Sign In",
        "signup": "Sign Up",
        "email": "Email",
        "email_ph": "your@email.com",
        "pass": "Password",
        "pass_ph": "••••••••",
        "name": "Full Name",
        "name_ph": "John Doe",
        "confirm": "Confirm Password",
        "confirm_ph": "••••••••",
        "signin_btn": "Sign In →",
        "signup_btn": "Create Account →",
        "wrong": "❌ Wrong email or password.",
        "fill": "Please fill in all fields.",
        "coming": "ℹ️ Registration coming soon. Use demo accounts below.",
        "footer": "© 2026 Orion Signals · Educational tool · Not financial advice",
        "demo": "Demo accounts",
    },
    "EL": {
        "tagline": "Δες μέσα από τον θόρυβο",
        "signin": "Σύνδεση",
        "signup": "Εγγραφή",
        "email": "Email",
        "email_ph": "το@email.σου",
        "pass": "Κωδικός",
        "pass_ph": "••••••••",
        "name": "Ονοματεπώνυμο",
        "name_ph": "Γιάννης Παπαδόπουλος",
        "confirm": "Επιβεβαίωση Κωδικού",
        "confirm_ph": "••••••••",
        "signin_btn": "Σύνδεση →",
        "signup_btn": "Δημιουργία Λογαριασμού →",
        "wrong": "❌ Λάθος email ή κωδικός.",
        "fill": "Συμπλήρωσε όλα τα πεδία.",
        "coming": "ℹ️ Η εγγραφή έρχεται σύντομα. Χρησιμοποίησε τους demo λογαριασμούς.",
        "footer": "© 2026 Orion Signals · Εκπαιδευτικό εργαλείο · Όχι επενδυτική συμβουλή",
        "demo": "Demo λογαριασμοί",
    }
}

lang = st.session_state.lang
t = T[lang]

# ── LANGUAGE TOGGLE ──
col_lang = st.columns([4, 1])
with col_lang[1]:
    if st.button("🌐 EL" if lang == "EN" else "🌐 EN"):
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

# ── TABS: SIGN IN / SIGN UP ──
tab_in, tab_up = st.tabs([t["signin"], t["signup"]])

with tab_in:
    email = st.text_input(t["email"], placeholder=t["email_ph"], key="si_email")
    password = st.text_input(t["pass"], type="password", placeholder=t["pass_ph"], key="si_pass")

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
    <div style="font-size:0.75rem; color:rgba(255,255,255,0.25); text-align:center; line-height:2.2;">
        <span style="background:rgba(124,58,237,0.2);color:#A78BFA;border:1px solid rgba(124,58,237,0.3);
              padding:2px 8px;border-radius:10px;font-size:0.7rem;">⚡ Pro</span>
        &nbsp; pro@orion.com &nbsp;/&nbsp; pro123<br>
        <span style="background:rgba(255,255,255,0.07);color:rgba(255,255,255,0.5);border:1px solid rgba(255,255,255,0.1);
              padding:2px 8px;border-radius:10px;font-size:0.7rem;">Entry</span>
        &nbsp; entry@orion.com &nbsp;/&nbsp; entry123
    </div>
    """, unsafe_allow_html=True)

with tab_up:
    su_name = st.text_input(t["name"], placeholder=t["name_ph"], key="su_name")
    su_email = st.text_input(t["email"], placeholder=t["email_ph"], key="su_email")
    su_pass = st.text_input(t["pass"], type="password", placeholder=t["pass_ph"], key="su_pass")
    su_confirm = st.text_input(t["confirm"], type="password", placeholder=t["confirm_ph"], key="su_confirm")

    if st.button(t["signup_btn"], key="signup_btn"):
        st.info(t["coming"])

st.markdown(f'<div class="login-footer">{t["footer"]}</div>', unsafe_allow_html=True)

