"""
Orion Signals — Auth Module
-----------------------------
Διαχείριση users και authentication.
Τώρα: hardcoded users για testing.
Αργότερα: PostgreSQL database.
"""

# ============================================================
# USERS DATABASE (hardcoded για τώρα)
# Αργότερα αντικαθίσταται με PostgreSQL
# ============================================================

USERS = {
    "admin@orion.com": {
        "password": "admin123",
        "plan": "pro",
        "name": "Admin",
    },
    "pro@orion.com": {
        "password": "pro123",
        "plan": "pro",
        "name": "Pro User",
    },
    "entry@orion.com": {
        "password": "entry123",
        "plan": "entry",
        "name": "Entry User",
    },
}


def login(email: str, password: str) -> dict | None:
    """
    Ελέγχει credentials.
    Επιστρέφει user dict αν είναι σωστά, αλλιώς None.
    """
    email = email.strip().lower()
    user = USERS.get(email)
    if user and user["password"] == password:
        return {
            "email": email,
            "plan": user["plan"],
            "name": user["name"],
        }
    return None


def is_pro(user: dict) -> bool:
    return user.get("plan") == "pro"


def is_entry(user: dict) -> bool:
    return user.get("plan") == "entry"

