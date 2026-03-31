from typing import Optional


class Task:
    def __init__(
        self,
        title: str,
        duration_minutes: int,
        priority: str,
        preferred_time: Optional[str] = None,
    ):
        self.title = title
        self.duration_minutes = duration_minutes
        self.priority = priority
        self.preferred_time = preferred_time


class Pet:
    def __init__(self, name: str, species: str, age: int):
        self.name = name
        self.species = species
        self.age = age


class Owner:
    def __init__(self, name: str, available_minutes: int):
        self.name = name
        self.available_minutes = available_minutes


class Scheduler:
    def __init__(self, tasks: list[Task], owner: Owner, pet: Pet):
        self.tasks = tasks
        self.owner = owner
        self.pet = pet

    def generate_schedule(self) -> list[Task]:
        pass

    def explain_plan(self) -> str:
        pass
