import datetime
import pytest
from pawpal_system import Task, RecurringTask, Pet, Owner, Scheduler, ScheduledTask


# ---------------------------------------------------------------------------
# Task Completion
# ---------------------------------------------------------------------------

class TestMarkComplete:
    def test_task_starts_incomplete(self):
        task = Task("Morning walk", 30, "high")
        assert task.completed is False

    def test_mark_complete_sets_completed_true(self):
        task = Task("Morning walk", 30, "high")
        task.mark_complete()
        assert task.completed is True

    def test_mark_complete_is_idempotent(self):
        """Calling mark_complete() twice should not raise and status stays True."""
        task = Task("Feeding", 10, "high")
        task.mark_complete()
        task.mark_complete()
        assert task.completed is True


# ---------------------------------------------------------------------------
# Task Addition
# ---------------------------------------------------------------------------

class TestPetTaskAddition:
    def test_new_pet_has_zero_tasks(self):
        pet = Pet("Mochi", "dog", 3)
        assert pet.task_count == 0

    def test_adding_one_task_increments_count(self):
        pet = Pet("Mochi", "dog", 3)
        pet.add_task(Task("Morning walk", 30, "high"))
        assert pet.task_count == 1

    def test_adding_multiple_tasks_increments_count(self):
        pet = Pet("Luna", "cat", 5)
        pet.add_task(Task("Feeding",   10, "high",   "morning"))
        pet.add_task(Task("Grooming",  10, "low",    "evening"))
        pet.add_task(Task("Play time", 15, "medium", "afternoon"))
        assert pet.task_count == 3

    def test_added_tasks_are_accessible(self):
        pet = Pet("Mochi", "dog", 3)
        task = Task("Teeth brushing", 5, "low")
        pet.add_task(task)
        assert pet.tasks[0] is task


# ---------------------------------------------------------------------------
# Sorting Correctness
# ---------------------------------------------------------------------------

class TestSortByTime:
    def test_scrambled_entries_sorted_chronologically(self):
        """Tasks inserted at 7 PM, 7 AM, 1 PM should come back as 7 AM, 1 PM, 7 PM."""
        entries = [
            ScheduledTask(Task("Evening snack",   10, "low"),    19 * 60, ""),
            ScheduledTask(Task("Morning feeding", 10, "high"),    7 * 60, ""),
            ScheduledTask(Task("Afternoon play",  20, "medium"), 13 * 60, ""),
        ]
        owner = Owner("Test", 120)
        pet = Pet("Test", "dog", 1)
        sched = Scheduler([], owner, pet)
        sched.scheduled = entries

        result = sched.sort_by_time()
        start_times = [e.start_minute for e in result]
        assert start_times == [7 * 60, 13 * 60, 19 * 60]

    def test_already_sorted_stays_sorted(self):
        entries = [
            ScheduledTask(Task("A", 10, "high"),  60, ""),
            ScheduledTask(Task("B", 10, "high"), 120, ""),
        ]
        sched = Scheduler([], Owner("X", 60), Pet("X", "dog", 1))
        sched.scheduled = entries

        result = sched.sort_by_time()
        assert [e.task.title for e in result] == ["A", "B"]

    def test_sort_does_not_mutate_original_list(self):
        entries = [
            ScheduledTask(Task("Late",  10, "low"),  600, ""),
            ScheduledTask(Task("Early", 10, "high"), 420, ""),
        ]
        sched = Scheduler([], Owner("X", 60), Pet("X", "dog", 1))
        sched.scheduled = entries

        sched.sort_by_time()
        assert sched.scheduled[0].task.title == "Late"


# ---------------------------------------------------------------------------
# Recurrence Logic
# ---------------------------------------------------------------------------

class TestRecurrenceLogic:
    def test_daily_mark_complete_creates_next_day(self):
        """Marking a daily task complete should return a new task due tomorrow."""
        today = datetime.date(2026, 3, 31)
        task = RecurringTask("Feeding", 10, "high", "daily", due_date=today)

        next_task = task.mark_complete()

        assert task.completed is True
        assert next_task.completed is False
        assert next_task.due_date == datetime.date(2026, 4, 1)

    def test_weekly_mark_complete_creates_next_week(self):
        today = datetime.date(2026, 3, 31)
        task = RecurringTask("Grooming", 20, "medium", "weekly", due_date=today)

        next_task = task.mark_complete()

        assert next_task.due_date == datetime.date(2026, 4, 7)

    def test_next_task_preserves_attributes(self):
        task = RecurringTask(
            "Walk", 30, "high", "daily",
            preferred_time="morning",
            due_date=datetime.date(2026, 1, 1),
        )
        next_task = task.mark_complete()

        assert next_task.title == task.title
        assert next_task.duration_minutes == task.duration_minutes
        assert next_task.priority == task.priority
        assert next_task.recurrence == task.recurrence
        assert next_task.preferred_time == task.preferred_time

    def test_next_task_is_independent_instance(self):
        task = RecurringTask("Feed", 10, "high", "daily", due_date=datetime.date(2026, 1, 1))
        next_task = task.mark_complete()

        assert next_task is not task


# ---------------------------------------------------------------------------
# Conflict Detection
# ---------------------------------------------------------------------------

class TestConflictDetection:
    def test_same_start_time_is_conflict(self):
        """Two tasks starting at the same minute must be flagged."""
        a = ScheduledTask(Task("Bath",  30, "medium"), 7 * 60, "")
        b = ScheduledTask(Task("Vet",   60, "high"),   7 * 60, "")

        conflicts = Scheduler.detect_conflicts([a, b])
        assert len(conflicts) == 1
        titles = {conflicts[0][0].task.title, conflicts[0][1].task.title}
        assert titles == {"Bath", "Vet"}

    def test_overlapping_ranges_detected(self):
        """Task A 7:00–7:30 and Task B 7:15–7:45 overlap."""
        a = ScheduledTask(Task("Walk",  30, "high"),   7 * 60,      "")
        b = ScheduledTask(Task("Train", 30, "medium"), 7 * 60 + 15, "")

        conflicts = Scheduler.detect_conflicts([a, b])
        assert len(conflicts) == 1

    def test_adjacent_tasks_no_conflict(self):
        """Task A ends at 7:30, Task B starts at 7:30 — no overlap."""
        a = ScheduledTask(Task("Walk",  30, "high"),  7 * 60,      "")
        b = ScheduledTask(Task("Feed",  10, "high"),  7 * 60 + 30, "")

        conflicts = Scheduler.detect_conflicts([a, b])
        assert len(conflicts) == 0

    def test_no_conflicts_returns_empty(self):
        a = ScheduledTask(Task("Morning", 30, "high"),  7 * 60,  "")
        b = ScheduledTask(Task("Evening", 30, "high"), 19 * 60, "")

        conflicts = Scheduler.detect_conflicts([a, b])
        assert conflicts == []

    def test_multiple_conflicts_all_returned(self):
        """Three tasks at the same time should produce three conflict pairs."""
        a = ScheduledTask(Task("A", 30, "high"), 7 * 60, "")
        b = ScheduledTask(Task("B", 30, "high"), 7 * 60, "")
        c = ScheduledTask(Task("C", 30, "high"), 7 * 60, "")

        conflicts = Scheduler.detect_conflicts([a, b, c])
        assert len(conflicts) == 3
