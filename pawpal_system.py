from typing import Optional

PRIORITY_RANK = {"high": 3, "medium": 2, "low": 1}
TIME_SLOT_ORDER = {"morning": 0, "afternoon": 1, "evening": 2}


class Task:
    def __init__(
        self,
        title: str,
        duration_minutes: int,
        priority: str,
        preferred_time: Optional[str] = None,
    ):
        """Create a task with a title, duration, priority, and optional preferred time slot."""
        self.title = title
        self.duration_minutes = duration_minutes
        self.priority = priority
        self.preferred_time = preferred_time
        self.completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def priority_score(self) -> int:
        """Return a numeric score for the priority level (high=3, medium=2, low=1)."""
        return PRIORITY_RANK.get(self.priority, 0)

    def __repr__(self) -> str:
        """Return a concise string representation of the task."""
        return f"Task({self.title!r}, {self.duration_minutes}min, {self.priority})"


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
