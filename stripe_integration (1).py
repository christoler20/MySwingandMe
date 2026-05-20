"""
stripe_integration.py
─────────────────────────────────────────────────────────────────────────────
Stripe billing for MySwing and Me — the $12.99 Speed tier.

HOW IT WORKS (Streamlit-friendly flow, no webhooks required):
  1. User clicks "Unlock Speed Lab"  → app calls create_checkout_session()
  2. App sends the user to Stripe's hosted Checkout page (st.link_button)
  3. User pays on Stripe
  4. Stripe redirects back to the app with  ?session_id=cs_xxxxx
  5. App calls verify_checkout_session() → confirms payment → unlocks the tier

GRACEFUL DEGRADATION:
  If Stripe secrets are not configured, stripe_configured() returns False and
  the app falls back to the existing "demo unlock" button. So the app keeps
  working before you finish Stripe setup.

PRODUCTION NOTE:
  This scaffold unlocks the tier for the current session. To persist a
  subscription across logins/devices you need user accounts (e.g. Supabase)
  and should store the Stripe customer_id against each user. See STRIPE_SETUP.md.
─────────────────────────────────────────────────────────────────────────────
"""

import streamlit as st

# Stripe SDK is optional at import time — app shouldn't crash if it's missing.
try:
    import stripe
    _STRIPE_SDK = True
except ImportError:
    _STRIPE_SDK = False


# ─────────────────────────────────────────────────────────────────────────────
#  CONFIG HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _secret(key, default=None):
    """Safely read a Streamlit secret without crashing if secrets.toml is absent."""
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


def stripe_configured():
    """True only if the Stripe SDK is installed AND the required secrets exist."""
    if not _STRIPE_SDK:
        return False
    return bool(_secret("STRIPE_SECRET_KEY")) and bool(_secret("STRIPE_SPEED_PRICE_ID"))


def _get_stripe():
    """Return the configured stripe module, or None if not set up."""
    if not stripe_configured():
        return None
    stripe.api_key = _secret("STRIPE_SECRET_KEY")
    return stripe


def app_base_url():
    """The deployed app URL Stripe redirects back to after checkout."""
    # Set APP_BASE_URL in secrets. Falls back to a sensible default.
    return _secret("APP_BASE_URL", "https://myswingandme-mpmqbbtupqjnxyb8ryvmts.streamlit.app")


# ─────────────────────────────────────────────────────────────────────────────
#  CHECKOUT
# ─────────────────────────────────────────────────────────────────────────────
def create_checkout_session(customer_email=None):
    """
    Create a Stripe Checkout Session for the Speed tier subscription.
    Returns the hosted checkout URL (string), or None on failure.
    """
    s = _get_stripe()
    if s is None:
        return None

    base = app_base_url().rstrip("/")
    price_id = _secret("STRIPE_SPEED_PRICE_ID")

    try:
        session = s.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            # Stripe substitutes the real session id into {CHECKOUT_SESSION_ID}
            success_url=f"{base}/?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base}/?checkout=cancelled",
            customer_email=customer_email or None,
            allow_promotion_codes=True,
            metadata={"product": "myswingandme_speed_tier"},
        )
        return session.url
    except Exception as e:
        st.error(f"Could not start checkout: {e}")
        return None


def verify_checkout_session(session_id):
    """
    Called when the user returns from Stripe with ?session_id=...
    Returns (is_paid: bool, info: dict).
    info contains customer_id / subscription_id / email when available.
    """
    s = _get_stripe()
    if s is None or not session_id:
        return False, {}

    try:
        session = s.checkout.Session.retrieve(session_id)
        is_paid = session.get("payment_status") == "paid"
        info = {
            "customer_id": session.get("customer"),
            "subscription_id": session.get("subscription"),
            "email": (session.get("customer_details") or {}).get("email"),
        }
        return is_paid, info
    except Exception as e:
        st.warning(f"Could not verify payment: {e}")
        return False, {}


# ─────────────────────────────────────────────────────────────────────────────
#  SUBSCRIPTION STATUS  (for when you add user accounts)
# ─────────────────────────────────────────────────────────────────────────────
def is_subscription_active(customer_id):
    """
    Check whether a Stripe customer has an active Speed-tier subscription.
    Use this once you have user accounts: store customer_id per user, then
    call this on login to decide whether to unlock the Speed tier.
    """
    s = _get_stripe()
    if s is None or not customer_id:
        return False
    try:
        subs = s.Subscription.list(customer=customer_id, status="active", limit=10)
        return len(subs.data) > 0
    except Exception:
        return False


def customer_portal_url(customer_id):
    """
    Returns a Stripe Customer Portal URL so a subscriber can manage or cancel
    their plan. Requires the Customer Portal to be enabled in the Stripe
    dashboard (Settings → Billing → Customer portal).
    """
    s = _get_stripe()
    if s is None or not customer_id:
        return None
    try:
        portal = s.billing_portal.Session.create(
            customer=customer_id,
            return_url=app_base_url(),
        )
        return portal.url
    except Exception:
        return None


def cancel_subscription_at_period_end(subscription_id):
    """
    Cancel a subscription at the end of the current billing period.
    The user keeps access until the period ends — no refund, but no further charges.
    This is the standard "cancel anytime" behavior.
    Returns True on success.
    """
    s = _get_stripe()
    if s is None or not subscription_id:
        return False
    try:
        s.Subscription.modify(subscription_id, cancel_at_period_end=True)
        return True
    except Exception:
        return False


def reactivate_subscription(subscription_id):
    """Undo a pending cancellation if user changes their mind before period end."""
    s = _get_stripe()
    if s is None or not subscription_id:
        return False
    try:
        s.Subscription.modify(subscription_id, cancel_at_period_end=False)
        return True
    except Exception:
        return False


def get_subscription_status(subscription_id):
    """
    Returns a dict with subscription details:
      {status, cancel_at_period_end, current_period_end (timestamp), price_id}
    or None if not found / not configured.
    """
    s = _get_stripe()
    if s is None or not subscription_id:
        return None
    try:
        sub = s.Subscription.retrieve(subscription_id)
        items = sub.get("items", {}).get("data", [])
        price_id = items[0]["price"]["id"] if items else None
        return {
            "status": sub.get("status"),
            "cancel_at_period_end": sub.get("cancel_at_period_end", False),
            "current_period_end": sub.get("current_period_end"),
            "price_id": price_id,
        }
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
#  RETURN-FROM-CHECKOUT HANDLER
# ─────────────────────────────────────────────────────────────────────────────
def handle_checkout_return():
    """
    Call this once near the top of app.py (after init_state()).
    Reads the URL for ?session_id=... — if payment is confirmed, unlocks the
    Speed tier in session state.
    Returns True if a successful unlock just happened.
    """
    try:
        params = st.query_params
    except Exception:
        return False

    session_id = params.get("session_id")
    if not session_id:
        return False

    # Already unlocked this session — clear the param and move on.
    if st.session_state.get("speed_tier_unlocked"):
        try:
            del st.query_params["session_id"]
        except Exception:
            pass
        return False

    is_paid, info = verify_checkout_session(session_id)
    if is_paid:
        st.session_state["speed_tier_unlocked"] = True
        # Stash the Stripe IDs — useful later when you add accounts.
        st.session_state["stripe_customer_id"] = info.get("customer_id")
        st.session_state["stripe_subscription_id"] = info.get("subscription_id")
        # Clean the URL so a refresh doesn't re-trigger.
        try:
            del st.query_params["session_id"]
        except Exception:
            pass
        return True

    return False
