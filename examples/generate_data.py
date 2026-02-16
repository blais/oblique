import random
import datetime

OUTPUT_FILE = "examples/nuclear_plant.oblique"
NUM_TASKS = 1500
NUM_BUGS = 400
NUM_MILESTONES = 50

# --- Data Constants ---

QUARTERS = [
    ("2026q2", "Q2 2026 - Foundation & Core Design"),
    ("2026q3", "Q3 2026 - Cooling Systems & Safety Checks"),
    ("2026q4", "Q4 2026 - Control Software & Initial Tests"),
]

TEAMS = [
    ("core", "Reactor Core Design"),
    ("cooling", "Cooling & Hydraulics"),
    ("safety", "Safety & Containment"),
    ("control", "Control Systems & Software"),
    ("civil", "Civil Engineering & Construction"),
    ("security", "Site Security & Access Control"),
]

ROLES = ["Lead", "Senior Eng", "Junior Eng", "PM", "Safety Officer"]

# Generate some realistic looking users
FIRST_NAMES = ["James", "Linda", "Robert", "Patricia", "John", "Jennifer", "Michael", "Elizabeth", "David", "Barbara", "William", "Susan", "Richard", "Jessica", "Joseph", "Sarah", "Thomas", "Karen", "Charles", "Lisa"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]

USERS = []
seen_uids = set()

for i in range(50):
    fn = random.choice(FIRST_NAMES)
    ln = random.choice(LAST_NAMES)
    base_uid = f"{fn.lower()[0]}{ln.lower()}"
    uid = base_uid
    
    counter = 1
    while uid in seen_uids:
        counter += 1
        uid = f"{base_uid}{counter}"
    
    seen_uids.add(uid)
    
    role = random.choice(ROLES)
    team = random.choice(TEAMS)[0]
    USERS.append((uid, f"{fn} {ln}", role, team))

VERBS = ["Implement", "Design", "Review", "Audit", "Test", "Deploy", "Refactor", "Construct", "Inspect", "Calibrate", "Document"]
NOUNS = [
    "Cooling Pump", "Control Rod Actuator", "Graphite Moderator", "Steam Generator", 
    "Turbine Valve", "Emergency Diesel Generator", "Radiation Sensor", "Containment Dome", 
    "Spent Fuel Pool", "SCADA Interface", "Fire Suppression System", "Seismic Dampener", 
    "Access Control Gate", "Perimeter Fence", "Coolant Filter", "Pressure Vessel",
    "Heat Exchanger", "Backup Battery Bank", "Ventilation Shaft", "Control Room Display"
]

BUG_PREFIXES = ["Leak in", "Crash in", "Misalignment of", "Corrosion detected on", "Signal noise in", "Overheating of", "Unexpected latency in", "Auth failure in", "Cracks found in"]

# --- Helper Functions ---

def generate_header():
    return r"""# Nuclear Power Plant Project Plan (Generated)
# Scope: 3 Quarters (Q2-Q4 2026)

# --- Type Definitions ---

# Strict Types (Must be defined)
/type/q Quarter
/type/p Component/Project
/type/m Milestone

# Lazy Types (Auto-created on reference)
/lazytype/u User
/lazytype/t Task
/lazytype/b Bug

# --- Rendering & Macros ---

# Render Quarters as simple headers
/render q [📅 \1]

# Render Users with @ symbol
/render u @\1

# Render Projects as strict tags
/render p [🏗️ \1]

# Render Tasks and Bugs
/render t Task #\1
/render b 🐞 Bug #\1
/render m 🚩 Milestone: \1

# Macros for quick entry
# Usage: @jdoe -> u/\1

# Usage: #core -> p/\1

# Usage: Q2 -> q/2026q2 (Simple alias mapping)
/macro \bQ2\b q/2026q2
/macro \bQ3\b q/2026q3
/macro \bQ4\b q/2026q4

# --- Static Definitions ---
"""

def generate_static_data():
    lines = []
    
    lines.append("\n# --- Quarters ---")
    for qid, desc in QUARTERS:
        lines.append(f"q/{qid} {desc}")

    lines.append("\n# --- Components / Teams ---")
    for tid, desc in TEAMS:
        lines.append(f"p/{tid} {desc}")

    lines.append("\n# --- Users ---")
    for uid, name, role, team in USERS:
        # u/jdoe John Doe (Lead, #core)
        lines.append(f"u/{uid} {name} ({role}, p/{team})")
        
    return "\n".join(lines)

def generate_milestones():
    lines = ["\n# --- Milestones ---"]
    for i in range(1, NUM_MILESTONES + 1):
        q = random.choice(QUARTERS)[0]
        noun = random.choice(NOUNS)
        lines.append(f"m/ms_{i} Final approval for {noun} in q/{q}")
    return "\n".join(lines)

def generate_tasks_and_bugs():
    lines = ["\n# --- Tasks & Bugs ---"]
    
    # Generate Tasks
    for i in range(1, NUM_TASKS + 1):
        verb = random.choice(VERBS)
        noun = random.choice(NOUNS)
        user = random.choice(USERS)[0]
        team = random.choice(TEAMS)[0]
        quarter = random.choice(QUARTERS)[0]
        
        # t/1001 Implement Cooling Pump logic for #cooling assigned to @jdoe scheduled for Q2
        desc = f"{verb} {noun} logic & specs"
        line = f"t/{1000+i} {desc} for p/{team} assigned to u/{user} in q/{quarter}"
        lines.append(line)

    # Generate Bugs
    for i in range(1, NUM_BUGS + 1):
        prefix = random.choice(BUG_PREFIXES)
        noun = random.choice(NOUNS)
        user = random.choice(USERS)[0]
        team = random.choice(TEAMS)[0]
        
        # b/500 Leak in Heat Exchanger identified in #cooling (cc @jdoe)
        desc = f"{prefix} {noun}"
        line = f"b/{5000+i} {desc} found in p/{team} (investigating: u/{user})"
        lines.append(line)
        
    return "\n".join(lines)

# --- Main Generation ---

def main():
    with open(OUTPUT_FILE, "w") as f:
        f.write(generate_header())
        f.write(generate_static_data())
        f.write(generate_milestones())
        f.write(generate_tasks_and_bugs())
    
    print(f"Generated {OUTPUT_FILE} with ~{len(QUARTERS) + len(TEAMS) + len(USERS) + NUM_MILESTONES + NUM_TASKS + NUM_BUGS} nodes.")

if __name__ == "__main__":
    main()
