import datetime
from pawpal_system import Task, RecurringTask, Owner, Pet, Scheduler, ScheduledTask, filter_by_pet

TODAY      = datetime.date.today()
TODAY_NAME = TODAY.strftime("%A")   # e.g. "Tuesday"
SEP        = "=" * 58

owner = Owner(name="Jordan", available_minutes=120)
mochi = Pet(name="Mochi", species="dog", age=3)
luna  = Pet(name="Luna",  species="cat", age=5)

# ---------------------------------------------------------------------------
# Step 3 — Recurring task definitions (RecurringTask extends Task)
# ---------------------------------------------------------------------------
mochi_tasks: list[Task] = [
    RecurringTask("Morning walk",     30, "high",   "daily",    "morning"),
    RecurringTask("Feeding",          10, "high",   "daily",    "morning"),
    RecurringTask("Training session", 20, "medium", "weekdays", "afternoon"),
    RecurringTask("Evening walk",     25, "high",   "daily",    "evening"),
    Task(         "Teeth brushing",    5, "low",               preferred_time="evening"),
]

luna_tasks: list[Task] = [
    RecurringTask("Feeding",             10, "high",   "daily",    "morning"),
    RecurringTask("Litter box cleaning", 10, "high",   "daily",    "afternoon"),
    RecurringTask("Play / enrichment",   15, "medium", "weekdays", "afternoon"),
    Task(         "Grooming",            10, "low",               preferred_time="evening"),
]

print(SEP)
print(f"  Today is {TODAY_NAME} ({TODAY}) — recurring task status")
print(SEP)
for task in mochi_tasks + luna_tasks:
    if isinstance(task, RecurringTask):
        status = "ACTIVE " if task.is_active_today(TODAY_NAME) else "skipped"
        print(f"  {status}  [{task.recurrence:9s}]  {task.title}")
print()

# Keep only tasks that are active today before handing them to the scheduler.
active_mochi = [
    t for t in mochi_tasks
    if not isinstance(t, RecurringTask) or t.is_active_today(TODAY_NAME)
]
active_luna = [
    t for t in luna_tasks
    if not isinstance(t, RecurringTask) or t.is_active_today(TODAY_NAME)
]

# ---------------------------------------------------------------------------
# Build schedules for both pets
# ---------------------------------------------------------------------------
mochi_sched = Scheduler(active_mochi, owner, mochi)
luna_sched  = Scheduler(active_luna,  owner, luna)
mochi_sched.generate_schedule()
luna_sched.generate_schedule()

for sched in (mochi_sched, luna_sched):
    print(SEP)
    print(f"  Today's Schedule — {sched.pet.name} ({sched.pet.species})")
    print(SEP)
    print(sched.explain_plan())
    print()

# ---------------------------------------------------------------------------
# Step 2 — Sorting: tasks inserted at scrambled clock times → sort_by_time() fixes them
#
# sort_by_time() uses a lambda on e.start_minute so any flat list of
# ScheduledTask objects can be re-ordered chronologically regardless of how
# they were inserted:
#   sorted(self.scheduled, key=lambda e: e.start_minute)
# ---------------------------------------------------------------------------
print(SEP)
print("  Step 2 — Sorting: ScheduledTasks inserted in scrambled order")
print(SEP)

# Manually create entries at out-of-order start times (minutes since midnight).
scrambled: list[ScheduledTask] = [
    ScheduledTask(Task("Evening snack",    10, "low"),    19 * 60, "manual"),  # 7:00 PM — inserted first
    ScheduledTask(Task("Morning feeding",  10, "high"),    7 * 60, "manual"),  # 7:00 AM — inserted second
    ScheduledTask(Task("Afternoon play",   20, "medium"), 13 * 60, "manual"),  # 1:00 PM — inserted third
]

print("  Insertion order (scrambled):")
for entry in scrambled:
    print(f"    {entry.time_range_str()}  {entry.task.title}")

# sorted() with a lambda key — same as sort_by_time() internally
print("  After sort_by_time() (lambda key=lambda e: e.start_minute):")
for entry in sorted(scrambled, key=lambda e: e.start_minute):
    print(f"    {entry.time_range_str()}  {entry.task.title}")
print()

# ---------------------------------------------------------------------------
# Step 2 — Filtering by status (completed / pending)
# ---------------------------------------------------------------------------
print(SEP)
print("  Step 2 — Filter by status (mark first two of Mochi's tasks done)")
print(SEP)

mochi_sched.scheduled[0].task.mark_complete()   # mark_complete() on a plain Task
mochi_sched.scheduled[1].task.mark_complete()

print("  Completed:")
for entry in mochi_sched.filter_by_status(completed=True):
    print(f"    ✓  {entry.task.title}")
print("  Still pending:")
for entry in mochi_sched.filter_by_status(completed=False):
    print(f"    ○  {entry.task.title}")
print()

# ---------------------------------------------------------------------------
# Step 2 — Filtering by pet (combined pool from multiple schedulers)
# ---------------------------------------------------------------------------
print(SEP)
print(f"  Step 2 — Filter by pet: {len(mochi_sched.scheduled) + len(luna_sched.scheduled)} entries → Luna only")
print(SEP)

all_entries: list[tuple[Pet, ScheduledTask]] = (
    [(mochi, e) for e in mochi_sched.scheduled]
    + [(luna,  e) for e in luna_sched.scheduled]
)
for entry in filter_by_pet(all_entries, "Luna"):
    print(f"  [{entry.time_range_str()}]  {entry.task.title}")
print()

# ---------------------------------------------------------------------------
# Step 3 — Automating recurring tasks
#
# When mark_complete() is called on a RecurringTask it:
#   1. Sets self.completed = True
#   2. Uses timedelta to compute the next due date
#   3. Returns a brand-new RecurringTask ready to be scheduled
#
# daily / weekdays / weekends → today + timedelta(days=1)
# weekly                      → today + timedelta(weeks=1)
# ---------------------------------------------------------------------------
print(SEP)
print("  Step 3 — Auto-spawn next occurrence on mark_complete()")
print(SEP)

feeding = RecurringTask(
    "Feeding", 10, "high", "daily", preferred_time="morning", due_date=TODAY
)
print(f"  Original  : {feeding!r}  completed={feeding.completed}")

next_feeding = feeding.mark_complete()          # returns the new RecurringTask
print(f"  After call: completed={feeding.completed}  (original is done)")
print(f"  Spawned   : {next_feeding!r}")
print(f"  Due date  : {next_feeding.due_date}  (+1 day via timedelta(days=1))")

weekly_task = RecurringTask(
    "Weekly grooming", 20, "medium", "weekly", preferred_time="morning", due_date=TODAY
)
next_weekly = weekly_task.mark_complete()
print(f"  Weekly task next due: {next_weekly.due_date}  (+7 days via timedelta(weeks=1))")
print()

# ---------------------------------------------------------------------------
# Step 4 — Conflict detection: explicit same-start-time clash
#
# Two tasks placed at 7:00 AM on the same schedule produce an immediate
# overlap.  detect_conflicts() returns the conflicting pairs as a list
# so the caller prints ⚠ WARNING messages rather than crashing.
# ---------------------------------------------------------------------------
print(SEP)
print("  Step 4 — Conflict detection: two tasks at 7:00 AM (same start time)")
print(SEP)

clash_a = ScheduledTask(Task("Bath time",       30, "medium"), 7 * 60, "manually placed")
clash_b = ScheduledTask(Task("Vet appointment", 60, "high"),   7 * 60, "manually placed")

direct_conflicts = Scheduler.detect_conflicts([clash_a, clash_b])
if direct_conflicts:
    for a, b in direct_conflicts:
        print(
            f"  ⚠ WARNING: '{a.task.title}' [{a.time_range_str()}]"
            f" conflicts with '{b.task.title}' [{b.time_range_str()}]"
        )
else:
    print("  No conflicts.")
print()

# Cross-pet conflicts: both schedulers start at 7:00 AM, so Jordan is
# double-booked across Mochi's and Luna's schedules.
print(SEP)
cross_conflicts = Scheduler.detect_conflicts(mochi_sched.scheduled + luna_sched.scheduled)
print(f"  Step 4 — Cross-pet conflicts: {len(cross_conflicts)} found")
print(SEP)
for a, b in cross_conflicts:
    print(
        f"  ⚠ WARNING: '{a.task.title}' [{a.time_range_str()}]"
        f" overlaps '{b.task.title}' [{b.time_range_str()}]"
    )
print()
