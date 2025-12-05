# Test-Driven Development (TDD) - Canon Workflow

**Source:** Kent Beck's "Canon TDD" (https://tidyfirst.substack.com/p/canon-tdd)

This document defines what TDD actually IS, as a specific workflow. This is not a prescription for how you MUST work, but rather a clear definition to prevent mischaracterizations of the practice.

---

## The Core TDD Cycle (Steps 2-4 Repeat)

TDD is an **iterative cycle**, not a linear process. You will go through steps 2-4 multiple times until your test list is exhausted.

```
1. Create test list (once at start, grows during development)
   ↓
   ┌─────────────────────────────────┐
   │  2. Write ONE test              │
   │  3. Make it pass                │ ← This cycle repeats
   │  4. Optionally refactor         │    many times
   └─────────────────────────────────┘
   ↓
5. Done (when test list is empty)
```

---

## Step 1: Create Test List (Once, Then Grows)

**What:** Analyze the desired behavior change and list all expected test scenarios.

**How:**
- Write down edge cases, failure modes, happy paths
- Keep it high-level (e.g., "negative input", "empty list", "concurrent access")
- Don't write actual test code yet
- Don't decide implementation details yet

**Key principle:** "Chill. There will be plenty of time to decide how the internals will look later."

**Example test list for "add user authentication":**
```
Test List:
- [ ] Valid credentials → success
- [ ] Invalid password → failure
- [ ] Non-existent user → failure
- [ ] Empty credentials → failure
- [ ] SQL injection attempt → safe failure
```

---

## Step 2: Write ONE Test (Pick from List)

**What:** Convert exactly **one** item from your test list into a concrete, automated test.

**How:**
- Pick the next test from your list (order matters!)
- Write test with: given, when, and then helper methods
- Mock out dependencies, but it's ok to use the file system as long as it's using the tempfile module. Make sure that the test is isolated from other tests. Make sure that the temp files/directories are cleaned up afterwards, but create an option to leave the files around for debugging.
- If you have multiple test methods that call the same given, when, and then methods, but only differ in the parameters passed to those methods, get rid of the duplication and use @pytest.mark.parametrize with the different parameters on a single test method.

**Don't:**
- ❌ Write multiple tests at once
- ❌ Write tests without assertions (just for coverage)
- ❌ Convert entire test list to tests before making any pass

**Example:**
```python
def test_valid_credentials_returns_success(self):
    """Valid username and password should authenticate successfully"""
    self.given_authenticator_configured_with("config.yaml")

    self.when_login_is_called_with("alice", "correct-password")

    self.then_result_is_success()

def test_valid_credentials_returns_success(self):
    """Invalid username and password should fail to authenticate"""
    self.given_authenticator_configured_with("config.yaml")

    self.when_login_is_called_with("alice", "WRONG")

    self.then_result_is_failure()

    
def given_authenticator_configured_with(self, config:str):
    self.authenticator = Authenticator(config)

def when_login_is_called_with(self, username:str, password:str):
    self.result = self.authenticator.login(username, password)

def then_result_is_success(self):
    assert self.result.success

def then_result_is_failure(self):
    assert not self.result.success
```

**Mark it off your list:**
```
Test List:
- [IN PROGRESS] Valid credentials → success
- [ ] Invalid password → failure
- [ ] Non-existent user → failure
...
```

---

## Step 3: Make It Pass (Discover New Tests)

**What:** Modify code so this test AND all previous tests pass.

**How:**
- Write the minimal code to pass
- Don't worry about elegance yet (that's refactoring)
- If you discover new test cases, **ADD THEM TO THE LIST**

**Critical insight:** While making code pass, you WILL discover tests you didn't think of. Add them to the list, don't implement them immediately.

**Example discovery:**
```python
# While implementing login(), you realize:
# "Oh, we need to handle database connection failures"

# ADD TO LIST (don't implement now):
Test List:
- [✓] Valid credentials → success
- [ ] Invalid password → failure
- [ ] Database connection failure → graceful error  ← NEW!
- [ ] Non-existent user → failure
...
```

**If discovery invalidates previous work:** You must decide:
- Continue with current approach?
- Or restart with different test order?

**Order matters:** Which test you pick next significantly affects:
- Programming experience
- Final result quality

---

## Step 4: Optionally Refactor

**What:** Improve the design/structure of code that makes tests pass.

**Key word: OPTIONAL**
- You don't have to refactor every cycle
- Only refactor when duplication/ugliness bothers you
- "Make it run, then make it right"

**How:**
- Extract methods/classes
- Remove duplication (but "duplication is a hint, not a command")
- Improve naming
- Simplify complex logic

**Don't:**
- ❌ Mix refactoring into the passing phase (step 3)
- ❌ Over-refactor beyond what's needed for this session
- ❌ Abstract too early

**Example refactoring:**
```python
# Before (passes tests, but duplicated):
def login(user, password):
    if user == "":
        return Error("empty user")
    if password == "":
        return Error("empty password")
    # ...

# After refactoring:
def login(user, password):
    self._validate_not_empty(user, "user")
    self._validate_not_empty(password, "password")
    # ...
```

**After refactoring:** All tests still pass (no behavior change).

---

## Step 5: Repeat Until List is Empty

**What:** Go back to Step 2, pick the next test from your list.

**The cycle continues:**
```
Current state:
- [✓] Valid credentials → success          ← Done
- [IN PROGRESS] Invalid password → failure ← Working on this now
- [ ] Database connection failure → error  ← Added during step 3
- [ ] Non-existent user → failure          ← Waiting
```

**You keep cycling:**
1. Write test for "invalid password"
2. Make it pass (maybe discover "locked account" → add to list)
3. Maybe refactor
4. Write test for "database connection failure"
5. Make it pass
6. Maybe refactor
7. ...continue until list is empty...

**End state:** "Transform fear for the behavior of the code into boredom."

---

## Anti-Patterns (What NOT to Do)

### ❌ Write all tests before any code
```
# WRONG:
test_valid_login()
test_invalid_password()
test_empty_credentials()
test_sql_injection()
# ...write 20 tests...
# ...THEN start implementing...

# RIGHT:
# Write test 1 → pass → refactor
# Write test 2 → pass → refactor
# ...one at a time...
```

### ❌ Write tests without assertions
```python
# WRONG (fake coverage):
def test_login_runs():
    auth.login("user", "pass")  # No assertion!

# RIGHT:
def test_login_with_valid_credentials_succeeds():
    result = auth.login("user", "pass")
    assert result.success is True
```

### ❌ Write tests for setters or dataclass properties
#### WRONG
```python
# WRONG:
@dataclass
class Foo:
    bar: str = "default"


result = Foo('abc')
assert result.bar == 'abc'
```
#### RIGHT:
Just write tests that enforce behavior. We'll pick up coverage of dataclasses that way. Also, dataclass instantiation is very unlikely to break.


### ❌ Mix refactoring into passing phase
```python
# WRONG sequence:
# 1. Write test
# 2. Make it pass WHILE ALSO refactoring everything

# RIGHT sequence:
# 1. Write test
# 2. Make it pass (even if ugly)
# 3. THEN refactor
```

### ❌ Delete assertions to make tests pass
```python
# WRONG:
def test_validation():
    result = validate(bad_input)
    # assert result.error is not None  ← Commented out to pass!

# RIGHT:
def test_validation():
    result = validate(bad_input)
    assert result.error is not None  # Fix the code, not the test
```

---

## Design Split: Interface vs Implementation

**Interface design** (how behavior is invoked):
- Happens during test writing (step 2)
- Defines public API, method signatures

**Implementation design** (how it works internally):
- Happens during passing phase (step 3)
- Refined during refactoring (step 4)

**Key insight:** Tests drive interface design. Implementation details emerge while making tests pass.

---

## Why This Workflow?

The TDD cycle ensures:
1. ✅ Existing functionality continues working (regression safety)
2. ✅ New behavior works as intended (correctness)
3. ✅ System remains ready for changes (maintainability)
4. ✅ Team confidence in code quality (psychological safety)

---

## Common Misunderstanding Corrected

**Strawman TDD:** "TDD suckz dude because I hate writing all the tests before I write any code"

**Canon TDD:** You maintain a test LIST, but only write ONE concrete test at a time. The list grows during development as you discover new scenarios.

---

## Using This Guide

When doing TDD work:

1. **Start with a test list** (can be rough, will grow)
2. **Pick one test** (order matters, start with simplest or most valuable)
3. **Write the test** (Given/When/Then, with assertions)
4. **Make it pass** (add discoveries to list, don't chase them)
5. **Maybe refactor** (only if duplication/ugliness bothers you)
6. **Repeat** until list is empty

**Remember:** It's a CYCLE, not a linear path. You'll go through steps 2-4 many times. The test list grows as you learn more about the problem.
