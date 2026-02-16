import random
import datetime
import math

OUTPUT_FILE = "rust/oblique/examples/nuclear_plant.oblique"
NUM_TASKS = 1500
NUM_BUGS = 400
NUM_MILESTONES = 60 # 20 per quarter

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

FIRST_NAMES = ["James", "Linda", "Robert", "Patricia", "John", "Jennifer", "Michael", "Elizabeth", "David", "Barbara", "William", "Susan", "Richard", "Jessica", "Joseph", "Sarah", "Thomas", "Karen", "Charles", "Lisa"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]

VERBS = ["Implement", "Design", "Review", "Audit", "Test", "Deploy", "Refactor", "Construct", "Inspect", "Calibrate", "Document", "Prototype", "Validating"]
NOUNS = [
    "Cooling Pump", "Control Rod Actuator", "Graphite Moderator", "Steam Generator", 
    "Turbine Valve", "Emergency Diesel Generator", "Radiation Sensor", "Containment Dome", 
    "Spent Fuel Pool", "SCADA Interface", "Fire Suppression System", "Seismic Dampener", 
    "Access Control Gate", "Perimeter Fence", "Coolant Filter", "Pressure Vessel",
    "Heat Exchanger", "Backup Battery Bank", "Ventilation Shaft", "Control Room Display"
]

BUG_PREFIXES = ["Leak in", "Crash in", "Misalignment of", "Corrosion detected on", "Signal noise in", "Overheating of", "Unexpected latency in", "Auth failure in", "Cracks found in", "Inconsistent readings from"]

# --- State ---
generated_tasks = [] # List of task IDs
generated_milestones = [] # List of milestone IDs
current_task_id = 1000
current_bug_id = 5000
current_ms_id = 0

# --- User Generation ---
USERS = []
seen_uids = set()

for i in range(60): # More users
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
/macro @([a-z0-9]+) u/\1
/macro #([a-z_]+) p/\1

# --- Static Definitions ---
"""

def generate_static_data():
    lines = []
    
    lines.append("\n# --- Components / Teams ---")
    for tid, desc in TEAMS:
        lines.append(f"p/{tid} {desc}")
        # Add diverse links between components (just description text for now, or new type?)
        # Let's keep it simple text.

    lines.append("\n# --- Users ---")
    for uid, name, role, team in USERS:
        # Link users to other users (mentoring)
        mentor_text = ""
        if random.random() < 0.2 and len(USERS) > 5:
            mentor = random.choice(USERS)
            if mentor[0] != uid:
                 mentor_text = f" (mentored by u/{mentor[0]} )"
        
        lines.append(f"u/{uid} {name} ({role}, p/{team}){mentor_text}")
        
    return "\n".join(lines)

def generate_quarter_data(quarter_idx):
    global current_task_id, current_bug_id, current_ms_id
    lines = []
    
    qid, qdesc = QUARTERS[quarter_idx]
    
    lines.append(f"\n# ==========================================")
    lines.append(f"# Planning for {qdesc}")
    lines.append(f"# ==========================================")
    lines.append(f"q/{qid} {qdesc}")
    
    # 1. Milestones for this quarter
    q_milestones = []
    num_ms = NUM_MILESTONES // len(QUARTERS)
    
    # Indent items under the Quarter
    indent = "  "
    
    for i in range(num_ms):
        current_ms_id += 1
        ms_id = f"ms_{qid}_{i+1}"
        noun = random.choice(NOUNS)
        
        # Link to previous milestones?
        dep_text = ""
        if generated_milestones and random.random() < 0.3:
            prev = random.choice(generated_milestones)
            dep_text = f" (requires m/{prev})"
            
        # No explicit "in q/{qid}" needed due to inheritance
        line = f"{indent}m/{ms_id} Final sign-off for {noun}{dep_text}"
        lines.append(line)
        q_milestones.append(ms_id)
        generated_milestones.append(ms_id)

    # 2. Tasks for this quarter
    num_tasks = NUM_TASKS // len(QUARTERS)
    
    q_tasks = []
    
    for i in range(num_tasks):
        current_task_id += 1
        tid = current_task_id
        
        verb = random.choice(VERBS)
        noun = random.choice(NOUNS)
        user = random.choice(USERS)[0]
        team = random.choice(TEAMS)[0]
        
        # Diverse links
        links = []
        
        # Link to component (always)
        links.append(f"p/{team}")
        
        # Link to user (always)
        links.append(f"u/{user}")
        
        # Quarter link implicit via indentation
        
        # Link to previous tasks (dependency)
        if generated_tasks and random.random() < 0.25:
            prev = random.choice(generated_tasks)
            links.append(f"depends on t/{prev}")
            
        # Link to Milestone (blocker/relation)
        if q_milestones and random.random() < 0.15:
            ms = random.choice(q_milestones)
            links.append(f"blocking m/{ms}")
            
        desc = f"{verb} {noun} logic & specs"
        
        link_text = f"for p/{team} assigned to u/{user}"
        extras = []
        if generated_tasks and random.random() < 0.25:
             prev = random.choice(generated_tasks)
             extras.append(f"depends on t/{prev}")
        
        if q_milestones and random.random() < 0.15:
            ms = random.choice(q_milestones)
            extras.append(f"targeting m/{ms}")
            
        if extras:
            link_text += " (" + ", ".join(extras) + " )"
            
        lines.append(f"{indent}t/{tid} {desc} {link_text}")
        q_tasks.append(tid)
        generated_tasks.append(tid)

    # 3. Bugs for this quarter (linked to this quarter's tasks)
    # Group bugs under tasks if linked?
    # Or just under Quarter?
    # Let's verify: "reorganize list items leveraging inheritance"
    # Grouping bugs under Quarter is inheritance.
    
    num_bugs = NUM_BUGS // len(QUARTERS)
    
    for i in range(num_bugs):
        current_bug_id += 1
        bid = current_bug_id
        
        prefix = random.choice(BUG_PREFIXES)
        noun = random.choice(NOUNS)
        user = random.choice(USERS)[0]
        team = random.choice(TEAMS)[0]
        
        # Link to a task
        task_link = ""
        # If we link to a task, maybe we indent under that task?
        # But we print tasks first, then bugs.
        # To indent under task, we'd need to print the bug immediately after the task.
        # Restructuring loop to interleave bugs would be complex for this script update.
        # Let's stick to indenting under Quarter.
        
        if q_tasks and random.random() < 0.7:
            task = random.choice(q_tasks)
            task_link = f" while working on t/{task}"
            
        line = f"{indent}b/{bid} {prefix} {noun} found in p/{team}{task_link} (assigned: u/{user} )"
        lines.append(line)

    return "\n".join(lines)

def main():
    with open(OUTPUT_FILE, "w") as f:
        f.write(generate_header())
        f.write(generate_static_data())
        
        for i in range(len(QUARTERS)):
            f.write(generate_quarter_data(i))
    
    print(f"Generated {OUTPUT_FILE}")

if __name__ == "__main__":
    main()