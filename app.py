import streamlit as st
from pawpal_system import Task, Owner, Pet, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Section 1 – Owner & Pet setup
# A st.form batches all widget changes so the vault guard only fires once
# the user clicks "Save", not on every keystroke.
# ---------------------------------------------------------------------------
st.subheader("Owner & Pet")

with st.form("setup_form"):
    col_o, col_t = st.columns(2)
    with col_o:
        owner_name = st.text_input("Owner name", value="Jordan")
    with col_t:
        available_minutes = st.number_input(
            "Available time (min/day)", min_value=30, max_value=480, value=120, step=15
        )

    col_p, col_a, col_s = st.columns(3)
    with col_p:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col_a:
        pet_age = st.number_input("Age (years)", min_value=0, max_value=30, value=3)
    with col_s:
        species = st.selectbox("Species", ["dog", "cat", "other"])

    submitted_setup = st.form_submit_button("Save owner & pet")

# Session vault: create or replace Owner/Pet only when inputs actually change.
if (
    "owner" not in st.session_state
    or st.session_state.owner.name != owner_name
    or st.session_state.owner.available_minutes != available_minutes
):
    st.session_state.owner = Owner(owner_name, int(available_minutes))

if (
    "pet" not in st.session_state
    or st.session_state.pet.name != pet_name
    or st.session_state.pet.species != species
    or st.session_state.pet.age != pet_age
):
    # Replacing the Pet clears its task list — warn the user if tasks exist.
    if "pet" in st.session_state and st.session_state.pet.task_count > 0:
        st.warning(
            "Pet details changed — the existing task list has been cleared "
            "because tasks belong to a specific pet."
        )
    st.session_state.pet = Pet(pet_name, species, int(pet_age))

owner: Owner = st.session_state.owner
pet: Pet = st.session_state.pet

st.caption(
    f"Vault: **{owner.name}** ({owner.available_minutes} min available) — "
    f"**{pet.name}** the {pet.species}, age {pet.age}"
)

st.divider()

# ---------------------------------------------------------------------------
# Section 2 – Add a task
#
# When the form is submitted:
#   1. A Task object is constructed via Task.__init__
#   2. pet.add_task(task) appends it to pet.tasks
#   3. Streamlit reruns; the display loop below reads pet.tasks and shows the
#      new entry — no separate list to keep in sync.
# ---------------------------------------------------------------------------
st.subheader("Add a Task")

with st.form("task_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input(
            "Duration (min)", min_value=1, max_value=240, value=20
        )
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    preferred_time = st.selectbox(
        "Preferred time slot (optional)",
        ["(none)", "morning", "afternoon", "evening"],
    )

    submitted_task = st.form_submit_button("Add task")

if submitted_task:
    # Build the real Task object and hand it to pet.add_task() — Phase 2 method.
    new_task = Task(
        title=task_title,
        duration_minutes=int(duration),
        priority=priority,
        preferred_time=None if preferred_time == "(none)" else preferred_time,
    )
    pet.add_task(new_task)   # <-- Pet.add_task() owns this data from here on
    st.success(f"Task '{new_task.title}' added to {pet.name}'s list.")

# Display comes from pet.tasks — the authoritative source.
if pet.tasks:
    st.write(f"Tasks assigned to **{pet.name}** ({pet.task_count} total):")
    rows = [
        {
            "Title": t.title,
            "Duration (min)": t.duration_minutes,
            "Priority": t.priority,
            "Preferred time": t.preferred_time or "—",
            "Done": "✓" if t.completed else "",
        }
        for t in pet.tasks
    ]
    st.table(rows)
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Section 3 – Generate schedule
#
# pet.tasks already holds Task objects, so no conversion is needed.
# Scheduler.generate_schedule() does the work; explain_plan() formats it.
# ---------------------------------------------------------------------------
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if not pet.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        scheduler = Scheduler(pet.tasks, owner, pet)
        scheduler.generate_schedule()
        st.success("Schedule generated!")
        st.text(scheduler.explain_plan())
