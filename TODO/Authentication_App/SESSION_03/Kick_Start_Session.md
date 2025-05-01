**Project Focus:** Django Quiz App - Modular Authentication

**Our Roadmap:** Sticking to the Authentication_App_Iteratin_Guide.md.

**Where We Are:**

*   Just completed: **Phase 2: Optional Linking of Quiz Attempts to Users**
*   Active Phase: Starting **Phase 3: Basic User-Facing Profile & Navigation**

**What's Next:**

*   Starting now: **Phase 3, Step 3.1: Create Profile View & URL (Login Required)** - Focusing on **writing and passing the verification tests** for the profile view's access control.
*   The aim is to: Create the basic `/profile/` URL and view, protected by `@login_required`, and verify access control via Django Test Client tests.

**Goal for Next Session:**

*   Let's implement this part: Write the verification tests for Step 3.1 in `pages/tests/test_views.py` and ensure they pass against the code implemented at the end of the last session (profile view creation).

**Verification Checkpoint:**

*   We'll know we're good when: The new tests in `pages/tests/test_views.py` pass, confirming that unauthenticated users are redirected from `/profile/` and authenticated users receive a 200 OK response.

