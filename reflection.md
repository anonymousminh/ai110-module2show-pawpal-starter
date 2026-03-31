# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

My initial UML design centered on four main classes that separate concerns between data representation, user context, and scheduling logic:

- **Task** — Represents a single pet care activity (e.g., walk, feeding, medication). Attributes include `title`, `duration_minutes`, `priority` (low/medium/high), and an optional `preferred_time` (morning/afternoon/evening).

- **Pet** — Represents the pet being cared for. Attributes include `name`, `species`, and `age`.

- **Owner** — Represents the pet owner. Attributes include `name` and `available_minutes` (the total time budget for the day).

- **Scheduler** — The core logic class. It takes a list of `Task` objects, an `Owner`, and a `Pet`, then produces an ordered daily plan. Its responsibilities are to filter and sort tasks by priority and time constraints, fit them within the owner's available time, and provide a short explanation for why each task was included and in what order.

The relationships are straightforward: the `Scheduler` depends on `Task`, `Owner`, and `Pet` as inputs, and outputs a list of scheduled tasks (each with an assigned time slot and rationale). `Owner` and `Pet` are associated but independent — an owner has one or more pets, and the schedule is built for one pet at a time.

**b. Design changes**

- Did your design change during implementation? Yes
- If yes, describe at least one change and why you made it.

I added **`ScheduledTask`** as a wrapper around a `Task` plus concrete `start_minute` and scheduling reason, so the plan is separate from the raw task list. **`RecurringTask`** extends `Task` for cadences (daily, weekdays, weekends, weekly) and `mark_complete()` returns the next occurrence with an updated due date. Module-level **`filter_by_pet`** and static **`detect_conflicts`** live outside the original four-class sketch because they operate on combined data from multiple pets. These changes kept the core `Scheduler` focused while supporting sorting, filtering, recurrence, and overlap checks.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

The scheduler applies three constraints in order: **time budget** (hard cap — tasks that don't fit are dropped), **preferred time slot** (morning → afternoon → evening), and **priority** (high > medium > low as a tiebreaker within a slot). Time budget came first because it's non-negotiable; slot preference came second because pet routines have a natural rhythm; priority breaks ties when the budget is nearly exhausted.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

The scheduler is **greedy**: it places tasks back-to-back in a single pass and drops any task that doesn't fit the remaining budget immediately, without looking ahead. This means a long low-priority task could block a short high-priority one that would have fit. This is reasonable because daily pet care tasks are few (typically under 10) and have natural time preferences, so the greedy result almost always matches what a human owner would choose — and it keeps the logic simple enough to explain in plain language.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used AI for brainstorming how to wire Streamlit session state to domain objects, for implementing sorting/filtering/conflict detection without reinventing patterns, and for tightening docstrings and tests. The most helpful prompts were concrete ones tied to this repo (e.g. “call `pet.add_task` from the form,” “use `timedelta` for the next recurring due date,” “add pytest cases for overlap vs. adjacent times”).

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

Early on, a suggestion was to keep tasks as plain dicts in `session_state` and only build `Task` objects at schedule time. I kept a single source of truth on the `Pet` (`pet.tasks` as real `Task` instances) so the UI and scheduler stay aligned. I verified by running the app and `pytest` and by checking that `preferred_time` and recurrence behavior stayed consistent end-to-end.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

Tests in `tests/test_pawpal.py` cover: **`mark_complete`** on plain tasks (including idempotency); **`Pet.add_task`** and task counts; **`sort_by_time`** (chronological order, no mutation of `scheduled`); **`RecurringTask.mark_complete`** (next day / next week, preserved fields, new object); and **`detect_conflicts`** (same start, partial overlap, adjacent non-overlap, multiple triple collisions). These matter because they guard the features users rely on (completion, ordering, recurrence, and double-booking warnings) without needing to click through the UI every time.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I am fairly confident for typical daily use (roughly **4/5**): the greedy scheduler, sort, recurrence spawn, and conflict logic all pass automated tests. Next I would test **zero- or negative-duration tasks**, **owner budget of zero**, **tasks longer than the full day**, **midnight wraparound** if start times ever leave the 7 AM–anchored model, and **integration tests** that run `generate_schedule` then `detect_conflicts` across two pets in one script.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

Separating **`ScheduledTask`** from **`Task`** made it easy to sort and detect conflicts on concrete clock times while keeping tasks reusable. The test suite gives quick feedback when changing scheduling rules.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I would teach the scheduler about **one owner, multiple pets** in a single pass (shared budget and explicit conflict resolution) instead of scheduling each pet independently and detecting overlaps afterward. I would also add **buffers** between tasks and optional **due_date** filtering in the UI.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

Small, testable units (sort, filter, conflicts, recurrence) are easier to get right than one giant “schedule everything” function — and AI is most useful when you verify its output with tests and real runs instead of trusting the first draft.
