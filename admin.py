"""
Orion Signals — Admin Dashboard
Βλέπει όλους τους users, subscriptions, στατιστικά.
"""
import streamlit as st
import pandas as pd
from auth import get_all_users, get_stats, PLAN_PRICES, USERS

def show_admin_dashboard(user):
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=Inter:wght@300;400;500&display=swap');
    #MainMenu,footer,.stDeployButton{display:none!important}
    [data-testid="stToolbar"]{display:none!important}
    .stApp{background:#080810;font-family:'Inter',sans-serif;color:#E2E8F0}
    [data-testid="stSidebar"]{background:#0D0D1A!important;border-right:1px solid rgba(124,58,237,0.15)!important}
    [data-testid="stSidebar"] *{color:#E2E8F0!important}
    .admin-header{display:flex;align-items:center;justify-content:space-between;
        padding:1rem 0 1.5rem;border-bottom:1px solid rgba(124,58,237,0.2);margin-bottom:1.5rem}
    .admin-logo{font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:800;color:#fff}
    .admin-logo span{color:#7C3AED}
    .admin-badge{background:rgba(239,68,68,0.15);color:#FCA5A5;
        border:1px solid rgba(239,68,68,0.3);padding:0.25rem 0.75rem;
        border-radius:20px;font-size:0.75rem;font-weight:600;letter-spacing:0.08em}
    [data-testid="metric-container"]{background:rgba(255,255,255,0.03)!important;
        border:1px solid rgba(124,58,237,0.15)!important;border-radius:12px!important;padding:1rem!important}
    [data-testid="metric-container"] label{color:rgba(255,255,255,0.5)!important;
        font-size:0.75rem!important;text-transform:uppercase!important;letter-spacing:0.08em!important}
    [data-testid="metric-container"] [data-testid="stMetricValue"]{color:#fff!important;
        font-family:'Syne',sans-serif!important;font-size:1.4rem!important}
    .stButton>button{background:linear-gradient(135deg,#7C3AED,#5B21B6)!important;
        color:white!important;border:none!important;border-radius:8px!important;
        font-family:'Syne',sans-serif!important;font-weight:700!important;
        transition:all 0.2s!important}
    .status-active{color:#00C853;font-weight:600}
    .status-inactive{color:#FF3D57;font-weight:600}
    .stTabs [data-baseweb="tab-list"]{background:transparent!important;
        border-bottom:1px solid rgba(124,58,237,0.2)!important;gap:0!important}
    .stTabs [data-baseweb="tab"]{background:transparent!important;
        color:rgba(255,255,255,0.4)!important;font-size:0.9rem!important;
        padding:0.75rem 1.5rem!important;border:none!important}
    .stTabs [aria-selected="true"]{color:#7C3AED!important;border-bottom:2px solid #7C3AED!important}
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="admin-header">
        <div class="admin-logo">🎯 Orion <span>Signals</span></div>
        <span class="admin-badge">⚡ ADMIN</span>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown(f"**👤 {user['name']}**")
        st.markdown("*Administrator*")
        st.markdown("---")
        if st.button("🚪 Logout"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    # Stats
    stats = get_stats()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Users",   stats["total_users"])
    c2.metric("Active",        stats["active"],
              delta=f"+{stats['active']} paying")
    c3.metric("Inactive",      stats["inactive"],
              delta=f"-{stats['inactive']}" if stats["inactive"] > 0 else "0",
              delta_color="inverse")
    c4.metric("MRR",           f"€{stats['mrr']}",
              delta=f"€{stats['mrr']}/mo")

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["👥 Users", "📊 Plans", "⚙️ Settings"])

    # ── TAB 1: USERS ──
    with tab1:
        st.markdown("#### All Users")

        all_users = get_all_users()
        df = pd.DataFrame(all_users)

        # Filter
        col1, col2 = st.columns(2)
        filter_plan = col1.selectbox("Filter by Plan",
                                      ["All"] + list(set(u["plan"] for u in all_users)))
        filter_status = col2.selectbox("Filter by Status",
                                        ["All", "active", "inactive"])

        if filter_plan != "All":
            df = df[df["plan"] == filter_plan]
        if filter_status != "All":
            df = df[df["subscription"] == filter_status]

        # Display
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("#### Manage User")

        col1, col2 = st.columns(2)
        sel_email = col1.selectbox("Select User",
                                    [u["email"] for u in all_users if u["role"] != "admin"])
        new_status = col2.selectbox("Set Subscription",
                                     ["active", "inactive"])

        if st.button("Update Subscription →", key="update_sub"):
            if sel_email in USERS:
                USERS[sel_email]["subscription"] = new_status
                st.success(f"✅ {sel_email} → {new_status}")
                st.rerun()

    # ── TAB 2: PLANS ──
    with tab2:
        st.markdown("#### Plan Distribution")

        plan_data = stats["plan_counts"]
        if plan_data:
            df_plans = pd.DataFrame([
                {"Plan": k, "Users": v, "MRR": f"€{v * PLAN_PRICES.get(k, 0)}"}
                for k, v in plan_data.items()
            ])
            st.dataframe(df_plans, use_container_width=True, hide_index=True)
        else:
            st.info("No active users yet.")

        st.markdown("#### Pricing")
        for plan, price in PLAN_PRICES.items():
            st.markdown(f"**{plan.capitalize()}**: €{price}/month")

    # ── TAB 3: SETTINGS ──
    with tab3:
        st.markdown("#### System Settings")
        st.info("Database integration, Stripe payments, and Telegram bot settings coming soon.")

        st.markdown("""
        <div style="background:rgba(124,58,237,0.08);border:1px solid rgba(124,58,237,0.2);
                    border-radius:10px;padding:1rem;margin-top:1rem;font-size:0.82rem;color:rgba(255,255,255,0.6);">
            <strong style="color:#A78BFA;">Coming Soon:</strong><br><br>
            🔧 PostgreSQL database connection<br>
            💳 Stripe payment management<br>
            📱 Telegram bot configuration<br>
            📧 Email notifications<br>
            📊 Revenue analytics
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.caption("⚠️ Admin panel — handle with care.")
