import pytest
from pawpal_system import Task, Pet


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
