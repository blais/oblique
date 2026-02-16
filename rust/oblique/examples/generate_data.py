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
current_task_id = 5000 # Manual IDs start high to avoid collision with auto-IDs
next_auto_task_id = 1
current_bug_id = 8000
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
    global current_task_id, current_bug_id, current_ms_id, next_auto_task_id
    lines = []
    
    qid, qdesc = QUARTERS[quarter_idx]
    
    lines.append(f"\n# ==========================================")
    lines.append(f"# Planning for {qdesc}")
    lines.append(f"# ==========================================")
    lines.append(f"q/{qid} {qdesc}")
    
    # 1. Milestones for this quarter
    q_milestones = []
    num_ms = NUM_MILESTONES // len(QUARTERS)
    
    for i in range(num_ms):
        current_ms_id += 1
        ms_id = f"ms_{qid}_{i+1}"
        noun = random.choice(NOUNS)
        
        # Messy indentation
        indent = " " * random.choice([2, 2, 2, 3, 4])
        
        # Link to previous milestones?
        dep_text = ""
        if generated_milestones and random.random() < 0.3:
            prev = random.choice(generated_milestones)
            # Mix of styles
            if random.random() < 0.5:
                dep_text = f" (requires m/{prev} )"
            else:
                dep_text = f" (dep: m/{prev} )"
            
        # Randomly add explicit quarter link despite indentation
        q_link = ""
        if random.random() < 0.2:
             q_link = f" in q/{qid}"

        line = f"{indent}m/{ms_id} Final sign-off for {noun}{dep_text}{q_link}"
        
        # Random comments
        if random.random() < 0.1:
            lines.append(f"{indent}# TODO: double check this date")
            
        lines.append(line)
        q_milestones.append(ms_id)
        generated_milestones.append(ms_id)

    # 2. Tasks for this quarter
    if random.random() < 0.8: # Sometimes skip the separator
        lines.append(f"\n# --- Tasks for {qid} ---")
    
    num_tasks = NUM_TASKS // len(QUARTERS)
    
    q_tasks = []
    
    for i in range(num_tasks):
        # Decide if auto or manual
        is_auto = random.random() < 0.9
        
        if is_auto:
            tid = next_auto_task_id
            next_auto_task_id += 1
        else:
            current_task_id += 1
            tid = current_task_id
        
        verb = random.choice(VERBS)
        noun = random.choice(NOUNS)
        user = random.choice(USERS)[0]
        team = random.choice(TEAMS)[0]
        
        # Messy indentation
        indent = " " * random.choice([2, 2, 3, 4])
        
        # Diverse links
        links = []
        
        # Link to component (mix #macro and p/ref)
        if random.random() < 0.6:
            links.append(f"#{team}")
        else:
            links.append(f"p/{team}")
        
        # Link to user (mix @macro and u/ref)
        if random.random() < 0.7:
            links.append(f"@{user}")
        else:
            links.append(f"u/{user}")
        
        # Randomly explicit quarter
        if random.random() < 0.1:
            links.append(f"q/{qid}")
        
        # Link to previous tasks
        if generated_tasks and random.random() < 0.25:
            prev = random.choice(generated_tasks)
            # Variations in text
            style = random.choice(["depends on", "after", "blocked by"])
            links.append(f"{style} t/{prev}")
            
        # Link to Milestone
        if q_milestones and random.random() < 0.15:
            ms = random.choice(q_milestones)
            links.append(f"blocking m/{ms}")
            
        desc = f"{verb} {noun} logic & specs"
        
        # Construct line with "natural" language mixed in
        link_text = " ".join(links)
        
        # Sometimes put links in parens, sometimes inline
        if random.random() < 0.5:
             full_text = f"{desc} ({link_text} )"
        else:
             full_text = f"{desc} - {link_text}"

        if is_auto:
            lines.append(f"{indent}t/ {full_text}")
        else:
            lines.append(f"{indent}t/{tid} {full_text}")
        
        # Random extra whitespace
        if random.random() < 0.05:
            lines.append("")

        q_tasks.append(tid)
        generated_tasks.append(tid)

    # 3. Bugs for this quarter
    lines.append(f"\n# --- Bugs reported in {qid} ---")
    num_bugs = NUM_BUGS // len(QUARTERS)
    
    for i in range(num_bugs):
        current_bug_id += 1
        bid = current_bug_id
        
        prefix = random.choice(BUG_PREFIXES)
        noun = random.choice(NOUNS)
        user = random.choice(USERS)[0]
        team = random.choice(TEAMS)[0]
        
        indent = " " * random.choice([2, 2, 4])
        
        # Link to a task
        task_link = ""
        if q_tasks and random.random() < 0.7:
            task = random.choice(q_tasks)
            if random.random() < 0.5:
                 task_link = f" during t/{task}"
            else:
                 task_link = f" related to t/{task}"
            
        assignee = f"@{user}" if random.random() < 0.8 else f"u/{user}"
        
        line = f"{indent}b/{bid} {prefix} {noun} found in #{team}{task_link} (assigned: {assignee} )"
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