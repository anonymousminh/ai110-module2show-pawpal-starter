from pawpal_system import Task, Owner, Pet, Scheduler

owner = Owner(name="Jordan", available_minutes=120)

mochi = Pet(name="Mochi", species="dog", age=3)
luna = Pet(name="Luna", species="cat", age=5)

mochi_tasks = [
    Task("Morning walk",      duration_minutes=30, priority="high",   preferred_time="morning"),
    Task("Feeding",           duration_minutes=10, priority="high",   preferred_time="morning"),
    Task("Training session",  duration_minutes=20, priority="medium", preferred_time="afternoon"),
    Task("Evening walk",      duration_minutes=25, priority="high",   preferred_time="evening"),
    Task("Teeth brushing",    duration_minutes=5,  priority="low",    preferred_time="evening"),
]

luna_tasks = [
    Task("Feeding",           duration_minutes=10, priority="high",   preferred_time="morning"),
    Task("Litter box cleaning", duration_minutes=10, priority="high", preferred_time="afternoon"),
    Task("Play / enrichment", duration_minutes=15, priority="medium", preferred_time="afternoon"),
    Task("Grooming",          duration_minutes=10, priority="low",    preferred_time="evening"),
]

separator = "=" * 52

for pet, tasks in [(mochi, mochi_tasks), (luna, luna_tasks)]:
    scheduler = Scheduler(tasks=tasks, owner=owner, pet=pet)
    scheduler.generate_schedule()

    print(separator)
    print(f"  Today's Schedule — {pet.name} ({pet.species})")
    print(separator)
    print(scheduler.explain_plan())
    print()
