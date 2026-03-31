import datetime
from typing import Optional

PRIORITY_RANK = {"high": 3, "medium": 2, "low": 1}
TIME_SLOT_ORDER = {"morning": 0, "afternoon": 1, "evening": 2}
_WEEKDAYS = {"monday", "tuesday", "wednesday", "thursday", "friday"}
_WEEKENDS = {"saturday", "sunday"}

# How far ahead to push a recurring task when it is marked complete.
_RECURRENCE_DELTA: dict[str, datetime.timedelta] = {
    "daily":    datetime.timedelta(days=1),
    "weekdays": datetime.timedelta(days=1),
    "weekends": datetime.timedelta(days=1),
    "weekly":   datetime.timedelta(weeks=1),
}


class Task:
    def __init__(
        self,
        title: str,
        duration_minutes: int,
        priority: str,
        preferred_time: Optional[str] = None,
        due_date: Optional[datetime.date] = None,
    ):
        """Create a task with a title, duration, priority, optional preferred time slot,
        and optional due date."""
        self.title = title
        self.duration_minutes = duration_minutes
        self.priority = priority
        self.preferred_time = preferred_time
        self.due_date: Optional[datetime.date] = due_date
        self.completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def priority_score(self) -> int:
        """Return a numeric score for the priority level (high=3, medium=2, low=1)."""
        return PRIORITY_RANK.get(self.priority, 0)

    def __repr__(self) -> str:
        due = f", due={self.due_date}" if self.due_date else ""
        return f"Task({self.title!r}, {self.duration_minutes}min, {self.priority}{due})"


class RecurringTask(Task):
    """A Task that repeats on a defined cadence (daily, weekdays, weekends, weekly)."""

    VALID_RECURRENCES = {"daily", "weekdays", "weekends", "weekly"}

    def __init__(
        self,
        title: str,
        duration_minutes: int,
        priority: str,
        recurrence: str,
        preferred_time: Optional[str] = None,
        due_date: Optional[datetime.date] = None,
    ):
        """Create a recurring task.

        Args:
            title: Human-readable name of the task.
            duration_minutes: How long the task takes.
            priority: One of 'high', 'medium', or 'low'.
            recurrence: Cadence — must be one of VALID_RECURRENCES
                ('daily', 'weekdays', 'weekends', 'weekly').
            preferred_time: Optional slot hint ('morning', 'afternoon', 'evening').
            due_date: The date this occurrence is due; used as the base when
                computing the next due date in mark_complete().

        Raises:
            ValueError: If recurrence is not one of VALID_RECURRENCES.
        """
        if recurrence not in self.VALID_RECURRENCES:
            raise ValueError(f"recurrence must be one of {self.VALID_RECURRENCES}")
        super().__init__(title, duration_minutes, priority, preferred_time, due_date)
        self.recurrence = recurrence

    def mark_complete(self) -> "RecurringTask":
        """Mark this occurrence complete and return a new RecurringTask for the next one.

        The next due date is calculated with timedelta so the caller can store or
        schedule it without any extra date arithmetic:
            daily / weekdays / weekends → today + 1 day
            weekly                      → today + 7 days
        """
        super().mark_complete()
        delta = _RECURRENCE_DELTA[self.recurrence]
        next_due = (self.due_date or datetime.date.today()) + delta
        return RecurringTask(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            recurrence=self.recurrence,
            preferred_time=self.preferred_time,
            due_date=next_due,
        )

    def is_active_today(self, day_of_week: str) -> bool:
        """Return True if this task should run on the given day of the week.

        Args:
            day_of_week: Full weekday name, case-insensitive (e.g. 'Tuesday').

        Returns:
            True when the recurrence cadence includes that day:
                'daily'    → always True
                'weekdays' → Monday–Friday
                'weekends' → Saturday–Sunday
                'weekly'   → Monday only
        """
        day = day_of_week.lower()
        if self.recurrence == "daily":
            return True
        if self.recurrence == "weekdays":
            return day in _WEEKDAYS
        if self.recurrence == "weekends":
            return day in _WEEKENDS
        if self.recurrence == "weekly":
            return day == "monday"
        return False

    def __repr__(self) -> str:
        due = f", due={self.due_date}" if self.due_date else ""
        return (
            f"RecurringTask({self.title!r}, {self.duration_minutes}min, "
            f"{self.priority}, recurrence={self.recurrence!r}{due})"
        )


class Pet:
    def __init__(self, name: str, species: str, age: int):
        """Create a pet with a name, species, and age."""
        self.name = name
        self.species = species
        self.age = age
        self.tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        """Append a task to this pet's task list."""
        self.tasks.append(task)

    @property
    def task_count(self) -> int:
        """Return the number of tasks assigned to this pet."""
        return len(self.tasks)


class Owner:
    def __init__(self, name: str, available_minutes: int):
        """Create an owner with a name and total daily time budget in minutes."""
        self.name = name
        self.available_minutes = available_minutes


class ScheduledTask:
    """A Task that has been placed into a time slot on the daily plan."""

    def __init__(self, task: Task, start_minute: int, reason: str):
        """Wrap a Task with its assigned start time (minutes since midnight) and scheduling reason."""
        self.task = task
        self.start_minute = start_minute
        self.reason = reason

    @property
    def end_minute(self) -> int:
        """Return the minute at which this task ends."""
        return self.start_minute + self.task.duration_minutes

    def time_range_str(self) -> str:
        """Return a human-readable time range string, e.g. '7:00 AM – 7:30 AM'."""
        return f"{self._fmt(self.start_minute)} – {self._fmt(self.end_minute)}"

    @staticmethod
    def _fmt(minutes: int) -> str:
        """Convert an absolute minute offset to a 12-hour clock string."""
        h, m = divmod(minutes, 60)
        period = "AM" if h < 12 else "PM"
        display_h = h % 12 or 12
        return f"{display_h}:{m:02d} {period}"


class Scheduler:
    DAY_START = 7 * 60  # 7:00 AM

    def __init__(self, tasks: list[Task], owner: Owner, pet: Pet):
        """Initialise the scheduler with a task list, an owner, and the pet being cared for."""
        self.tasks = tasks
        self.owner = owner
        self.pet = pet
        self.scheduled: list[ScheduledTask] = []
        self.dropped: list[tuple[Task, str]] = []

    def _sort_key(self, task: Task) -> tuple:
        """Sort by preferred time slot first, then by priority descending."""
        slot = TIME_SLOT_ORDER.get(task.preferred_time, 3)
        return (slot, -task.priority_score())

    def generate_schedule(self) -> list[ScheduledTask]:
        """Greedily build a daily schedule ordered by preferred time slot and priority."""
        sorted_tasks = sorted(self.tasks, key=self._sort_key)
        budget = self.owner.available_minutes
        cursor = self.DAY_START
        self.scheduled.clear()
        self.dropped.clear()

        for task in sorted_tasks:
            if task.duration_minutes > budget:
                self.dropped.append(
                    (task, f"Not enough time remaining ({budget} min left)")
                )
                continue

            reason = self._build_reason(task, cursor)
            entry = ScheduledTask(task, cursor, reason)
            self.scheduled.append(entry)
            cursor += task.duration_minutes
            budget -= task.duration_minutes

        return self.scheduled

    def _build_reason(self, task: Task, current_minute: int) -> str:
        """Compose a short human-readable explanation for why a task was scheduled."""
        parts = [f"{task.priority}-priority task for {self.pet.name}"]
        if task.preferred_time:
            parts.append(f"preferred in the {task.preferred_time}")
        parts.append(f"takes {task.duration_minutes} min")
        return "; ".join(parts)

    def sort_by_time(self) -> list[ScheduledTask]:
        """Return the scheduled entries sorted by start time (earliest first).

        Uses a lambda key on ``start_minute`` so the result is always in true
        chronological order, independent of the order tasks were inserted or
        the slot-based ordering used by generate_schedule().

        Returns:
            A new sorted list of ScheduledTask objects; self.scheduled is unchanged.
        """
        return sorted(self.scheduled, key=lambda e: e.start_minute)

    def filter_by_status(self, completed: bool) -> list[ScheduledTask]:
        """Return only entries whose underlying task matches the given completion status.

        Args:
            completed: Pass True to get finished tasks, False to get pending ones.

        Returns:
            A filtered list of ScheduledTask objects from self.scheduled.
        """
        return [e for e in self.scheduled if e.task.completed == completed]

    @staticmethod
    def detect_conflicts(entries: list[ScheduledTask]) -> list[tuple[ScheduledTask, ScheduledTask]]:
        """Find pairs of scheduled tasks whose time windows overlap.

        Pass entries from one or more schedulers combined to detect double-booking
        across pets.  Two entries conflict when one starts before the other ends:
            a.start < b.end  AND  b.start < a.end
        """
        sorted_entries = sorted(entries, key=lambda e: e.start_minute)
        conflicts: list[tuple[ScheduledTask, ScheduledTask]] = []
        for i, a in enumerate(sorted_entries):
            for b in sorted_entries[i + 1:]:
                if b.start_minute >= a.end_minute:
                    break  # list is sorted; nothing after b can overlap a
                conflicts.append((a, b))
        return conflicts

    def explain_plan(self) -> str:
        """Return a formatted summary of the schedule, including dropped tasks and time budget."""
        if not self.scheduled:
            return "No tasks were scheduled."

        lines = [
            f"Daily plan for {self.pet.name} "
            f"({self.pet.species}, age {self.pet.age}), "
            f"managed by {self.owner.name} "
            f"({self.owner.available_minutes} min available):\n"
        ]

        total_used = 0
        for i, entry in enumerate(self.scheduled, start=1):
            lines.append(
                f"  {i}. [{entry.time_range_str()}] {entry.task.title} "
                f"({entry.task.duration_minutes} min) — {entry.reason}"
            )
            total_used += entry.task.duration_minutes

        remaining = self.owner.available_minutes - total_used
        lines.append(f"\nTime used: {total_used} min | Remaining: {remaining} min")

        if self.dropped:
            lines.append("\nDropped tasks:")
            for task, reason in self.dropped:
                lines.append(f"  - {task.title}: {reason}")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def filter_by_pet(
    entries: list[tuple["Pet", ScheduledTask]], pet_name: str
) -> list[ScheduledTask]:
    """From a combined multi-pet list of (Pet, ScheduledTask) pairs, return
    only the entries belonging to the named pet."""
    return [entry for pet, entry in entries if pet.name == pet_name]
