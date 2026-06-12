"""
Orion Signals — Admin Dashboard
Full access: όλα τα dashboards + user management.
"""
import streamlit as st
import pandas as pd
from auth import get_all_users, get_stats, PLAN_PRICES, USERS, PLAN_NAMES

def show_admin_dashboard(user):
    # Override layout σε wide για admin
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=Inter:wght@300;400;500&display=swap');
    #MainMenu,footer,.stDeployButton{display:none!important}
    [data-testid="stToolbar"]{display:none!important}
    .stApp{background:#080810;font-family:'Inter',sans-serif;color:#E2E8F0}
    [data-testid="stSidebar"]{background:#0D0D1A!important;border-right:1px solid rgba(124,58,237,0.15)!important}
    [data-testid="stSidebar"] *{color:#E2E8F0!important}
    .block-container{max-width:100%!important;padding:1rem 2rem!important}
    .admin-header{display:flex;align-items:center;justify-content:space-between;
        padding:1rem 0 1.5rem;border-bottom:1px solid rgba(239,68,68,0.2);margin-bottom:1.5rem}
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
        transition:all 0.2s!important;box-shadow:0 4px 15px rgba(124,58,237,0.3)!important}
    .stTabs [data-baseweb="tab-list"]{background:transparent!important;
        border-bottom:1px solid rgba(124,58,237,0.2)!important;gap:0!important}
    .stTabs [data-baseweb="tab"]{background:transparent!important;
        color:rgba(255,255,255,0.4)!important;font-size:0.9rem!important;
        padding:0.75rem 1.5rem!important;border:none!important}
    .stTabs [aria-selected="true"]{color:#7C3AED!important;border-bottom:2px solid #7C3AED!important}
    .stTextInput>div>div>input,.stSelectbox>div>div{background:rgba(255,255,255,0.05)!important;
        border:1px solid rgba(124,58,237,0.3)!important;border-radius:8px!important;color:#fff!important}
    .status-active{color:#00C853;font-weight:600}
    .status-inactive{color:#FF3D57;font-weight:600}
    .user-card{background:rgba(255,255,255,0.02);border:1px solid rgba(124,58,237,0.15);
        border-radius:10px;padding:0.8rem 1rem;margin-bottom:0.5rem}
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="admin-header">
        <div class="admin-logo">🎯 Orion <span>Signals</span></div>
        <span class="admin-badge">⚡ ADMIN PANEL</span>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown(f"**👤 {user['name']}**")
        st.markdown("*Administrator*")
        st.markdown("---")

        st.markdown("**🎯 Quick Access**")
        st.caption("Launch any dashboard:")

        if st.button("📈 Entry Dashboard", key="admin_entry"):
            st.session_state.admin_view = "entry"
            st.rerun()
        if st.button("⚡ Pro Dashboard", key="admin_pro"):
            st.session_state.admin_view = "pro"
            st.rerun()
        if st.button("₿ Crypto Dashboard", key="admin_crypto"):
            st.session_state.admin_view = "crypto"
            st.rerun()
        if st.button("🌐 Combined Dashboard", key="admin_combined"):
            st.session_state.admin_view = "combined"
            st.rerun()

        st.markdown("---")
        if st.button("🏠 Back to Admin Panel", key="admin_home"):
            st.session_state.admin_view = None
            st.rerun()
        st.markdown("---")
        if st.button("🚪 Logout"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    # ── ADMIN VIEW ROUTING ──
    if "admin_view" not in st.session_state:
        st.session_state.admin_view = None

    admin_view = st.session_state.admin_view

    # Launch Entry
    if admin_view == "entry":
        col1, col2 = st.columns([1,5])
        with col1:
            if st.button("← Admin", key="back_entry"):
                st.session_state.admin_view = None
                st.rerun()
        admin_user = {**user, "plan": "entry", "subscription": "active"}
        from entry_app import show_entry_dashboard
        show_entry_dashboard(admin_user)
        return

    # Launch Pro
    if admin_view == "pro":
        col1, col2 = st.columns([1,5])
        with col1:
            if st.button("← Admin", key="back_pro"):
                st.session_state.admin_view = None
                st.rerun()
        admin_user = {**user, "plan": "pro", "subscription": "active"}
        from pro_app import show_pro_dashboard
        show_pro_dashboard(admin_user)
        return

    # Launch Crypto Entry
    if admin_view == "crypto_entry":
        col1, col2 = st.columns([1,5])
        with col1:
            if st.button("← Admin", key="back_crypto_entry"):
                st.session_state.admin_view = None
                st.rerun()
        admin_user = {**user, "plan": "crypto_entry", "subscription": "active"}
        from crypto_entry_app import show_crypto_entry_dashboard
        show_crypto_entry_dashboard(admin_user)
        return

    # Launch Crypto Pro
    if admin_view == "crypto_pro":
        col1, col2 = st.columns([1,5])
        with col1:
            if st.button("← Admin", key="back_crypto_pro"):
                st.session_state.admin_view = None
                st.rerun()
        admin_user = {**user, "plan": "crypto_pro", "subscription": "active"}
        from crypto_pro_app import show_crypto_pro_dashboard
        show_crypto_pro_dashboard(admin_user)
        return

    # Launch Combined
    if admin_view == "combined":
        col1, col2 = st.columns([1,5])
        with col1:
            if st.button("← Admin", key="back_combined"):
                st.session_state.admin_view = None
                st.rerun()
        admin_user = {**user, "plan": "combined", "subscription": "active"}
        from combined_app import show_combined_dashboard
        show_combined_dashboard(admin_user)
        return

    # ── MAIN ADMIN PANEL ──
    stats = get_stats()

    # Quick Access
    st.markdown("#### 🎯 Launch Dashboard")
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1:
        if st.button("📈 Stocks Entry", key="qa_entry", use_container_width=True):
            st.session_state.admin_view = "entry"
            st.rerun()
    with c2:
        if st.button("⚡ Stocks Pro", key="qa_pro", use_container_width=True):
            st.session_state.admin_view = "pro"
            st.rerun()
    with c3:
        if st.button("₿ Crypto Entry", key="qa_crypto_entry", use_container_width=True):
            st.session_state.admin_view = "crypto_entry"
            st.rerun()
    with c4:
        if st.button("🚀 Crypto Pro", key="qa_crypto_pro", use_container_width=True):
            st.session_state.admin_view = "crypto_pro"
            st.rerun()
    with c5:
        if st.button("🌐 Combined", key="qa_combined", use_container_width=True):
            st.session_state.admin_view = "combined"
            st.rerun()

    st.markdown("---")

    # Stats row
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Total Users",  stats["total_users"])
    c2.metric("Active",       stats["active"])
    c3.metric("Inactive",     stats["inactive"],
              delta=f"-{stats['inactive']}" if stats["inactive"]>0 else None,
              delta_color="inverse")
    c4.metric("MRR",          f"€{stats['mrr']}")
    c5.metric("ARR",          f"€{stats['mrr']*12:,}")

    st.markdown("---")

    # Tabs
    tab1,tab2,tab3,tab4 = st.tabs([
        "👥 Users",
        "📊 Analytics",
        "⚙️ User Management",
        "🔑 Admin Rights"
    ])

    # ── TAB 1: USERS ──
    with tab1:
        st.markdown("#### All Users")

        all_users = get_all_users()
        df = pd.DataFrame(all_users)

        c1,c2,c3 = st.columns(3)
        fp = c1.selectbox("Plan",   ["All"]+list(set(u["plan"] for u in all_users)))
        fs = c2.selectbox("Status", ["All","active","inactive"])
        fr = c3.selectbox("Role",   ["All","user","admin"])

        dff = df.copy()
        if fp != "All": dff = dff[dff["plan"]==fp]
        if fs != "All": dff = dff[dff["subscription"]==fs]
        if fr != "All": dff = dff[dff["role"]==fr]

        st.dataframe(dff, use_container_width=True, hide_index=True)

        st.caption(f"Showing {len(dff)} of {len(df)} users")

    # ── TAB 2: ANALYTICS ──
    with tab2:
        st.markdown("#### Plan Distribution")

        plan_data = stats["plan_counts"]
        if plan_data:
            col1, col2 = st.columns(2)
            with col1:
                df_plans = pd.DataFrame([{
                    "Plan":    PLAN_NAMES.get(k, k),
                    "Users":   v,
                    "Revenue": f"€{v * PLAN_PRICES.get(k, 0)}/mo"
                } for k,v in plan_data.items()])
                st.dataframe(df_plans, use_container_width=True, hide_index=True)

            with col2:
                st.markdown("**Revenue Breakdown**")
                for plan,count in plan_data.items():
                    price = PLAN_PRICES.get(plan, 0)
                    rev = count * price
                    pct = (rev / stats["mrr"] * 100) if stats["mrr"] > 0 else 0
                    st.markdown(f"""
                    <div style="margin-bottom:0.5rem;">
                        <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
                            <span style="font-size:0.82rem;color:rgba(255,255,255,0.7);">{PLAN_NAMES.get(plan,plan)}</span>
                            <span style="font-size:0.82rem;color:#A78BFA;">€{rev}/mo</span>
                        </div>
                        <div style="background:rgba(255,255,255,0.08);border-radius:4px;height:6px;">
                            <div style="background:#7C3AED;width:{pct}%;height:6px;border-radius:4px;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No active subscribers yet.")

        st.markdown("---")
        st.markdown("#### MRR Summary")
        c1,c2,c3 = st.columns(3)
        c1.metric("Monthly Revenue", f"€{stats['mrr']}")
        c2.metric("Annual Revenue",  f"€{stats['mrr']*12:,}")
        c3.metric("Avg Revenue/User",
                  f"€{stats['mrr']//stats['active'] if stats['active']>0 else 0}/mo")

    # ── TAB 3: USER MANAGEMENT ──
    with tab3:
        st.markdown("#### Manage User Subscription")

        all_users = get_all_users()
        non_admin = [u for u in all_users if u["role"] != "admin"]

        sel_email = st.selectbox("Select User",
                                  [u["email"] for u in non_admin],
                                  key="mgmt_email")

        if sel_email:
            sel_user = next((u for u in non_admin if u["email"]==sel_email), None)
            if sel_user:
                c1,c2,c3 = st.columns(3)
                c1.markdown(f"**Name:** {sel_user['name']}")
                c2.markdown(f"**Plan:** {sel_user['plan']}")
                c3.markdown(f"**Status:** {sel_user['subscription']}")

                st.markdown("---")
                c1,c2 = st.columns(2)
                new_plan = c1.selectbox("Change Plan",
                    ["entry","pro","crypto","combined"],
                    index=["entry","pro","crypto","combined"].index(
                        sel_user["plan"].lower()
                    ) if sel_user["plan"].lower() in ["entry","pro","crypto","combined"] else 0,
                    key="mgmt_plan")
                new_status = c2.selectbox("Change Status",
                    ["active","inactive"],
                    index=0 if sel_user["subscription"]=="active" else 1,
                    key="mgmt_status")

                if st.button("💾 Save Changes", key="mgmt_save"):
                    if sel_email in USERS:
                        USERS[sel_email]["plan"] = new_plan
                        USERS[sel_email]["subscription"] = new_status
                        st.success(f"✅ {sel_email} updated → {new_plan} / {new_status}")
                        st.rerun()

    # ── TAB 4: ADMIN RIGHTS ──
    with tab4:
        st.markdown("#### Grant / Revoke Admin Rights")
        st.warning("⚠️ Admin users have full access to all dashboards and user data.")

        all_users = get_all_users()
        non_admin = [u for u in all_users if u["role"] != "admin"]
        admins    = [u for u in all_users if u["role"] == "admin"]

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Current Admins**")
            for a in admins:
                st.markdown(f"""
                <div class="user-card">
                    <strong style="color:#A78BFA;">👑 {a['name']}</strong><br>
                    <span style="font-size:0.78rem;color:rgba(255,255,255,0.4);">{a['email']}</span>
                </div>
                """, unsafe_allow_html=True)

        with col2:
            st.markdown("**Grant Admin Rights**")
            grant_email = st.selectbox("Select User",
                [u["email"] for u in non_admin],
                key="grant_email")

            if st.button("👑 Grant Admin Rights", key="grant_admin"):
                if grant_email in USERS:
                    USERS[grant_email]["role"] = "admin"
                    USERS[grant_email]["plan"] = "admin"
                    st.success(f"✅ {grant_email} is now an admin!")
                    st.rerun()

            st.markdown("---")
            st.markdown("**Revoke Admin Rights**")
            revoke_email = st.selectbox("Select Admin to Revoke",
                [a["email"] for a in admins if a["email"] != user["email"]],
                key="revoke_email") if len(admins) > 1 else None

            if revoke_email:
                if st.button("❌ Revoke Admin Rights", key="revoke_admin"):
                    if revoke_email in USERS:
                        USERS[revoke_email]["role"] = "user"
                        USERS[revoke_email]["plan"] = "entry"
                        st.success(f"✅ {revoke_email} admin rights revoked.")
                        st.rerun()

    st.markdown("---")
    st.caption("⚠️ Admin panel — changes are session-only until database is connected.")
