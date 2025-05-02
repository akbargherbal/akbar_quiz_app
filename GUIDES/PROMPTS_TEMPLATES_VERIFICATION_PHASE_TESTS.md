**Revised Prompts for Generating Phase Verification Scripts (LLM Decides Location)**

**General Instruction for the LLM (Assumed Context):**
"You have access to the `Authentication_App_Iteration_Guide.md` which details the step-by-step implementation plan for a Django authentication app, including specific objectives and outcomes for each phase. You may also have access to the LGID methodology study document which describes the purpose of Phase Verification Scripts."

---

**Prompt to Generate Phase 1 Verification Script**

```text
Generate a `pytest` script to serve as the Phase Verification Script for Phase 1, as defined in the `Authentication_App_Iteration_Guide.md`.

This script must contain automated tests that verify the specific objectives, configurations, and outcomes described for Phase 1 in the guide have been successfully implemented (focusing on settings, core auth URL configurations, template directory setup, and basic auth URL accessibility). This provides verifiable evidence of phase completion.

Provide the complete script content first.

Then, **explicitly state:**
1.  The recommended full file path for this script within the Django project structure (e.g., `src/core/tests/test_phase1_verification.py`).
2.  The specific `manage.py test` command needed to run *only* this verification script.
```

---

**Prompt to Generate Phase 2 Verification Script**

```text
Generate a `pytest` script to serve as the Phase Verification Script for Phase 2 (User Registration), as defined in the `Authentication_App_Iteration_Guide.md`.

This script must contain automated tests that verify the specific objectives and outcomes described for Phase 2 in the guide (focusing on the availability and basic context of the signup view and form). This provides verifiable evidence of phase completion.

Provide the complete script content first.

Then, **explicitly state:**
1.  The recommended full file path for this script within the Django project structure.
2.  The specific `manage.py test` command needed to run *only* this verification script.
```

---

**Prompt to Generate Phase 3 Verification Script**

```text
Generate or update a `pytest` script to serve as the Phase Verification Script for Phase 3 (Optional Linking), as defined in the `Authentication_App_Iteration_Guide.md`.

This script must contain automated tests that verify the specific objectives and model modification outcomes described for Phase 3 in the guide (particularly the changes to the `QuizAttempt` model regarding the optional `user` ForeignKey). If updating an existing file is the logical choice, ensure relevant existing tests are preserved or updated appropriately. This provides verifiable evidence of phase completion.

Provide the complete script content first.

Then, **explicitly state:**
1.  The recommended full file path for this script within the Django project structure (even if updating an existing file).
2.  The specific `manage.py test` command needed to run *only* this verification script.
```

---

**Prompt to Generate Phase 4 Verification Script**

```text
Generate or update a `pytest` script to serve as the Phase Verification Script for Phase 4 (Basic Profile & Navigation), as defined in the `Authentication_App_Iteration_Guide.md`.

This script must contain automated tests that verify the specific objectives and outcomes described for Phase 4 in the guide (focusing on profile view access control - `@login_required` behavior verification via test client, expected context data availability, and considering the redirect URL change mentioned in the guide). If updating an existing file is the logical choice, ensure relevant existing tests are preserved or updated appropriately. This provides verifiable evidence of phase completion.

Provide the complete script content first.

Then, **explicitly state:**
1.  The recommended full file path for this script within the Django project structure (even if updating an existing file).
2.  The specific `manage.py test` command needed to run *only* this verification script.
```

---

**Prompt to Generate Phase 5 Verification Script**

```text
Generate a `pytest` script to serve as the Phase Verification Script for Phase 5 (Password Management), as defined in the `Authentication_App_Iteration_Guide.md`.

This script must contain automated tests that verify the specific objectives and outcomes described for Phase 5 in the guide (focusing on the email backend configuration and the basic accessibility - GET returning 200 OK - of the various password management views/URLs). This provides verifiable evidence of phase completion.

Provide the complete script content first.

Then, **explicitly state:**
1.  The recommended full file path for this script within the Django project structure.
2.  The specific `manage.py test` command needed to run *only* this verification script.
```

