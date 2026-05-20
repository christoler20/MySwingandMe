import streamlit as st
import anthropic

# Stripe billing — optional module; app still runs if it's missing.
try:
    import stripe_integration as billing
except Exception:
    billing = None
import base64
import json
import datetime
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MySwing and Me · AI Golf Coach",
    page_icon="⛳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
#  GLOBAL CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Barlow:ital,wght@0,300;0,400;0,500;0,600;1,400&family=Barlow+Condensed:wght@400;600;700&display=swap');

:root {
  --night:   #080E1A;
  --card:    #0D1829;
  --border:  #1A2D4A;
  --green:   #1B5E35;
  --lime:    #4ADE80;
  --gold:    #F59E0B;
  --amber:   #D97706;
  --cream:   #F0EBE0;
  --muted:   #6B8BAF;
  --danger:  #EF4444;
  --warn:    #F97316;
  --coach:   #7C3AED;
  --coach2:  #A855F7;
}

html, body, [data-testid="stAppViewContainer"] {
  background: var(--night) !important;
  color: var(--cream) !important;
  font-family: 'Barlow', sans-serif;
}
[data-testid="stSidebar"] {
  background: var(--card) !important;
  border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] * { color: var(--cream) !important; }

h1,h2,h3,h4 { font-family:'Bebas Neue',sans-serif; letter-spacing:.06em; }
h1 { color: var(--gold) !important; font-size:2.8rem; }
h2 { color: var(--lime) !important; font-size:1.8rem; }
h3 { color: var(--cream) !important; font-size:1.3rem; }

/* Buttons */
.stButton > button {
  background: linear-gradient(135deg, var(--green), #2D7A4F) !important;
  color: var(--cream) !important; border: none !important;
  border-radius: 3px !important; font-family:'Barlow Condensed',sans-serif !important;
  font-weight:700 !important; font-size:1rem !important;
  letter-spacing:.08em !important; padding:.65rem 1.6rem !important;
  text-transform: uppercase !important;
  transition: all .2s !important; box-shadow: 0 2px 12px rgba(27,94,53,.4) !important;
}
.stButton > button:hover { background: linear-gradient(135deg,#2D7A4F,var(--lime)) !important; color:#000 !important; }

/* Inputs */
.stTextArea textarea {
  background: var(--card) !important; color: var(--cream) !important;
  border: 1px solid var(--border) !important; border-radius:4px !important;
  font-family:'Barlow',sans-serif !important; font-size:.92rem !important;
}
.stSelectbox > div > div, .stMultiSelect > div > div {
  background: var(--card) !important; border: 1px solid var(--border) !important;
}

/* Cards */
.card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: 6px; padding: 1.3rem 1.5rem; margin-bottom: 1rem;
}
.card-gold { border-left: 3px solid var(--gold); }
.card-green { border-left: 3px solid var(--lime); }
.card-coach { border-left: 3px solid var(--coach2); background: #110C20; }
.card-warn  { border-left: 3px solid var(--warn); }
.card-danger{ border-left: 3px solid var(--danger); }

/* Hero */
.hero { padding: .5rem 0 1.2rem 0; }
.hero-title { font-family:'Bebas Neue',sans-serif; font-size:3.8rem; color:var(--gold); letter-spacing:.1em; line-height:1; margin:0; }
.hero-sub { font-family:'Barlow',sans-serif; color:var(--muted); font-size:1rem; margin-top:.3rem; letter-spacing:.04em; }

/* Badge */
.badge { display:inline-block; font-family:'Barlow Condensed',sans-serif; font-size:.72rem;
  font-weight:600; letter-spacing:.06em; padding:.15rem .55rem; border-radius:2px; margin:.15rem .1rem; }
.badge-green  { background:rgba(74,222,128,.15); color:var(--lime); border:1px solid rgba(74,222,128,.3); }
.badge-gold   { background:rgba(245,158,11,.15);  color:var(--gold); border:1px solid rgba(245,158,11,.3); }
.badge-purple { background:rgba(168,85,247,.15); color:var(--coach2); border:1px solid rgba(168,85,247,.3); }
.badge-red    { background:rgba(239,68,68,.15);  color:var(--danger); border:1px solid rgba(239,68,68,.3); }
.badge-warn   { background:rgba(249,115,22,.15); color:var(--warn);   border:1px solid rgba(249,115,22,.3); }

/* Foundation steps */
.foundation-step {
  background: var(--card); border:1px solid var(--border); border-radius:6px;
  padding:1rem 1.2rem; margin:.5rem 0; position:relative; overflow:hidden;
}
.foundation-step.active { border-color: var(--lime); background: rgba(74,222,128,.05); }
.foundation-step.locked { opacity:.5; }
.step-num {
  font-family:'Bebas Neue',sans-serif; font-size:3rem; color:var(--border);
  position:absolute; right:1rem; top:50%; transform:translateY(-50%); line-height:1;
}

/* Coach bubble */
.coach-bubble {
  background: linear-gradient(135deg, #110C20, #1A1035);
  border: 1px solid var(--coach2); border-radius: 8px;
  padding: 1rem 1.2rem; margin: .6rem 0;
  box-shadow: 0 0 20px rgba(124,58,237,.2);
}
.coach-name {
  font-family:'Bebas Neue',sans-serif; color:var(--coach2);
  font-size:1rem; letter-spacing:.1em; margin-bottom:.3rem;
}
.coach-msg { font-size:.92rem; line-height:1.6; color:var(--cream); }
.user-bubble {
  background: var(--card); border: 1px solid var(--border);
  border-radius: 8px; padding:.8rem 1.1rem; margin:.5rem 0;
}
.user-name { font-family:'Bebas Neue',sans-serif; color:var(--muted); font-size:.9rem; letter-spacing:.1em; margin-bottom:.2rem; }

/* Baseline status */
.baseline-complete {
  background: linear-gradient(135deg, rgba(27,94,53,.4), rgba(74,222,128,.1));
  border: 1px solid var(--lime); border-radius:6px; padding:1rem 1.3rem;
}
.baseline-needed {
  background: linear-gradient(135deg, rgba(249,115,22,.15), rgba(245,158,11,.05));
  border: 1px solid var(--warn); border-radius:6px; padding:1rem 1.3rem;
}

/* Progress bar override */
.stProgress > div > div { background: var(--lime) !important; }

/* Metrics */
.metric-row { display:flex; gap:.8rem; margin:.8rem 0; }
.metric-box {
  flex:1; background:var(--card); border:1px solid var(--border);
  border-radius:5px; padding:.7rem .9rem; text-align:center;
}
.metric-val { font-family:'Bebas Neue',sans-serif; font-size:1.9rem; color:var(--gold); }
.metric-lbl { font-size:.7rem; color:var(--muted); text-transform:uppercase; letter-spacing:.06em; }

/* Sidebar nav */
.nav-item {
  padding:.5rem .8rem; border-radius:4px; cursor:pointer; margin:.2rem 0;
  font-family:'Barlow Condensed',sans-serif; font-size:1rem; font-weight:600;
  letter-spacing:.05em; color:var(--cream);
}

div[data-testid="stMarkdownContainer"] p { color: var(--cream); line-height:1.65; }
label { color: var(--muted) !important; font-size:.78rem !important; letter-spacing:.07em !important; text-transform:uppercase !important; }
.stAlert { border-radius:5px !important; }
[data-testid="stExpander"] { background:var(--card) !important; border:1px solid var(--border) !important; border-radius:5px !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "baseline_complete": False,
        "baseline_data": {},          # raw answers + image b64
        "baseline_analysis": "",      # AI text of baseline diagnosis
        "baseline_date": None,
        "foundation_level": None,     # "address"|"backswing"|"downswing"|"impact"|"finish"
        "foundation_score": {},       # per-level scores 0-100
        "current_level": "address",   # which level user is working on
        "coach_history": [],          # list of {role, content, timestamp, alert_type}
        "session_log": [],            # list of check-ins
        "regression_flags": [],       # detected regressions
        "profile": {},
        "page": "🏠 Home",
        "coach_lessons": [],          # list of {date, coach_name, format, focus, notes, file_b64?, file_name?}
        "equipment_recs": "",         # latest AI equipment recommendation
        "speed_tier_unlocked": False, # $12.99 Speed tier access
        "speed_log": [],              # list of {date, driver_speed, session_type, note}
        "speed_plan": "",             # latest AI speed-training plan
        "pro_tier_unlocked": False,   # $9.99 Pro tier access (benchmarks, etc.)
        "benchmark_log": [],          # list of {date, metrics: {...}, handicap, note}
        "disclaimer_accepted": False, # tracks if user has acknowledged disclaimer
        "swing_library": [],          # list of saved swings {id, date, label, image_b64, mime, tags, notes, ai_notes, angle, position, club, level}
        "compare_selection": [],      # list of swing ids selected for comparison
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

def has_premium_access():
    """True if user has Pro tier OR Speed tier (Speed includes Pro)."""
    return st.session_state.get("speed_tier_unlocked", False) or st.session_state.get("pro_tier_unlocked", False)

# ── Stripe: handle return from Checkout (?session_id=...) ──
if billing is not None:
    try:
        if billing.handle_checkout_return():
            st.success("🎉 Payment confirmed — Speed Lab unlocked! Welcome to the Speed tier.")
            st.balloons()
    except Exception:
        pass  # never let billing break the app

# ─────────────────────────────────────────────────────────────────────────────
#  DISCLAIMER GATE
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.disclaimer_accepted:
    st.markdown("""
    <style>
    .disclaimer-wrap {
      max-width: 720px; margin: 2rem auto; background: #0D1829;
      border: 2px solid #F59E0B; border-radius: 12px; padding: 2rem;
      box-shadow: 0 0 40px rgba(245,158,11,.15);
    }
    .disclaimer-wrap h1 {
      font-family: 'Bebas Neue', sans-serif; color: #F59E0B;
      letter-spacing: .08em; font-size: 2rem; margin: 0 0 .5rem;
    }
    .disclaimer-wrap .sub {
      color: #6B8BAF; font-size: .85rem; letter-spacing: .08em;
      text-transform: uppercase; margin-bottom: 1.5rem;
    }
    .disclaimer-wrap p { color: #F0EBE0; line-height: 1.6; font-size: .95rem; }
    .disclaimer-wrap strong { color: #F59E0B; }
    .disclaimer-wrap .points {
      background: #080E1A; border-left: 3px solid #F59E0B;
      padding: 1rem 1.2rem; border-radius: 4px; margin: 1rem 0;
    }
    .disclaimer-wrap .points li { margin: .4rem 0; color: #F0EBE0; }
    </style>
    <div class="disclaimer-wrap">
      <h1>⚠️ Important Disclaimer</h1>
      <div class="sub">Please read before using MySwing and Me</div>
      <p><strong>MySwing and Me is a self-diagnostic tool.</strong> It is designed to help you understand
      your own golf swing, track your progress, and develop a structured practice routine. It uses
      AI to give general guidance based on the information you provide.</p>
      <div class="points">
        <ul>
          <li>MySwing and Me is <strong>NOT a replacement for a qualified golf professional, PGA instructor, or certified coach</strong>.</li>
          <li>AI-generated diagnoses and recommendations are based on self-reported data and may be inaccurate or incomplete.</li>
          <li>The exercises, stretches, and drills suggested are general fitness guidance. Consult a doctor or licensed physical therapist before beginning any new exercise program — especially if you have injuries or health conditions.</li>
          <li>Equipment recommendations are educational suggestions only. Visit a <strong>certified club fitter</strong> for actual fitting decisions.</li>
          <li>For serious swing improvement, persistent injury, or competitive play, work with a <strong>licensed PGA/LPGA professional in person</strong>.</li>
          <li>Anthropic and the creators of MySwing and Me are not liable for any injury, equipment expense, or performance outcome resulting from use of this app.</li>
        </ul>
      </div>
      <p style="font-size:.85rem;color:#6B8BAF;margin-top:1rem;">
      By continuing, you acknowledge that you have read and understood this disclaimer.
      </p>
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_b:
        if st.button("✓  I UNDERSTAND — CONTINUE TO MYSWING AND ME", use_container_width=True, type="primary"):
            st.session_state.disclaimer_accepted = True
            st.rerun()
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
#  DATA
# ─────────────────────────────────────────────────────────────────────────────
FOUNDATION_LEVELS = [
    {
        "id": "address",
        "label": "ADDRESS & SETUP",
        "icon": "🧍",
        "desc": "Grip, stance width, ball position, posture, alignment, weight distribution",
        "why": "Every fault in the swing traces back to setup. You cannot build on a broken foundation.",
        "key_checks": ["Grip pressure (4/10)", "Spine angle 30-45°", "Knees flexed, not locked", "Ball position correct for club", "Shoulders square to target", "Weight 50/50 or slightly forward"],
    },
    {
        "id": "backswing",
        "label": "TAKEAWAY & BACKSWING",
        "icon": "↗️",
        "desc": "One-piece takeaway, hip/shoulder turn, club plane, wrist hinge, weight load",
        "why": "The backswing loads the spring. A faulty load produces a faulty release — always.",
        "key_checks": ["One-piece takeaway (no early wrist break)", "Club stays on plane to P2", "Hip turn 45°, shoulder turn 90°", "No sway — rotate, don't slide", "Weight loads to trail leg", "Lead arm relatively straight"],
    },
    {
        "id": "transition",
        "label": "TRANSITION & DOWNSWING",
        "icon": "↘️",
        "desc": "Weight shift, hip lead, lag preservation, club path, sequence",
        "why": "The kinematic sequence — hips → torso → arms → club — is where power and accuracy are born.",
        "key_checks": ["Hips initiate downswing (not arms)", "Weight shifts to lead side", "Club drops inside — not over the top", "Lag maintained past P6", "Hips begin to clear before impact", "No early extension"],
    },
    {
        "id": "impact",
        "label": "IMPACT POSITION",
        "icon": "💥",
        "desc": "Shaft lean, hip position, head behind ball, lead wrist flat, club path/face",
        "why": "Impact is the only moment that matters to the ball. Everything else serves this position.",
        "key_checks": ["Hands ahead of ball (shaft lean)", "Hips 30-40° open to target", "Head behind ball", "Lead wrist flat or bowed (not cupped)", "Weight 80%+ on lead foot", "Eyes on ball"],
    },
    {
        "id": "finish",
        "label": "FOLLOW-THROUGH & FINISH",
        "icon": "🏁",
        "desc": "Extension through impact, release, high finish, balance",
        "why": "A balanced, full finish proves everything before it happened correctly.",
        "key_checks": ["Full extension of arms post-impact", "Full hip rotation (belt buckle to target)", "Weight fully on lead foot", "Trail heel up", "High finish — hands above shoulder", "Hold balance 3 seconds"],
    },
]

EXERCISE_DB = {
    "Hip Mobility": [
        {"name": "90/90 Hip Stretch", "target": "Hip rotation", "sets": "3×45 sec/side", "freq": "Daily", "level": "address", "desc": "Sit with front/back leg at 90°. Lean over front shin. Critical for proper address posture and hip turn."},
        {"name": "Hip Circle Rotations", "target": "Hip joint mobility", "sets": "2×10 each way", "freq": "Daily warm-up", "level": "address", "desc": "Hands on hips, draw large slow circles. Warms the hip joint before every session."},
        {"name": "Lateral Band Walks", "target": "Glute medius", "sets": "3×15 steps/way", "freq": "4×/week", "level": "backswing", "desc": "Band above knees, walk in golf posture. Prevents hip sway in backswing."},
        {"name": "Deep Squat Hold", "target": "Hip flexors, ankles", "sets": "3×30 sec", "freq": "Daily", "level": "address", "desc": "Builds the mobility foundation for a correct athletic address position."},
    ],
    "Core Rotation": [
        {"name": "Med Ball Rotational Throw", "target": "Obliques, transverse abs", "sets": "3×10/side", "freq": "4×/week", "level": "transition", "desc": "Explosive throw against wall from golf posture. #1 swing speed builder. Trains sequencing."},
        {"name": "Cable Wood Chop", "target": "Obliques, lats", "sets": "3×12/side", "freq": "3×/week", "level": "transition", "desc": "Mimics downswing plane. Trains hip-to-shoulder power transfer."},
        {"name": "Pallof Press", "target": "Anti-rotation stability", "sets": "3×12/side", "freq": "3×/week", "level": "address", "desc": "Builds stable core that allows rotational speed without swaying."},
        {"name": "Dead Bug", "target": "Deep core", "sets": "3×8/side", "freq": "Daily", "level": "address", "desc": "Foundation of all rotational power. Press lower back into floor throughout."},
        {"name": "Landmine Rotation", "target": "Full rotational chain", "sets": "3×10/side", "freq": "3×/week", "level": "transition", "desc": "Best single exercise for golf power. Full hip-to-shoulder rotation with load."},
    ],
    "Shoulder & Thoracic": [
        {"name": "Thoracic Rotation (Quadruped)", "target": "T-spine mobility", "sets": "2×10/side", "freq": "Daily", "level": "backswing", "desc": "On hands/knees, rotate elbow to ceiling. Unlocks backswing shoulder turn immediately."},
        {"name": "Doorway Chest Stretch", "target": "Pec minor", "sets": "3×30 sec", "freq": "Daily", "level": "backswing", "desc": "Tight pecs are the #1 cause of restricted backswing turn. Fix this first."},
        {"name": "Band Pull-Aparts", "target": "Rear delts, rhomboids", "sets": "3×20", "freq": "Daily", "level": "address", "desc": "Counteracts forward shoulder posture. Enables proper address shoulder position."},
        {"name": "Sleeper Stretch", "target": "Posterior shoulder", "sets": "3×30 sec/side", "freq": "Daily", "level": "impact", "desc": "Reduces lead shoulder impingement risk. Allows full release through impact."},
    ],
    "Wrist & Forearm": [
        {"name": "Wrist Roller", "target": "Forearm flexors/extensors", "sets": "3×up/down", "freq": "3×/week", "level": "impact", "desc": "Builds forearm endurance for consistent club control through impact."},
        {"name": "Forearm Pronation/Supination", "target": "Forearm rotation", "sets": "3×15/direction", "freq": "Daily", "level": "impact", "desc": "Trains the wrist release pattern through impact. Critical for proper face control."},
        {"name": "Wrist Flexion/Extension Stretch", "target": "Wrist tendons", "sets": "3×20 sec/direction", "freq": "Daily", "level": "impact", "desc": "Prevents golfer's elbow. Improves wrist hinge for lag and release."},
    ],
    "Power & Explosiveness": [
        {"name": "Barbell Hip Thrust", "target": "Glute max", "sets": "4×10", "freq": "3×/week", "level": "transition", "desc": "Glutes are the engine of your downswing. This is non-negotiable for power."},
        {"name": "Romanian Deadlift", "target": "Hamstrings, glutes", "sets": "3×10", "freq": "3×/week", "level": "transition", "desc": "Builds posterior chain that generates ground force and prevents early extension."},
        {"name": "Jump Squats", "target": "Explosive lower body", "sets": "4×6", "freq": "2×/week", "level": "finish", "desc": "Trains fast-twitch fibers that create clubhead speed. Correlates directly with driver distance."},
        {"name": "Single Leg Balance", "target": "Proprioception", "sets": "3×30 sec/side", "freq": "Daily", "level": "finish", "desc": "Builds balance needed for a repeatable swing and complete finish."},
    ],
    "Golf Drills": [
        {"name": "Feet Together Drill", "target": "Balance, rotation", "sets": "20 swings", "freq": "Every practice", "level": "address", "desc": "Forces proper weight transfer. Instantly reveals balance faults in setup and swing."},
        {"name": "Slow Motion Swing (10%)", "target": "Proprioception, positions", "sets": "15 reps", "freq": "Every practice", "level": "backswing", "desc": "Pause at address, top, impact, finish. Grooves positions into muscle memory."},
        {"name": "Impact Bag Work", "target": "Impact position", "sets": "50 strikes", "freq": "3×/week", "level": "impact", "desc": "Trains shaft lean, hip clearance, flat lead wrist. The fastest way to improve impact."},
        {"name": "Towel Under Armpits", "target": "Connected swing", "sets": "20 swings", "freq": "Every practice", "level": "backswing", "desc": "Tuck towel under armpits, swing without dropping. Trains one-piece takeaway."},
        {"name": "Alignment Stick Plane Drill", "target": "Swing plane", "sets": "15 swings", "freq": "3×/week", "level": "transition", "desc": "Stick in ground at ball, swing without hitting it. Trains correct path/plane."},
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
#  SPEED LAB — premium swing-speed training ($12.99 tier)
#  Evidence-based: overspeed/overload neural training, rotational power,
#  strength foundation, and mobility. Built on TPI / SuperSpeed / Stack /
#  GolfForever training principles.
# ─────────────────────────────────────────────────────────────────────────────
SPEED_PILLARS = [
    {
        "id": "overspeed",
        "label": "OVERSPEED & OVERLOAD",
        "icon": "⚡",
        "desc": "Train your nervous system to fire faster by swinging lighter-than-normal implements at max effort, then heavier ones to build force.",
        "science": "When you swing something lighter than your driver as fast as possible, your nervous system recruits muscle fibers at a faster rate. Studies show meaningful clubhead-speed gains within about 3 weeks of consistent overspeed work.",
    },
    {
        "id": "rotational",
        "label": "ROTATIONAL POWER",
        "icon": "🔄",
        "desc": "Explosive rotational throws and chops that train the hip-to-core-to-shoulder sequence — the engine of clubhead speed.",
        "science": "You only get ~0.5–0.7 seconds to generate force in a golf swing. Rotational power work trains the body to apply force fast, in the exact sequence the downswing demands.",
    },
    {
        "id": "strength",
        "label": "STRENGTH FOUNDATION",
        "icon": "🏋️",
        "desc": "Squats, hinges, and lat work build the raw force-production capacity that overspeed training then teaches you to apply quickly.",
        "science": "Overspeed improves the RATE you apply force; strength raises the CEILING of force available. Without a strength base, speed gains plateau fast.",
    },
    {
        "id": "mobility",
        "label": "MOBILITY & SEQUENCING",
        "icon": "🤸",
        "desc": "Hip and thoracic mobility plus sequencing drills so your body can actually access the speed it builds — safely.",
        "science": "Speed built on a restricted body leaks power and invites injury. Mobility ensures full turn; sequencing ensures the power arrives at the ball, not before it.",
    },
]

# Overspeed protocol — SuperSpeed/Stack-style, 3 sessions/week, ~15 min
OVERSPEED_PROTOCOL = [
    {"phase": "Warm-up", "detail": "5 min: arm circles, hip rotations, 10 easy practice swings building speed", "swings": "—"},
    {"phase": "Light stick — dominant side", "detail": "Swing the lightest club/stick as FAST as possible. Full effort.", "swings": "3 swings × 2 sets"},
    {"phase": "Light stick — non-dominant side", "detail": "Same, opposite side. Trains both sides of the nervous system.", "swings": "3 swings × 2 sets"},
    {"phase": "Medium stick — both sides", "detail": "Slightly heavier. Maintain max intent on every swing.", "swings": "3 swings × 2 sets each side"},
    {"phase": "Heavy stick — both sides", "detail": "Heaviest implement. Builds force while holding speed intent.", "swings": "3 swings × 1 set each side"},
    {"phase": "Cooldown radar set", "detail": "6 swings with your actual driver — log the speed. This is your transfer test.", "swings": "6 swings"},
]

# 8-week swing-speed program (3 phases)
SPEED_PROGRAM = [
    {
        "weeks": "Weeks 1–3",
        "phase": "PHASE 1 · PRIME THE SYSTEM",
        "focus": "Establish baseline speed. Begin overspeed protocol 3×/week. Light strength + daily mobility.",
        "weekly": "3× overspeed sessions · 2× strength (hip thrust, RDL, rows) · daily 90/90 + thoracic mobility",
        "expect": "This is where the fastest gains happen — most golfers see 3–5 mph by end of week 3 as the nervous system adapts.",
    },
    {
        "weeks": "Weeks 4–6",
        "phase": "PHASE 2 · BUILD THE ENGINE",
        "focus": "Add rotational power (med ball throws, landmine). Heavier strength loads. Keep overspeed 3×/week.",
        "weekly": "3× overspeed · 3× strength + rotational power · daily mobility · 2× jump/plyometric work",
        "expect": "Overspeed gains plateau here — that's expected. Strength and rotational power become the new growth driver.",
    },
    {
        "weeks": "Weeks 7–8",
        "phase": "PHASE 3 · CONVERT TO THE COURSE",
        "focus": "Transfer speed to real swings. On-ball speed sessions. Peak overspeed intensity. Deload before testing.",
        "weekly": "3× overspeed · 2× strength (reduced volume) · 2× on-ball max-speed driver sessions · daily mobility",
        "expect": "Re-test your driver speed. Properly executed, an 8-week block commonly produces a 5–8% clubhead-speed increase.",
    },
]

# Speed-specific exercises (premium — Speed tier only)
SPEED_EXERCISES = {
    "Overspeed Training": [
        {"name": "Light Stick Max Swings", "target": "Neural firing rate", "sets": "3 swings × 2 sets/side", "freq": "3×/week", "desc": "Swing a stick ~20% lighter than your driver at absolute max speed. Trains the nervous system to allow faster motion."},
        {"name": "Step-Change Swings", "target": "Speed under movement", "sets": "5 swings/side", "freq": "3×/week", "desc": "Take a step into each swing. Adds dynamic load and trains speed while the body is already moving."},
        {"name": "Non-Dominant Side Swings", "target": "Bilateral neural speed", "sets": "3 swings × 2 sets", "freq": "3×/week", "desc": "Swing left-handed (for righties). Research links non-dominant training to measurable dominant-side speed gains."},
        {"name": "Heavy Stick Overload", "target": "Force production", "sets": "3 swings × 2 sets/side", "freq": "3×/week", "desc": "Swing a stick heavier than your driver with full speed intent. Builds force while preserving the fast pattern."},
    ],
    "Rotational Power": [
        {"name": "Med Ball Side Throw", "target": "Obliques, hip-core transfer", "sets": "3 × 6/side", "freq": "3×/week", "desc": "Explosive rotational throw into a wall from golf posture. The single most swing-specific power exercise."},
        {"name": "Med Ball Step-Behind Throw", "target": "Full kinematic sequence", "sets": "3 × 5/side", "freq": "2×/week", "desc": "Step behind, load, and launch. Trains the ground-up sequence: legs, hips, core, arms."},
        {"name": "Landmine Rotational Press", "target": "Rotational strength + power", "sets": "3 × 8/side", "freq": "2×/week", "desc": "Drive a barbell from hip to shoulder with rotation. Loaded power through the full swing arc."},
        {"name": "Cable / Band Speed Chop", "target": "Downswing speed pattern", "sets": "3 × 10/side", "freq": "3×/week", "desc": "High-to-low chop at maximum speed. Mimics the downswing plane and trains it to fire fast."},
    ],
    "Strength Foundation": [
        {"name": "Barbell Back Squat", "target": "Lower-body force", "sets": "4 × 5", "freq": "2×/week", "desc": "The #1 lift for raising clubhead speed potential. Builds the leg drive that powers the swing from the ground."},
        {"name": "Romanian Deadlift", "target": "Posterior chain", "sets": "3 × 8", "freq": "2×/week", "desc": "Trains the hip hinge — the exact pattern of your golf setup — and builds glute/hamstring power."},
        {"name": "Weighted Pull-Up / Lat Pulldown", "target": "Lats", "sets": "3 × 8", "freq": "2×/week", "desc": "The lead lat stretches in the backswing and fires hard in the downswing. A huge, underrated speed contributor."},
        {"name": "Trap Bar Jump", "target": "Explosive triple extension", "sets": "4 × 4", "freq": "2×/week", "desc": "Light load, max jump. Trains fast force — the bridge between gym strength and swing speed."},
    ],
    "Mobility & Sequencing": [
        {"name": "90/90 Hip Switches", "target": "Hip rotation range", "sets": "2 × 8/side", "freq": "Daily", "desc": "Unlocks the hip turn that lets you load and unload fully. Restricted hips cap your speed ceiling."},
        {"name": "Open Book Thoracic Rotation", "target": "Upper-back mobility", "sets": "2 × 10/side", "freq": "Daily", "desc": "Frees the thoracic spine for a bigger shoulder turn — more turn means more potential speed."},
        {"name": "Step-Through Sequencing Drill", "target": "Kinematic sequence", "sets": "10 reps", "freq": "3×/week", "desc": "Rehearses hips → torso → arms → club firing order so built speed actually arrives at impact."},
        {"name": "Pelvic Tilt Speed Drill", "target": "Lower-body initiation", "sets": "2 × 10", "freq": "3×/week", "desc": "Trains the lower body to start the downswing — the timing key that lets the chain accelerate."},
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
#  BENCHMARK COMPARISONS — Pro & Speed tier feature
#  Source data: GOLFTEC SwingTRU motion study, Trackman, PGA Tour ShotLink,
#  Swing Man Golf 2025 PGA Tour averages, multiple instructor references.
# ─────────────────────────────────────────────────────────────────────────────
BENCHMARKS = {
    "swing_speed": {
        "label": "Driver Swing Speed",
        "icon": "⚡",
        "unit": "mph",
        "amateur_high":  85.0,   # 20+ handicap (high)
        "amateur_mid":   93.4,   # 14-15 handicap (average male amateur)
        "amateur_low":  105.0,   # 0-5 handicap (scratch)
        "lpga_tour":     94.5,
        "pga_tour":     116.5,   # 2025 PGA Tour season average
        "long_drive":   145.0,
        "min": 50, "max": 150, "default": 92,
        "higher_is_better": True,
        "notes": "Each 1 mph of swing speed adds ~2–2.5 yards of carry. PGA Tour 2025 avg: 116.5 mph.",
    },
    "shoulder_turn": {
        "label": "Shoulder Turn at Top",
        "icon": "🔄",
        "unit": "°",
        "amateur_high":  65.0,
        "amateur_mid":   78.0,
        "amateur_low":   88.0,
        "pga_tour":      93.0,   # GolfTEC "magic number"
        "min": 30, "max": 130, "default": 80,
        "higher_is_better": True,
        "notes": "GolfTEC's data points to ~93° as the tour 'magic number'. Most weekend players are 10–30° short.",
    },
    "hip_turn_top": {
        "label": "Hip Turn at Top",
        "icon": "🌀",
        "unit": "°",
        "amateur_high":  20.0,
        "amateur_mid":   30.0,
        "amateur_low":   38.0,
        "pga_tour":      45.0,
        "min": 5, "max": 70, "default": 30,
        "higher_is_better": True,
        "notes": "Tour pros average ~45° of hip turn at the top. Most amateurs stop in the 25–35° range.",
    },
    "hip_open_impact": {
        "label": "Hips Open at Impact",
        "icon": "🔓",
        "unit": "°",
        "amateur_high":  19.5,
        "amateur_mid":   28.0,
        "amateur_low":   32.0,
        "pga_tour":      36.0,
        "min": 0, "max": 60, "default": 22,
        "higher_is_better": True,
        "notes": "GOLFTEC SwingTRU: PGA Tour averages 36° hips open at impact; high-cap amateurs only 19.5° — nearly 2× difference.",
    },
    "shaft_lean_iron": {
        "label": "Shaft Lean at Impact (7-iron)",
        "icon": "📐",
        "unit": "°",
        "amateur_high":  -1.0,   # often backward/scooping
        "amateur_mid":    3.0,
        "amateur_low":    5.0,
        "pga_tour":       7.0,
        "min": -10, "max": 15, "default": 2,
        "higher_is_better": True,
        "notes": "Tour pros lean the shaft 6–8° forward at impact (hands ahead of clubhead). Amateurs often near 0° or scooping (negative).",
    },
}

COACH_PERSONAS = {
    "The Grinder 🔥": {
        "style": "You are a no-nonsense, intense golf coach in the tradition of Butch Harmon and Claude Harmon III. Direct, blunt, demanding, but deeply knowledgeable. You call out mistakes the moment you see them. You push hard but you're never cruel — you push because you believe in the player. Use short punchy sentences. No fluff.",
        "color": "danger",
        "emoji": "🔥",
    },
    "The Mentor 🎓": {
        "style": "You are a wise, patient golf instructor who teaches through understanding and encouragement. You explain the 'why' behind every correction. You notice small improvements and acknowledge them. You are firm but warm. Your corrections feel like insights, not criticism.",
        "color": "gold",
        "emoji": "🎓",
    },
    "The Competitor ⚡": {
        "style": "You are a high-performance golf coach who speaks like a sports psychologist meets elite trainer. You use data, comparisons to tour pros, and performance benchmarks. You get excited about progress metrics. You frame corrections as competitive advantages. You challenge the player to compete against their past self.",
        "color": "coach",
        "emoji": "⚡",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
#  ANTHROPIC CLIENT
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_client():
    return anthropic.Anthropic()

# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def img_to_b64(file_obj):
    data = file_obj.getvalue()
    return base64.standard_b64encode(data).decode("utf-8")

def level_index(level_id):
    return next((i for i, l in enumerate(FOUNDATION_LEVELS) if l["id"] == level_id), 0)

def get_level(level_id):
    return next((l for l in FOUNDATION_LEVELS if l["id"] == level_id), FOUNDATION_LEVELS[0])

def score_color(score):
    if score >= 75: return "badge-green"
    if score >= 50: return "badge-gold"
    return "badge-red"

def detect_regressions(log):
    """Compare last two sessions. Return list of regression strings."""
    if len(log) < 2: return []
    prev, curr = log[-2], log[-1]
    regressions = []
    for fault in curr.get("faults", []):
        if fault in prev.get("faults", []):
            regressions.append(fault)
    return regressions

# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:.5rem 0 .8rem">
      <div style="font-family:'Bebas Neue',sans-serif;font-size:2rem;color:#F59E0B;letter-spacing:.1em;">⛳ MySwing and Me</div>
      <div style="font-family:'Barlow',sans-serif;color:#6B8BAF;font-size:.82rem;letter-spacing:.05em;">AI GOLF COACH · v2.0</div>
    </div>
    """, unsafe_allow_html=True)

    # Baseline status chip
    if st.session_state.baseline_complete:
        st.markdown(f"""
        <div class="baseline-complete">
          <span style="font-family:'Bebas Neue',sans-serif;color:#4ADE80;font-size:.95rem;">✓ BASELINE SET</span><br>
          <span style="font-size:.75rem;color:#6B8BAF;">{st.session_state.baseline_date}</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="baseline-needed">
          <span style="font-family:'Bebas Neue',sans-serif;color:#F97316;font-size:.95rem;">⚠ NO BASELINE YET</span><br>
          <span style="font-size:.75rem;color:#6B8BAF;">Start here → Set Baseline</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**NAVIGATION**")

    pages = [
        ("🏠", "Home"),
        ("📐", "Set Baseline"),
        ("🔬", "Foundation Analysis"),
        ("🤖", "Coach Session"),
        ("🎬", "Swing Library"),
        ("🎒", "Equipment Fit"),
        ("👔", "Pro Lessons"),
        ("⚡", "Speed Lab"),
        ("📊", "Benchmarks"),
        ("💪", "Exercise Library"),
        ("📊", "My Progress"),
    ]
    for icon, name in pages:
        label = f"{icon} {name}"
        is_active = st.session_state.page == label
        if st.button(
            label,
            key=f"nav_{name}",
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            st.session_state.page = label
            st.rerun()

    st.markdown("---")
    st.markdown("**GOLFER PROFILE**")
    handicap = st.selectbox("Handicap", ["Beginner (30+)", "High (20-29)", "Mid (10-19)", "Low (1-9)", "Scratch/Pro"], key="hcp")
    dominant = st.selectbox("Hand", ["Right-handed", "Left-handed"], key="dom")
    coach_persona = st.selectbox("Coach Style", list(COACH_PERSONAS.keys()), key="persona")

    st.session_state.profile = {"handicap": handicap, "dominant": dominant, "coach": coach_persona}

    st.markdown("---")
    st.markdown("""
    <div style="background:#080E1A;border-left:3px solid #F59E0B;padding:.6rem .8rem;border-radius:4px;font-size:.72rem;color:#6B8BAF;line-height:1.5;">
      <strong style="color:#F59E0B;font-family:'Bebas Neue',sans-serif;letter-spacing:.06em;">⚠ DISCLAIMER</strong><br>
      MySwing and Me is a self-diagnostic tool. It is <strong>not a substitute for a professional PGA/LPGA golf coach</strong>. Equipment recommendations are educational only — see a certified club fitter for real fitting decisions.
    </div>
    """, unsafe_allow_html=True)

page = st.session_state.page

# ─────────────────────────────────────────────────────────────────────────────
#  PAGE: HOME
# ─────────────────────────────────────────────────────────────────────────────
if "Home" in page:
    st.markdown("""
    <div class="hero">
      <div class="hero-title">MYSWING AND ME</div>
      <div class="hero-sub">AI Golf Diagnosis · Foundational Coaching · Progress Tracking</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    if not st.session_state.baseline_complete:
        st.markdown("""
        <div class="card card-warn">
          <h3 style="color:#F97316;margin-top:0;">START HERE: SET YOUR BASELINE</h3>
          <p>Before any coaching or diagnosis can begin, MySwing and Me needs to see where you are right now.
          Upload or record your swing — the AI will establish your starting point and determine which
          foundational level to build from. Every plan is built from your baseline up.</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📐  SET MY BASELINE NOW", use_container_width=True):
                st.session_state.page = "📐 Set Baseline"
                st.rerun()
        with col2:
            st.markdown("""
            <div class="card" style="text-align:center;padding:.9rem;">
              <div style="font-family:'Bebas Neue',sans-serif;font-size:1rem;color:#6B8BAF;">HOW IT WORKS</div>
            </div>
            """, unsafe_allow_html=True)

    else:
        # Dashboard for returning user
        st.markdown(f"""
        <div class="baseline-complete">
          <span style="font-family:'Bebas Neue',sans-serif;color:#4ADE80;font-size:1.1rem;">✓ BASELINE ACTIVE — {st.session_state.baseline_date}</span><br>
          <span style="font-size:.85rem;color:#F0EBE0;">Currently working on: <strong>{get_level(st.session_state.current_level)['label']}</strong></span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("")

        # Foundation progress
        st.markdown("### FOUNDATION PROGRESS")
        cols = st.columns(5)
        for i, level in enumerate(FOUNDATION_LEVELS):
            score = st.session_state.foundation_score.get(level["id"], 0)
            is_current = level["id"] == st.session_state.current_level
            with cols[i]:
                border = "2px solid #4ADE80" if is_current else "1px solid #1A2D4A"
                st.markdown(f"""
                <div style="background:#0D1829;border:{border};border-radius:5px;padding:.6rem;text-align:center;">
                  <div style="font-size:1.4rem;">{level['icon']}</div>
                  <div style="font-family:'Bebas Neue',sans-serif;font-size:.75rem;color:#6B8BAF;letter-spacing:.05em;">{level['label']}</div>
                  <div style="font-family:'Bebas Neue',sans-serif;font-size:1.6rem;color:{'#4ADE80' if score>=75 else '#F59E0B' if score>=50 else '#EF4444'};">{score}%</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("")

        # Regression alerts
        regressions = st.session_state.regression_flags
        if regressions:
            st.markdown(f"""
            <div class="card card-danger">
              <span style="font-family:'Bebas Neue',sans-serif;color:#EF4444;font-size:1rem;">⚠️ COACH ALERT: OLD HABITS DETECTED</span><br>
              <p style="margin:.5rem 0 0;">Your coach has flagged recurring patterns: <strong>{', '.join(regressions)}</strong></p>
            </div>
            """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("🤖  COACH SESSION", use_container_width=True):
                st.session_state.page = "🤖 Coach Session"
                st.rerun()
        with col2:
            if st.button("🔬  FOUNDATION WORK", use_container_width=True):
                st.session_state.page = "🔬 Foundation Analysis"
                st.rerun()
        with col3:
            lib_count = len(st.session_state.swing_library)
            if st.button(f"🎬  SWING LIBRARY ({lib_count})", use_container_width=True):
                st.session_state.page = "🎬 Swing Library"
                st.rerun()
        with col4:
            if st.button("📊  MY PROGRESS", use_container_width=True):
                st.session_state.page = "📊 My Progress"
                st.rerun()

    # How it works
    st.markdown("---")
    st.markdown("### HOW MYSWING AND ME WORKS")
    steps = [
        ("1", "📐 SET BASELINE", "Upload or record your current swing. AI analyzes your starting point across all 5 foundation levels.", "gold"),
        ("2", "🔬 FOUNDATION FIRST", "You start from your weakest foundational level — not wherever you think the problem is. Build bottom-up.", "green"),
        ("3", "🤖 AI COACH WATCHES", "Check in with your coach after every session. It spots regressions, pushes your progress, and holds you accountable.", "coach"),
        ("4", "📊 TRACK EVERYTHING", "Every session is logged. Your coach compares against your baseline to detect if old habits return.", "warn"),
    ]
    cols = st.columns(4)
    for i, (num, title, desc, color) in enumerate(steps):
        with cols[i]:
            st.markdown(f"""
            <div class="card card-{color}" style="height:100%;">
              <div style="font-family:'Bebas Neue',sans-serif;font-size:2.5rem;color:#1A2D4A;">{num}</div>
              <div style="font-family:'Bebas Neue',sans-serif;font-size:1rem;color:#F59E0B;letter-spacing:.05em;">{title}</div>
              <p style="font-size:.84rem;color:#6B8BAF;margin-top:.5rem;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  PAGE: SET BASELINE
# ─────────────────────────────────────────────────────────────────────────────
elif "Set Baseline" in page:
    st.markdown('<div class="hero"><div class="hero-title">SET YOUR BASELINE</div><div class="hero-sub">This is your starting point — everything is built from here</div></div>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("""
    <div class="card card-gold">
      <strong>Why baseline first?</strong> MySwing and Me uses your baseline to determine which foundational
      level to start from, detect if you regress to old patterns, and measure real improvement over time.
      Be honest — the more accurate this is, the better your coaching will be.
    </div>
    """, unsafe_allow_html=True)

    tab1, tab_rec, tab_review, tab2 = st.tabs(["📸  Upload Swing (Both Angles)", "🎥  Live Recorder (Phone)", "🐢  Slow-Mo Review", "✍️  Self-Assessment"])

    with tab1:
        st.markdown("### 📐 Two-Angle Swing Diagnosis")
        st.markdown("""
        <div class="card card-gold">
          <strong>For the most accurate diagnosis, upload BOTH angles.</strong> Each view reveals
          different faults — the AI cross-references them for the best baseline. You can submit just one
          if needed, but two-angle analysis is significantly more accurate.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")
        col_dtl, col_fo = st.columns(2, gap="large")

        # ── DOWN THE LINE ──
        with col_dtl:
            st.markdown("""
            <div style="background:#0D1829;border:2px solid #1A2D4A;border-radius:8px;padding:1rem;margin-bottom:.8rem;">
              <div style="font-family:'Bebas Neue',sans-serif;color:#F59E0B;font-size:1.3rem;letter-spacing:.06em;">📐 ANGLE 1 · DOWN THE LINE</div>
              <div style="font-size:.8rem;color:#6B8BAF;margin-top:.2rem;">Camera directly behind golfer, pointed at target</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            **What this view reveals:**
            - ✓ Swing plane (steep vs flat)
            - ✓ Club path (in-to-out vs out-to-in)
            - ✓ Spine angle maintenance
            - ✓ Early extension (standing up through impact)
            - ✓ Trail elbow position at top
            - ✓ Shaft alignment at key positions
            - ✓ Posture loss
            """)

            st.markdown("**📋 Camera setup:**")
            st.caption("• Stand 8–12 ft directly behind golfer\n• Phone at hip-to-hand height\n• Camera lens pointed straight at the target")

            dtl_position = st.selectbox(
                "Swing position captured (DTL)",
                ["Full swing video", "Address/Setup", "Halfway back (P2)", "Top of backswing (P4)", "Halfway down (P6)", "Impact (P7)", "Finish (P10)"],
                key="dtl_pos"
            )

            dtl_img = st.file_uploader("Upload DOWN-THE-LINE image", type=["jpg","jpeg","png"], key="dtl_upload")
            dtl_cam = st.camera_input("Or take DTL photo now", key="dtl_cam")

            dtl_source = dtl_cam if dtl_cam else dtl_img
            if dtl_source:
                st.image(dtl_source, caption=f"DTL · {dtl_position}", use_container_width=True)
                st.session_state.baseline_data["dtl_image"] = img_to_b64(dtl_source)
                st.session_state.baseline_data["dtl_position"] = dtl_position
                st.session_state.baseline_data["has_dtl"] = True
                st.markdown('<div style="color:#4ADE80;font-size:.85rem;font-weight:600;">✓ DTL angle captured</div>', unsafe_allow_html=True)

        # ── FACE ON ──
        with col_fo:
            st.markdown("""
            <div style="background:#0D1829;border:2px solid #1A2D4A;border-radius:8px;padding:1rem;margin-bottom:.8rem;">
              <div style="font-family:'Bebas Neue',sans-serif;color:#A855F7;font-size:1.3rem;letter-spacing:.06em;">🎯 ANGLE 2 · FACE ON</div>
              <div style="font-size:.8rem;color:#6B8BAF;margin-top:.2rem;">Camera directly facing golfer, perpendicular to target</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            **What this view reveals:**
            - ✓ Weight shift (sway vs rotation)
            - ✓ Head movement (lateral and vertical)
            - ✓ Hip slide vs hip rotation
            - ✓ Lead arm structure (straight vs chicken wing)
            - ✓ Reverse pivot
            - ✓ Lead wrist position at impact (flat/cupped/bowed)
            - ✓ Balance through swing
            - ✓ Finish position quality
            """)

            st.markdown("**📋 Camera setup:**")
            st.caption("• Stand 8–12 ft directly perpendicular to target line\n• Phone at hip height\n• Golfer should be facing the camera in setup")

            fo_position = st.selectbox(
                "Swing position captured (Face-on)",
                ["Full swing video", "Address/Setup", "Halfway back (P2)", "Top of backswing (P4)", "Halfway down (P6)", "Impact (P7)", "Finish (P10)"],
                key="fo_pos"
            )

            fo_img = st.file_uploader("Upload FACE-ON image", type=["jpg","jpeg","png"], key="fo_upload")
            fo_cam = st.camera_input("Or take face-on photo now", key="fo_cam")

            fo_source = fo_cam if fo_cam else fo_img
            if fo_source:
                st.image(fo_source, caption=f"Face-on · {fo_position}", use_container_width=True)
                st.session_state.baseline_data["fo_image"] = img_to_b64(fo_source)
                st.session_state.baseline_data["fo_position"] = fo_position
                st.session_state.baseline_data["has_fo"] = True
                st.markdown('<div style="color:#4ADE80;font-size:.85rem;font-weight:600;">✓ Face-on angle captured</div>', unsafe_allow_html=True)

        # Summary status
        st.markdown("---")
        has_dtl = st.session_state.baseline_data.get("has_dtl", False)
        has_fo = st.session_state.baseline_data.get("has_fo", False)

        if has_dtl and has_fo:
            st.markdown("""<div class="card card-green"><strong>✅ Both angles captured.</strong> The AI will perform full two-angle cross-reference diagnosis when you submit your baseline.</div>""", unsafe_allow_html=True)
        elif has_dtl or has_fo:
            missing = "Face-on" if has_dtl else "Down-the-line"
            st.markdown(f"""<div class="card card-warn"><strong>⚠️ One angle captured.</strong> Diagnosis will work but accuracy improves significantly with both angles. Consider adding the <strong>{missing}</strong> view.</div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div class="card"><strong>📸 No images yet.</strong> Upload at least one angle, or complete only the Self-Assessment tab for a text-based diagnosis.</div>""", unsafe_allow_html=True)

        # Video upload (optional bonus)
        with st.expander("➕ Optionally upload full swing video"):
            uploaded_video = st.file_uploader("Upload swing video (MP4/MOV/WEBM)", type=["mp4","mov","webm"], key="baseline_video_upload")
            if uploaded_video:
                st.video(uploaded_video)
                st.success("✓ Video uploaded. Best practice: screenshot key frames (address, top, impact) and upload as DTL/Face-on images for AI vision analysis.")
                st.session_state.baseline_data["has_video"] = True

    with tab_rec:
        st.markdown("### 🎥 Live Swing Recorder")
        st.markdown("""
        <div class="card card-green">
          <strong>📱 Open this on your phone for best results.</strong> The recorder uses your phone's camera with built-in alignment guides:
          a centered <span style="color:#4ADE80;">green frame box</span> for golfer positioning, an
          <span style="color:#F59E0B;">orange spine/shaft plane line</span>, a
          <span style="color:#A855F7;">purple hip line</span>, and a
          <span style="color:#4ADE80;">ball position crosshair</span>. Toggle any guide on/off during recording.
        </div>
        """, unsafe_allow_html=True)

        col_a, col_b = st.columns([1, 1])
        with col_a:
            st.markdown("""
            **🎯 What the guidelines do:**
            - **Frame Box** — keeps the whole golfer centered consistently across every recording
            - **Head Zone (top)** — checks for head movement during swing
            - **Hip Line (middle)** — reference for hip rotation/sway
            - **Spine Axis** (face-on) — keeps you vertical, detects sway
            - **Shaft Plane** (down-the-line) — reference for swing plane
            - **Ball Crosshair** — consistent ball placement every record
            - **Rule-of-thirds Grid** — pro framing
            """)

        with col_b:
            st.markdown("""
            **📋 How to use:**
            1. Open MySwing and Me on your **phone** browser
            2. Tap the **🎥 Live Recorder** tab
            3. Select angle (down-the-line or face-on) and dominant hand
            4. Tap **Start Camera** → allow camera access
            5. Position your phone, align yourself inside the green box
            6. Tap the **red record button** (or use 3-sec timer)
            7. Take your swing → tap stop
            8. **Save** the video → upload back here for AI analysis
            """)

        st.markdown("---")

        # Embed the recorder
        try:
            recorder_html = Path(__file__).parent.joinpath("recorder.html").read_text()
            st.components.v1.html(recorder_html, height=700, scrolling=False)
        except Exception as e:
            st.error(f"Recorder not loaded: {e}")
            st.info("Make sure recorder.html is in the same folder as app.py")

        st.markdown("---")
        st.markdown("### Upload Recorded Video")
        st.caption("After recording, save the video to your device, then upload it here.")
        recorded_video = st.file_uploader("Upload your recorded swing", type=["webm","mp4","mov"], key="recorded_video")
        if recorded_video:
            st.video(recorded_video)
            st.success("✓ Recorded swing loaded. Take a screenshot of a key frame (top of backswing, impact, etc.) and upload it as an image in the 'Upload / Photo' tab for AI image analysis.")
            st.session_state.baseline_data["has_recorded_video"] = True

    with tab_review:
        st.markdown("### 🐢 Slow-Motion Swing Review")
        st.markdown("""
        <div class="card card-coach">
          <strong>📺 Review any swing video frame-by-frame.</strong> The slow-mo player lets you
          <strong>play, pause, stop, scrub, step frame-by-frame, and play at 0.1×, 0.25×, 0.5×, 1×, or 2× speed</strong>.
          Critical for spotting faults you can't see at full speed.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")
        col_info, col_keys = st.columns([1, 1])
        with col_info:
            st.markdown("""
            **🎯 What to look for in slow-mo:**
            - **At 0.1×–0.25× speed:** Spot tiny faults invisible at full speed
            - **Frame step (◀▶):** Lock onto exact swing positions (P4 top, P6 transition, P7 impact)
            - **Loop mode (🔁):** Replay a specific section over and over
            - **Scrubber:** Jump to any moment instantly
            """)
        with col_keys:
            st.markdown("""
            **⌨ Keyboard shortcuts:**
            - **Spacebar** → Play / Pause
            - **← / →** → Frame back / forward
            - **↑ / ↓** → Speed up / slow down
            - **Click video** → Play / Pause
            """)

        st.markdown("---")

        # Embed the slow-mo video player
        try:
            player_html = Path(__file__).parent.joinpath("video_player.html").read_text()
            st.components.v1.html(player_html, height=620, scrolling=False)
        except Exception as e:
            st.error(f"Player not loaded: {e}")
            st.info("Make sure video_player.html is in the same folder as app.py")

        st.markdown("---")
        st.markdown("""
        <div class="card card-gold">
          <strong>💡 Pro Tip:</strong> Once you spot a fault in slow-mo, <strong>screenshot that exact frame</strong>
          (use your OS screenshot — Mac: ⌘+Shift+4, Windows: Win+Shift+S) and upload it as a DTL or Face-on image
          in the "Upload Swing" tab. The AI will analyze the freeze-frame for surgical fault diagnosis.
        </div>
        """, unsafe_allow_html=True)

    with tab2:
        st.markdown("### Complete the Swing Assessment")
        st.caption("Answer as honestly as possible. This is your starting point — not a test.")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Setup & Posture**")
            setup_issues = st.multiselect("Posture/setup faults you notice", [
                "Standing too upright", "Too bent over", "Knees too straight", "Ball too far forward",
                "Ball too far back", "Grip too strong", "Grip too weak", "Shoulders open",
                "Shoulders closed", "Weight on heels", "Looks correct to me"
            ], key="bl_setup")

            grip_comfort = st.slider("Grip comfort / naturalness (1=awkward, 10=natural)", 1, 10, 5, key="bl_grip")
            posture_confidence = st.slider("Confidence in your address position (1-10)", 1, 10, 5, key="bl_posture")

            st.markdown("**Backswing**")
            backswing_issues = st.multiselect("Backswing faults", [
                "Club goes too flat", "Club goes too steep", "Hip sway (don't rotate)",
                "Short backswing (restricted turn)", "Over-rotation", "Head moves off ball",
                "Reverse pivot", "Flying right elbow", "Lead arm collapses"
            ], key="bl_back")

        with col2:
            st.markdown("**Ball Flight**")
            flight = st.selectbox("Primary ball flight", [
                "Straight", "Draw (right-to-left)", "Strong draw/hook", "Fade (left-to-right)",
                "Strong fade/slice", "Push (straight right)", "Pull (straight left)",
                "Pop-up", "Low/no height", "Inconsistent"
            ], key="bl_flight")

            contact = st.selectbox("Typical ball contact", [
                "Solid/center", "Slightly thin", "Slightly fat", "Very fat (ground first)",
                "Off heel", "Off toe", "Very inconsistent"
            ], key="bl_contact")

            st.markdown("**Downswing / Impact**")
            downswing_issues = st.multiselect("Downswing faults", [
                "Over the top (slicing motion)", "Too inside (hooking path)", "Early extension (stand up through impact)",
                "Chicken wing (lead arm bends)", "Flipping/scooping at impact", "Weight stays on back foot",
                "Can't hold finish / lose balance", "Hips don't clear"
            ], key="bl_down")

            feel_issues = st.multiselect("What you FEEL most", [
                "Rushing the downswing", "Arms disconnected from body", "Casting the club early",
                "Too much tension everywhere", "Losing balance forward", "Losing balance backward",
                "Can't generate power", "Inconsistent tempo"
            ], key="bl_feel")

        overall_note = st.text_area("Anything else to describe your swing?", height=70,
                                     placeholder="e.g. I chunk my irons but not my driver. My driver goes left 80% of the time...",
                                     key="bl_note")

        st.session_state.baseline_data.update({
            "setup_issues": setup_issues,
            "grip_comfort": grip_comfort,
            "posture_confidence": posture_confidence,
            "backswing_issues": backswing_issues,
            "flight": flight,
            "contact": contact,
            "downswing_issues": downswing_issues,
            "feel_issues": feel_issues,
            "note": overall_note,
        })

    st.markdown("---")
    submit_baseline = st.button("🔬  ANALYZE & SET MY BASELINE", use_container_width=True)

    if submit_baseline:
        bd = st.session_state.baseline_data
        profile = st.session_state.profile

        # Detect which angles are available
        has_dtl = bd.get("has_dtl", False) and bd.get("dtl_image")
        has_fo = bd.get("has_fo", False) and bd.get("fo_image")
        # Backward-compat: also accept legacy single image
        has_legacy = bd.get("has_image", False) and bd.get("image")

        # Build angle-specific instructions
        angle_instructions = ""
        if has_dtl and has_fo:
            angle_instructions = """
## 🎥 TWO-ANGLE VISUAL ANALYSIS — CRITICAL

You have BOTH camera angles. Cross-reference them for maximum diagnostic accuracy.

### Image 1 — DOWN-THE-LINE view (behind golfer, looking at target)
This view is BEST for detecting:
- Swing plane (steep vs flat shaft angle)
- Club path (in-to-out vs out-to-in / over-the-top)
- Spine angle and posture maintenance
- Early extension (lower body thrusting toward ball)
- Trail elbow position at top of backswing
- Shaft alignment at P2, P4, P6 positions
- Hands position relative to ball at impact (in-line, ahead, or trailing)

Position captured: {dtl_pos}

### Image 2 — FACE-ON view (perpendicular to target)
This view is BEST for detecting:
- Weight shift / pressure pattern (sway vs rotation)
- Head movement (lateral and vertical)
- Hip slide vs hip rotation through transition
- Lead arm structure (straight vs chicken wing)
- Reverse pivot (weight going backward into impact)
- Lead wrist position at impact (flat / cupped / bowed)
- Balance throughout swing
- Finish position quality

Position captured: {fo_pos}

CROSS-REFERENCE RULE: If a fault appears in only one view but the other view doesn't confirm it, flag it as "possible" rather than definite. Faults visible in BOTH views are HIGH-CONFIDENCE diagnoses.
""".format(dtl_pos=bd.get('dtl_position','unknown'), fo_pos=bd.get('fo_position','unknown'))
        elif has_dtl:
            angle_instructions = f"""
## 🎥 DOWN-THE-LINE VISUAL ANALYSIS

You have only the DOWN-THE-LINE view (camera behind golfer pointing at target).
Position captured: {bd.get('dtl_position','unknown')}

This view is BEST for: swing plane, club path, spine angle, early extension, trail elbow, shaft alignment at key positions.

This view is LIMITED for: weight shift, head movement (lateral), hip slide vs rotation, lead arm structure, lead wrist position, balance, finish quality.

Note in your diagnosis what you CAN see clearly and what would require a face-on view to confirm.
"""
        elif has_fo:
            angle_instructions = f"""
## 🎥 FACE-ON VISUAL ANALYSIS

You have only the FACE-ON view (camera directly facing golfer, perpendicular to target).
Position captured: {bd.get('fo_position','unknown')}

This view is BEST for: weight shift, head movement, hip slide vs rotation, lead arm structure, reverse pivot, lead wrist position, balance, finish position.

This view is LIMITED for: swing plane, club path, spine angle from behind, early extension, trail elbow position.

Note in your diagnosis what you CAN see clearly and what would require a down-the-line view to confirm.
"""
        elif has_legacy:
            angle_instructions = f"""
## 🎥 SINGLE-ANGLE VISUAL ANALYSIS
Camera angle: {bd.get('angle','unknown')}, Position: {bd.get('position','unknown')}

Note in your diagnosis what you can see clearly. Mention that two-angle analysis (down-the-line + face-on) would improve diagnostic accuracy.
"""
        else:
            angle_instructions = """
## 🎥 NO VISUAL DATA
No swing images provided. Base diagnosis on self-assessment only. RECOMMEND in your summary that the golfer add both DTL and Face-on swing photos for higher-confidence diagnosis.
"""

        # Build messages for AI
        text_prompt = f"""You are an elite PGA golf instructor performing an INITIAL BASELINE ASSESSMENT.
This is the golfer's starting point — you must be thorough, honest, and foundational.

GOLFER PROFILE: Handicap: {profile.get('handicap','Unknown')}, Hand: {profile.get('dominant','Right-handed')}

SELF-ASSESSMENT DATA:
- Setup issues noticed: {bd.get('setup_issues', [])}
- Grip comfort: {bd.get('grip_comfort', 5)}/10
- Posture confidence: {bd.get('posture_confidence', 5)}/10
- Backswing faults: {bd.get('backswing_issues', [])}
- Ball flight: {bd.get('flight', 'Unknown')}
- Contact quality: {bd.get('contact', 'Unknown')}
- Downswing/impact faults: {bd.get('downswing_issues', [])}
- Physical feel during swing: {bd.get('feel_issues', [])}
- Additional notes: {bd.get('note', 'None')}

{angle_instructions}

Analyze this baseline and respond in this EXACT structure:

## 📍 BASELINE DIAGNOSIS

### Visual Observations By Angle
{"For each angle provided, list the specific faults visible." if (has_dtl or has_fo or has_legacy) else "(No images provided — skip this section)"}

### Starting Foundation Level
Determine which of these 5 levels this golfer must start from (pick the EARLIEST broken one):
1. ADDRESS & SETUP
2. TAKEAWAY & BACKSWING  
3. TRANSITION & DOWNSWING
4. IMPACT POSITION
5. FOLLOW-THROUGH & FINISH

State: **STARTING LEVEL: [level name]** and explain in 2 sentences WHY this is the right starting point.

### Foundation Scores (0-100 for each level)
Rate each level based on what's reported AND visible. Format exactly as:
SCORES: address=[0-100], backswing=[0-100], transition=[0-100], impact=[0-100], finish=[0-100]

### Root Cause Analysis
What are the 1-2 actual ROOT CAUSES (not symptoms) driving everything observed? Be specific and mechanistic. If you have two angles, note which angle confirmed each root cause.

### Primary Faults (Ranked)
List top 5 faults, ranked from most foundational to most downstream. Tag each fault with [DTL], [FACE-ON], [BOTH], or [SELF-REPORT] showing the source of evidence.

### Baseline Summary
2-3 sentences summary of this golfer's current state for future reference. What defines their swing right now?

### Immediate Focus
The ONE thing to work on first. Not two things — one."""

        # Build message content with images
        content_blocks = []

        if has_dtl:
            content_blocks.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": bd["dtl_image"]}
            })
            content_blocks.append({
                "type": "text",
                "text": f"[IMAGE 1 ABOVE: DOWN-THE-LINE view, position: {bd.get('dtl_position','unknown')}]"
            })

        if has_fo:
            content_blocks.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": bd["fo_image"]}
            })
            content_blocks.append({
                "type": "text",
                "text": f"[IMAGE 2 ABOVE: FACE-ON view, position: {bd.get('fo_position','unknown')}]"
            })

        if has_legacy and not (has_dtl or has_fo):
            content_blocks.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": bd["image"]}
            })
            content_blocks.append({
                "type": "text",
                "text": f"[IMAGE ABOVE: angle: {bd.get('angle','unknown')}, position: {bd.get('position','unknown')}]"
            })

        content_blocks.append({"type": "text", "text": text_prompt})

        messages = [{"role": "user", "content": content_blocks}]

        with st.spinner(f"Analyzing your swing ({sum([has_dtl, has_fo, has_legacy])} angle(s))..."):
            client = get_client()
            st.markdown("## 📊 Your Baseline Analysis")
            result_placeholder = st.empty()
            full_text = ""

            with client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=2800,
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    full_text += text
                    result_placeholder.markdown(full_text)

            # Parse starting level and scores from response
            starting_level = "address"
            for level in FOUNDATION_LEVELS:
                if level["label"].lower() in full_text.lower() and "STARTING LEVEL" in full_text:
                    # look for which label follows STARTING LEVEL:
                    pass
            # Simple parse: find STARTING LEVEL line
            for line in full_text.split("\n"):
                if "STARTING LEVEL:" in line:
                    for lvl in FOUNDATION_LEVELS:
                        if lvl["label"] in line.upper():
                            starting_level = lvl["id"]
                            break
                    break

            # Parse scores
            scores = {}
            for line in full_text.split("\n"):
                if "SCORES:" in line:
                    try:
                        parts = line.replace("SCORES:", "").strip().split(",")
                        for p in parts:
                            k, v = p.strip().split("=")
                            scores[k.strip()] = int(v.strip())
                    except:
                        scores = {"address":40,"backswing":35,"transition":30,"impact":25,"finish":35}
                    break

            if not scores:
                scores = {"address":40,"backswing":35,"transition":30,"impact":25,"finish":35}

            # Save baseline
            st.session_state.baseline_complete = True
            st.session_state.baseline_analysis = full_text
            st.session_state.baseline_date = datetime.datetime.now().strftime("%B %d, %Y")
            st.session_state.current_level = starting_level
            st.session_state.foundation_level = starting_level
            st.session_state.foundation_score = scores
            st.session_state.session_log.append({
                "date": st.session_state.baseline_date,
                "type": "baseline",
                "faults": bd.get("downswing_issues",[]) + bd.get("backswing_issues",[]),
                "scores": scores,
                "note": "Initial baseline assessment"
            })

            # Seed coach with baseline context
            st.session_state.coach_history = [{
                "role": "coach",
                "content": f"I've completed your baseline analysis. Your starting foundation level is **{get_level(starting_level)['label']}** — that's where we build from. Everything else downstream of that is a symptom, not the cause. When you're ready, let's get to work.",
                "timestamp": st.session_state.baseline_date,
                "alert_type": "baseline"
            }]

            # Auto-save baseline images to Swing Library (handles both angles)
            ts = int(datetime.datetime.now().timestamp() * 1000)
            if bd.get("has_dtl") and bd.get("dtl_image"):
                st.session_state.swing_library.append({
                    "id": f"swing_{ts}_dtl",
                    "label": "⭐ BASELINE · DOWN-THE-LINE",
                    "date": datetime.date.today().strftime("%Y-%m-%d"),
                    "date_display": st.session_state.baseline_date,
                    "club": "All clubs",
                    "position": bd.get("dtl_position","Full swing"),
                    "angle": "Down the line (behind)",
                    "level": get_level(starting_level)["label"],
                    "tags": ["Baseline", "DTL"],
                    "notes": f"Baseline DTL view. Starting level: {get_level(starting_level)['label']}",
                    "ai_notes": "",
                    "image_b64": bd["dtl_image"],
                    "mime": "image/jpeg",
                    "saved_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
            if bd.get("has_fo") and bd.get("fo_image"):
                st.session_state.swing_library.append({
                    "id": f"swing_{ts}_fo",
                    "label": "⭐ BASELINE · FACE-ON",
                    "date": datetime.date.today().strftime("%Y-%m-%d"),
                    "date_display": st.session_state.baseline_date,
                    "club": "All clubs",
                    "position": bd.get("fo_position","Full swing"),
                    "angle": "Face on (front)",
                    "level": get_level(starting_level)["label"],
                    "tags": ["Baseline", "Face-On"],
                    "notes": f"Baseline face-on view. Starting level: {get_level(starting_level)['label']}",
                    "ai_notes": "",
                    "image_b64": bd["fo_image"],
                    "mime": "image/jpeg",
                    "saved_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
            # Legacy single-image fallback
            if bd.get("has_image") and bd.get("image") and not (bd.get("has_dtl") or bd.get("has_fo")):
                st.session_state.swing_library.append({
                    "id": f"swing_{ts}",
                    "label": "⭐ BASELINE SWING",
                    "date": datetime.date.today().strftime("%Y-%m-%d"),
                    "date_display": st.session_state.baseline_date,
                    "club": "All clubs",
                    "position": bd.get("position","Full swing"),
                    "angle": bd.get("angle","Down the line (behind)"),
                    "level": get_level(starting_level)["label"],
                    "tags": ["Baseline"],
                    "notes": f"Initial baseline. Starting level: {get_level(starting_level)['label']}",
                    "ai_notes": "",
                    "image_b64": bd["image"],
                    "mime": "image/jpeg",
                    "saved_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })

            st.success("✅ Baseline set! Images saved to your Swing Library. Navigate to Foundation Analysis or Coach Session to begin.")

# ─────────────────────────────────────────────────────────────────────────────
#  PAGE: FOUNDATION ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
elif "Foundation Analysis" in page:
    st.markdown('<div class="hero"><div class="hero-title">FOUNDATION ANALYSIS</div><div class="hero-sub">Build your swing from the ground up — level by level</div></div>', unsafe_allow_html=True)
    st.markdown("---")

    if not st.session_state.baseline_complete:
        st.warning("⚠️ You need to set your baseline first.")
        if st.button("Go to Set Baseline"):
            st.session_state.page = "📐 Set Baseline"
            st.rerun()
        st.stop()

    current_idx = level_index(st.session_state.current_level)

    # Foundation ladder
    st.markdown("### YOUR FOUNDATION LADDER")
    for i, level in enumerate(FOUNDATION_LEVELS):
        score = st.session_state.foundation_score.get(level["id"], 0)
        is_current = level["id"] == st.session_state.current_level
        is_locked = i > current_idx
        is_done = i < current_idx and score >= 70

        status = "🔒 LOCKED" if is_locked else ("✅ PASSED" if is_done else ("▶ CURRENT FOCUS" if is_current else "○ NEEDS WORK"))
        border = "2px solid #4ADE80" if is_current else ("1px solid #2D7A4F" if is_done else "1px solid #1A2D4A")
        opacity = "0.45" if is_locked else "1"

        st.markdown(f"""
        <div style="background:#0D1829;border:{border};border-radius:6px;padding:.9rem 1.2rem;margin:.4rem 0;opacity:{opacity};display:flex;align-items:center;gap:1rem;">
          <div style="font-size:1.8rem;min-width:2.2rem;">{level['icon']}</div>
          <div style="flex:1;">
            <div style="font-family:'Bebas Neue',sans-serif;font-size:1.1rem;color:{'#4ADE80' if is_current else '#F0EBE0'};letter-spacing:.05em;">{level['label']}</div>
            <div style="font-size:.8rem;color:#6B8BAF;">{level['desc']}</div>
          </div>
          <div style="text-align:right;min-width:6rem;">
            <div style="font-family:'Bebas Neue',sans-serif;font-size:1.5rem;color:{'#4ADE80' if score>=75 else '#F59E0B' if score>=50 else '#EF4444'};">{score}%</div>
            <div style="font-size:.7rem;color:#6B8BAF;">{status}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Current level deep dive
    current = get_level(st.session_state.current_level)
    st.markdown(f"### {current['icon']} CURRENT FOCUS: {current['label']}")

    st.markdown(f"""
    <div class="card card-gold">
      <strong>Why this level?</strong> {current['why']}
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("**Key checks for this level:**")
        for check in current["key_checks"]:
            st.markdown(f"- {check}")

    with col2:
        st.markdown("**Self-check session:**")
        scores_input = {}
        for check in current["key_checks"]:
            scores_input[check] = st.slider(check, 1, 10, 5, key=f"sc_{check}")

    st.markdown("---")
    st.markdown("### SESSION CHECK-IN")
    st.caption("After your practice session, report back so your coach can track progress.")

    col1, col2 = st.columns(2)
    with col1:
        session_faults = st.multiselect(
            "Faults that showed up today",
            [f for level in FOUNDATION_LEVELS for f in level["key_checks"]] +
            ["Reverting to old grip", "Losing posture mid-swing", "Early extension returning",
             "Casting the club again", "Slicing returning", "Hooking returning"],
            key="session_faults"
        )
        session_wins = st.text_area("What improved today?", height=70, placeholder="e.g. Hip turn felt much better on irons...", key="session_wins")

    with col2:
        rpe = st.slider("Session difficulty (1=too easy, 10=too hard)", 1, 10, 6, key="rpe")
        confidence = st.slider("Confidence in current focus area (1-10)", 1, 10, 5, key="conf")
        session_image = st.file_uploader("Upload today's swing (optional)", type=["jpg","jpeg","png"], key="session_img")

    checkin_btn = st.button("📊  SUBMIT SESSION CHECK-IN & GET COACH FEEDBACK", use_container_width=True)

    if checkin_btn:
        baseline_faults = st.session_state.session_log[0].get("faults", []) if st.session_state.session_log else []
        regressions = [f for f in session_faults if f in baseline_faults]

        if regressions:
            st.session_state.regression_flags = regressions

        log_entry = {
            "date": datetime.datetime.now().strftime("%B %d, %Y %H:%M"),
            "type": "session",
            "level": st.session_state.current_level,
            "faults": session_faults,
            "wins": session_wins,
            "rpe": rpe,
            "confidence": confidence,
            "scores": {k: v for k, v in scores_input.items()},
        }
        st.session_state.session_log.append(log_entry)

        # Update foundation score
        avg_score = int(sum(scores_input.values()) / len(scores_input) * 10)
        st.session_state.foundation_score[st.session_state.current_level] = avg_score

        # Check level-up
        level_up = avg_score >= 75 and current_idx < len(FOUNDATION_LEVELS) - 1

        # Generate coach feedback
        persona = COACH_PERSONAS[st.session_state.profile.get("coach", list(COACH_PERSONAS.keys())[0])]
        regression_warning = f"\n\nCRITICAL: These baseline faults have RETURNED: {regressions}. You MUST address this directly and firmly. Old habits creeping back." if regressions else ""

        coach_prompt = f"""{persona['style']}

CONTEXT:
- Golfer: {st.session_state.profile.get('handicap','Unknown')}, {st.session_state.profile.get('dominant','Right-handed')}
- Baseline analysis: {st.session_state.baseline_analysis[:800]}...
- Current foundation level: {current['label']}
- Level score: {avg_score}/100
- Sessions completed: {len(st.session_state.session_log)}

THIS SESSION REPORT:
- Faults that appeared: {session_faults}
- What improved: {session_wins if session_wins else 'Not reported'}
- Session difficulty: {rpe}/10
- Confidence in focus area: {confidence}/10
- Baseline regressions detected: {regressions if regressions else 'None'}
{regression_warning}

Respond as their personal coach. Be specific to what they just reported.
{"LEVEL UP: They've earned progression to the next level! Celebrate it briefly, then explain what's next." if level_up else ""}
{"REGRESSION ALERT: Call out the returning habits by name. Be direct. Explain why this specific fault keeps coming back and what they need to do differently." if regressions else ""}

Keep your response under 180 words. Be direct. No fluff. Reference specific things they reported."""

        with st.spinner("Coach is reviewing your session..."):
            client = get_client()
            full_coach = ""
            coach_placeholder = st.empty()

            with client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=400,
                messages=[{"role": "user", "content": coach_prompt}]
            ) as stream:
                for text in stream.text_stream:
                    full_coach += text
                    coach_placeholder.markdown(f"""
                    <div class="coach-bubble">
                      <div class="coach-name">🤖 YOUR COACH · {st.session_state.profile.get('coach','').upper()}</div>
                      <div class="coach-msg">{full_coach}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.session_state.coach_history.append({
                "role": "coach",
                "content": full_coach,
                "timestamp": log_entry["date"],
                "alert_type": "regression" if regressions else ("levelup" if level_up else "checkin")
            })

            if level_up:
                new_idx = current_idx + 1
                st.session_state.current_level = FOUNDATION_LEVELS[new_idx]["id"]
                st.balloons()
                st.success(f"🎉 Level Up! Moving to: {FOUNDATION_LEVELS[new_idx]['label']}")
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
#  PAGE: COACH SESSION
# ─────────────────────────────────────────────────────────────────────────────
elif "Coach Session" in page:
    st.markdown('<div class="hero"><div class="hero-title">COACH SESSION</div><div class="hero-sub">Your AI coach watches, corrects, and pushes you forward</div></div>', unsafe_allow_html=True)
    st.markdown("---")

    persona_key = st.session_state.profile.get("coach", list(COACH_PERSONAS.keys())[0])
    persona = COACH_PERSONAS[persona_key]

    if not st.session_state.baseline_complete:
        st.warning("Your coach needs your baseline before starting sessions.")
        if st.button("Set Baseline First"):
            st.session_state.page = "📐 Set Baseline"
            st.rerun()
        st.stop()

    # Regression banner
    if st.session_state.regression_flags:
        st.markdown(f"""
        <div class="card card-danger">
          <div style="font-family:'Bebas Neue',sans-serif;color:#EF4444;font-size:1rem;">🚨 COACH ALERT: REGRESSION DETECTED</div>
          <p style="margin:.4rem 0 0;">Old habits have returned: <strong>{', '.join(st.session_state.regression_flags)}</strong><br>
          Your coach will address this in the session below.</p>
        </div>
        """, unsafe_allow_html=True)

    # Coach history display
    st.markdown(f"### {persona['emoji']} {persona_key.upper()} — COACHING LOG")

    if not st.session_state.coach_history:
        st.markdown("""
        <div class="coach-bubble">
          <div class="coach-name">🤖 YOUR COACH</div>
          <div class="coach-msg">Waiting for your baseline. Set it first so I know where we're starting from.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for entry in st.session_state.coach_history[-8:]:  # show last 8
            if entry["role"] == "coach":
                alert_colors = {"regression": "#EF4444", "baseline": "#F59E0B", "levelup": "#4ADE80", "checkin": "#A855F7"}
                border_color = alert_colors.get(entry.get("alert_type", "checkin"), "#A855F7")
                st.markdown(f"""
                <div class="coach-bubble" style="border-color:{border_color};">
                  <div class="coach-name" style="color:{border_color};">🤖 COACH · {entry.get('timestamp','')}</div>
                  <div class="coach-msg">{entry['content']}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="user-bubble">
                  <div class="user-name">YOU · {entry.get('timestamp','')}</div>
                  <div style="font-size:.9rem;">{entry['content']}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### TALK TO YOUR COACH")

    # Quick buttons for common situations
    st.markdown("**Quick check-ins:**")
    qcols = st.columns(4)
    quick_prompts = [
        ("😤 Old habit returned", "I just caught myself reverting to an old fault during my session."),
        ("📈 Had a breakthrough", "I had a breakthrough today and want to tell you about it."),
        ("😕 Stuck / no progress", "I feel stuck and am not making progress. I need guidance."),
        ("🏌️ Played a round", "I just played a round and want to report what happened on the course."),
    ]
    for i, (label, prompt_text) in enumerate(quick_prompts):
        with qcols[i]:
            if st.button(label, key=f"quick_{i}", use_container_width=True):
                st.session_state["prefill_msg"] = prompt_text

    user_msg = st.text_area(
        "Message your coach",
        value=st.session_state.get("prefill_msg", ""),
        height=100,
        placeholder="Tell your coach what happened in your session, what fault showed up, what improved, or ask a question...",
        key="coach_input"
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        send_btn = st.button("💬  SEND TO COACH", use_container_width=True)
    with col2:
        clear_btn = st.button("Clear Chat", use_container_width=True)

    if clear_btn:
        st.session_state.coach_history = []
        st.session_state.regression_flags = []
        st.rerun()

    if send_btn and user_msg.strip():
        # Add user message
        timestamp = datetime.datetime.now().strftime("%b %d %H:%M")
        st.session_state.coach_history.append({
            "role": "user",
            "content": user_msg,
            "timestamp": timestamp
        })

        # Check for regression keywords
        regression_keywords = ["back to", "old habit", "slicing again", "hooking again", "still doing", "can't stop", "keeps happening", "fault returned", "reverting"]
        has_regression_language = any(kw in user_msg.lower() for kw in regression_keywords)

        # Build full context
        recent_log = st.session_state.session_log[-3:] if st.session_state.session_log else []
        recent_coach = st.session_state.coach_history[-6:]

        conversation_history = []
        for entry in recent_coach:
            role = "user" if entry["role"] == "user" else "assistant"
            conversation_history.append({"role": role, "content": entry["content"]})

        # Build pro lessons context
        pro_lessons_context = ""
        if st.session_state.coach_lessons:
            recent_lessons = st.session_state.coach_lessons[-3:]
            pro_lessons_context = "\n\nREAL-WORLD COACH LESSONS (CRITICAL — STAY ALIGNED WITH THESE):\n"
            for ln in recent_lessons:
                pro_lessons_context += f"\n- {ln.get('date','?')} with {ln.get('coach_name','?')} ({ln.get('focus','?')}): "
                pro_lessons_context += f"Worked on: {ln.get('worked_on','')[:150]}. "
                if ln.get('corrections'): pro_lessons_context += f"Corrections: {ln['corrections'][:150]}. "
                if ln.get('drills'): pro_lessons_context += f"Drills assigned: {ln['drills'][:150]}."

        system_prompt = f"""{persona['style']}

YOU ARE AN AI GOLF COACH IN AN ONGOING COACHING RELATIONSHIP. You have full context on this golfer.

GOLFER FILE:
- Profile: {st.session_state.profile.get('handicap','Unknown')}, {st.session_state.profile.get('dominant','Right-handed')}
- Baseline set: {st.session_state.baseline_date}
- Current foundation level: {get_level(st.session_state.current_level)['label']}
- Foundation scores: {st.session_state.foundation_score}
- Active regression flags: {st.session_state.regression_flags}
- Sessions completed: {len(st.session_state.session_log)}
- Pro lessons logged: {len(st.session_state.coach_lessons)}
- Recent session summary: {json.dumps(recent_log, indent=2) if recent_log else 'No sessions yet'}

BASELINE ANALYSIS (abbreviated):
{st.session_state.baseline_analysis[:600]}...
{pro_lessons_context}

COACHING RULES:
1. If the golfer mentions reverting to old faults, call it out IMMEDIATELY and SPECIFICALLY. Name the fault. Explain why it keeps returning. Give them the correction and a drill.
2. If they're making progress, acknowledge it briefly and push them to the next challenge.
3. Always connect your coaching back to their foundation level and baseline.
4. Never give generic advice — always specific to THEIR swing file.
5. If they seem to be coasting, push harder.
6. Keep responses under 200 words unless they ask a technical question.
7. **IMPORTANT**: If they have logged pro lessons, ALIGN your coaching with what their real-world coach has been teaching. Reference the corrections and drills their pro coach gave them. Never contradict their pro coach — reinforce.
8. You are a SUPPLEMENT to their real coach, not a replacement. Remind them when appropriate to bring tough questions to their pro.
{"9. REGRESSION DETECTED: They're reverting to baseline faults. Lead with this. Be direct." if has_regression_language else ""}

Respond as their coach right now."""

        with st.spinner(f"{persona['emoji']} Coach is responding..."):
            client = get_client()
            full_response = ""
            coach_placeholder = st.empty()

            with client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                system=system_prompt,
                messages=conversation_history,
            ) as stream:
                for text in stream.text_stream:
                    full_response += text
                    coach_placeholder.markdown(f"""
                    <div class="coach-bubble">
                      <div class="coach-name" style="color:{'#EF4444' if has_regression_language else '#A855F7'};">
                        🤖 {persona_key.upper()} · {timestamp}
                        {' 🚨 REGRESSION ALERT' if has_regression_language else ''}
                      </div>
                      <div class="coach-msg">{full_response}</div>
                    </div>
                    """, unsafe_allow_html=True)

        st.session_state.coach_history.append({
            "role": "coach",
            "content": full_response,
            "timestamp": timestamp,
            "alert_type": "regression" if has_regression_language else "message"
        })

        if "prefill_msg" in st.session_state:
            del st.session_state["prefill_msg"]

        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
#  PAGE: SWING LIBRARY (Store & Compare Swings Over Time)
# ─────────────────────────────────────────────────────────────────────────────
elif "Swing Library" in page:
    st.markdown('<div class="hero"><div class="hero-title">SWING LIBRARY</div><div class="hero-sub">Save every swing · compare progress · watch yourself evolve</div></div>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("""
    <div class="card card-gold">
      <strong>📂 Your personal swing archive.</strong> Save snapshots of your swing over time, tag them by club/position/level,
      and compare side-by-side to see exactly what's changing. Use this as visual proof of your improvement journey.
    </div>
    """, unsafe_allow_html=True)

    # ── Tabs: Save / Browse / Compare / Timeline
    tab_save, tab_browse, tab_compare, tab_timeline = st.tabs([
        "💾  Save New Swing",
        "🗂  Browse Library",
        "⚖️  Compare Swings",
        "📅  Timeline View"
    ])

    # ── Tab 1: Save New Swing ──────────────────────────────────────────────
    with tab_save:
        st.markdown("### Save a Swing Snapshot")
        st.caption("Capture or upload an image and tag it for your timeline.")

        col1, col2 = st.columns(2, gap="large")

        with col1:
            st.markdown("**Image Source**")
            save_method = st.radio(
                "How are you adding this swing?",
                ["📁 Upload image", "📷 Use camera"],
                horizontal=True,
                key="save_method",
                label_visibility="collapsed"
            )

            new_swing_img = None
            if "Upload" in save_method:
                new_swing_img = st.file_uploader("Upload swing image", type=["jpg","jpeg","png"], key="lib_upload")
            else:
                new_swing_img = st.camera_input("Capture swing", key="lib_camera")

            if new_swing_img:
                st.image(new_swing_img, caption="Preview", use_container_width=True)

        with col2:
            st.markdown("**Tag This Swing**")

            swing_label = st.text_input(
                "Label (required)",
                placeholder="e.g. Driver — top of backswing — week 3",
                key="lib_label"
            )

            swing_date = st.date_input("Date", value=datetime.date.today(), key="lib_date")

            swing_club = st.selectbox(
                "Club used",
                ["Driver", "3-Wood", "5-Wood", "Hybrid", "Long iron (3-5)", "Mid iron (6-7)",
                 "Short iron (8-9)", "Pitching wedge", "Gap wedge", "Sand wedge", "Lob wedge",
                 "Putter", "Other"],
                key="lib_club"
            )

            swing_position = st.selectbox(
                "Swing position",
                ["Full swing", "Address/Setup", "Takeaway (P2)", "Top of backswing (P4)",
                 "Transition (P5)", "Pre-impact (P6)", "Impact (P7)", "Post-impact (P8)",
                 "Follow-through", "Finish position"],
                key="lib_position"
            )

            swing_angle = st.selectbox(
                "Camera angle",
                ["Down the line (behind)", "Face on (front)", "45° angle", "Overhead", "Other"],
                key="lib_angle"
            )

            swing_level = st.selectbox(
                "Foundation level focus",
                [l["label"] for l in FOUNDATION_LEVELS],
                index=level_index(st.session_state.current_level) if st.session_state.baseline_complete else 0,
                key="lib_level"
            )

            swing_tags = st.multiselect(
                "Tags (optional)",
                ["Baseline", "Practice session", "On course", "Pro lesson",
                 "Breakthrough", "Regression", "Good shot", "Bad shot",
                 "Recording with guidelines", "Slow-mo screenshot"],
                key="lib_tags"
            )

            swing_notes = st.text_area(
                "Notes (what happened, what changed, what to remember)",
                placeholder="e.g. Finally felt the hip turn unlock. Coach drill #3 paying off. Need to keep working...",
                height=100,
                key="lib_notes"
            )

        st.markdown("---")

        col_save, col_analyze = st.columns(2)
        with col_save:
            save_btn = st.button("💾  SAVE TO LIBRARY", use_container_width=True)
        with col_analyze:
            save_and_analyze_btn = st.button("🔬  SAVE + AI ANALYZE", use_container_width=True)

        if (save_btn or save_and_analyze_btn) and new_swing_img and swing_label.strip():
            swing_id = f"swing_{int(datetime.datetime.now().timestamp() * 1000)}"
            img_b64 = img_to_b64(new_swing_img)
            mime = "image/jpeg" if new_swing_img.name.lower().endswith(("jpg","jpeg")) else "image/png"

            ai_notes = ""
            if save_and_analyze_btn:
                with st.spinner("AI analyzing this swing..."):
                    client = get_client()
                    baseline_ctx = st.session_state.baseline_analysis[:500] if st.session_state.baseline_analysis else "No baseline"
                    analyze_prompt = f"""You are a PGA golf instructor analyzing a swing image for an ongoing student.

Context:
- Date: {swing_date.strftime('%B %d, %Y')}
- Club: {swing_club}
- Position captured: {swing_position}
- Camera angle: {swing_angle}
- Foundation level focus: {swing_level}
- Student notes: {swing_notes if swing_notes else 'None'}
- Baseline context: {baseline_ctx}

Provide a CONCISE swing analysis (max 200 words) covering:
1. **What's working** — 1-2 specific positives
2. **What to fix** — 1-2 specific faults visible
3. **Quick reference** — 1 sentence for future comparison

Be specific and reference visible body positions. This will be saved alongside the image for future comparison."""

                    response = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=500,
                        messages=[{
                            "role": "user",
                            "content": [
                                {"type": "image", "source": {"type": "base64", "media_type": mime, "data": img_b64}},
                                {"type": "text", "text": analyze_prompt}
                            ]
                        }]
                    )
                    ai_notes = response.content[0].text

            swing_entry = {
                "id": swing_id,
                "label": swing_label,
                "date": swing_date.strftime("%Y-%m-%d"),
                "date_display": swing_date.strftime("%B %d, %Y"),
                "club": swing_club,
                "position": swing_position,
                "angle": swing_angle,
                "level": swing_level,
                "tags": swing_tags,
                "notes": swing_notes,
                "ai_notes": ai_notes,
                "image_b64": img_b64,
                "mime": mime,
                "saved_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            st.session_state.swing_library.append(swing_entry)
            st.success(f"✓ Swing saved to library! ({len(st.session_state.swing_library)} total swings stored)")
            if ai_notes:
                st.markdown(f"""
                <div class="card card-coach">
                  <strong style="color:#A855F7;">🤖 AI ANALYSIS</strong><br>
                  {ai_notes}
                </div>
                """, unsafe_allow_html=True)
            st.balloons()

        elif save_btn or save_and_analyze_btn:
            if not new_swing_img:
                st.warning("Please upload or capture an image first.")
            elif not swing_label.strip():
                st.warning("Please add a label for this swing.")

    # ── Tab 2: Browse Library ──────────────────────────────────────────────
    with tab_browse:
        st.markdown("### Your Saved Swings")

        if not st.session_state.swing_library:
            st.info("📂 Your library is empty. Save your first swing in the 'Save New Swing' tab.")
        else:
            # Stats row
            total_swings = len(st.session_state.swing_library)
            unique_clubs = len(set(s["club"] for s in st.session_state.swing_library))
            tagged_baseline = sum(1 for s in st.session_state.swing_library if "Baseline" in s.get("tags", []))
            tagged_breakthrough = sum(1 for s in st.session_state.swing_library if "Breakthrough" in s.get("tags", []))

            cols = st.columns(4)
            with cols[0]: st.markdown(f"""<div class="metric-box"><div class="metric-val">{total_swings}</div><div class="metric-lbl">Total Swings</div></div>""", unsafe_allow_html=True)
            with cols[1]: st.markdown(f"""<div class="metric-box"><div class="metric-val">{unique_clubs}</div><div class="metric-lbl">Different Clubs</div></div>""", unsafe_allow_html=True)
            with cols[2]: st.markdown(f"""<div class="metric-box"><div class="metric-val">{tagged_baseline}</div><div class="metric-lbl">Baseline Swings</div></div>""", unsafe_allow_html=True)
            with cols[3]: st.markdown(f"""<div class="metric-box"><div class="metric-val">{tagged_breakthrough}</div><div class="metric-lbl">Breakthroughs</div></div>""", unsafe_allow_html=True)

            st.markdown("---")

            # Filters
            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            with col_f1:
                filter_club = st.multiselect("Club", sorted(set(s["club"] for s in st.session_state.swing_library)), key="f_club")
            with col_f2:
                filter_position = st.multiselect("Position", sorted(set(s["position"] for s in st.session_state.swing_library)), key="f_pos")
            with col_f3:
                filter_level = st.multiselect("Level", sorted(set(s["level"] for s in st.session_state.swing_library)), key="f_lvl")
            with col_f4:
                all_tags = sorted(set(t for s in st.session_state.swing_library for t in s.get("tags", [])))
                filter_tags = st.multiselect("Tags", all_tags, key="f_tags")

            sort_order = st.radio(
                "Sort by",
                ["Newest first", "Oldest first", "By club", "By position"],
                horizontal=True,
                key="lib_sort"
            )

            # Filter
            filtered = st.session_state.swing_library
            if filter_club: filtered = [s for s in filtered if s["club"] in filter_club]
            if filter_position: filtered = [s for s in filtered if s["position"] in filter_position]
            if filter_level: filtered = [s for s in filtered if s["level"] in filter_level]
            if filter_tags: filtered = [s for s in filtered if any(t in s.get("tags",[]) for t in filter_tags)]

            # Sort
            if sort_order == "Newest first":
                filtered = sorted(filtered, key=lambda x: x["saved_at"], reverse=True)
            elif sort_order == "Oldest first":
                filtered = sorted(filtered, key=lambda x: x["saved_at"])
            elif sort_order == "By club":
                filtered = sorted(filtered, key=lambda x: x["club"])
            else:
                filtered = sorted(filtered, key=lambda x: x["position"])

            st.markdown(f"**Showing {len(filtered)} of {total_swings} swings**")
            st.markdown("---")

            # Grid display
            for i in range(0, len(filtered), 2):
                cols = st.columns(2, gap="medium")
                for j, swing in enumerate(filtered[i:i+2]):
                    with cols[j]:
                        # Image
                        st.image(f"data:{swing['mime']};base64,{swing['image_b64']}", use_container_width=True)

                        # Title + date
                        st.markdown(f"""
                        <div style="background:#0D1829;border:1px solid #1A2D4A;border-top:none;border-radius:0 0 6px 6px;padding:.9rem 1rem;margin-top:-0.5rem;">
                          <div style="font-family:'Bebas Neue',sans-serif;color:#F59E0B;font-size:1.05rem;letter-spacing:.04em;">{swing['label']}</div>
                          <div style="font-size:.78rem;color:#6B8BAF;margin:.2rem 0;">📅 {swing['date_display']}</div>
                          <div style="margin:.4rem 0;">
                            <span class="badge badge-gold">⛳ {swing['club']}</span>
                            <span class="badge badge-green">📍 {swing['position']}</span>
                          </div>
                          <div style="margin:.3rem 0;">
                            <span class="badge badge-purple">{swing['angle']}</span>
                            <span class="badge badge-warn">{swing['level']}</span>
                          </div>
                          {('<div style="margin:.3rem 0;">' + ''.join([f'<span class="badge badge-green">#{t}</span>' for t in swing.get("tags",[])]) + '</div>') if swing.get("tags") else ''}
                          {f'<div style="font-size:.83rem;color:#F0EBE0;margin-top:.5rem;line-height:1.5;border-top:1px solid #1A2D4A;padding-top:.5rem;">📝 {swing["notes"]}</div>' if swing.get("notes") else ''}
                          {f'<div style="font-size:.82rem;color:#A855F7;margin-top:.4rem;line-height:1.5;border-top:1px solid #1A2D4A;padding-top:.5rem;"><strong>🤖 AI:</strong> {swing["ai_notes"]}</div>' if swing.get("ai_notes") else ''}
                        </div>
                        """, unsafe_allow_html=True)

                        # Action row
                        b1, b2, b3 = st.columns([1, 1, 1])
                        with b1:
                            if st.button("⚖ Compare", key=f"cmp_{swing['id']}", use_container_width=True):
                                if swing["id"] not in st.session_state.compare_selection:
                                    if len(st.session_state.compare_selection) < 4:
                                        st.session_state.compare_selection.append(swing["id"])
                                        st.success(f"Added to comparison ({len(st.session_state.compare_selection)}/4)")
                                    else:
                                        st.warning("Max 4 swings in comparison. Clear some first.")
                                else:
                                    st.info("Already in comparison")
                        with b2:
                            img_bytes = base64.b64decode(swing['image_b64'])
                            st.download_button(
                                "⬇ Save",
                                img_bytes,
                                file_name=f"{swing['label'].replace(' ','_')}_{swing['date']}.{'jpg' if 'jpeg' in swing['mime'] else 'png'}",
                                mime=swing['mime'],
                                key=f"dl_{swing['id']}",
                                use_container_width=True
                            )
                        with b3:
                            if st.button("🗑 Delete", key=f"del_{swing['id']}", use_container_width=True):
                                st.session_state.swing_library = [s for s in st.session_state.swing_library if s["id"] != swing["id"]]
                                if swing["id"] in st.session_state.compare_selection:
                                    st.session_state.compare_selection.remove(swing["id"])
                                st.rerun()

                        st.markdown("")  # spacer

    # ── Tab 3: Compare Swings ──────────────────────────────────────────────
    with tab_compare:
        st.markdown("### Side-by-Side Comparison")
        st.caption("Compare up to 4 swings at once. Tap '⚖ Compare' on swings in the Browse tab to add them here.")

        selected = [s for s in st.session_state.swing_library if s["id"] in st.session_state.compare_selection]

        if not selected:
            st.info("🔍 No swings selected for comparison yet. Go to the **Browse Library** tab and tap '⚖ Compare' on the swings you want to compare.")
        else:
            col_top1, col_top2 = st.columns([3, 1])
            with col_top1:
                st.markdown(f"**Comparing {len(selected)} swings**")
            with col_top2:
                if st.button("✕  Clear All", use_container_width=True):
                    st.session_state.compare_selection = []
                    st.rerun()

            st.markdown("---")

            # Display side by side
            num_swings = len(selected)
            cols = st.columns(num_swings, gap="small")
            for idx, swing in enumerate(selected):
                with cols[idx]:
                    st.markdown(f"""
                    <div style="text-align:center;padding:.5rem 0;background:#0D1829;border-radius:6px 6px 0 0;border:1px solid #1A2D4A;border-bottom:none;">
                      <div style="font-family:'Bebas Neue',sans-serif;color:#F59E0B;font-size:.95rem;letter-spacing:.05em;">SWING {idx+1}</div>
                      <div style="font-size:.75rem;color:#6B8BAF;">{swing['date_display']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.image(f"data:{swing['mime']};base64,{swing['image_b64']}", use_container_width=True)

                    st.markdown(f"""
                    <div style="background:#0D1829;border:1px solid #1A2D4A;border-top:none;border-radius:0 0 6px 6px;padding:.7rem .9rem;">
                      <div style="font-family:'Bebas Neue',sans-serif;font-size:.9rem;color:#F0EBE0;line-height:1.2;">{swing['label']}</div>
                      <div style="margin-top:.4rem;font-size:.72rem;">
                        <span class="badge badge-gold">{swing['club']}</span>
                        <span class="badge badge-green">{swing['position']}</span>
                      </div>
                      <div style="margin-top:.3rem;font-size:.72rem;">
                        <span class="badge badge-purple">{swing['angle']}</span>
                      </div>
                      {f'<div style="font-size:.78rem;color:#F0EBE0;margin-top:.5rem;line-height:1.4;">{swing["notes"][:120]}{"..." if len(swing.get("notes","")) > 120 else ""}</div>' if swing.get("notes") else ''}
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button(f"Remove", key=f"rm_cmp_{swing['id']}", use_container_width=True):
                        st.session_state.compare_selection.remove(swing["id"])
                        st.rerun()

            st.markdown("---")

            # AI comparison
            if len(selected) >= 2:
                st.markdown("### 🤖 AI Comparison Analysis")
                st.caption("Have the AI coach compare these swings and tell you what's changed.")

                if st.button("🔬  RUN AI COMPARISON", use_container_width=True):
                    with st.spinner("AI analyzing differences..."):
                        client = get_client()

                        # Build content array with all images + comparison prompt
                        content_blocks = []
                        for i, swing in enumerate(selected):
                            content_blocks.append({
                                "type": "image",
                                "source": {"type": "base64", "media_type": swing["mime"], "data": swing["image_b64"]}
                            })

                        swings_info = "\n".join([
                            f"- Swing {i+1} ({swing['date_display']}): {swing['label']} | Club: {swing['club']} | Position: {swing['position']} | Angle: {swing['angle']} | Notes: {swing.get('notes','none')}"
                            for i, swing in enumerate(selected)
                        ])

                        baseline_ctx = st.session_state.baseline_analysis[:600] if st.session_state.baseline_analysis else "No baseline"

                        compare_prompt = f"""You are a PGA golf instructor comparing this student's swings over time.

GOLFER CONTEXT:
- Handicap: {st.session_state.profile.get('handicap','Unknown')}
- Hand: {st.session_state.profile.get('dominant','Right-handed')}
- Current focus: {get_level(st.session_state.current_level)['label'] if st.session_state.baseline_complete else 'Not set'}

BASELINE: {baseline_ctx}

SWINGS BEING COMPARED (in order):
{swings_info}

You see {len(selected)} images in chronological order. Analyze them as a progression.

Respond in this structure:

## 📊 PROGRESS OBSERVED
What HAS improved between swings? Reference specific visible changes.

## ⚠️ REGRESSIONS / NEW ISSUES
What got worse or new issues that appeared? Be specific.

## 🔍 KEY DIFFERENCES
List 3-5 specific body position differences between earliest and latest swing. Reference what you actually see.

## 🎯 WHAT THIS TELLS US
What does this progression mean? Is the work paying off? What's the trajectory?

## 📝 NEXT FOCUS
Based on what you see now, what should they work on next?

Be specific. Reference the swing numbers (Swing 1, Swing 2, etc.) and visible positions. Avoid vague language."""

                        content_blocks.append({"type": "text", "text": compare_prompt})

                        st.markdown("---")
                        result_placeholder = st.empty()
                        full_text = ""
                        with client.messages.stream(
                            model="claude-sonnet-4-20250514",
                            max_tokens=2000,
                            messages=[{"role": "user", "content": content_blocks}]
                        ) as stream:
                            for text in stream.text_stream:
                                full_text += text
                                result_placeholder.markdown(f"""
                                <div class="card card-coach">
                                  <div style="font-family:'Bebas Neue',sans-serif;color:#A855F7;font-size:1.1rem;letter-spacing:.05em;margin-bottom:.5rem;">🤖 COMPARISON ANALYSIS</div>
                                  {full_text}
                                </div>
                                """, unsafe_allow_html=True)

    # ── Tab 4: Timeline View ───────────────────────────────────────────────
    with tab_timeline:
        st.markdown("### Swing Timeline")
        st.caption("Chronological view of your improvement journey.")

        if not st.session_state.swing_library:
            st.info("📅 No swings to timeline yet. Save some swings to build your history.")
        else:
            # Group by month
            sorted_swings = sorted(st.session_state.swing_library, key=lambda x: x["date"], reverse=True)

            from collections import defaultdict
            by_month = defaultdict(list)
            for s in sorted_swings:
                month_key = s["date"][:7]  # YYYY-MM
                by_month[month_key].append(s)

            for month_key in sorted(by_month.keys(), reverse=True):
                year, month = month_key.split("-")
                month_name = datetime.date(int(year), int(month), 1).strftime("%B %Y").upper()

                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:1rem;margin:1.5rem 0 .8rem;">
                  <div style="font-family:'Bebas Neue',sans-serif;font-size:1.4rem;color:#F59E0B;letter-spacing:.1em;">{month_name}</div>
                  <div style="flex:1;height:1px;background:#1A2D4A;"></div>
                  <div style="background:#0D1829;border:1px solid #1A2D4A;border-radius:12px;padding:.2rem .7rem;font-size:.75rem;color:#6B8BAF;">{len(by_month[month_key])} swings</div>
                </div>
                """, unsafe_allow_html=True)

                # Display swings for this month as horizontal cards
                for swing in by_month[month_key]:
                    col_img, col_info = st.columns([1, 3], gap="medium")
                    with col_img:
                        st.image(f"data:{swing['mime']};base64,{swing['image_b64']}", use_container_width=True)
                    with col_info:
                        tags_html = ''.join([f'<span class="badge badge-green">#{t}</span>' for t in swing.get("tags",[])])
                        st.markdown(f"""
                        <div style="padding:.5rem .3rem;">
                          <div style="font-family:'Bebas Neue',sans-serif;color:#F0EBE0;font-size:1.1rem;letter-spacing:.04em;">{swing['label']}</div>
                          <div style="font-size:.78rem;color:#6B8BAF;margin:.2rem 0 .5rem;">📅 {swing['date_display']} · saved {swing['saved_at'][:10]}</div>
                          <div style="margin:.3rem 0;">
                            <span class="badge badge-gold">⛳ {swing['club']}</span>
                            <span class="badge badge-green">📍 {swing['position']}</span>
                            <span class="badge badge-purple">{swing['angle']}</span>
                          </div>
                          {f'<div style="margin:.3rem 0;">{tags_html}</div>' if tags_html else ''}
                          {f'<div style="font-size:.85rem;color:#F0EBE0;margin-top:.5rem;line-height:1.5;">📝 {swing["notes"]}</div>' if swing.get("notes") else ''}
                          {f'<div style="font-size:.82rem;color:#A855F7;margin-top:.4rem;line-height:1.5;"><strong>🤖 AI:</strong> {swing["ai_notes"]}</div>' if swing.get("ai_notes") else ''}
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("<div style='height:.6rem;'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  PAGE: EQUIPMENT FIT (Clubs & Shafts)
# ─────────────────────────────────────────────────────────────────────────────
elif "Equipment Fit" in page:
    st.markdown('<div class="hero"><div class="hero-title">EQUIPMENT FIT</div><div class="hero-sub">Club & shaft recommendations matched to your swing</div></div>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("""
    <div class="card card-gold">
      <strong>⚠️ This is educational guidance, not a substitute for in-person club fitting.</strong>
      The recommendations below are general suggestions based on your swing data. For purchasing decisions, visit a
      certified club fitter (Club Champion, True Spec, PGA Tour Superstore, GolfTec) with a launch monitor.
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.baseline_complete:
        st.warning("Set your baseline first so recommendations can be tailored to your swing.")
        if st.button("Go to Set Baseline"):
            st.session_state.page = "📐 Set Baseline"
            st.rerun()
        st.stop()

    st.markdown("### 📋 SWING & PHYSICAL DATA")
    st.caption("More accurate inputs = more accurate recommendations. Use a launch monitor or driving range data if available.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Driver Swing Speed (mph)**")
        swing_speed = st.slider("Estimated driver swing speed", 60, 130, 95, key="eq_speed")
        st.caption("Avg amateur ~85-95 · LPGA ~94 · PGA ~113")

        carry_distance = st.slider("Driver carry distance (yards)", 130, 320, 230, key="eq_carry")
        st.caption("Avg amateur ~215 · LPGA ~218 · PGA ~280")

        ball_flight_height = st.select_slider(
            "Typical ball flight height",
            options=["Very low", "Low", "Medium", "High", "Very high (ballooning)"],
            value="Medium",
            key="eq_height"
        )

        spin_issue = st.selectbox(
            "Spin pattern (if known)",
            ["Don't know", "Too much spin (ball ballooning)", "Not enough spin (low launching, knuckling)", "Spin seems right"],
            key="eq_spin"
        )

    with col2:
        st.markdown("**Physical & Tempo**")
        height_in = st.slider("Your height (inches)", 60, 80, 70, key="eq_height_in")
        wrist_to_floor = st.slider("Wrist-to-floor measurement (inches)", 26, 42, 34, key="eq_wtf")
        st.caption("Stand naturally, measure from wrist crease to floor")

        tempo = st.select_slider(
            "Swing tempo",
            options=["Very slow/smooth", "Smooth", "Moderate", "Quick", "Very fast/aggressive"],
            value="Moderate",
            key="eq_tempo"
        )

        release = st.selectbox(
            "Hand release type",
            ["Don't know", "Early release (cast/flip)", "Late release (lots of lag)", "Neutral release"],
            key="eq_release"
        )

        strength = st.select_slider(
            "Physical strength",
            options=["Below average", "Average", "Above average", "Very strong"],
            value="Average",
            key="eq_strength"
        )

    st.markdown("### 🎯 CURRENT EQUIPMENT (Optional)")
    col3, col4 = st.columns(2)
    with col3:
        current_driver = st.text_input("Current driver (brand/model)", placeholder="e.g. TaylorMade Stealth 2", key="eq_cur_driver")
        current_irons = st.text_input("Current irons (brand/model)", placeholder="e.g. Callaway Apex 21", key="eq_cur_irons")
    with col4:
        current_shaft = st.selectbox("Current driver shaft flex", ["Don't know", "Ladies (L)", "Senior (A)", "Regular (R)", "Stiff (S)", "X-Stiff (X)"], key="eq_cur_shaft")
        equipment_age = st.selectbox("Current set age", ["< 1 year", "1-3 years", "3-5 years", "5-10 years", "10+ years"], key="eq_age")

    st.markdown("---")
    gen_eq_btn = st.button("🎒  GENERATE EQUIPMENT RECOMMENDATIONS", use_container_width=True)

    if gen_eq_btn:
        baseline_summary = st.session_state.baseline_analysis[:1000] if st.session_state.baseline_analysis else "No baseline analysis available"
        recent_faults = []
        for log in st.session_state.session_log[-3:]:
            recent_faults.extend(log.get("faults", []))

        eq_prompt = f"""You are a PGA-certified master club fitter and equipment specialist. Generate detailed, specific club and shaft recommendations for this golfer.

GOLFER PROFILE:
- Handicap: {st.session_state.profile.get('handicap','Unknown')}
- Hand: {st.session_state.profile.get('dominant','Right-handed')}
- Height: {height_in} inches
- Wrist-to-floor: {wrist_to_floor} inches
- Strength: {strength}

SWING DATA:
- Driver swing speed: {swing_speed} mph
- Driver carry: {carry_distance} yards
- Ball flight height: {ball_flight_height}
- Spin pattern: {spin_issue}
- Tempo: {tempo}
- Release type: {release}

CURRENT EQUIPMENT:
- Driver: {current_driver or 'Not specified'}
- Irons: {current_irons or 'Not specified'}
- Shaft flex: {current_shaft}
- Equipment age: {equipment_age}

SWING DIAGNOSIS CONTEXT (from baseline):
{baseline_summary}

Recent swing faults observed: {recent_faults}

Provide your recommendations in this EXACT structure:

## ⚠️ DISCLAIMER
Lead with a 1-sentence reminder that these are educational suggestions and a certified fitter with a launch monitor should make final decisions.

## 🏌️ DRIVER RECOMMENDATIONS

### Head Type
Recommend draw-bias, neutral, fade-bias, or low-spin head. Explain WHY based on their fault pattern.

### Loft
Specific loft range (e.g. "10.5° to 12°") with reasoning based on their swing speed, attack angle, and ball flight height.

### Shaft Flex
Recommend specific flex (L/A/R/S/X) based on swing speed AND tempo. Explain the tempo factor.

### Shaft Weight & Profile
Light/mid/heavy weight in grams. Tip-stiff vs. tip-flex profile. Explain why for their release pattern.

### Specific Models to Demo
Suggest 2-3 current driver models that match. Be specific (e.g. "TaylorMade Qi10 Max with Mitsubishi Tensei Blue 60 R-flex").

## ⛳ IRON RECOMMENDATIONS

### Iron Type
Game improvement / players distance / players iron / blade. Match to handicap and fault pattern.

### Shaft Material
Steel vs. graphite — justify based on age, swing speed, strength, and any joint considerations.

### Iron Shaft Flex & Weight
Specific flex and weight range. Explain.

### Length & Lie Angle
Standard vs. +/- inches, lie angle based on wrist-to-floor measurement.

### Specific Models to Demo
2-3 specific iron sets that fit.

## 🪙 WEDGE RECOMMENDATIONS
Suggested wedge setup (gaps, bounces, grinds) based on their game.

## 🥄 PUTTER RECOMMENDATIONS
Blade vs. mallet, weight, length — based on tempo and stroke type.

## 💰 BUDGET TIERS
- **Premium fit ($2000+):** Best-case recommendations
- **Mid-range ($800-2000):** Smart compromises
- **Budget-friendly (<$800):** Where to save without sacrificing fit

## 🎯 PRIORITY ORDER
Rank order of equipment changes (e.g. "Fix driver shaft first because it's amplifying your fade").

## 🏟️ WHERE TO GET FITTED
List specific fitter options (Club Champion, True Spec, PGA Tour Superstore, etc.) and what to expect.

Be specific, use real product names, give real numbers. Avoid vague advice."""

        with st.spinner("Building your equipment fit profile..."):
            client = get_client()
            st.markdown("---")
            st.markdown("## 🎒 Your Equipment Recommendations")
            result_placeholder = st.empty()
            full_text = ""
            with client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=3000,
                messages=[{"role": "user", "content": eq_prompt}]
            ) as stream:
                for text in stream.text_stream:
                    full_text += text
                    result_placeholder.markdown(full_text)

            st.session_state.equipment_recs = full_text
            st.success("✓ Equipment recommendations saved. Bring this to your fitter for context.")

    elif st.session_state.equipment_recs:
        st.markdown("---")
        st.markdown("## 📋 Your Most Recent Equipment Recommendations")
        st.markdown(st.session_state.equipment_recs)

# ─────────────────────────────────────────────────────────────────────────────
#  PAGE: PRO LESSONS (Integrate real-world coaching)
# ─────────────────────────────────────────────────────────────────────────────
elif "Pro Lessons" in page:
    st.markdown('<div class="hero"><div class="hero-title">PRO LESSONS</div><div class="hero-sub">Log lessons from your real-world coach — the AI integrates them</div></div>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("""
    <div class="card card-green">
      <strong>👔 Working with a real coach is highly recommended.</strong> Use this page to log notes,
      video links, drill assignments, or files from your PGA/LPGA professional. The MySwing and Me AI coach
      will incorporate your lessons into every diagnosis and coaching session — keeping everything aligned
      with what your real-world coach is teaching you.
    </div>
    """, unsafe_allow_html=True)

    tab_add, tab_view = st.tabs(["➕  Add Lesson", "📚  View My Lessons"])

    with tab_add:
        st.markdown("### Log a New Lesson")
        st.caption("After every lesson with your real coach, log the key takeaways here. This keeps your AI coach in sync.")

        col1, col2 = st.columns(2)
        with col1:
            lesson_date = st.date_input("Lesson date", value=datetime.date.today(), key="ln_date")
            coach_name = st.text_input("Coach name", placeholder="e.g. John Smith, PGA Professional", key="ln_coach")
            lesson_format = st.selectbox(
                "Lesson format",
                ["In-person 1-on-1", "Group lesson", "Video lesson (remote)", "Phone/Zoom coaching", "Club fitting session", "On-course playing lesson", "Other"],
                key="ln_format"
            )

        with col2:
            lesson_length = st.selectbox("Length", ["30 min", "45 min", "60 min", "90 min", "2 hours", "Half day", "Full day"], key="ln_length")
            primary_focus = st.selectbox(
                "Primary focus area",
                [l["label"] for l in FOUNDATION_LEVELS] + ["Short game", "Putting", "Course management", "Mental game", "Equipment", "Full swing assessment"],
                key="ln_focus"
            )
            lesson_cost = st.text_input("Cost (optional)", placeholder="$100", key="ln_cost")

        st.markdown("### 📝 Lesson Notes")
        what_worked_on = st.text_area(
            "What did you work on?",
            placeholder="e.g. Coach noticed I was rolling my wrists at takeaway. We worked on a one-piece move with my chest leading the takeaway...",
            height=120,
            key="ln_work"
        )

        key_corrections = st.text_area(
            "Key corrections / swing thoughts coach gave you",
            placeholder="e.g. 1. Logo on shirt points at ball at top of swing. 2. Pressure into lead foot first. 3. Hold finish for 3 seconds...",
            height=120,
            key="ln_corrections"
        )

        drills_assigned = st.text_area(
            "Drills coach assigned",
            placeholder="e.g. 1. Towel under armpits drill - 20 swings daily. 2. Alignment stick plane drill - 3x/week. 3. Slow-mo swings...",
            height=100,
            key="ln_drills"
        )

        homework = st.text_area(
            "Homework / next steps",
            placeholder="e.g. Work on takeaway drills for 2 weeks before next lesson. Film 3 swings/week and send to coach...",
            height=80,
            key="ln_homework"
        )

        next_lesson = st.date_input("Next scheduled lesson (optional)", value=None, key="ln_next")

        st.markdown("### 📎 Upload Lesson Files (Optional)")
        st.caption("Video links, swing analysis images, written notes from coach, etc.")

        lesson_file = st.file_uploader(
            "Upload lesson material (PDF, image, video screenshot)",
            type=["pdf", "jpg", "jpeg", "png", "txt", "md"],
            key="ln_file"
        )
        video_link = st.text_input("Or paste a video URL (YouTube, Vimeo, etc.)", placeholder="https://...", key="ln_video")

        st.markdown("---")
        save_lesson = st.button("💾  SAVE LESSON & SYNC WITH AI COACH", use_container_width=True)

        if save_lesson and what_worked_on.strip():
            file_data = None
            file_name = None
            if lesson_file:
                file_data = base64.standard_b64encode(lesson_file.getvalue()).decode("utf-8")
                file_name = lesson_file.name

            lesson_entry = {
                "date": lesson_date.strftime("%B %d, %Y"),
                "coach_name": coach_name or "Unnamed Coach",
                "format": lesson_format,
                "length": lesson_length,
                "focus": primary_focus,
                "cost": lesson_cost,
                "worked_on": what_worked_on,
                "corrections": key_corrections,
                "drills": drills_assigned,
                "homework": homework,
                "next_lesson": next_lesson.strftime("%B %d, %Y") if next_lesson else None,
                "file_name": file_name,
                "file_b64": file_data,
                "video_link": video_link,
                "logged_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            st.session_state.coach_lessons.append(lesson_entry)

            # Notify AI coach
            sync_msg = f"""📋 NEW PRO LESSON LOGGED — {lesson_date.strftime('%B %d, %Y')}

Coach: {coach_name or 'Unnamed'} ({lesson_format})
Focus: {primary_focus}

What we worked on: {what_worked_on[:200]}...

Key corrections: {key_corrections[:200] if key_corrections else 'None noted'}

Drills assigned: {drills_assigned[:200] if drills_assigned else 'None noted'}

I'll incorporate these corrections into all future coaching. Stay aligned with your coach's plan."""

            st.session_state.coach_history.append({
                "role": "coach",
                "content": sync_msg,
                "timestamp": datetime.datetime.now().strftime("%b %d %H:%M"),
                "alert_type": "lesson"
            })

            st.success(f"✓ Lesson saved! The AI coach now knows about this lesson and will integrate it into future sessions.")
            st.balloons()

        elif save_lesson:
            st.warning("Please at least fill in 'What did you work on?' before saving.")

    with tab_view:
        st.markdown("### 📚 Your Lesson Library")

        if not st.session_state.coach_lessons:
            st.info("No lessons logged yet. Add your first lesson in the 'Add Lesson' tab.")
        else:
            st.markdown(f"**{len(st.session_state.coach_lessons)} lessons logged**")

            # Show stats
            unique_coaches = set(l.get("coach_name", "Unknown") for l in st.session_state.coach_lessons)
            cols = st.columns(3)
            with cols[0]:
                st.markdown(f"""<div class="metric-box"><div class="metric-val">{len(st.session_state.coach_lessons)}</div><div class="metric-lbl">Total Lessons</div></div>""", unsafe_allow_html=True)
            with cols[1]:
                st.markdown(f"""<div class="metric-box"><div class="metric-val">{len(unique_coaches)}</div><div class="metric-lbl">Coaches Worked With</div></div>""", unsafe_allow_html=True)
            with cols[2]:
                if st.session_state.coach_lessons:
                    latest = st.session_state.coach_lessons[-1].get("date", "?")
                else:
                    latest = "-"
                st.markdown(f"""<div class="metric-box"><div class="metric-val" style="font-size:1.1rem;line-height:2.4rem;">{latest}</div><div class="metric-lbl">Latest Lesson</div></div>""", unsafe_allow_html=True)

            st.markdown("---")

            for idx, lesson in enumerate(reversed(st.session_state.coach_lessons)):
                real_idx = len(st.session_state.coach_lessons) - 1 - idx
                with st.expander(f"📅 {lesson.get('date','?')} · {lesson.get('coach_name','?')} · {lesson.get('focus','?')}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Format:** {lesson.get('format','?')}")
                        st.markdown(f"**Length:** {lesson.get('length','?')}")
                        if lesson.get('cost'): st.markdown(f"**Cost:** {lesson['cost']}")
                    with col2:
                        if lesson.get('next_lesson'): st.markdown(f"**Next Lesson:** {lesson['next_lesson']}")
                        if lesson.get('video_link'): st.markdown(f"**Video:** [Watch lesson]({lesson['video_link']})")
                        if lesson.get('file_name'): st.markdown(f"**Attachment:** {lesson['file_name']}")

                    st.markdown("**📝 Worked on:**")
                    st.markdown(lesson.get('worked_on','-'))

                    if lesson.get('corrections'):
                        st.markdown("**🎯 Key corrections:**")
                        st.markdown(lesson['corrections'])

                    if lesson.get('drills'):
                        st.markdown("**🏋️ Drills assigned:**")
                        st.markdown(lesson['drills'])

                    if lesson.get('homework'):
                        st.markdown("**📚 Homework:**")
                        st.markdown(lesson['homework'])

                    if st.button(f"🗑 Delete this lesson", key=f"del_lesson_{real_idx}"):
                        st.session_state.coach_lessons.pop(real_idx)
                        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
#  PAGE: SPEED LAB  ($12.99 premium tier)
# ─────────────────────────────────────────────────────────────────────────────
elif "Speed Lab" in page:
    st.markdown('<div class="hero"><div class="hero-title">⚡ SPEED LAB</div><div class="hero-sub">Evidence-based swing-speed training — overspeed, power, strength, mobility</div></div>', unsafe_allow_html=True)
    st.markdown("---")

    # ── PAYWALL ──
    if not st.session_state.speed_tier_unlocked:
        st.markdown("""
        <div class="card card-gold">
          <h3 style="color:#F59E0B;margin-top:0;">🔒 SPEED LAB — PREMIUM TIER</h3>
          <p>Speed Lab is the highest tier of MySwing and Me. It includes a complete, science-backed
          swing-speed system on top of <strong>everything in Pro</strong> — unlimited AI diagnoses,
          the full AI coach, two-angle analysis, slow-mo review, equipment fitting, and pro-lesson sync.</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([1, 1], gap="large")
        with col1:
            st.markdown("""
            ### ⚡ What Speed Lab Adds
            - **8-week swing-speed program** — 3 progressive phases
            - **Overspeed/overload protocol** — the 15-min, 3×/week system
            - **16 speed-specific exercises** — overspeed, rotational power, strength, mobility
            - **AI speed coach** — a personalized plan from your numbers
            - **Speed tracker** — log driver speed, watch the trend line
            - Everything in **Pro** included
            """)
        with col2:
            st.markdown("""
            <div class="card" style="border:1px solid #F59E0B;text-align:center;">
              <div style="font-family:'Bebas Neue',sans-serif;font-size:1.3rem;color:#F59E0B;letter-spacing:.06em;">SPEED TIER</div>
              <div style="font-family:'Bebas Neue',sans-serif;font-size:3.2rem;color:#4ADE80;line-height:1;margin:.4rem 0;">$12.99<span style="font-size:1rem;color:#6B8BAF;"> /mo</span></div>
              <div style="font-size:.82rem;color:#6B8BAF;margin-bottom:1rem;">Includes all Pro features · Cancel anytime</div>
            </div>
            """, unsafe_allow_html=True)

            # ── Stripe checkout (live) or demo fallback ──
            if billing is not None and billing.stripe_configured():
                checkout_email = st.text_input(
                    "Email for your subscription",
                    placeholder="you@example.com",
                    key="speed_checkout_email"
                )
                if st.button("⚡  CONTINUE TO SECURE CHECKOUT", use_container_width=True):
                    url = billing.create_checkout_session(customer_email=checkout_email or None)
                    if url:
                        st.session_state["_speed_checkout_url"] = url
                # Once a session exists, show the link button to Stripe
                if st.session_state.get("_speed_checkout_url"):
                    st.link_button(
                        "💳  Pay $12.99/mo with Stripe →",
                        st.session_state["_speed_checkout_url"],
                        use_container_width=True,
                    )
                    st.caption("Opens Stripe's secure checkout. You'll return here automatically after payment.")
            else:
                # Stripe not configured yet — demo unlock so the app still works
                if st.button("⚡  UNLOCK SPEED LAB — $12.99/mo", use_container_width=True):
                    st.session_state.speed_tier_unlocked = True
                    st.success("Speed Lab unlocked! (Demo mode — add Stripe secrets for live billing.)")
                    st.rerun()
                st.caption("Demo mode: Stripe is not configured. See STRIPE_SETUP.md to enable live billing.")

        st.markdown("---")
        st.markdown("""
        <div class="card">
          <strong>The science, briefly:</strong> Swing speed is built on four pillars — overspeed/overload
          neural training, rotational power, a strength foundation, and mobility. Research on overspeed
          protocols shows meaningful clubhead-speed gains within about 3 weeks, and a well-built 8-week
          block commonly produces a 5–8% speed increase. Speed Lab packages all four pillars into one plan.
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # ── UNLOCKED CONTENT ──
    st.markdown('<div class="card card-green"><strong>✓ Speed Tier Active.</strong> Full Speed Lab unlocked, plus all Pro features.</div>', unsafe_allow_html=True)

    # Manage / cancel subscription (if billed through Stripe)
    if billing is not None and billing.stripe_configured() and st.session_state.get("stripe_customer_id"):
        portal = billing.customer_portal_url(st.session_state["stripe_customer_id"])
        if portal:
            st.link_button("⚙️  Manage or cancel my subscription", portal)

    tab_sci, tab_prog, tab_proto, tab_ex, tab_coach, tab_track = st.tabs(
        ["🔬 The 4 Pillars", "📅 8-Week Program", "⚡ Overspeed Protocol", "🏋️ Speed Exercises", "🤖 AI Speed Plan", "📈 Speed Tracker"]
    )

    # — Pillars —
    with tab_sci:
        st.markdown("### The Four Pillars of Swing Speed")
        st.caption("Speed isn't one thing. It's four trainable systems working together.")
        for p in SPEED_PILLARS:
            st.markdown(f"""
            <div class="card card-gold">
              <div style="font-family:'Bebas Neue',sans-serif;font-size:1.3rem;color:#F59E0B;letter-spacing:.05em;">{p['icon']} {p['label']}</div>
              <p style="margin:.5rem 0;">{p['desc']}</p>
              <p style="font-size:.86rem;color:#6B8BAF;border-left:2px solid #F59E0B;padding-left:.8rem;margin-top:.6rem;">
                <strong style="color:#F59E0B;">Why it works:</strong> {p['science']}
              </p>
            </div>
            """, unsafe_allow_html=True)

    # — 8-week program —
    with tab_prog:
        st.markdown("### Your 8-Week Swing-Speed Program")
        st.caption("Three phases. Each builds on the last. Re-test your driver speed at the end.")
        for ph in SPEED_PROGRAM:
            st.markdown(f"""
            <div class="card card-green">
              <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:.5rem;">
                <span style="font-family:'Bebas Neue',sans-serif;font-size:1.2rem;color:#4ADE80;letter-spacing:.05em;">{ph['phase']}</span>
                <span style="font-family:'DM Mono',monospace;font-size:.8rem;color:#6B8BAF;">{ph['weeks']}</span>
              </div>
              <p style="margin:.6rem 0 .4rem;"><strong>Focus:</strong> {ph['focus']}</p>
              <p style="font-size:.88rem;color:#6B8BAF;margin:.3rem 0;"><strong>Weekly:</strong> {ph['weekly']}</p>
              <p style="font-size:.86rem;color:#F59E0B;margin-top:.5rem;">📌 {ph['expect']}</p>
            </div>
            """, unsafe_allow_html=True)
        st.info("⚠️ Speed training is intense. Warm up fully, train when fresh (not fatigued), and take a deload week if you feel run down. Consult a doctor before starting if you have any injury history.")

    # — Overspeed protocol —
    with tab_proto:
        st.markdown("### The Overspeed Protocol")
        st.caption("~15 minutes · 3×/week · the core speed session. Use speed sticks, or light/heavy training clubs.")
        for i, step in enumerate(OVERSPEED_PROTOCOL, 1):
            st.markdown(f"""
            <div class="card" style="border-left:3px solid #F59E0B;">
              <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:.5rem;">
                <span style="font-family:'Bebas Neue',sans-serif;font-size:1.05rem;color:#F59E0B;letter-spacing:.04em;">{i}. {step['phase']}</span>
                <span style="font-family:'DM Mono',monospace;font-size:.78rem;color:#4ADE80;">{step['swings']}</span>
              </div>
              <p style="font-size:.9rem;margin-top:.4rem;">{step['detail']}</p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("""
        <div class="card card-gold">
          <strong>Key rule:</strong> every overspeed swing is a MAX-EFFORT swing. Half-speed reps train half-speed
          patterns. Rest fully between sets — this is neural training, not cardio. Always log your cooldown
          driver speed in the Speed Tracker to measure transfer.
        </div>
        """, unsafe_allow_html=True)

    # — Speed exercises —
    with tab_ex:
        st.markdown("### Speed-Specific Exercise Library")
        st.caption("16 exercises across the four pillars. Premium — Speed tier only.")
        for cat, exs in SPEED_EXERCISES.items():
            st.markdown(f"#### {cat}")
            cols = st.columns(2)
            for i, ex in enumerate(exs):
                with cols[i % 2]:
                    st.markdown(f"""
                    <div style="background:#0D1A2D;border-left:3px solid #F59E0B;border-radius:4px;padding:.9rem 1.1rem;margin:.5rem 0;">
                      <div style="font-family:'Bebas Neue',sans-serif;font-size:1.05rem;color:#F59E0B;">{ex['name']}</div>
                      <div style="margin:.3rem 0;">
                        <span class="badge badge-gold">🎯 {ex['target']}</span>
                        <span class="badge badge-green">📅 {ex['freq']}</span>
                        <span class="badge badge-gold">🔁 {ex['sets']}</span>
                      </div>
                      <div style="font-size:.85rem;color:#F0EBE0;margin-top:.3rem;line-height:1.5;">{ex['desc']}</div>
                    </div>
                    """, unsafe_allow_html=True)

    # — AI speed plan —
    with tab_coach:
        st.markdown("### Get Your Personalized AI Speed Plan")
        st.caption("Enter your numbers — the AI builds a speed plan around your starting point.")
        col1, col2 = st.columns(2)
        with col1:
            cur_speed = st.slider("Current driver swing speed (mph)", 60, 130, 92, key="sp_cur")
            target_speed = st.slider("Target driver swing speed (mph)", 70, 145, 102, key="sp_tgt")
            age_band = st.selectbox("Age range", ["Under 25", "25-39", "40-54", "55-64", "65+"], key="sp_age")
        with col2:
            train_days = st.slider("Days per week you can train", 2, 6, 3, key="sp_days")
            gym = st.checkbox("I have gym / weights access", key="sp_gym")
            sticks = st.checkbox("I have speed sticks or weighted training clubs", key="sp_sticks")
            injuries = st.multiselect("Any injury considerations?",
                ["Lower back", "Shoulder", "Wrist/elbow", "Hip", "Knee", "None"], key="sp_inj")

        if st.button("⚡  GENERATE MY SPEED PLAN", use_container_width=True):
            sp_prompt = f"""You are an elite golf-fitness coach specializing in swing speed (TPI / SuperSpeed / Stack methodology).

GOLFER:
- Current driver speed: {cur_speed} mph
- Target driver speed: {target_speed} mph
- Age range: {age_band}
- Training days available: {train_days}/week
- Gym access: {gym}
- Speed sticks / weighted clubs: {sticks}
- Injury considerations: {injuries}

Build a personalized swing-speed plan using this structure:

## ⚡ YOUR SPEED PLAN

### Reality Check
Is the {target_speed} mph target realistic from {cur_speed} mph, and in what timeframe? Be honest.

### Your Weekly Schedule
Day-by-day for a typical week, fitted to {train_days} training days. Specify overspeed sessions, strength, rotational power, mobility.

### Overspeed Approach
{"They have speed sticks — give specific protocol." if sticks else "They have NO speed sticks — give alternatives (max-effort swings with a driver, light/heavy club pairs) and note speed sticks would help."}

### Strength & Power Priorities
Top 4-5 exercises given their gym access ({gym}) and injuries ({injuries}). Adapt around any injuries named.

### 8-Week Progression
What changes across weeks 1-3, 4-6, 7-8.

### Realistic Outcome
Expected mph gain over 8 weeks, with the honest caveat that results vary.

### Safety Notes
Specific cautions for their age band and any injuries listed.

Keep it specific, practical, and motivating. Around 450 words."""

            with st.spinner("Building your speed plan..."):
                client = get_client()
                st.markdown("## ⚡ Your Personalized Speed Plan")
                ph = st.empty()
                full = ""
                with client.messages.stream(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1800,
                    messages=[{"role": "user", "content": sp_prompt}]
                ) as stream:
                    for t in stream.text_stream:
                        full += t
                        ph.markdown(full)
                st.session_state.speed_plan = full
                st.success("✓ Speed plan saved.")
        elif st.session_state.speed_plan:
            st.markdown("---")
            st.markdown("## ⚡ Your Saved Speed Plan")
            st.markdown(st.session_state.speed_plan)

    # — Speed tracker —
    with tab_track:
        st.markdown("### Driver Speed Tracker")
        st.caption("Log your driver speed after each session. Watch the trend.")
        col1, col2, col3 = st.columns(3)
        with col1:
            log_speed = st.number_input("Driver speed (mph)", 50.0, 150.0, 92.0, 0.5, key="trk_speed")
        with col2:
            log_type = st.selectbox("Session", ["Overspeed session", "On-ball / range", "Strength day", "Test / baseline"], key="trk_type")
        with col3:
            log_note = st.text_input("Note (optional)", key="trk_note")
        if st.button("➕ Log This Speed", use_container_width=True):
            st.session_state.speed_log.append({
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "driver_speed": log_speed,
                "session_type": log_type,
                "note": log_note,
            })
            st.success(f"Logged {log_speed} mph.")
            st.rerun()

        if st.session_state.speed_log:
            speeds = [e["driver_speed"] for e in st.session_state.speed_log]
            first, latest, best = speeds[0], speeds[-1], max(speeds)
            gain = latest - first
            c1, c2, c3, c4 = st.columns(4)
            for c, val, lbl in [
                (c1, f"{first:.1f}", "First Logged"),
                (c2, f"{latest:.1f}", "Latest"),
                (c3, f"{best:.1f}", "Personal Best"),
                (c4, f"{'+' if gain>=0 else ''}{gain:.1f}", "Total Gain (mph)")
            ]:
                with c:
                    st.markdown(f'<div class="metric-box"><div class="metric-val">{val}</div><div class="metric-lbl">{lbl}</div></div>', unsafe_allow_html=True)
            st.markdown("")
            try:
                st.line_chart({"Driver Speed (mph)": speeds})
            except Exception:
                pass
            with st.expander("📋 Full speed log"):
                for e in reversed(st.session_state.speed_log):
                    note = f" — {e['note']}" if e.get("note") else ""
                    st.markdown(f"**{e['driver_speed']:.1f} mph** · {e['session_type']} · {e['date']}{note}")
        else:
            st.info("No speed logged yet. Record your baseline driver speed to start tracking.")

# ─────────────────────────────────────────────────────────────────────────────
#  PAGE: BENCHMARKS  (Pro + Speed tier feature)
# ─────────────────────────────────────────────────────────────────────────────
elif "Benchmarks" in page:
    st.markdown('<div class="hero"><div class="hero-title">📊 BENCHMARKS</div><div class="hero-sub">Your swing metrics vs PGA Tour & average amateur — see exactly where you stand</div></div>', unsafe_allow_html=True)
    st.markdown("---")

    # ── PAYWALL ──
    if not has_premium_access():
        st.markdown("""
        <div class="card card-gold">
          <h3 style="color:#F59E0B;margin-top:0;">🔒 BENCHMARKS — Pro & Speed Tier Feature</h3>
          <p>See your shoulder turn, hip turn, swing speed, and shaft lean side-by-side with
          PGA Tour and average amateur benchmarks. Get a personalized AI gap analysis showing
          exactly which numbers to attack first for the fastest improvement.</p>
        </div>
        """, unsafe_allow_html=True)

        col_pro, col_speed = st.columns(2, gap="medium")

        with col_pro:
            st.markdown("""
            <div class="card" style="text-align:center;height:100%;">
              <div style="font-family:'Bebas Neue',sans-serif;font-size:1.2rem;color:#F0EBE0;letter-spacing:.06em;">PRO</div>
              <div style="font-family:'Bebas Neue',sans-serif;font-size:2.8rem;color:#4ADE80;line-height:1;margin:.4rem 0;">$9.99<span style="font-size:.9rem;color:#6B8BAF;"> /mo</span></div>
              <div style="font-size:.78rem;color:#6B8BAF;margin-bottom:.8rem;">All Pro features + Benchmarks</div>
              <ul style="text-align:left;font-size:.85rem;color:#F0EBE0;line-height:1.7;padding-left:1.1rem;">
                <li>Unlimited AI swing diagnoses</li>
                <li>Two-angle analysis & slow-mo</li>
                <li>AI coach + pro lesson sync</li>
                <li>Equipment fitting</li>
                <li>📊 Benchmark comparisons</li>
              </ul>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Unlock Pro — $9.99/mo", use_container_width=True, key="unlock_pro"):
                st.session_state.pro_tier_unlocked = True
                st.success("Pro tier unlocked! (Demo mode — Stripe checkout would go here.)")
                st.rerun()

        with col_speed:
            st.markdown("""
            <div class="card" style="text-align:center;height:100%;border:1px solid #F59E0B;">
              <div style="font-family:'Bebas Neue',sans-serif;font-size:1.2rem;color:#F59E0B;letter-spacing:.06em;">⚡ SPEED · MOST POPULAR</div>
              <div style="font-family:'Bebas Neue',sans-serif;font-size:2.8rem;color:#4ADE80;line-height:1;margin:.4rem 0;">$12.99<span style="font-size:.9rem;color:#6B8BAF;"> /mo</span></div>
              <div style="font-size:.78rem;color:#6B8BAF;margin-bottom:.8rem;">Everything in Pro + Speed Lab</div>
              <ul style="text-align:left;font-size:.85rem;color:#F0EBE0;line-height:1.7;padding-left:1.1rem;">
                <li><strong>Everything in Pro</strong>, plus:</li>
                <li>⚡ 8-week swing speed program</li>
                <li>⚡ Overspeed/overload protocol</li>
                <li>⚡ 16 speed exercises</li>
                <li>⚡ AI speed coach + tracker</li>
              </ul>
            </div>
            """, unsafe_allow_html=True)
            if billing is not None and billing.stripe_configured():
                if st.button("⚡ Continue to Stripe — $12.99/mo", use_container_width=True, key="unlock_speed_from_bm", type="primary"):
                    url = billing.create_checkout_session()
                    if url:
                        st.session_state["_speed_checkout_url"] = url
                if st.session_state.get("_speed_checkout_url"):
                    st.link_button("💳 Pay with Stripe →", st.session_state["_speed_checkout_url"], use_container_width=True)
            else:
                if st.button("⚡ Unlock Speed — $12.99/mo", use_container_width=True, key="unlock_speed_demo", type="primary"):
                    st.session_state.speed_tier_unlocked = True
                    st.success("Speed tier unlocked! (Demo mode.)")
                    st.rerun()
        st.stop()

    # ── UNLOCKED CONTENT ──
    tier_name = "Speed" if st.session_state.speed_tier_unlocked else "Pro"
    st.markdown(f'<div class="card card-green"><strong>✓ {tier_name} Tier Active.</strong> Full benchmark comparisons unlocked.</div>', unsafe_allow_html=True)

    tab_input, tab_compare, tab_analysis, tab_history = st.tabs(
        ["📝 Enter Your Numbers", "📊 Compare to Benchmarks", "🤖 AI Gap Analysis", "📈 Tracking History"]
    )

    # — Enter numbers —
    with tab_input:
        st.markdown("### Enter Your Current Swing Metrics")
        st.caption("From a launch monitor (TrackMan, SkyTrak, Hella Golf Sim), a swing speed radar, or video analysis. Best estimates are fine — track them over time.")

        col1, col2 = st.columns(2)
        user_metrics = {}
        keys = list(BENCHMARKS.keys())
        for i, key in enumerate(keys):
            b = BENCHMARKS[key]
            target_col = col1 if i % 2 == 0 else col2
            with target_col:
                st.markdown(f"**{b['icon']} {b['label']}**")
                val = st.slider(
                    f"Your {b['label'].lower()} ({b['unit']})",
                    float(b["min"]), float(b["max"]),
                    float(st.session_state.get(f"bm_{key}", b["default"])),
                    0.5,
                    key=f"bm_{key}",
                    label_visibility="collapsed",
                )
                user_metrics[key] = val
                st.caption(b["notes"])
                st.markdown("")

        st.markdown("---")
        col_h, col_n = st.columns([1, 2])
        with col_h:
            handicap_level = st.selectbox(
                "Your handicap range",
                ["Beginner (25+)", "High (15-24)", "Mid (8-14)", "Low (1-7)", "Scratch / Pro"],
                index=2,
                key="bm_hcp",
            )
        with col_n:
            log_note = st.text_input("Note (optional)", placeholder="e.g. After 4 weeks of speed training...", key="bm_note")

        if st.button("💾  Save These Numbers to My History", use_container_width=True):
            st.session_state.benchmark_log.append({
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "metrics": user_metrics.copy(),
                "handicap": handicap_level,
                "note": log_note,
            })
            st.success("✓ Logged. Switch to the 'Compare' or 'Tracking History' tab.")

    # — Compare tab (visual bars) —
    with tab_compare:
        st.markdown("### Your Numbers vs The Benchmarks")
        st.caption("Lime green = you · Gold = PGA Tour avg · Muted blue = avg amateur (your handicap)")

        # Map handicap level to amateur tier
        hcp_to_tier = {
            "Beginner (25+)": "amateur_high",
            "High (15-24)": "amateur_high",
            "Mid (8-14)": "amateur_mid",
            "Low (1-7)": "amateur_low",
            "Scratch / Pro": "amateur_low",
        }
        amateur_key = hcp_to_tier.get(st.session_state.get("bm_hcp", "Mid (8-14)"), "amateur_mid")

        for key, b in BENCHMARKS.items():
            user_val = st.session_state.get(f"bm_{key}", b["default"])
            am_val = b[amateur_key]
            pro_val = b["pga_tour"]

            # Compute bar widths (scaled to max in this metric)
            scale_max = max(pro_val, user_val, am_val, b["max"] * 0.85)
            scale_min = min(0, b["min"], user_val, am_val)
            span = scale_max - scale_min
            def pct(v):
                return max(2, min(100, (v - scale_min) / span * 100))

            gap_to_pro = pro_val - user_val
            gap_to_am = user_val - am_val
            arrow_pro = "↑" if gap_to_pro > 0 else "↓" if gap_to_pro < 0 else "="
            color_user = "#4ADE80" if user_val >= am_val else "#F97316"

            st.markdown(f"""
            <div class="card" style="padding:1.2rem 1.4rem;">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.8rem;">
                <span style="font-family:'Bebas Neue',sans-serif;font-size:1.2rem;color:#F0EBE0;letter-spacing:.04em;">{b['icon']} {b['label']}</span>
                <span style="font-family:'DM Mono',monospace;font-size:.78rem;color:#6B8BAF;">Gap to Tour: <strong style="color:#F59E0B;">{arrow_pro} {abs(gap_to_pro):.1f} {b['unit']}</strong></span>
              </div>

              <div style="margin:.5rem 0;">
                <div style="display:flex;justify-content:space-between;font-size:.72rem;color:#6B8BAF;margin-bottom:.2rem;font-family:'DM Mono',monospace;letter-spacing:.06em;">
                  <span>YOU</span><span style="color:{color_user};">{user_val:.1f} {b['unit']}</span>
                </div>
                <div style="background:#1A2D4A;height:12px;border-radius:4px;overflow:hidden;">
                  <div style="background:{color_user};width:{pct(user_val):.1f}%;height:100%;"></div>
                </div>
              </div>

              <div style="margin:.5rem 0;">
                <div style="display:flex;justify-content:space-between;font-size:.72rem;color:#6B8BAF;margin-bottom:.2rem;font-family:'DM Mono',monospace;letter-spacing:.06em;">
                  <span>AVG AMATEUR (your handicap)</span><span style="color:#7A92B5;">{am_val:.1f} {b['unit']}</span>
                </div>
                <div style="background:#1A2D4A;height:12px;border-radius:4px;overflow:hidden;">
                  <div style="background:#7A92B5;width:{pct(am_val):.1f}%;height:100%;"></div>
                </div>
              </div>

              <div style="margin:.5rem 0;">
                <div style="display:flex;justify-content:space-between;font-size:.72rem;color:#6B8BAF;margin-bottom:.2rem;font-family:'DM Mono',monospace;letter-spacing:.06em;">
                  <span>PGA TOUR AVERAGE</span><span style="color:#F59E0B;">{pro_val:.1f} {b['unit']}</span>
                </div>
                <div style="background:#1A2D4A;height:12px;border-radius:4px;overflow:hidden;">
                  <div style="background:#F59E0B;width:{pct(pro_val):.1f}%;height:100%;"></div>
                </div>
              </div>

              <div style="font-size:.78rem;color:#6B8BAF;margin-top:.8rem;border-left:2px solid #F59E0B;padding-left:.7rem;">
                {b['notes']}
              </div>
            </div>
            """, unsafe_allow_html=True)

        # Summary metric cards
        st.markdown("---")
        st.markdown("### Quick Summary")
        s_cols = st.columns(len(BENCHMARKS))
        for i, (key, b) in enumerate(BENCHMARKS.items()):
            user_val = st.session_state.get(f"bm_{key}", b["default"])
            pro_val = b["pga_tour"]
            gap = pro_val - user_val
            pct_to_pro = max(0, min(100, (user_val / pro_val * 100) if pro_val else 0))
            with s_cols[i]:
                st.markdown(f"""
                <div class="metric-box">
                  <div style="font-size:1.4rem;">{b['icon']}</div>
                  <div class="metric-val">{pct_to_pro:.0f}%</div>
                  <div class="metric-lbl">of Tour {b['label'].split()[0]}</div>
                </div>
                """, unsafe_allow_html=True)

    # — AI gap analysis —
    with tab_analysis:
        st.markdown("### AI Gap Analysis")
        st.caption("Your AI coach prioritizes the biggest gaps and tells you exactly what to attack first.")

        if st.button("🤖  ANALYZE MY BENCHMARK GAPS", use_container_width=True):
            user_data = {key: st.session_state.get(f"bm_{key}", b["default"]) for key, b in BENCHMARKS.items()}
            hcp = st.session_state.get("bm_hcp", "Mid (8-14)")
            bm_prompt = f"""You are an elite TPI-certified golf coach analyzing a golfer's swing metrics against PGA Tour benchmarks.

GOLFER:
- Handicap: {hcp}

THEIR NUMBERS vs PGA TOUR AVG vs AVG AMATEUR (their handicap):
- Driver swing speed: {user_data['swing_speed']} mph (Tour avg 116.5, amateur avg 93.4)
- Shoulder turn at top: {user_data['shoulder_turn']}° (Tour avg 93°, amateur avg 78°)
- Hip turn at top: {user_data['hip_turn_top']}° (Tour 45°, amateur 30°)
- Hips open at impact: {user_data['hip_open_impact']}° (Tour 36°, amateur 28°)
- Shaft lean at impact (7-iron): {user_data['shaft_lean_iron']}° forward (Tour 7°, amateur 3°)

Respond with this structure:

## 📊 YOUR GAP ANALYSIS

### Where You're Strong
The 1-2 metrics where they match or beat their handicap-tier average. Acknowledge briefly.

### The Biggest Gap (Priority #1)
Identify the SINGLE biggest gap to Tour-level numbers and explain:
- What this gap costs them (yards, consistency, etc.)
- WHY it matters mechanically
- The specific drill/exercise that addresses it
- Realistic timeline to close half the gap

### Second-Biggest Priority
Same treatment, less detailed.

### Third Priority
1-2 sentences only.

### What to Ignore For Now
1 metric that's "good enough" given their other gaps — don't waste training time on this.

### 30-Day Goal
One concrete, measurable target across these 5 metrics for the next 30 days.

Be specific, honest, and motivating. Around 350 words."""

            with st.spinner("Analyzing your gaps..."):
                client = get_client()
                st.markdown("## 🤖 Your Benchmark Gap Analysis")
                ph = st.empty()
                full = ""
                with client.messages.stream(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1500,
                    messages=[{"role": "user", "content": bm_prompt}]
                ) as stream:
                    for t in stream.text_stream:
                        full += t
                        ph.markdown(full)
                st.success("✓ Save this analysis — re-run it monthly to track progress.")

    # — Tracking history —
    with tab_history:
        st.markdown("### Benchmark Tracking History")
        if not st.session_state.benchmark_log:
            st.info("No history yet. Save your numbers from the 'Enter Your Numbers' tab to start tracking.")
        else:
            st.markdown(f"**{len(st.session_state.benchmark_log)} entries logged**")

            # Trend chart for swing speed (the most-tracked metric)
            try:
                speeds = [e["metrics"].get("swing_speed", 0) for e in st.session_state.benchmark_log]
                dates = [e["date"][:10] for e in st.session_state.benchmark_log]
                if speeds:
                    st.markdown("**Swing Speed Trend (mph)**")
                    st.line_chart({"Driver swing speed": speeds})
                    first, latest = speeds[0], speeds[-1]
                    gain = latest - first
                    st.markdown(f"**Change since first log:** {'+' if gain >= 0 else ''}{gain:.1f} mph")
            except Exception:
                pass

            st.markdown("---")
            for entry in reversed(st.session_state.benchmark_log):
                with st.expander(f"📅 {entry['date']} · {entry.get('handicap','?')}"):
                    m = entry["metrics"]
                    for key, b in BENCHMARKS.items():
                        v = m.get(key)
                        if v is None:
                            continue
                        st.markdown(f"- {b['icon']} **{b['label']}:** {v:.1f} {b['unit']}")
                    if entry.get("note"):
                        st.markdown(f"_{entry['note']}_")

# ─────────────────────────────────────────────────────────────────────────────
#  PAGE: EXERCISE LIBRARY
# ─────────────────────────────────────────────────────────────────────────────
elif "Exercise Library" in page:
    st.markdown('<div class="hero"><div class="hero-title">EXERCISE LIBRARY</div><div class="hero-sub">Golf-specific exercises mapped to your foundation level</div></div>', unsafe_allow_html=True)
    st.markdown("---")

    current_level_id = st.session_state.current_level if st.session_state.baseline_complete else None

    col1, col2, col3 = st.columns(3)
    with col1:
        selected_cats = st.multiselect("Category", list(EXERCISE_DB.keys()), default=list(EXERCISE_DB.keys()))
    with col2:
        level_filter = st.selectbox("Foundation level", ["All levels"] + [l["label"] for l in FOUNDATION_LEVELS])
    with col3:
        freq_filter = st.selectbox("Frequency", ["All", "Daily", "3-4×/week", "Every practice"])

    st.markdown("---")

    for cat in selected_cats:
        exercises = EXERCISE_DB[cat]

        # Filter by level
        if level_filter != "All levels":
            level_id = next((l["id"] for l in FOUNDATION_LEVELS if l["label"] == level_filter), None)
            exercises = [e for e in exercises if e.get("level") == level_id]

        # Filter by freq
        if freq_filter == "Daily":
            exercises = [e for e in exercises if "Daily" in e["freq"]]
        elif freq_filter == "3-4×/week":
            exercises = [e for e in exercises if "week" in e["freq"]]
        elif freq_filter == "Every practice":
            exercises = [e for e in exercises if "practice" in e["freq"]]

        if not exercises:
            continue

        st.markdown(f"### {cat}")
        cols = st.columns(2)
        for i, ex in enumerate(exercises):
            ex_level = get_level(ex.get("level","address"))
            is_relevant = ex.get("level") == current_level_id
            border_color = "#4ADE80" if is_relevant else "#1A2D4A"
            with cols[i % 2]:
                st.markdown(f"""
                <div style="background:#0D1829;border-left:3px solid {border_color};border-radius:4px;padding:.9rem 1.1rem;margin:.5rem 0;">
                  <div style="font-family:'Bebas Neue',sans-serif;font-size:1.1rem;color:{'#4ADE80' if is_relevant else '#F59E0B'};">{ex['name']} {'⭐' if is_relevant else ''}</div>
                  <div style="margin:.3rem 0;">
                    <span class="badge badge-{'green' if is_relevant else 'gold'}">{ex_level['icon']} {ex_level['label']}</span>
                    <span class="badge badge-green">📅 {ex['freq']}</span>
                    <span class="badge badge-gold">🔁 {ex['sets']}</span>
                  </div>
                  <div style="font-size:.84rem;color:#6B8BAF;margin-top:.4rem;">🎯 {ex['target']}</div>
                  <div style="font-size:.85rem;color:#F0EBE0;margin-top:.3rem;line-height:1.5;">{ex['desc']}</div>
                </div>
                """, unsafe_allow_html=True)

    if st.session_state.baseline_complete:
        st.markdown(f"""
        <div class="card card-green" style="margin-top:1.5rem;">
          ⭐ = Exercises recommended for your current level: <strong>{get_level(current_level_id)['label']}</strong>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  PAGE: MY PROGRESS
# ─────────────────────────────────────────────────────────────────────────────
elif "My Progress" in page:
    st.markdown('<div class="hero"><div class="hero-title">MY PROGRESS</div><div class="hero-sub">Your improvement tracked against baseline</div></div>', unsafe_allow_html=True)
    st.markdown("---")

    if not st.session_state.baseline_complete:
        st.warning("No baseline set yet. Set your baseline to start tracking progress.")
        st.stop()

    # Summary metrics
    sessions = len([s for s in st.session_state.session_log if s.get("type") == "session"])
    regressions_total = len(st.session_state.regression_flags)
    avg_score = int(sum(st.session_state.foundation_score.values()) / max(len(st.session_state.foundation_score), 1))
    levels_passed = sum(1 for s in st.session_state.foundation_score.values() if s >= 75)

    st.markdown(f"""
    <div class="metric-row">
      <div class="metric-box"><div class="metric-val">{sessions}</div><div class="metric-lbl">Sessions Logged</div></div>
      <div class="metric-box"><div class="metric-val">{avg_score}%</div><div class="metric-lbl">Avg Foundation Score</div></div>
      <div class="metric-box"><div class="metric-val">{levels_passed}/5</div><div class="metric-lbl">Levels Passed</div></div>
      <div class="metric-box"><div class="metric-val" style="color:{'#EF4444' if regressions_total>0 else '#4ADE80'};">{regressions_total}</div><div class="metric-lbl">Active Regressions</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Foundation scores
    st.markdown("### FOUNDATION SCORES vs BASELINE")
    for level in FOUNDATION_LEVELS:
        score = st.session_state.foundation_score.get(level["id"], 0)
        baseline_score = st.session_state.session_log[0].get("scores", {}).get(level["id"], score) if st.session_state.session_log else score
        delta = score - baseline_score
        col1, col2, col3 = st.columns([2, 5, 1])
        with col1:
            st.markdown(f"**{level['icon']} {level['label']}**")
        with col2:
            st.progress(score / 100)
        with col3:
            delta_str = f"+{delta}" if delta > 0 else str(delta)
            color = "#4ADE80" if delta >= 0 else "#EF4444"
            st.markdown(f'<span style="color:{color};font-family:Bebas Neue;font-size:1.1rem;">{score}% ({delta_str})</span>', unsafe_allow_html=True)

    st.markdown("---")

    # Session log
    st.markdown("### SESSION HISTORY")
    if len(st.session_state.session_log) <= 1:
        st.info("No practice sessions logged yet. Complete sessions in Foundation Analysis to build your history.")
    else:
        for entry in reversed(st.session_state.session_log[1:]):
            with st.expander(f"📅 {entry.get('date','Unknown')} — {get_level(entry.get('level','address'))['label']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Faults this session:** {', '.join(entry.get('faults',[])) or 'None reported'}")
                    st.markdown(f"**Wins:** {entry.get('wins','Not reported')}")
                with col2:
                    st.markdown(f"**Confidence:** {entry.get('confidence','?')}/10")
                    st.markdown(f"**Difficulty:** {entry.get('rpe','?')}/10")

    # Regression history
    if st.session_state.regression_flags:
        st.markdown("---")
        st.markdown("### 🚨 ACTIVE REGRESSION FLAGS")
        st.markdown("""
        <div class="card card-danger">
          Your coach has flagged these faults returning to baseline patterns. Until these are resolved, they will appear in every coaching session.
        </div>
        """, unsafe_allow_html=True)
        for flag in st.session_state.regression_flags:
            st.markdown(f"- ⚠️ **{flag}**")

        if st.button("✅ Mark Regressions as Resolved (after coach confirms)"):
            st.session_state.regression_flags = []
            st.success("Regression flags cleared. Keep up the good work.")
            st.rerun()

    # Baseline reference
    st.markdown("---")
    with st.expander("📐 View Original Baseline Analysis"):
        if st.session_state.baseline_analysis:
            st.markdown(st.session_state.baseline_analysis)
        else:
            st.info("Baseline analysis not available.")
