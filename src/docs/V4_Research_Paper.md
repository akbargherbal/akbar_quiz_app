## **LLM-Guided Iterative Development (LGID): A Practical and Adaptive Framework for the Independent Django Developer**

**Version:** 2.1 (Revised based on experimental findings and to enhance Iteration Guide clarity)
**Date:** 2025-05-08

**Abstract:**

Independent Django developers face unique resource constraints, making Large Language Models (LLMs) attractive for accelerating development, primarily observed in generating boilerplate code (models, views, forms). However, unmanaged LLM interaction risks subtle inaccuracies, integration complexities, and significant debugging overhead, counteracting potential gains. This paper introduces the refined **LLM-Guided Iterative Development (LGID)** framework, validated and improved through practical application. It emphasizes **upfront requirements planning (Stage 0)**, where developers define scope and core architecture (potentially using LLMs for drafting assistance), followed by **LLM-assisted iterative implementation (Stages 1..N)** against that plan. Developers act as critical reviewers, integrators, and debuggers, leveraging LLMs as coding assistants. LGID incorporates **adaptive rigor** in implementation tracking (Lean/Standard Iteration Guides) and verification intensity, acknowledging observed variations in testing practices while recommending heuristics for stronger integration. Key refinements include guidance on leveraging LLMs for **debugging assistance**, incorporating an explicit **code refinement step**, promoting **TDD-lite practices** by generating tests alongside implementation, and providing enhanced **prompting strategies**, including those for generating appropriately abstracted planning documents. Supported by concrete templates and grounded in observed developer practices, the refined LGID provides a robust framework for solo developers to build high-quality Django applications, balancing structured planning with flexible, LLM-accelerated execution while mitigating risks identified through practical usage.

**1. Introduction**

**1.1. The LLM Opportunity and Challenge for Indie Developers:**
Large Language Models offer transformative potential, particularly appealing to independent Django developers seeking efficiency. LLMs demonstrably accelerate the generation of boilerplate code (models, forms, views, admin configurations), freeing developers for more complex tasks. However, practical experiments reveal significant challenges: LLMs can produce subtly incorrect or overly complex code, miss dependencies, and require careful context management. Integrating LLM output often introduces non-trivial debugging complexities, particularly at component boundaries. Without structure, relying heavily on LLMs can lead to architectural drift and consume more time in review and debugging than initially saved. These risks are amplified for solo developers lacking extensive peer review.

**1.2. The Need for Structured Guidance with Upfront Planning:**
Empirical evidence confirms that simply prompting an LLM with high-level requests ("build feature X") is inefficient and risky. Effective LLM leverage requires a process where the developer maintains firm control over architecture, quality, and verification. This control must be grounded in **well-defined initial requirements**. While iterative _implementation_ is beneficial, attempting to discover core requirements iteratively using LLMs introduces significant friction, integration problems, and necessitates costly refactoring, validating the need for foundational decisions before iterative building commences.

**1.3. Introducing the Refined LGID: Upfront Planning, Iterative Execution, Informed by Practice:**
This paper details the **LLM-Guided Iterative Development (LGID)** framework, refined based on observed developer workflows and challenges. It integrates LLM assistance within a structure prioritizing **clear requirements established in Stage 0**, followed by iterative, verifiable implementation phases. Key principles, validated and enhanced by practice:

- **Structured Upfront Planning:** Core architecture and feature requirements are defined and documented in `Project_Requirements.md` _before_ iterative development starts (Stage 0). LLMs were observed assisting effectively in drafting these requirements. This stage proved crucial in providing context for subsequent LLM prompts and preventing scope creep.
- **Iteration & Modularity in Implementation:** Build _against_ the plan in small, verifiable increments, often aligned with Django app boundaries or pre-defined phases. Developers consistently followed this pattern using `Iteration_Guide.md`.
- **Developer as Central Controller:** The developer remains the architect, requirements finalizer (Stage 0), **critical code reviewer**, integrator, and primary debugger. Findings underscore that significant developer oversight is non-negotiable.
- **Adaptive Rigor (Implementation & Verification):** Allows adjusting procedural overhead (Lean/Standard Iteration Guides, verification depth). Findings show developers utilize this strategically, though it can lead to variability. Refined LGID includes heuristics for verification decisions.
- **Leveraging LLMs Effectively:** Focus LLM use on boilerplate generation, test creation, configuration assistance, and increasingly, **debugging assistance** and **code refinement prompts**.
- **Practical Aids:** Provides updated templates and examples (Appendices A-E) reflecting observed best practices and addressing identified gaps (e.g., TDD-lite prompts, refinement step, guidance on Iteration Guide granularity).
- **Skill Development Focus:** Acknowledges necessary skills (testing, prompt engineering, planning) and incorporates guidance based on observed challenges and successes.

**1.4. Purpose of this Document:**
This study aims to:

- Detail the components of the refined LGID methodology, incorporating empirical findings.
- Illustrate its practical application, highlighting adaptive decision points informed by real-world usage.
- Analyze its feasibility and provide strategies based on observed challenges and developer workarounds.
- Offer updated, actionable templates and examples reflecting successful patterns and addressing weaknesses, including clear guidance on planning document abstraction.
- Advocate for the refined LGID as a practical, evidence-based strategy for maximizing LLM benefits while mitigating observed risks in solo Django development.

**2. The LGID Methodology: Core Components & Refinements**

LGID structures development around **upfront planning** followed by **LLM-assisted iterative implementation cycles**, tracked via an Iteration Guide and verified adaptively but rigorously.

**2.1. The Project Requirements Document (`Project_Requirements.md`): The Foundational Blueprint**

- A **mandatory component** created during Stage 0. Foundational for providing LLM context and guiding development.
- Central Markdown document defining vision, core architecture, and features.
- **Breaks project into logical Phases** and lists **specific, numbered requirements** per phase. This structure was consistently used and valued.
- LLMs can assist in brainstorming and drafting requirements (observed practice), but the developer **must** finalize and approve this document before proceeding.
- Serves as the **single source of truth**, minimizing ambiguity and requirement discovery friction during implementation phases. Changes require explicit updates here.

**2.2. The Iteration Guide (`AppName_Iteration_Guide.md`): Tracking Implementation**

- A living Markdown document per app/feature **tracking implementation progress against `Project_Requirements.md`**.
- Outlines **Phases** (matching `Project_Requirements.md`) and **Implementation Steps**, tracking Objective (derived from Requirements), Key Tasks, Deliverables, and Verification.
- **Does NOT define requirements**; it references them (e.g., "Step 1.1: Implement Req 1.a - Post Model"). This linkage was critical for context in prompts.
- Offers **two template options** (See fully fleshed-out examples with annotations in Appendix A) for adaptive rigor in tracking:
  - **Standard Guide:** Provides a detailed structure suitable for complex phases or when maximum traceability is desired. It's designed for comprehensive planning without being overly prescriptive.
    -   **Important Clarification on Detail Level:** The 'Key Tasks' in a Standard Guide should remain at a summary or objective level (typically 1-3 high-level actions per step). They are intended to guide the developer's thinking and overall approach, not to prescribe specific commands, code snippets, or minute sub-tasks. Similarly, the 'Verification Checklist' should list key verification activities or goals, not detailed test case descriptions. The developer retains autonomy in decomposing these tasks and checks into specific actions during implementation. See Appendix A for an annotated example demonstrating this desired level of abstraction.
  - **Lean Guide:** A checklist-style format focusing on objectives, direct references to requirements, minimal task listing, and essential verification points. This is often adopted for its efficiency in simpler phases or by developers more comfortable with less explicit tracking.
- Emphasizes the guide as a _tool_: developers choose the appropriate template. Linking steps/phases to commits (e.g., `git commit -m "Complete Step 1.1 (Ref #Step-1.1, implements Req 1.a)"`) is a recommended practice for traceability.
- **Anti-Pattern to Avoid:** A common pitfall is generating Iteration Guides where 'Key Tasks' or 'Verification' sections become overly granular, listing specific API calls, shell commands, detailed UI interaction sequences, or pseudo-code. This transforms the guide from a flexible planning tool into a rigid, micro-managed script, which constrains developer agency, quickly becomes outdated, and diminishes its utility. LGID promotes Iteration Guides as high-level roadmaps, not turn-by-turn directions. Referencing the examples in Appendix A and using targeted prompts (see Appendix B) can help avoid this.

**2.3. Upfront Requirements Specification & Phased Implementation**

- **Stage 0 is Critical:** Development **does not begin** until `Project_Requirements.md` is drafted. This proved essential for successful LLM utilization in subsequent stages by providing clear scope and context. Foundational decisions are locked in here.
- **Phased Execution:** Work proceeds phase by phase according to `Project_Requirements.md`. Each phase delivers a verifiable increment.
- **Handling Changes:** If requirements change _after_ Stage 0, `Project_Requirements.md` is updated _first_. Future implementation phases are adjusted, or specific, controlled refactoring is planned and documented. This avoids chaotic, ad-hoc changes during implementation.
- **Addressing Architectural Foresight:** Stage 0 planning forces upfront architectural consideration, mitigating major structural issues discovered late in development.

**2.4. Granular Implementation Steps & Focused LLM Prompts**

- Break phase _implementation_ into small, actionable steps documented in the Iteration Guide (respecting the abstraction levels discussed in Section 2.2).
- Use highly specific, context-aware prompts referencing the requirement(s) from `Project_Requirements.md`. Findings show this is the predominant and most effective prompting strategy.
- Provides an **Enhanced Example Prompt Library (Appendix B)** illustrating effective prompts for common tasks (models, views, forms, admin, tests, config, basic debugging, refinement suggestions, and generating Iteration Guides themselves) based on observed usage and addressing missed opportunities.

**2.5. Defined Roles (Reflecting Practice)**

- **Developer** = Architect, Project Manager, Requirements Definer/Approver (Stage 0), **Critical Code Reviewer**, **Integrator**, **Primary Debugger**, QA Engineer, Prompt Engineer.
- **LLM** = **Requirements Drafting Assistant (Stage 0)**, **Planning Document Drafting Assistant (e.g., Iteration Guides - Stage 1..N)**, **Boilerplate Code Generator** (models, views, forms, tests, admin, etc.), **Configuration Assistant**, **Basic Debugging Assistant** (explaining errors, suggesting fixes when prompted with context), **Refactoring Suggestion Engine** (when prompted).

**2.6. Verification with Adaptive Rigor (Refined Approach)**

- Verification at multiple stages is essential. Findings show multi-layered verification (step, phase, regression) is practiced.
- **Adaptive Rigor in Verification Intensity:**
  - **Step-Level Verification:** _Always Recommended._ Minimum checks observed and recommended: Code linting/formatting, `python manage.py check`, `makemigrations`/`migrate` (if applicable), developer code review (manual inspection against requirements), basic security checks (Appendix D). **Crucially, generate basic unit tests (TDD-lite) for new logic alongside implementation code** (use LLM assist - Appendix B). This strengthens continuous validation. Check for implicit dependencies (e.g., Pillow) introduced by LLM code.
  - **Phase Verification Scripts (`test_phaseX_verification.py`):** _Adaptive._ Recommended for complex phases, foundational work, or high-risk integrations. _Optional_ for simple phases where step-level tests + regression tests provide sufficient confidence.
    - **Decision Heuristic:** Consider creating a script if the phase introduces significant new interactions, modifies core shared components, involves complex logic susceptible to integration errors, or touches security-sensitive areas. Document the decision (include/omit) and rationale in the Iteration Guide. (See Appendix C guidance).
  - **Regression Testing:** _Always Essential._ Running the full test suite (`pytest` or `manage.py test`) after each phase proved vital for catching unintended side effects.
  - **Leverage LLM for Debugging:** When verification fails (step, phase, or regression), **explicitly prompt the LLM with the error message, traceback, and relevant code snippets** to ask for explanations, potential causes, or fixes (See Appendix B). This addresses a key missed opportunity.
  - **No Progression on Critical Failure:** Halt, diagnose (using LLM assist if helpful), fix, and re-verify before moving forward.

**3. The Refined LGID Development Pipeline**

1.  **Stage 0: Strategic Planning, Requirements Definition & Initialization:**
    - Define goals, architecture.
    - **Create `Project_Requirements.md`:** Document vision, architecture, phases, requirements per phase (LLM assist optional for drafting). Developer finalizes.
    - Standard project setup, version control.
    - Developer **chooses Standard or Lean Iteration Guide template** (see Appendix A for examples). An LLM can assist in drafting the Iteration Guide using prompts like those in Appendix B.
2.  **Stage 1..N: Phased Implementation:**
    - **Step X.0: Phase Kick-off: Review Requirements & Plan/Refine Implementation Steps:**
      - Consult `Project_Requirements.md` for Phase X requirements.
      - Create or refine implementation steps in `AppName_Iteration_Guide.md` (developer-led, LLM-assisted optional, ensuring appropriate abstraction).
    - **Step X.1...X.N: Implement Phase X Steps:**
      - For each step:
        - Write focused prompts referencing requirement(s) and step plan.
        - LLM generates code/artifacts (e.g., model code + basic unit test skeleton).
        - Developer reviews critically against requirements, quality, security (Appendix D). Check for implicit dependencies.
        - Developer integrates code, making necessary manual adjustments.
        - Developer performs **Step-Level Verification** (lint, check, migrations, run _new_ unit tests, manual review).
        - **If verification fails:** Use LLM assist with error context for diagnosis/fixes. Re-verify.
        - Document step completion/verification in Iteration Guide. Link commit.
    - **(Optional but Recommended) Step X.N+1: Code Refinement:**
      - Prompt LLM to review the newly integrated code for the phase (or specific complex parts) for potential improvements, clarity, or adherence to best practices.
      - Developer critically evaluates suggestions and applies useful refinements. Document briefly in Iteration Guide.
    - **Step X.N+2: Phase Verification (Adaptive):**
      - Developer **decides if a Phase Verification Script is warranted** based on heuristics (complexity, risk, interactions). Document decision.
      - If yes: Generate/update script (LLM-assisted optional), run it.
      - **If script fails:** Use LLM assist with error context. Fix and re-verify. Document results.
    - **Step X.N+3: Run Full Regression Tests:** Run relevant test suites.
      - **If tests fail:** Use LLM assist with error context. Fix regressions. Re-verify.
    - Mark phase as complete in Iteration Guide.

**4. Addressing Practical Concerns & Scaling LGID (Informed by Findings)**

- **4.1. Managing Overhead & Scaling:**
  - Use the **Lean Iteration Guide** (Appendix A) and make **informed decisions** about skipping Phase Scripts for simpler phases (document rationale). The upfront investment in `Project_Requirements.md` consistently pays off by reducing downstream confusion and rework.
- **4.2. Bridging Skill Gaps:**
  - _Planning:_ Use LLM in Stage 0 for drafting requirements. For Iteration Guides, use LLMs with clear prompts specifying desired abstraction (Appendix B) and reference good examples (Appendix A). Focus on clear, testable requirements.
  - _Testing:_ Start with LLM-generated basic unit tests (TDD-lite, Appendix B). Focus phase scripts (Appendix C) on key integration points. Treat tests as vital code.
  - _Prompt Engineering:_ Study Appendix B (enhanced). Provide clear requirement context. Iterate. Explicitly prompt for debugging and refinement. Effective context management was noted as important, especially when prompting for planning documents to ensure they meet the desired level of detail.
- **4.3. Maintaining Documents & Tests:**
  - _Requirements Doc:_ Keep it the source of truth. Update deliberately.
  - _Iteration Guides:_ Keep them lean (or appropriately detailed for Standard) but accurate for tracking execution and verification decisions. Link commits.
  - _Tests:_ Maintain them. Refactor. Integrate phase checks into broader suites over time.
- **4.4. Tooling and Automation:**
  - Use `cookiecutter` for scaffolding. Integrate checks into CI/CD (Appendix E) - linters, `manage.py check`, `pytest` - aligns with professional practices and reinforces verification. Consider simple scripts/extensions for guide management or prompt generation (recommendation).
- **4.5. Economic Feasibility & Costs:**
  - LLM API costs remain low for focused tasks. The major investment is developer time for Stage 0 planning, **critical review/integration (significant effort observed)**, and verification. This is offset by **accelerated boilerplate generation**, reduced debugging time (if LLM assist used effectively), and improved maintainability.
- **4.6. Feasibility Summary:** LGID is technically feasible. Operational feasibility is high due to structure, adaptability, and alignment with observed effective practices. Economic feasibility strong due to targeted LLM efficiencies balanced against necessary developer oversight and risk reduction from upfront planning.

**5. Benefits of Refined LGID (Validated & Enhanced)**

- **Predictability & Reduced Risk:** Upfront requirements (Stage 0) minimize surprises and provide LLM context.
- **Controlled Acceleration:** LLMs speed up **boilerplate implementation, test generation, and initial drafting of planning documents**.
- **Improved Quality & Consistency:** Structured review against requirements, integrated testing (including TDD-lite), and regression checks catch issues early. Developer oversight is key.
- **Enhanced Developer Control:** Developer directs architecture, approves requirements, reviews all code, manages integration, and sets the abstraction level for planning.
- **More Efficient Debugging:** Issues caught earlier. **Leveraging LLM for diagnosis** speeds up resolution. Integration debugging remains a challenge requiring developer skill.
- **Increased & Earlier Test Coverage:** Process now explicitly encourages TDD-lite and leverages LLMs for test generation.
- **Living Documentation:** Requirements doc = plan; Iteration guide = execution log (at an appropriate level of detail).
- **Flexibility in Process:** Adaptive rigor (tracking/verification) allows tailoring effort, guided by heuristics.
- **Actionable Guidance:** Updated templates/examples (especially for Iteration Guides in Appendix A and prompting in Appendix B) reflect practice and address identified needs for clarity and appropriate abstraction.
- **Leverages LLM Proactivity:** Encourages evaluating useful LLM suggestions (validators, constraints, etc.) within the review step.

**6. Challenges & Mitigation in Refined LGID (Based on Findings)**

- **LLM Output Imperfections:** Requires **vigilant developer review and correction**. This applies to code, documentation, and planning artifacts.
    - Mitigation: Review against specific requirements; Use LLM for refinement prompts; Robust verification. For planning documents like Iteration Guides, LLMs might generate overly verbose or minutely detailed content. **Mitigation for this includes providing clear, complete examples of desired output (see revised Appendix A) and using precise prompts that specify the expected abstraction level (see new prompt in revised Appendix B).**
- **Integration & Debugging Complexity:** Integrating LLM code and debugging subtle issues remains a primary developer task. Mitigation: Small implementation steps; Step-level verification; **Use LLM for debugging assistance (new)**; Developer expertise remains crucial.
- **Verification Variability:** Adaptive rigor can lead to gaps if not applied judiciously. Mitigation: Clearer **heuristics for phase verification decisions**; Emphasize TDD-lite for continuous checks; Mandatory regression testing.
- **Effective Prompt Engineering & Context:** Requires skill and iteration.
    - Mitigation: Enhanced **Prompt Library (Appendix B)**; Emphasize requirement linkage; Prompt for specific tasks (debug, refine). This principle is particularly critical when prompting for the generation of planning documents like the Iteration Guide. Reinforce that **clearly defining the expected level of detail and referencing established templates (like the revised Appendix A) is crucial for obtaining useful, appropriately abstracted outputs.**
- **Upfront Planning Effort (Stage 0):** Requires dedicated time but prevents larger downstream problems (validated by findings). Mitigation: Use LLM assist for drafting; View as essential investment.
- **Discipline:** Adherence to process (updates, verification) is key. Mitigation: Lean Guide option; Clear benefits demonstrated by practice.
- **Handling Requirement Changes:** Requires disciplined updates to `Project_Requirements.md` and replanning. Mitigation: Emphasize Stage 0 importance; Treat changes formally.

**7. Illustrative Case Study Snippet: Adding Comments (Refined Process)**

- **Scenario:** Add comments to a blog app (Phase 2).
- **LGID Application:**
  - **Stage 0:** `Project_Requirements.md` created (possibly LLM-drafted), defining architecture and Phase 1/Phase 2 requirements (2.a-2.f as before). Developer finalizes.
  - **(Assume Phase 1 completed)**
  - **Phase 2 Kick-off (Step 2.0):** Review Reqs 2.a-2.f. Developer chooses Lean Guide (`blog_Iteration_Guide.md` - see Appendix A for Lean template structure). Plans high-level steps/actions for the guide: 2.1 (Model+Admin+Basic Test), 2.2 (Form+Test), 2.3 (View GET), 2.4 (Template Update), 2.5 (View POST+Test). (LLM could assist in drafting this guide structure using a prompt similar to Appendix B, but adapted for a Lean Guide).
  - **Step 2.1 (Implement Model, Admin & Basic Test - Req 2.a, 2.c):**
    - _Prompt Example (for code):_ "Per Req 2.a & 2.c, generate `Comment` model for `blog/models.py`. Include admin registration in `blog/admin.py`. Also, generate a basic `pytest` test structure in `blog/tests/test_models.py` to check `__str__` output for a sample `Comment`."
    - _Verification:_ Review LLM code against Reqs. Check dependencies. Run `makemigrations`/`migrate`. Run the _new_ basic test. Mark complete in Lean Guide.
  - **(Steps 2.2 - 2.5 proceed similarly, potentially generating tests for form validation (Step 2.2) and POST logic (Step 2.5), performing step-level verification, using LLM debug assist if a step's test fails. Key tasks in the guide remain high-level.)**
  - **(Optional) Step 2.6 (Code Refinement):**
    - _Prompt Example:_ "Review the `PostDetailView` (GET and POST handling for comments) implemented for Reqs 2.b/2.d/2.e. Any suggestions for clarity, efficiency, or adherence to Django best practices?" Evaluate suggestions.
  - **Step 2.7 (Phase 2 Verification Decision):**
    - _Decision:_ Phase involves form handling, auth, DB interaction. _Heuristic:_ Introduces new interactions and modifies core view. Developer decides _to create_ `test_phase2_verification.py` (Appendix C style) checking integration points (form display, logged-in post success, anonymous post failure). Rationale documented in Lean Guide. Script created (LLM assist optional) and run. (If it failed, LLM would be prompted with error/traceback).
  - **Step 2.8 (Regression):** Run full `pytest`. Fix issues (using LLM assist if needed). Mark Phase 2 complete.
- **Reflection:** Requirements defined upfront. Lean Guide used, with high-level actions. **TDD-lite** applied. **Optional refinement** considered. **Adaptive verification decision** made. **LLM debugging** planned. LLM assisted based on clear specs.

**8. Conclusion**

The refined LLM-Guided Iterative Development (LGID) framework, informed by practical developer experience, offers a robust and adaptive approach for solo Django developers. By mandating **upfront requirements planning (Stage 0)** and structuring **LLM-assisted iterative implementation** against that plan, LGID leverages LLM strengths (boilerplate generation, drafting assistance for code and planning documents) while mitigating observed weaknesses (inaccuracies, integration challenges, overly detailed LLM outputs). The emphasis on the **developer's critical role** in review, integration, debugging, and setting appropriate abstraction levels for planning, augmented by **targeted LLM assistance for debugging and refinement**, is crucial. Incorporating **TDD-lite practices** and **heuristics for adaptive verification** strengthens quality assurance. LGID provides a practical, evidence-based pathway for independent developers to harness LLM power effectively, building architecturally sound, maintainable Django applications with improved predictability, velocity, and quality control.

---

**Appendices:**

**Appendix A: Iteration Guide Templates (Updated Examples with Annotations)**

This appendix provides complete examples of both Standard and Lean Iteration Guides. These templates are designed to guide the developer (and any LLM assisting in their creation) to maintain an appropriate level of detail, focusing on high-level planning and tracking rather than micro-management.

**A.1 Standard Iteration Guide Example (`blog_app_Standard_Iteration_Guide.md`)**

**Project:** MyDjangoBlog
**App/Feature:** Blog App - User Authentication & Core Post Functionality
**Guide Type:** Standard

---

**Phase 1: User Authentication and Basic Post Management**

**Overall Objective(s) for Phase 1 (from `Project_Requirements.md`):**
-   Req 1.a: Implement custom user model with email as username.
-   Req 1.b: Implement user registration, login, logout functionality.
-   Req 1.c: Create `Post` model (title, content, author, timestamps).
-   Req 1.d: Basic Django admin integration for `User` and `Post` models.
-   Req 1.e: Authenticated users can create new posts.
-   Req 1.f: List all posts on homepage, view individual posts.

---

**Implementation Steps:**

**Step 1.1: Setup Custom User Model**
-   **Objective(s) (from `Project_Requirements.md`):** Req 1.a
-   **Key Tasks:**
    ```
    <!-- Annotation: Key Tasks should be high-level summaries of the main actions.
         The developer will decompose these into specific sub-tasks, commands,
         and detailed coding steps during actual implementation. This guide is for
         planning and tracking progress at a strategic level, not a micro-plan.
         Typically 1-3 key tasks per step. -->
    ```
    1.  Define `CustomUser` model inheriting from `AbstractUser`, using email as `USERNAME_FIELD`.
    2.  Define `CustomUserManager` for the new user model.
    3.  Update `settings.py` to use `AUTH_USER_MODEL`.
-   **Deliverables:**
    -   `users/models.py` (with `CustomUser`, `CustomUserManager`)
    -   `settings.py` (updated `AUTH_USER_MODEL`)
    -   Initial migration files for the `users` app.
-   **Verification Checklist:**
    ```
    <!-- Annotation: Verification is a checklist of what to confirm or achieve,
         not detailed test script content or step-by-step QA procedures.
         Specific unit tests, integration tests, and manual checks will be
         performed by the developer based on these goals. -->
    ```
    -   [ ] Code lints successfully (`flake8`, `black`).
    -   [ ] `python manage.py check` passes.
    -   [ ] `python manage.py makemigrations users` and `migrate` run without errors.
    -   [ ] `CustomUser` model structure reviewed against Req 1.a.
    -   [ ] Able to create a superuser using the custom model.
-   **Status:** Not Started
-   **Commit(s):**

**Step 1.2: Implement User Authentication Views & Forms**
-   **Objective(s) (from `Project_Requirements.md`):** Req 1.b
-   **Key Tasks:**
    1.  Create forms for user registration and login.
    2.  Implement views for registration, login, and logout.
    3.  Define URL patterns for authentication views.
-   **Deliverables:**
    -   `users/forms.py` (RegistrationForm, LoginForm)
    -   `users/views.py` (registration_view, login_view, logout_view)
    -   `users/urls.py`
    -   Associated templates (`register.html`, `login.html`)
-   **Verification Checklist:**
    -   [ ] User registration flow works as expected.
    -   [ ] User login/logout functionality operational.
    -   [ ] Form validation (e.g., password mismatch, existing email) behaves correctly.
    -   [ ] Basic unit tests for forms (e.g., valid/invalid data) pass.
    -   [ ] Relevant templates render correctly.
-   **Status:** Not Started
-   **Commit(s):**

**Step 1.3: Define and Register Post Model**
-   **Objective(s) (from `Project_Requirements.md`):** Req 1.c, Req 1.d (Post part)
-   **Key Tasks:**
    1.  Define `Post` model in `blog/models.py` with specified fields and foreign key to `CustomUser`.
    2.  Register `Post` model with Django admin, customizing display if necessary.
    3.  Generate and apply migrations for the `blog` app.
-   **Deliverables:**
    -   `blog/models.py` (with `Post` model)
    -   `blog/admin.py` (with `PostAdmin`)
    -   Migration files for `blog` app.
-   **Verification Checklist:**
    -   [ ] `python manage.py makemigrations blog` and `migrate` run cleanly.
    -   [ ] `Post` model structure review against Req 1.c.
    -   [ ] Admin interface for `Post` model accessible; CUD operations functional.
    -   [ ] Basic unit tests for `Post` model (`__str__`, any custom methods) pass.
-   **Status:** Not Started
-   **Commit(s):**

**(Further steps for Phase 1, e.g., Post Creation Views/Forms, Post List/Detail Views, would follow a similar structure.)**

---

**A.2 Lean Iteration Guide Example (`project_docs_Lean_Iteration_Guide.md`)**

**Project:** MyDjangoBlog
**App/Feature:** Documentation Site Setup
**Guide Type:** Lean

---

**Phase 3: Initial Documentation Site Setup**

**Overall Objective(s) for Phase 3 (from `Project_Requirements.md`):**
-   Req 3.a: Integrate Sphinx for project documentation.
-   Req 3.b: Basic `index.rst` and `conf.py` configuration.
-   Req 3.c: Document an overview of the project architecture.

---

**Implementation Checklist:**

**[ ] Step 3.1: Initialize Sphinx**
    -   **Objective:** Req 3.a
    -   **Key Action(s):**
        ```
        <!-- Annotation: Key Actions in a Lean Guide are very concise,
             focusing on the primary outcome or the main task cluster.
             The developer is expected to know the sub-steps. -->
        ```
        -   Install Sphinx, run `sphinx-quickstart`.
    -   **Verification:**
        ```
        <!-- Annotation: Verification in a Lean Guide is a brief confirmation.
             Detailed step-level checks (linting, basic functionality) are assumed
             as per general LGID practice, even if not explicitly listed here. -->
        ```
        -   Sphinx directory structure created. Basic HTML build (`make html`) successful.
    -   **Commit(s):**

**[ ] Step 3.2: Basic Configuration & Index Page**
    -   **Objective:** Req 3.b
    -   **Key Action(s):**
        -   Configure `conf.py` (theme, extensions if any).
        -   Create initial content for `index.rst`.
    -   **Verification:**
        -   `index.html` renders with chosen theme and basic content.
    -   **Commit(s):**

**[ ] Step 3.3: Draft Architecture Overview**
    -   **Objective:** Req 3.c
    -   **Key Action(s):**
        -   Create `architecture.rst` and write initial overview.
        -   Link `architecture.rst` from `index.rst`.
    -   **Verification:**
        -   Architecture page accessible from index and renders content.
    -   **Commit(s):**

---

**Appendix B: Enhanced Example Prompt Library**

This appendix provides examples of prompts for various tasks within the LGID framework. They are designed to elicit useful responses from LLMs while maintaining developer control and adhering to LGID principles.

**(Existing prompt examples for Model+Basic Test, View+Basic Test, Form+Basic Test, Admin, Config would be here, updated as needed for clarity and consistency with TDD-lite focus.)**

**New Addition:**

### Prompt for Generating a Standard Iteration Guide

**Context:**
You are assisting a Django developer using the LGID framework. The developer has already created a `Project_Requirements.md` document. You need to generate a `Standard_Iteration_Guide.md` for a specific phase outlined in the requirements.

**Instruction:**
"Generate a `Standard_Iteration_Guide.md` for **Phase [Number/Name of Phase from Project_Requirements.md - e.g., Phase 2: Commenting System]** for the **[AppName]** app.

Refer to the following `Project_Requirements.md` snippet for the scope of this phase:
```markdown
### Phase 2: Commenting System (for 'blog' app)
- Req 2.a: Users can add comments to blog posts. Comment model should include text, author (User FK), post (Post FK), creation timestamp.
- Req 2.b: Comments displayed on the post detail page, oldest first.
- Req 2.c: Basic admin integration for comments (list, view, delete).
- Req 2.d: Only authenticated users can post comments.
- Req 2.e: Implement a form for submitting comments.
- Req 2.f: Comment submission handled via POST request on the post detail view.
```

**Output Format and Structure:**
Use the Standard Iteration Guide template structure. For guidance on the appropriate level of detail and structure, refer to the example provided in **Appendix A.1 (Standard Iteration Guide Example) of the LGID paper (Version 2.1)**. Specifically ensure:

*   **Overall Objective(s) for Phase:** List the requirement IDs and a brief summary for this phase.
*   **Implementation Steps:**
    *   Break down the phase into logical implementation steps (e.g., "Define Comment Model & Admin," "Implement Comment Form & View Logic," "Update Template to Display Comments & Form").
    *   For each step:
        *   **Objective(s):** Clearly state the requirement ID(s) from `Project_Requirements.md` that the step addresses.
        *   **Key Tasks:** List **1-3 high-level summary actions** needed to complete the step. *Critical: Do NOT include specific shell commands, detailed code snippets, or minute sub-tasks.* These are for the developer to determine during implementation. For example, a Key Task might be "Define Comment model and register with admin," *NOT* "Run `python manage.py startapp comments`. Add `Comment` class to `models.py` with fields X, Y, Z. Add `CommentAdmin` to `admin.py`." The goal is strategic guidance, not a micro-plan.
        *   **Deliverables:** List the key files or artifacts created/modified (e.g., `models.py`, `forms.py`, specific templates).
        *   **Verification Checklist:** Provide a **checklist of key verification goals or activities** (e.g., "Code lints successfully," "Migrations run cleanly," "Comment submission by authenticated user successful," "Comments display correctly"). *Critical: Do NOT write detailed test cases or exhaustive test scripts.* This should be a high-level checklist.
        *   **Status:** (Default to 'Not Started')
        *   **Commit(s):** (Leave blank)

**Goal:**
The generated Iteration Guide should serve as a high-level plan and tracking document for the developer, empowering them to manage the detailed execution. It must align with the principles of developer agency and the desired level of abstraction for planning documents as emphasized in the LGID framework. It should be suitable for the `AppName_Standard_Iteration_Guide.md` file.
"

---

### Prompts for Debugging Assistance

**Prompt: Explain This Error**
```
"I'm working on my Django project. When I try to [action, e.g., 'access the /admin/ page'], I get the following error and traceback. Can you explain what this error typically means and point to potential areas in my code to investigate?

Error:
```
[Paste full error message and traceback here]
```

Relevant code snippets:
[Optionally, paste relevant snippets from models.py, views.py, urls.py, settings.py, etc. that you suspect might be involved. Keep snippets concise but provide enough context.]
```

**Prompt: Suggest Fixes for This Error (with Context)**
```
"Following up on the previous error, I've investigated [mention what you found or suspect]. Here's the error again:
```
[Paste full error message and traceback here]
```
And here's the relevant code I believe is causing the issue:
`[filename.py]`
```python
[Paste specific code block here]
```
Based on this, can you suggest potential fixes or modifications to resolve this error? Explain the reasoning behind your suggestions."
```

---

### Prompts for Code Refinement/Review

**Prompt: Review Django Code for Best Practices**
```
"Please review the following Django [model/view/form/template] code from my `[app_name]/[file_name.py]` file.
It's intended to [briefly describe functionality and relevant requirements, e.g., 'handle user registration and ensure unique emails, per Req 1.b'].

```python
[Paste code snippet here]
```

Could you:
1. Identify any areas that don't follow Django best practices?
2. Suggest improvements for clarity, efficiency, or security?
3. Point out any potential bugs or edge cases I might have missed?
Please explain your suggestions."
```

---

### Prompts for Checking Security Aspects (based on Appendix D)

**Prompt: Security Check for Django View**
```
"I've written this Django view in `[app_name]/views.py` to handle [describe functionality, e.g., 'processing a user-submitted form for creating a new blog post'].
```python
[Paste view code here]
```
And here is the relevant form from `[app_name]/forms.py`:
```python
[Paste form code here]
```
Referring to common Django security considerations (like those in Appendix D of the LGID framework, e.g., CSRF, XSS, input validation, authorization checks, query parameter safety):
1. Are there any obvious security vulnerabilities in this code?
2. What specific checks or improvements should I consider adding to enhance its security?
For example, is my form validation sufficient? Am I handling authorization correctly before performing actions?"
```

---

**Appendix C: Example Phase Verification Script Template (`pytest`) & Decision Guidance** (Updated)

This appendix provides a template for phase-specific verification scripts using `pytest` and offers guidance on deciding when to create such scripts.

**C.1. Example `pytest` Phase Verification Script (`test_phase1_user_auth_post_integration.py`)**

```python
# project/tests/test_phase1_user_auth_post_integration.py
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
# from blog.models import Post # Assuming Post model is in blog app

User = get_user_model()

@pytest.mark.django_db
def test_phase1_user_registration_and_login(client):
    """
    Tests core user registration and login flow.
    Corresponds to objectives of Req 1.a, 1.b.
    """
    # Registration
    register_url = reverse('users:register') # Assuming 'users' namespace and 'register' name
    user_data = {
        'email': 'testphase1user@example.com',
        'password': 'strongpassword123',
        'password_confirm': 'strongpassword123'
    }
    response = client.post(register_url, data=user_data)
    assert response.status_code == 302 # Or 200 if redirecting to a success page
    assert User.objects.filter(email=user_data['email']).exists()

    # Login
    login_url = reverse('users:login')
    login_data = {'username': user_data['email'], 'password': user_data['password']}
    response = client.post(login_url, data=login_data)
    assert response.status_code == 302 # Or 200, check for user in session
    # assert '_auth_user_id' in client.session # More robust login check

@pytest.mark.django_db
def test_phase1_authenticated_user_can_create_post(client, django_user_model):
    """
    Tests if an authenticated user can create a post.
    Corresponds to objectives of Req 1.e.
    Requires Post model and creation view/form to be implemented.
    """
    # Create and login user
    username = "testcreator@example.com"
    password = "password"
    user = django_user_model.objects.create_user(email=username, password=password)
    client.login(email=username, password=password)

    # Attempt to create a post (adjust URL and form data as per your app)
    # create_post_url = reverse('blog:post_create')
    # post_data = {'title': 'My Phase 1 Test Post', 'content': 'Some great content here.'}
    # response = client.post(create_post_url, data=post_data)
    # assert response.status_code == 302 # Assuming redirect after successful post
    # assert Post.objects.filter(title=post_data['title'], author=user).exists()
    pytest.skip("Post creation endpoint not yet fully defined for this example")


# Add more tests relevant to Phase 1 objectives, e.g.:
# - Test anonymous user cannot access post creation page.
# - Test post list and detail views display correctly (if part of phase).
```

**C.2. Guidance on Creating Phase Verification Scripts (Heuristics)**

A dedicated Phase Verification Script is **recommended but adaptive**. The decision to create one (or rely on step-level unit/integration tests and full regression suites) depends on the phase's nature. Document your decision and rationale in the Iteration Guide.

**Consider creating a Phase Verification Script if the Phase:**

1.  **Introduces Significant New Component Interactions:** e.g., A new app interacting deeply with an existing one, first-time integration of a major third-party library.
2.  **Modifies Core Shared Components or Critical Paths:** e.g., Changes to custom user model, authentication system, core data processing logic.
3.  **Involves Complex Logic Prone to Integration Errors:** e.g., Multi-step workflows, state changes across multiple models, complex permission logic.
4.  **Touches Security-Sensitive Areas:** e.g., Authentication, authorization, payment processing, user data handling.
5.  **Establishes Foundational Functionality:** e.g., The first set of CRUD operations for a primary model, initial API endpoint setup.
6.  **Benefits from End-to-End Style Tests:** Where testing the flow through several components is more valuable than isolated unit tests for verifying the phase's main objectives.

**When might you OMIT a dedicated Phase Script (and document why)?**

*   **Very Simple, Isolated Changes:** e.g., Adding a single, non-critical field to a model already well-tested, minor UI tweaks with no backend logic change.
*   **Highly Reused/Library-like Components:** Where comprehensive unit tests for the component itself provide sufficient confidence, and its integration points are simple and already covered.
*   **Purely Refactoring Phases:** If the refactoring is covered by existing comprehensive unit and integration tests that confirm behavioral equivalence.
*   **Developer Confidence & Risk Assessment:** If step-level tests are thorough, regression tests are robust, and the developer assesses the risk of integration issues within the phase as very low.

**Goal:** The Phase Verification Script should provide confidence that the primary objectives of the phase are met from an integration perspective, complementing finer-grained unit tests.

---

**Appendix D: Example Security Checklist (Step-Level)** (Updated/Refined)

This checklist is intended for use during the **Step-Level Verification** by the developer. It's not exhaustive but covers common Django-specific concerns.

**For each relevant code change (Models, Views, Forms, Templates):**

**D.1. Input Validation & Sanitization:**
    - [ ] **Forms:** Are all user-supplied inputs validated by Django Forms or model validation?
    - [ ] **Model Fields:** Are appropriate `validators`, `max_length`, `choices`, etc., used on model fields?
    - [ ] **Query Parameters:** If using raw query parameters in views, are they validated/cast appropriately before use (especially in DB queries to prevent injection if not using ORM safely)?
    - [ ] **Output Escaping (Templates):** Is `{% autoescape %}` on? Is `|safe` filter used judiciously and only on trusted content? (Django default is on, but good to be mindful).
    - [ ] **File Uploads:** If handling uploads, are file types, sizes, and names validated? (Consider `django-cleanup` or custom validation).

**D.2. Authentication & Authorization:**
    - [ ] **Protected Views:** Are views that require login protected with `@login_required`, `LoginRequiredMixin`, or equivalent permission checks (`@permission_required`, `PermissionRequiredMixin`, custom checks)?
    - [ ] **Object-Level Permissions:** For views modifying specific objects, are checks in place to ensure the logged-in user *owns* or *has permission* to modify/delete that specific object (not just any object of that type)?
    - [ ] **CSRF Protection:** Are forms submitted via POST using the `{% csrf_token %}` template tag? (Django default, but verify). Are AJAX POSTs handling CSRF tokens correctly?
    - [ ] **Password Management:** Using Django's built-in password hashing? Not storing plain-text passwords?

**D.3. ORM & Database:**
    - [ ] **QuerySet Usage:** Primarily using Django ORM methods (which handle SQL injection prevention)?
    - [ ] **Raw SQL:** If raw SQL (`.raw()`, `cursor.execute()`) is used, are queries properly parameterized to prevent SQL injection?
    - [ ] **Migrations:** Are migrations reviewed for unintended data loss or problematic operations before applying to production?

**D.4. Session Management:**
    - [ ] **Sensitive Data in Session:** Avoid storing highly sensitive data directly in sessions if possible. If necessary, ensure it's minimized and cleared appropriately.
    - [ ] **Session Fixation:** (Generally handled by Django, but be aware if customizing session handling).

**D.5. Error Handling & Information Disclosure:**
    - [ ] **DEBUG Mode:** Is `DEBUG = False` in production settings?
    - [ ] **Sensitive Info in Errors:** Do production error pages/logs avoid leaking sensitive configuration details, internal paths, or user data?

**D.6. Third-Party Packages:**
    - [ ] **Package Security:** Are third-party packages kept up-to-date to patch known vulnerabilities? (Use tools like `piprot` or `safety`).
    - [ ] **Package Trust:** Are packages sourced from reputable locations?

**D.7. HTTPS:**
    - [ ] **Production Deployment:** Is HTTPS enforced in production (via web server/load balancer config)?
    - [ ] **Secure Cookies:** Are `SESSION_COOKIE_SECURE` and `CSRF_COOKIE_SECURE` set to `True` in production settings?

**D.8. Admin Security:**
    - [ ] **Admin URL:** Consider changing the default `/admin/` URL.
    - [ ] **Strong Admin Passwords:** Enforce strong passwords for admin users.
    - [ ] **Limit Admin Access:** Restrict admin access by IP if feasible and appropriate.

**Note:** This checklist complements, but does not replace, thorough security reviews or penetration testing for critical applications.

---

**Appendix E: Example CI/CD Snippet (GitHub Actions)** (Reinforces automated checks)

This example shows a basic GitHub Actions workflow to run linters, Django checks, and tests on each push.

```yaml
# .github/workflows/django_ci.yml
name: Django CI

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      max-parallel: 4
      matrix:
        python-version: [3.9, "3.10", "3.11"] # Or your supported Python versions

    services:
      postgres: # Example: Add a PostgreSQL service if your tests need it
        image: postgres:13
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install Dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt # Or requirements_dev.txt
        # Install any system dependencies if needed, e.g., for Pillow or psycopg2
        # sudo apt-get update && sudo apt-get install -y libpq-dev gcc

    - name: Lint with Flake8
      run: |
        pip install flake8
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

    - name: Run Django System Checks
      run: |
        python manage.py check

    - name: Run Tests with Pytest
      env: # Set environment variables for tests if needed
        DATABASE_URL: "postgres://test_user:test_password@localhost:5432/test_db"
        SECRET_KEY: "ci_secret_key_for_testing"
        DEBUG: "False"
        # Add other necessary environment variables
      run: |
        pip install pytest pytest-django
        pytest
```

This CI/CD snippet helps automate some of the verification steps, ensuring consistency and early feedback.

---

## **Appendix F: Example - Extending an Existing App (Adding Image Uploads to Blog Posts)**

This appendix illustrates how the LGID framework is applied when extending an existing Django application. We'll assume a project already has a `blog` app with a `Post` model, and we want to add functionality for users to upload an image associated with each blog post.

### F.1. Snippet from `Project_Requirements.md` (New Phase for Extension)

```markdown
# Project Requirements: MyAwesomeWebApp

**Version:** 1.5 (Added Post Image Uploads)
**Date:** 2025-05-09

## ... (Previous sections and phases exist) ...

---

### Phase 7: Post Image Uploads (NEW FEATURE - Blog App Extension)

- **Objective:** Enhance the existing `blog` app to allow authenticated users to upload a single representative image for each `Post`. This image should be displayed on the post's detail page and optionally as a thumbnail on the post list.
- **Requirements:**
  - `7.a`: **Model Update (`blog/models.py`):** Add an `ImageField` named `post_image` to the existing `Post` model. This field should be optional (allow `null=True`, `blank=True`). Configure necessary `upload_to` path.
  - `7.b`: **Media Configuration (`settings.py`):** Ensure `MEDIA_URL` and `MEDIA_ROOT` are correctly configured in project settings to serve uploaded images.
  - `7.c`: **Form Update (`blog/forms.py`):** Update any existing `PostForm` (used for creating/editing posts) to include the `post_image` field. Ensure the form's `enctype` is set to `"multipart/form-data"` where it's rendered.
  - `7.d`: **View Logic (`blog/views.py`):** Modify existing `PostCreateView` and `PostUpdateView` (or equivalent functional views) to handle image file uploads and save them with the `Post` instance.
  - `7.e`: **Template Updates (`blog/templates/blog/`):**
    -   Modify `post_detail.html` to display the `post_image` if one exists for the post.
    -   (Optional) Modify `post_list.html` (or item snippet) to display a thumbnail of `post_image` if it exists.
    -   Ensure post creation/update form templates correctly set `enctype="multipart/form-data"`.
  - `7.f`: **Admin Integration (`blog/admin.py`):** Update `PostAdmin` to display the `post_image` (e.g., as a read-only field showing a thumbnail or link) in the admin interface.
  - `7.g`: **Verification:** Ensure that posts can be created/edited with or without an image. Verify image display and graceful degradation if no image is present. Basic image validation (e.g., via `django-imagekit` or simple form validation for file type/size) is desirable but can be a follow-up refinement if not initially included.

---
## ... (Other phases may follow) ...
```

### F.2. Corresponding `Iteration_Guide.md` (Standard Template Example)

```markdown
# Iteration Guide: Blog App - Post Image Uploads

**Scope:** Implementing Phase 7: Post Image Uploads for the `blog` app.
**Template:** Standard Iteration Guide (LGID v2.1)
**Current Date:** 2025-05-09
**Overall Status:** Phase 7 Planned

---
---

## Phase 7: Post Image Uploads

**Version:** 1.0
**Date:** 2025-05-09
**Phase Objective:** Enhance the `blog` app to allow users to upload an image for each `Post`, displayed on detail/list pages.
**Related Requirements:** 7.a, 7.b, 7.c, 7.d, 7.e, 7.f, 7.g
**Phase Status:** Planned 📝

---

### Implementation Steps

#### Step 7.1: Update `Post` Model and Configure Media Settings

*   **Objective(s) (from `Project_Requirements.md`):** Req 7.a, Req 7.b
*   **Key Tasks:**
    ```
    <!-- Annotation: Key Tasks are high-level summaries.
         The developer will handle Pillow installation if needed,
         specific upload_to logic, and detailed settings. -->
    ```
    1.  Add `ImageField` (`post_image`) to `Post` model in `blog/models.py` (optional, define `upload_to`).
    2.  Ensure `MEDIA_URL` and `MEDIA_ROOT` are defined in `settings.py`.
    3.  Generate and apply database migrations for the `blog` app.
*   **Deliverables:**
    *   Updated `blog/models.py`.
    *   Updated `settings.py` (if `MEDIA_URL`/`MEDIA_ROOT` were not already set).
    *   New migration file(s) in `blog/migrations/`.
*   **Verification Checklist:**
    ```
    <!-- Annotation: Verification goals, not scripts. Developer performs checks. -->
    ```
    -   `[ ]` `python manage.py check` passes.
    -   `[ ]` `python manage.py makemigrations blog` and `migrate` run successfully.
    -   `[ ]` `post_image` field visible in `Post` model via shell or DB inspection.
    -   `[ ]` **Unit Test:** (Optional) Basic test in `test_models.py` confirming `post_image` field exists.
*   **Status:** To Do ⏳
*   **Commit(s):**

#### Step 7.2: Update `PostForm` and Form Rendering Templates

*   **Objective(s) (from `Project_Requirements.md`):** Req 7.c
*   **Key Tasks:**
    1.  Modify `PostForm` in `blog/forms.py` to include the `post_image` field.
    2.  Ensure templates rendering this form (e.g., `post_form.html`) have `enctype="multipart/form-data"` on the `<form>` tag.
*   **Deliverables:**
    *   Updated `blog/forms.py`.
    *   Updated relevant form-rendering templates (e.g., `blog/templates/blog/post_form.html`).
*   **Verification Checklist:**
    -   `[ ]` `PostForm` renders the `post_image` file input field correctly.
    -   `[ ]` Form tag in template includes correct `enctype`.
    -   `[ ]` **Unit Test:** (Optional) Test in `test_forms.py` that `post_image` is a field in `PostForm`.
*   **Status:** To Do ⏳
*   **Commit(s):**

#### Step 7.3: Update View Logic for Image Handling

*   **Objective(s) (from `Project_Requirements.md`):** Req 7.d
*   **Key Tasks:**
    1.  Modify `PostCreateView` and `PostUpdateView` (or equivalent functions) in `blog/views.py` to correctly handle `request.FILES` for the `post_image`.
    2.  Ensure images are saved to the `Post` instance.
    3.  Handle cases where no image is uploaded (field is optional).
*   **Deliverables:**
    *   Updated `blog/views.py`.
*   **Verification Checklist:**
    -   `[ ]` **Manual E2E Check:** Create a new post with an image; image is saved and associated with the post.
    -   `[ ]` **Manual E2E Check:** Edit an existing post to add/change/remove an image.
    -   `[ ]` **Manual E2E Check:** Create/edit a post without an image; no errors occur.
    -   `[ ]` **Unit Tests:** Add/run tests in `test_views.py` mocking file uploads to verify view logic for create/update with and without image.
*   **Status:** To Do ⏳
*   **Commit(s):**

#### Step 7.4: Update Templates to Display Images

*   **Objective(s) (from `Project_Requirements.md`):** Req 7.e
*   **Key Tasks:**
    1.  Modify `blog/templates/blog/post_detail.html` to display `post.post_image.url` if an image exists.
    2.  (Optional) Modify `blog/templates/blog/post_list.html` (or item snippet) to display `post.post_image.url` (perhaps as a thumbnail).
    3.  Implement graceful display (e.g., placeholder or nothing) if `post.post_image` is not set.
*   **Deliverables:**
    *   Updated `blog/templates/blog/post_detail.html`.
    *   (Optional) Updated `blog/templates/blog/post_list.html` or `_post_item.html`.
*   **Verification Checklist:**
    -   `[ ]` **Manual E2E Check:** Uploaded image displays correctly on the post detail page.
    -   `[ ]` (If implemented) Image/thumbnail displays on post list page.
    -   `[ ]` No errors or broken image icons if a post has no image.
*   **Status:** To Do ⏳
*   **Commit(s):**

#### Step 7.5: Update Admin Interface

*   **Objective(s) (from `Project_Requirements.md`):** Req 7.f
*   **Key Tasks:**
    1.  Modify `PostAdmin` in `blog/admin.py` to include `post_image` in `list_display` (e.g., using a method to render a thumbnail) and/or `readonly_fields` on the change form.
*   **Deliverables:**
    *   Updated `blog/admin.py`.
*   **Verification Checklist:**
    -   `[ ]` **Manual Admin Check:** `post_image` is visible and displays appropriately (thumbnail/link) in the Django admin for `Post` objects.
    -   `[ ]` Admin interface remains functional for creating/editing posts.
*   **Status:** To Do ⏳
*   **Commit(s):**

#### Step 7.6: Phase 7 Verification & (Optional) Basic Validation

*   **Objective(s) (from `Project_Requirements.md`):** Req 7.g
*   **Key Tasks:**
    1.  Perform comprehensive end-to-end testing of the entire feature: create post with image, edit to change image, edit to remove image, view post with/without image on site and admin.
    2.  (Optional, per Req 7.g refinement) If implementing basic validation (e.g., file type/size), add relevant validators to the model field or form.
    3.  (Optional, per LGID) Decide if a `test_phase7_verification.py` script is warranted based on complexity. Document decision. If yes, create and run it.
*   **Deliverables:**
    *   (If validation added) Updated `blog/models.py` or `blog/forms.py`.
    *   (If created) `blog/tests/test_phase7_verification.py`.
*   **Verification Checklist:**
    -   `[ ]` All step-level verification checks passed.
    -   `[ ]` All relevant existing unit and integration tests for the `blog` app pass.
    -   `[ ]` **E2E Test:** Full user flow (create/edit/view post with/without image) works as expected.
    -   `[ ]` (If implemented) Basic image validation works (rejects invalid, accepts valid).
    -   `[ ]` (If created) Phase verification script passes.
*   **Status:** To Do ⏳
*   **Commit(s):**

---
```

This appendix provides a focused example. In a real project, the `Project_Requirements.md` would be more extensive, and the `Iteration_Guide.md` might use the Lean template for simpler phases or if the developer prefers less explicit tracking for certain tasks. The key is the clear link between upfront requirements and the planned iterative steps, with the Iteration Guide maintaining a high-level planning focus.