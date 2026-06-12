"""
Orion Signals — Auth Module
-----------------------------
Τώρα: hardcoded users για testing.
Αργότερα: PostgreSQL database.

Plans: entry | pro | crypto | combined | admin
Subscription: active | inactive | trial
"""

from datetime import datetime, timedelta

# ============================================================
# USERS DATABASE (hardcoded για τώρα)
# ============================================================
USERS = {
    "admin@orion.com": {
        "password":      "admin123",
        "plan":          "admin",
        "role":          "admin",
        "name":          "Admin",
        "username":      "admin",
        "subscription":  "active",
        "joined":        "01/01/2026",
        "last_login":    None,
    },
    "entry@orion.com": {
        "password":      "entry123",
        "plan":          "entry",
        "role":          "user",
        "name":          "Entry User",
        "username":      "entry_user",
        "subscription":  "active",
        "joined":        "01/06/2026",
        "last_login":    None,
    },
    "pro@orion.com": {
        "password":      "pro123",
        "plan":          "pro",
        "role":          "user",
        "name":          "Pro User",
        "username":      "pro_user",
        "subscription":  "active",
        "joined":        "01/06/2026",
        "last_login":    None,
    },
    "crypto@orion.com": {
        "password":      "crypto123",
        "plan":          "crypto",
        "role":          "user",
        "name":          "Crypto User",
        "username":      "crypto_user",
        "subscription":  "active",
        "joined":        "01/06/2026",
        "last_login":    None,
    },
    "combined@orion.com": {
        "password":      "combined123",
        "plan":          "combined",
        "role":          "user",
        "name":          "Combined User",
        "username":      "combined_user",
        "subscription":  "active",
        "joined":        "01/06/2026",
        "last_login":    None,
    },
    "inactive@orion.com": {
        "password":      "inactive123",
        "plan":          "entry",
        "role":          "user",
        "name":          "Inactive User",
        "username":      "inactive_user",
        "subscription":  "inactive",
        "joined":        "01/05/2026",
        "last_login":    None,
    },
}

PLAN_PRICES = {
    "entry":    29,
    "pro":      79,
    "crypto":   49,
    "combined": 150,
}

PLAN_NAMES = {
    "entry":    "Entry",
    "pro":      "Pro",
    "crypto":   "Crypto",
    "combined": "Pro + Crypto",
    "admin":    "Admin",
}


# ============================================================
# AUTH FUNCTIONS
# ============================================================

def login(email: str, password: str) -> dict | None:
    email = email.strip().lower()
    user = USERS.get(email)
    if user and user["password"] == password:
        # Update last login
        USERS[email]["last_login"] = datetime.now().strftime("%d/%m/%Y %H:%M")
        return {
            "email":        email,
            "plan":         user["plan"],
            "role":         user["role"],
            "name":         user["name"],
            "username":     user["username"],
            "subscription": user["subscription"],
            "joined":       user["joined"],
        }
    return None


def has_active_subscription(user: dict) -> bool:
    """Ελέγχει αν ο χρήστης έχει ενεργή συνδρομή."""
    return user.get("subscription") == "active"


def is_admin(user: dict) -> bool:
    return user.get("role") == "admin"

def is_pro(user: dict) -> bool:
    return user.get("plan") == "pro"

def is_entry(user: dict) -> bool:
    return user.get("plan") == "entry"

def is_crypto(user: dict) -> bool:
    return user.get("plan") == "crypto"

def is_combined(user: dict) -> bool:
    return user.get("plan") == "combined"


def get_all_users() -> list:
    """Επιστρέφει όλους τους users για το admin panel."""
    users = []
    for email, data in USERS.items():
        users.append({
            "email":        email,
            "name":         data["name"],
            "username":     data["username"],
            "plan":         PLAN_NAMES.get(data["plan"], data["plan"]),
            "role":         data["role"],
            "subscription": data["subscription"],
            "joined":       data["joined"],
            "last_login":   data["last_login"] or "Never",
            "price":        f"€{PLAN_PRICES.get(data['plan'], 0)}/mo" if data["plan"] != "admin" else "-",
        })
    return users


def get_stats() -> dict:
    """Στατιστικά για το admin dashboard."""
    all_users = [u for u in USERS.values() if u["role"] != "admin"]
    active = [u for u in all_users if u["subscription"] == "active"]

    plan_counts = {}
    for u in active:
        plan_counts[u["plan"]] = plan_counts.get(u["plan"], 0) + 1

    mrr = sum(PLAN_PRICES.get(u["plan"], 0) for u in active)

    return {
        "total_users":  len(all_users),
        "active":       len(active),
        "inactive":     len(all_users) - len(active),
        "mrr":          mrr,
        "plan_counts":  plan_counts,
    }

