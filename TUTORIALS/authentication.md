Okay, let's walk through Django Authentication and Authorization step-by-step, assuming you're starting from scratch.

**Django Authentication & Authorization Tutorial**

**Goal:** Understand how to manage users (who they are) and control what they can do within your Django application.

**Core Concepts:**

1.  **Authentication (AuthN): "Who are you?"**
    *   This is the process of verifying a user's identity.
    *   Typically involves asking for credentials like a username and password.
    *   If the credentials match a known user, the system "authenticates" them, confirming they are who they claim to be.
    *   Think of it like showing your ID to a security guard.

2.  **Authorization (AuthZ): "What are you allowed to do?"**
    *   This happens *after* a user is authenticated.
    *   It's the process of determining if the identified user has permission to access a specific resource or perform a particular action.
    *   Examples: Can this user view this page? Can they edit this blog post? Can they access the admin section?
    *   Think of it like the security guard checking your ticket to see if you're allowed into the VIP section.

**Phase 1: The Starting Point - No Authentication**

Imagine your current quiz app (or any simple Django site). Right now, *anyone* can visit any URL you've defined (like `/quiz/1/` or `/`). There's no concept of logging in or different user types.

*   **URLs:** You have defined URL patterns in `urls.py`.
*   **Views:** Your views in `views.py` simply process requests and render templates, assuming every visitor is anonymous.
*   **Templates:** Your HTML templates might display content, but they don't change based on who is visiting.

This is perfectly fine for public content, but not for features like saving user-specific quiz results, having administrative areas, or personalized dashboards.

**Phase 2: Introducing Django's Built-in Auth System**

Django comes with a powerful, secure, and convenient authentication system built-in, located in `django.contrib.auth`. We almost always use this instead of reinventing the wheel.

**Benefits:**

*   Provides a `User` model out-of-the-box.
*   Includes views for common actions (login, logout, password management).
*   Handles password hashing securely.
*   Integrates with Django's admin interface.
*   Provides a robust permission system.

**Step 2.1: Setup - Enabling the Auth App**

For the auth system to work, you need to make sure it's properly configured in your project's settings.

1.  **Check `settings.py`:** Open `core/settings.py` (or your project's settings file).
2.  **`INSTALLED_APPS`:** Ensure these apps are listed (they usually are by default):
    ```python
    INSTALLED_APPS = [
        # ... other apps
        'django.contrib.admin',
        'django.contrib.auth', # <<< The core auth app
        'django.contrib.contenttypes', # <<< Needed by auth
        'django.contrib.sessions', # <<< Needed for login state
        'django.contrib.messages',
        'django.contrib.staticfiles',
        # Your apps
        'multi_choice_quiz',
        'pages',
        # ...
    ]
    ```
3.  **`MIDDLEWARE`:** Ensure these middleware classes are listed (order matters!):
    ```python
    MIDDLEWARE = [
        # ... other middleware
        'django.contrib.sessions.middleware.SessionMiddleware', # <<< Handles session data (login status)
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware', # <<< Adds the `user` object to requests
        'django.contrib.messages.middleware.MessageMiddleware',
        # ... other middleware
    ]
    ```
    *   `SessionMiddleware`: Manages session data across requests (how Django remembers you're logged in).
    *   `AuthenticationMiddleware`: Checks the session data and attaches the corresponding `User` object (or an `AnonymousUser` object) to every incoming `request` object, making `request.user` available in your views.

**Step 2.2: Creating the Database Tables**

The `django.contrib.auth` app defines several database models (like `User`, `Group`, `Permission`). You need to create the corresponding tables in your database.

1.  **Run Migrations:** Open your terminal, navigate to the `src` directory (where `manage.py` is), activate your virtual environment, and run:
    ```bash
    python manage.py migrate
    ```
2.  **What it does:** Django looks at all the `INSTALLED_APPS`, finds any database changes (migrations) that haven't been applied yet, and creates/updates the necessary tables in your `db.sqlite3` file (or your configured database). You'll see lines mentioning "Applying auth..." and "Applying contenttypes...".

Now your database has tables ready to store users, groups, and permissions.

**Step 2.3: The `User` Model**

Django provides a default `User` model (`django.contrib.auth.models.User`). It includes common fields like:

*   `username`: A unique identifier for login.
*   `password`: The user's password (stored securely hashed, not plain text!).
*   `email`: Email address.
*   `first_name`, `last_name`: Optional name fields.
*   `is_active`: Boolean. Inactive users cannot log in.
*   `is_staff`: Boolean. Users with this flag can access the Django admin interface.
*   `is_superuser`: Boolean. Users with this flag have *all* permissions, bypassing explicit permission checks.

**Step 2.4: Creating Your First User - The Superuser**

To manage your site (especially via the admin interface), you need an initial user account with full privileges.

1.  **Run `createsuperuser`:** In your terminal (in the `src` directory):
    ```bash
    python manage.py createsuperuser
    ```
2.  **Follow Prompts:** Django will ask you for:
    *   `Username`: Choose a username (e.g., `admin`).
    *   `Email address`: Enter an email.
    *   `Password`: Enter a strong password (it won't be shown as you type).
    *   `Password (again)`: Confirm the password.
3.  **Success:** If the passwords match, it will say "Superuser created successfully."

This creates a `User` record in your database with both `is_staff` and `is_superuser` set to `True`.

**Step 2.5: Logging into the Admin**

Now you can use the superuser account to access the powerful Django admin interface.

1.  **Start the Development Server:**
    ```bash
    python manage.py runserver
    ```
2.  **Go to Admin URL:** Open your web browser and navigate to `http://127.0.0.1:8000/admin/`.
3.  **Login:** Enter the username and password you just created for the superuser.
4.  **Explore:** You'll see the Django administration dashboard. You can already see sections for "Users" and "Groups" provided by `django.contrib.auth`. You can click on "Users" to see (and edit) the superuser account you created. You can also see the models you registered from your own apps (`multi_choice_quiz`, etc.).

**Phase 3: Basic Authentication in Your App (Login/Logout)**

Okay, you have a user in the database, but how do regular users log in and out through your actual site, not just the admin? Django provides default views and URL patterns for this.

**Step 3.1: Include Default Auth URLs**

You can quickly add functional login, logout, and password management URLs.

1.  **Edit Project `urls.py`:** Open `core/urls.py`.
2.  **Add `include`:** Import `include` from `django.urls` and add a line to include the default auth URLs, usually prefixed under `accounts/`.
    ```python
    # core/urls.py
    from django.contrib import admin
    from django.urls import path, include # Make sure include is imported

    urlpatterns = [
        path('admin/', admin.site.urls),
        path('quiz/', include('multi_choice_quiz.urls')),
        path('', include('pages.urls')),

        # Add this line for default auth views
        path('accounts/', include('django.contrib.auth.urls')),
    ]
    ```
3.  **What URLs are added?** This single line adds several URL patterns under `/accounts/`, including:
    *   `accounts/login/` [name='login']
    *   `accounts/logout/` [name='logout']
    *   `accounts/password_change/` [name='password_change']
    *   `accounts/password_change/done/` [name='password_change_done']
    *   `accounts/password_reset/` [name='password_reset']
    *   `accounts/password_reset/done/` [name='password_reset_done']
    *   `accounts/reset/<uidb64>/<token>/` [name='password_reset_confirm']
    *   `accounts/reset/done/` [name='password_reset_complete']

**Step 3.2: Create Basic Authentication Templates**

Django's default auth views expect certain templates to exist. If they don't, you'll get a `TemplateDoesNotExist` error. You need to create them.

1.  **Create Directory:** Inside your project's *main* templates directory (if you have one defined in `settings.TEMPLATES['DIRS']`) or inside an app's template directory (e.g., `pages/templates/`), create a new directory named `registration`.
    *   Example using `pages` app: `src/pages/templates/registration/`
2.  **Create `login.html`:** Inside the `registration` directory, create `login.html`. This is the template Django uses for the `accounts/login/` URL.
    ```html
    {# src/pages/templates/registration/login.html #}
    {% extends 'pages/base.html' %} {# Or your main base template #}

    {% block title %}Login{% endblock %}

    {% block content %}
      <div class="container mx-auto px-4 py-8 max-w-md">
        <h2 class="text-2xl font-bold text-center mb-6 text-text-secondary">Login</h2>

        {% if form.errors %}
          <p class="text-red-500 text-center mb-4">Your username and password didn't match. Please try again.</p>
        {% endif %}

        {% if next %}
          {% if user.is_authenticated %}
            <p class="text-yellow-500 text-center mb-4">Your account doesn't have access to this page. To proceed,
            please login with an account that has access.</p>
          {% else %}
            <p class="text-yellow-500 text-center mb-4">Please login to see this page.</p>
          {% endif %}
        {% endif %}

        <form method="post" action="{% url 'login' %}" class="bg-surface p-6 rounded-lg shadow-md border border-border space-y-4">
          {% csrf_token %} {# IMPORTANT Security Token #}

          <div>
              <label for="{{ form.username.id_for_label }}" class="block text-sm font-medium text-text-secondary mb-1">Username:</label>
              {{ form.username }}
          </div>
          <div>
              <label for="{{ form.password.id_for_label }}" class="block text-sm font-medium text-text-secondary mb-1">Password:</label>
              {{ form.password }}
          </div>

          <button type="submit" class="w-full bg-accent-primary hover:bg-accent-hover text-white font-bold py-2 px-4 rounded-lg transition-colors">
            Login
          </button>
          <input type="hidden" name="next" value="{{ next }}"> {# Handles redirect after login #}
        </form>

        {# Optional: Link to password reset page #}
        <p class="text-center mt-4 text-sm">
          <a href="{% url 'password_reset' %}" class="text-accent-heading hover:text-accent-primary">Lost password?</a>
        </p>
        {# Optional: Link to signup page if you have one #}
        <p class="text-center mt-2 text-sm text-text-muted">
            Don't have an account? <a href="{% url 'pages:signup' %}" class="text-accent-heading hover:text-accent-primary">Sign up</a>
        </p>
      </div>

      {# Add basic styling for form inputs if needed, or rely on Tailwind/base CSS #}
      <style>
          input[type="text"], input[type="password"] {
              display: block;
              width: 100%;
              padding: 0.75rem;
              border: 1px solid #475569; /* border */
              background-color: rgba(51, 65, 85, 0.4); /* tag-bg/40 */
              color: #E5E7EB; /* text-secondary */
              border-radius: 0.5rem; /* rounded-lg */
          }
          input[type="text"]:focus, input[type="password"]:focus {
              outline: none;
              border-color: #7C3AED; /* accent-primary */
              box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.3);
          }
      </style>
    {% endblock %}
    ```
    *   **Explanation:**
        *   It extends your base template.
        *   Uses `{{ form }}` which Django's login view automatically provides. This renders the username and password fields.
        *   Includes `{% csrf_token %}` which is essential security against Cross-Site Request Forgery attacks on POST requests.
        *   Handles potential form errors.
        *   Includes a hidden `next` field, which tells Django where to redirect the user after successful login (often used when protecting pages).
3.  **Create `logged_out.html` (Optional but Recommended):** Inside `registration`, create `logged_out.html`. This is where users are redirected after clicking logout.
    ```html
    {# src/pages/templates/registration/logged_out.html #}
    {% extends 'pages/base.html' %}

    {% block title %}Logged Out{% endblock %}

    {% block content %}
    <div class="container mx-auto px-4 py-8 text-center max-w-md">
        <h2 class="text-2xl font-bold mb-4 text-text-secondary">Logged Out</h2>
        <p class="text-text-primary mb-4">You have been successfully logged out.</p>
        <a href="{% url 'login' %}" class="bg-accent-primary hover:bg-accent-hover text-white font-bold py-2 px-4 rounded-lg transition-colors">Login again</a>
    </div>
    {% endblock %}
    ```
4.  **(Optional) Create Password Reset Templates:** You'd also need templates for password reset (`password_reset_form.html`, `password_reset_done.html`, `password_reset_confirm.html`, `password_reset_complete.html`) in the `registration` directory if you want that functionality.

**Step 3.3: Add Login/Logout Links to Base Template**

Now, modify your base template (`pages/templates/pages/base.html`) to show "Login" or "Logout" links depending on the user's status.

```html
{# src/pages/templates/pages/base.html - Snippet within header/nav #}

{# ... inside your nav element ... #}
<nav class="hidden md:flex items-center space-x-6">
    <a href="{% url 'pages:home' %}" class="text-text-secondary hover:text-accent-heading transition-colors">Home</a>
    <a href="{% url 'pages:quizzes' %}" class="text-text-secondary hover:text-accent-heading transition-colors">Quizzes</a>
    <a href="{% url 'pages:about' %}" class="text-text-secondary hover:text-accent-heading transition-colors">About</a>

    <div class="flex space-x-4 ml-6">
        {% if user.is_authenticated %}
            {# User is logged in #}
            <span class="text-text-secondary hidden lg:inline">Welcome, {{ user.username }}!</span>
             <a href="{% url 'pages:profile' %}" class="border border-border rounded-lg px-4 py-2 text-text-secondary hover:bg-tag-bg transition-colors">Profile</a>
            <form method="post" action="{% url 'logout' %}">
                {% csrf_token %}
                <button type="submit" class="bg-red-600 hover:bg-red-700 text-white rounded-lg px-4 py-2 transition-colors">Logout</button>
            </form>
        {% else %}
            {# User is logged out #}
            <a href="{% url 'login' %}" class="border border-border rounded-lg px-4 py-2 text-text-secondary hover:bg-tag-bg transition-colors">Login</a>
            <a href="{% url 'pages:signup' %}" class="bg-accent-primary hover:bg-accent-hover text-white rounded-lg px-4 py-2 transition-colors">Sign Up</a>
        {% endif %}
    </div>
</nav>
{# Remember to add similar logic for the mobile menu if you have one #}
```

*   **Explanation:**
    *   The `AuthenticationMiddleware` makes the `user` object available in templates.
    *   `{% if user.is_authenticated %}` checks if the current request belongs to a logged-in user.
    *   We show the username and a Logout button (which is a POST form for security) if logged in.
    *   We show Login and Sign Up links if logged out.

**Step 3.4: Test Login/Logout**

1.  **Run Server:** `python manage.py runserver`
2.  **Go to Home:** Visit `http://127.0.0.1:8000/`. You should see "Login" and "Sign Up".
3.  **Go to Login:** Click "Login" or go to `http://127.0.0.1:8000/accounts/login/`.
4.  **Login:** Enter your superuser credentials.
5.  **Redirect:** Upon successful login, Django, by default, redirects to `/accounts/profile/`. You probably haven't defined this URL yet (we used `/profile/` in the `pages` app). You can either:
    *   Create `/accounts/profile/` URL and view.
    *   **Or (Better):** Tell Django where to redirect after login by adding `LOGIN_REDIRECT_URL = '/'` (or `/quizzes/` or `/profile/`) to your `core/settings.py`. Let's redirect to the homepage:
        ```python
        # core/settings.py
        # ... other settings ...

        LOGIN_REDIRECT_URL = '/'
        LOGOUT_REDIRECT_URL = '/' # Optional: Where to go after logout (defaults to logged_out.html)
        ```
6.  **Verify Login:** After logging in (and adding `LOGIN_REDIRECT_URL`), you should be redirected to the homepage and see "Welcome, [your_username]!" and the "Logout" button in the header.
7.  **Logout:** Click the "Logout" button. You should be redirected to the homepage (or `/accounts/logged_out/` if you didn't set `LOGOUT_REDIRECT_URL`) and see the "Login" link again.

You now have basic user login and logout functionality!

**Phase 4: Basic Authorization - Controlling Access**

Now that users can log in, how do we restrict access?

**Step 4.1: Protecting Views with `login_required`**

The simplest form of authorization is requiring a user to be logged in to access a view.

1.  **Choose a View:** Let's protect the (currently placeholder) profile page (`pages/views.py`).
2.  **Import Decorator:** At the top of `pages/views.py`, add:
    ```python
    from django.contrib.auth.decorators import login_required
    ```
3.  **Apply Decorator:** Add `@login_required` directly above the view function definition:
    ```python
    # pages/views.py
    from django.shortcuts import render
    from django.contrib.auth.decorators import login_required # Import

    # ... other views ...

    @login_required # <<< Apply the decorator
    def profile_view(request):
        """Placeholder user profile page."""
        # Fetch user-specific data here later
        quiz_attempts = [] # Placeholder
        context = {'quiz_attempts': quiz_attempts}
        return render(request, "pages/profile.html", context)
    ```
4.  **How it Works:**
    *   If the user *is* logged in, the view executes normally.
    *   If the user is *not* logged in, Django automatically redirects them to the login page (`/accounts/login/` by default, configurable via `LOGIN_URL` in `settings.py`). It also adds a `?next=/profile/` parameter to the login URL, so after successful login, the user is sent back to the profile page they originally requested.

**Step 4.2: Checking User Status in Views/Templates**

You can conditionally show/hide content or perform different actions based on user attributes.

*   **In Templates:** (We already did this for Login/Logout links)
    ```html
    {% if user.is_authenticated %}
      <p>Welcome back!</p>
      {% if user.is_staff %}
        <a href="/admin/">Admin Panel</a>
      {% endif %}
    {% else %}
      <p>Please log in.</p>
    {% endif %}
    ```
*   **In Views:**
    ```python
    # pages/views.py
    from django.shortcuts import render
    from django.http import HttpResponseForbidden

    def some_admin_action_view(request):
        if not request.user.is_staff:
            # Option 1: Show a forbidden error
            # return HttpResponseForbidden("You do not have permission to view this.")
            # Option 2: Redirect them somewhere else
            # return redirect('pages:home')
            # Option 3: Render a specific "permission denied" template
            return render(request, 'pages/permission_denied.html', status=403)

        # --- Staff-only logic here ---
        # ... perform admin action ...
        return render(request, 'pages/admin_action_done.html')
    ```

**Step 4.3: Introduction to Permissions Framework**

For more fine-grained control than just `is_staff` or `is_superuser`, Django has a built-in permissions system.

1.  **Permissions are Auto-Created:** When you run `migrate`, Django automatically creates four default permissions for *each* model defined in your `INSTALLED_APPS` (unless customized):
    *   `add_<modelname>` (e.g., `multi_choice_quiz.add_quiz`)
    *   `change_<modelname>` (e.g., `multi_choice_quiz.change_quiz`)
    *   `delete_<modelname>` (e.g., `multi_choice_quiz.delete_quiz`)
    *   `view_<modelname>` (e.g., `multi_choice_quiz.view_quiz`)
2.  **Managing Permissions:**
    *   **Admin Interface:** The easiest way to manage permissions is via the Django Admin (`/admin/`).
    *   **Users:** Go to the "Users" section, select a user. Scroll down to the "Permissions" section. You can assign specific permissions directly to a user (e.g., give user 'bob' permission to `add_quiz`).
    *   **Groups:** It's usually better practice to assign permissions to **Groups** and then add users to those groups. Create groups (e.g., "Quiz Editors", "Content Moderators") in the "Groups" section of the admin, assign the relevant permissions to the group, and then assign users to that group.
3.  **Checking Permissions:**
    *   **In Views:** Use the `request.user.has_perm()` method:
        ```python
        # multi_choice_quiz/views.py
        from django.contrib.auth.decorators import permission_required

        # Option 1: Use a decorator (redirects to login if check fails)
        @permission_required('multi_choice_quiz.add_question', raise_exception=False)
        def add_question_view(request, quiz_id):
            # ... view logic to add a question ...
            pass

        # Option 2: Check manually within the view
        def edit_quiz_view(request, quiz_id):
            quiz = get_object_or_404(Quiz, pk=quiz_id)
            if not request.user.has_perm('multi_choice_quiz.change_quiz', quiz): # Can optionally check obj permission
                return HttpResponseForbidden("You cannot edit this quiz.")
            # ... view logic to edit the quiz ...
            pass
        ```
        *Note: `permission_required` decorator often needs `LoginRequiredMixin` or `@login_required` as well.*
    *   **In Templates:** Use the `{{ perms }}` object (requires `django.contrib.auth.context_processors.auth` in `settings.TEMPLATES['OPTIONS']['context_processors']`, which is default):
        ```html
        {% if perms.multi_choice_quiz.add_question %}
          <a href="{% url 'multi_choice_quiz:add_question' quiz.id %}">Add New Question</a>
        {% endif %}

        {% if perms.multi_choice_quiz.change_quiz %}
          <a href="{% url 'multi_choice_quiz:edit_quiz' quiz.id %}">Edit Quiz</a>
        {% endif %}
        ```

**Summary & Where We Are**

*   You started with no user concept.
*   You enabled Django's `auth` app and created database tables (`migrate`).
*   You created an initial admin user (`createsuperuser`).
*   You included default URLs and templates for basic login/logout.
*   You learned how to protect views using `@login_required`.
*   You saw how to check user status (`is_authenticated`, `is_staff`) in views and templates.
*   You were introduced to Django's more powerful Groups and Permissions system for fine-grained authorization, manageable via the Admin and checkable via `has_perm`.

**Next Steps (Beyond this Tutorial):**

*   **Custom Login/Signup Templates:** Style the `registration/login.html` (and other auth templates) using your Tailwind CSS from the `pages` app to match the site's look and feel.
*   **Signup View:** Create a view and template (`pages/signup.html`) that actually processes user registration (creates new `User` objects).
*   **Password Reset:** Implement the password reset flow templates.
*   **Custom User Model:** If the default `User` model isn't sufficient (e.g., you want users to log in with email instead of username), you can create a custom User model (more advanced topic).
*   **Object-Level Permissions:** Explore libraries like `django-guardian` if you need permissions specific to individual database objects (e.g., "User Bob can edit *this specific* quiz, but not that one").

This tutorial covers the fundamentals provided by Django itself. You now have the tools to manage user identity and control access within your application. Remember to prioritize security, especially around password handling (which Django helps with) and protecting sensitive views/actions.