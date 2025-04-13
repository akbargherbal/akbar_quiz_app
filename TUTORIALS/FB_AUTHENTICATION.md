Okay, let's elevate this Django Authentication and Authorization tutorial based on the principles of clarity, progressive building, mental models, and practical application.

**Target Audience:** Beginners to Django who understand basic views, templates, URLs, models, and migrations, but have little to no experience with user management.

**Rewritten Tutorial: Mastering Django Authentication & Authorization**

**Introduction: Why User Management Matters**

Imagine a website – maybe a blog, an e-commerce store, or our quiz application. Some content might be public (like a blog post or a product listing), but often we need more:

- **Personalization:** Showing a user _their_ quiz history or _their_ shopping cart.
- **Security:** Protecting sensitive data or administrative areas.
- **Roles & Permissions:** Allowing certain users (editors, admins) to perform actions others cannot (writing posts, managing products).

This is where **Authentication** (Who are you?) and **Authorization** (What can you do?) become essential. Django provides a robust, secure, and highly recommended built-in system to handle this, saving you from reinventing a complex and critical wheel.

**Our Goal:** To progressively build user management into a Django application, starting with nothing and ending with a functional login, logout, signup, and permission-controlled system.

---

**Part 1: Understanding the Core Concepts (AuthN vs. AuthZ)**

Before touching any code, let's solidify the two key ideas:

1.  **Authentication (AuthN): Verifying Identity ("Who are you?")**

    - **Concept:** The process of proving you are who you claim to be.
    - **Mechanism:** Typically involves providing credentials (like a username and password) that the system checks against its records.
    - **Analogy:** Showing your driver's license (credential) to a security guard (system) to prove your identity matches the name on their list. If it matches, you are _authenticated_.
    - **Django Context:** Django checks provided credentials against the `User` model in the database.

2.  **Authorization (AuthZ): Granting Permissions ("What can you do?")**
    - **Concept:** The process of determining if an _already authenticated_ user has the right to access a specific resource or perform a specific action. This happens _after_ successful authentication.
    - **Mechanism:** The system checks the authenticated user's assigned permissions or roles against the requirements of the requested resource/action.
    - **Analogy:** After the guard confirms your identity (authentication), they check your ticket (permissions/role) to see if you have access to the VIP lounge (resource/action). Just because you're authenticated doesn't mean you can go everywhere!
    - **Django Context:** Django checks flags like `is_staff`, `is_superuser`, or specific assigned permissions associated with the `request.user` object.

**Key Takeaway:** You must be **authenticated** _before_ the system can determine if you are **authorized**.

---

**Part 2: Laying the Groundwork - Setting Up Django's Auth System**

Our starting point is a basic Django project (like our quiz app) where anyone can access any defined URL. Let's integrate Django's built-in auth capabilities.

**Why Use Django's Built-in System?**

- **Security:** Handles password hashing, session security, and CSRF protection correctly (hard things to get right!).
- **Completeness:** Provides models, views, forms, and middleware for common tasks (login, logout, password management).
- **Integration:** Seamlessly works with the Django admin and other parts of the framework.
- **Maintainability:** Leverages well-tested, community-vetted code.

**Step 2.1: Verify Project Configuration (`settings.py`)**

Django projects created with `startproject` usually have the necessary settings, but let's verify and understand them. Open your project's `settings.py` (e.g., `core/settings.py`).

1.  **`INSTALLED_APPS`:** Ensure these are present. They enable the core features:

    ```python
    # core/settings.py
    INSTALLED_APPS = [
        # ... other core apps
        'django.contrib.admin',         # The admin interface (uses auth)
        'django.contrib.auth',          # <<< Core authentication framework (models, backends)
        'django.contrib.contenttypes',  # <<< Framework for associating models (used by auth permissions)
        'django.contrib.sessions',      # <<< Manages user sessions (how login state persists)
        'django.contrib.messages',      # Feedback messages (e.g., "Login successful")
        'django.contrib.staticfiles',
        # Your apps (e.g., 'multi_choice_quiz', 'pages')
        # ...
    ]
    ```

    - **`django.contrib.auth`**: Provides the `User` model, permission system, and authentication backend logic.
    - **`django.contrib.contenttypes`**: Allows permissions to be associated generically with any model.
    - **`django.contrib.sessions`**: Handles storing a user's logged-in status between requests using cookies and server-side storage.

2.  **`MIDDLEWARE`:** The order is important here! Middleware processes requests and responses sequentially.
    ```python
    # core/settings.py
    MIDDLEWARE = [
        # ... other middleware like SecurityMiddleware ...
        'django.contrib.sessions.middleware.SessionMiddleware',      # <<< Reads/writes session data (MUST be before Auth)
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',               # Protects against Cross-Site Request Forgery
        'django.contrib.auth.middleware.AuthenticationMiddleware', # <<< Associates user with request (MUST be after Session)
        'django.contrib.messages.middleware.MessageMiddleware',    # Enables displaying messages
        # ... other middleware like XFrameOptionsMiddleware ...
    ]
    ```
    - **`SessionMiddleware`**: When a request comes in, it looks for a session cookie. If found, it retrieves the corresponding session data from the database (or configured session store). When the response goes out, it saves any changes to the session and sets the session cookie.
    - **`AuthenticationMiddleware`**: _After_ `SessionMiddleware` has loaded the session data, this middleware looks for authentication information within that data (e.g., a user ID). If found, it fetches the corresponding `User` object from the database and attaches it to the incoming `request` object as `request.user`. If no authentication data is found (or the user is invalid), it attaches a special `AnonymousUser` object. This makes `request.user` available in _all_ your views.

**Mental Model: Request Flow with Auth Middleware**

```
Browser Request --> Django Server
    |
    V
SessionMiddleware: Reads session cookie, loads session data (e.g., {'_auth_user_id': '5'})
    |
    V
AuthenticationMiddleware: Sees '_auth_user_id' in session, fetches User(id=5), sets request.user = User(id=5)
    |
    V
Your View: Can now access request.user (the logged-in user object)
    |
    V
Response Generation
    |
    V
SessionMiddleware: Saves any session changes, sets session cookie
    |
    V
Browser Response <-- Django Server
```

**Step 2.2: Create Database Tables (`migrate`)**

The auth app (and contenttypes, sessions) define database models (`User`, `Group`, `Permission`, `Session`, etc.). We need to create the corresponding tables.

1.  **Navigate:** Open your terminal in the directory containing `manage.py`.
2.  **Activate Environment:** Ensure your virtual environment is active.
3.  **Run Migrate:**
    ```bash
    python manage.py migrate
    ```
4.  **Output:** You'll see Django applying migrations, including lines for `auth`, `contenttypes`, and `sessions`. This creates/updates tables in your database (e.g., `db.sqlite3`).

**Step 2.3: Understanding the `User` Model**

Django's built-in `User` model (`django.contrib.auth.models.User`) is now available. Key fields include:

- `username`: Unique identifier used for login (required).
- `password`: The user's password. **Crucially, Django does _not_ store this as plain text.** It stores a secure _hash_ of the password. When a user logs in, Django hashes the provided password and compares it to the stored hash.
- `email`: Email address (optional by default, but often made required).
- `first_name`, `last_name`: Optional.
- `is_active`: Boolean. If `False`, the user account exists but cannot log in. Useful for disabling accounts without deleting them.
- `is_staff`: Boolean. Grants access to the Django admin interface.
- `is_superuser`: Boolean. A powerful flag granting _all_ permissions automatically, bypassing normal permission checks. Use with caution!

---

**Part 3: The Admin & Your First User**

To manage users and permissions initially, we need a "superuser" account.

**Step 3.1: Create a Superuser**

1.  **Run Command:** In your terminal (same place as `manage.py`):
    ```bash
    python manage.py createsuperuser
    ```
2.  **Follow Prompts:** Provide a username, email (optional here, but good practice), and a strong password.
3.  **Result:** This creates a `User` instance in your database with `is_active=True`, `is_staff=True`, and `is_superuser=True`.

**Step 3.2: Explore the Django Admin**

The admin interface is a powerful tool, especially for managing auth.

1.  **Run Server:** `python manage.py runserver`
2.  **Access Admin:** Open `http://127.0.0.1:8000/admin/` in your browser.
3.  **Login:** Use the superuser credentials you just created.
4.  **Explore:**
    - You'll see an "AUTHENTICATION AND AUTHORIZATION" section.
    - Click on "Users": You can see your superuser account. Click on it to view/edit details, including permissions (`is_staff`, `is_superuser`, and fine-grained permissions we'll see later).
    - Click on "Groups": Groups are used to manage permissions for multiple users efficiently (more on this later).

The admin provides a ready-made interface for managing the `User` and related models provided by `django.contrib.auth`.

---

**Part 4: Enabling User Login and Logout on Your Site**

The admin login is separate. How do regular users log in and out via the main website interface? Django provides built-in views and URLs.

**Step 4.1: Include Default Auth URLs**

We can add a whole set of authentication-related URL patterns with one line.

1.  **Edit Project `urls.py`:** Open your main `core/urls.py` (or equivalent).
2.  **Add `include`:**

    ```python
    # core/urls.py
    from django.contrib import admin
    from django.urls import path, include # Ensure include is imported

    urlpatterns = [
        path('admin/', admin.site.urls),
        path('quiz/', include('multi_choice_quiz.urls')), # Example app
        path('', include('pages.urls')),             # Example app

        # Add this line for default auth views
        path('accounts/', include('django.contrib.auth.urls')),
        # This convention ('accounts/') is common, but you can choose another path.
    ]
    ```

3.  **What this does:** It maps URLs starting with `/accounts/` to Django's pre-built views for:
    - `accounts/login/` (Login view)
    - `accounts/logout/` (Logout view)
    - `accounts/password_change/`, `.../done/`
    - `accounts/password_reset/`, `.../done/`, `.../confirm/...`, `.../complete/`
    - These views handle the logic (checking passwords, updating session data, etc.).

**Step 4.2: Create Required Templates**

Django's default views need corresponding templates to render the forms and messages. If these templates aren't found, you'll get a `TemplateDoesNotExist` error.

1.  **Template Directory:** Django looks for templates in directories specified in `settings.TEMPLATES['DIRS']` and within `templates` subdirectories of each app in `INSTALLED_APPS`. A common practice is to have a project-level `templates` directory. Inside that directory (or an app's `templates` directory), create a folder named `registration`. The auth views specifically look inside a `registration/` folder.

    - Example: `src/templates/registration/` (if `BASE_DIR / 'templates'` is in `settings.TEMPLATES['DIRS']`).
    - Alternative: `src/pages/templates/registration/` (if using app directories). Choose one location. Let's assume `src/templates/registration/`.

2.  **Create `login.html`:** This is the most crucial one.

    ```html
    {# src/templates/registration/login.html #} {% extends 'pages/base.html' %}
    {# Or your project's base template #} {% block title %}Login{% endblock %}
    {% block content %}
    <div class="container mx-auto px-4 py-8 max-w-md">
      <h2 class="text-2xl font-bold text-center mb-6 text-text-secondary">
        Login
      </h2>

      {# Display generic form errors (e.g., incorrect credentials) #} {% if
      form.non_field_errors %}
      <div
        class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4"
        role="alert"
      >
        {% for error in form.non_field_errors %}
        <p>{{ error }}</p>
        {% endfor %}
      </div>
      {% endif %} {# Display message about needing to log in #} {% if next %} {%
      if user.is_authenticated %}
      <p class="text-yellow-600 text-center mb-4">
        Your account doesn't have access to this page. Please log in with an
        account that has access.
      </p>
      {% else %}
      <p class="text-yellow-600 text-center mb-4">
        Please log in to view this page.
      </p>
      {% endif %} {% endif %}

      <form
        method="post"
        action="{% url 'login' %}"
        class="bg-surface p-6 rounded-lg shadow-md border border-border space-y-4"
      >
        {% csrf_token %} {# **CRITICAL:** Prevents Cross-Site Request Forgery
        attacks #} {# Render form fields manually or using {{ form.as_p }} / {{
        form.as_ul }} / {{ form.as_table }} #}
        <div class="mb-4">
          <label
            for="{{ form.username.id_for_label }}"
            class="block text-sm font-medium text-text-secondary mb-1"
            >Username:</label
          >
          <input
            type="text"
            name="{{ form.username.name }}"
            id="{{ form.username.id_for_label }}"
            required
            class="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-accent-primary focus:border-accent-primary bg-input-bg text-text-primary"
            value="{{ form.username.value|default:'' }}"
          />
          {% if form.username.errors %}
          <div class="text-red-500 text-xs mt-1">
            {% for error in form.username.errors %}{{ error }}{% endfor %}
          </div>
          {% endif %}
        </div>

        <div class="mb-4">
          <label
            for="{{ form.password.id_for_label }}"
            class="block text-sm font-medium text-text-secondary mb-1"
            >Password:</label
          >
          <input
            type="password"
            name="{{ form.password.name }}"
            id="{{ form.password.id_for_label }}"
            required
            class="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-accent-primary focus:border-accent-primary bg-input-bg text-text-primary"
          />
          {% if form.password.errors %}
          <div class="text-red-500 text-xs mt-1">
            {% for error in form.password.errors %}{{ error }}{% endfor %}
          </div>
          {% endif %}
        </div>

        <button
          type="submit"
          class="w-full bg-accent-primary hover:bg-accent-hover text-white font-bold py-2 px-4 rounded-lg transition-colors"
        >
          Login
        </button>

        {# Hidden field to redirect user back to the page they were trying to
        access #}
        <input type="hidden" name="next" value="{{ next }}" />
      </form>

      <p class="text-center mt-4 text-sm">
        <a
          href="{% url 'password_reset' %}"
          class="text-accent-heading hover:text-accent-primary"
          >Lost password?</a
        >
      </p>
      <p class="text-center mt-2 text-sm text-text-muted">
        Don't have an account?
        <a
          href="{% url 'signup' %}"
          class="text-accent-heading hover:text-accent-primary"
          >Sign up</a
        >
        {# We'll create this URL later #}
      </p>
    </div>
    {% endblock %}
    ```

    - **Key Elements:**
      - `{% extends ... %}`: Inherits your site's base layout.
      - `{% csrf_token %}`: Essential security token for any POST form. It prevents malicious sites from tricking your users into submitting data to your site unknowingly.
      - `form.non_field_errors`, `form.username.errors`, `form.password.errors`: Django's `AuthenticationForm` (used by the login view) automatically provides error messages here if login fails or input is invalid.
      - `action="{% url 'login' %}"`: Submits the form back to the named URL for the login view.
      - `{{ form.username }}`, `{{ form.password }}`: These are rendered input fields provided by the form object passed from the view to the template context. We rendered them manually here for better styling control, but `{{ form.as_p }}` is simpler.
      - `{{ next }}`: If the user was redirected _to_ the login page from a protected page, this hidden input ensures they are sent _back_ to that original page (`/profile/`, for example) after successful login.

3.  **Create `logged_out.html`:** Displayed after successful logout.

    ```html
    {# src/templates/registration/logged_out.html #} {% extends
    'pages/base.html' %} {% block title %}Logged Out{% endblock %} {% block
    content %}
    <div class="container mx-auto px-4 py-8 text-center max-w-md">
      <h2 class="text-2xl font-bold mb-4 text-text-secondary">Logged Out</h2>
      <p class="text-text-primary mb-4">
        You have been successfully logged out.
      </p>
      <a
        href="{% url 'login' %}"
        class="inline-block bg-accent-primary hover:bg-accent-hover text-white font-bold py-2 px-4 rounded-lg transition-colors"
        >Login again</a
      >
    </div>
    {% endblock %}
    ```

4.  **(Optional but Recommended) Password Reset Templates:** For the password reset functionality (URLs included above) to work, you'd need to create these templates inside `registration/`:
    - `password_reset_form.html` (Form to enter email)
    - `password_reset_done.html` (Confirmation email has been sent)
    - `password_reset_email.html` (The content of the email itself - plain text)
    - `password_reset_subject.txt` (Subject line for the email - plain text)
    - `password_reset_confirm.html` (Form to enter new password after clicking email link)
    - `password_reset_complete.html` (Confirmation password has been changed)
      _(We won't detail these here, but know they are needed for that feature)._

**Step 4.3: Configure Login/Logout Redirects**

By default, after login, Django redirects to `/accounts/profile/`. After logout, it shows the `logged_out.html` template. We often want to customize this.

1.  **Edit `settings.py`:** Add these variables at the bottom:

    ```python
    # core/settings.py
    # ... other settings ...

    LOGIN_REDIRECT_URL = '/'  # Or '/dashboard/', '/profile/' - Where to go after successful login
    LOGOUT_REDIRECT_URL = '/' # Optional: Where to go after clicking logout (instead of showing logged_out.html)
    LOGIN_URL = '/accounts/login/' # The URL name of the login page itself (default is usually fine)
    ```

    - `LOGIN_REDIRECT_URL`: Crucial for user experience. Send users to a meaningful page after they log in.
    - `LOGOUT_REDIRECT_URL`: Often set to the homepage for simplicity. If not set, Django renders `registration/logged_out.html`.
    - `LOGIN_URL`: Tells decorators like `@login_required` where to send unauthenticated users.

**Step 4.4: Add Conditional Links in Base Template**

Modify your base template (`pages/base.html` or equivalent) to show dynamic links based on authentication status.

```html
{# src/templates/pages/base.html - Example Navbar Snippet #}
<nav class="{# ... your navbar styles ... #}">
  {# ... other nav links like Home, About ... #}
  <a href="{% url 'pages:home' %}" class="...">Home</a>
  <a href="{% url 'pages:quizzes' %}" class="...">Quizzes</a>

  <div class="ml-auto flex items-center space-x-4">
    {% if user.is_authenticated %} {# User is logged in #}
    <span class="text-text-secondary hidden lg:inline"
      >Hi, {{ user.username }}!</span
    >
    {# Link to a profile page (we'll make this require login later) #}
    <a href="{% url 'pages:profile' %}" class="...">Profile</a>

    {# Logout MUST be a POST request for security (prevents CSRF) #}
    <form method="post" action="{% url 'logout' %}" class="inline">
      {% csrf_token %}
      <button type="submit" class="bg-red-600 hover:bg-red-700 ...">
        Logout
      </button>
    </form>
    {% else %} {# User is logged out #}
    <a href="{% url 'login' %}" class="...">Login</a>
    {# Link to a signup page (we'll create this next) #}
    <a href="{% url 'signup' %}" class="bg-accent-primary ...">Sign Up</a>
    {% endif %}
  </div>
</nav>
{# Apply similar logic to mobile menu if applicable #}
```

- **`user.is_authenticated`**: This boolean attribute (made available by `AuthenticationMiddleware`) is the key. It's `True` for logged-in users (instances of the `User` model) and `False` for anonymous users (`AnonymousUser` instance).
- **Logout Form:** Notice logout is a mini-form with `method="post"` and `{% csrf_token %}`. This is crucial. A simple `<a>` link for logout is insecure, as malicious sites could potentially trigger a logout action on your site without the user's intent (CSRF attack).

**Step 4.5: Test the Login/Logout Flow**

1.  **Run Server:** `python manage.py runserver`
2.  **Visit Site:** Go to `http://127.0.0.1:8000/`. You should see "Login" and "Sign Up" links. `request.user` is currently `AnonymousUser`.
3.  **Go to Login:** Click "Login" (navigates to `/accounts/login/`).
4.  **Attempt Login:** Enter your _superuser_ credentials.
5.  **Redirect & Verify:** You should be redirected to the `LOGIN_REDIRECT_URL` (e.g., the homepage `/`). The navbar should now show "Hi, [superuser_username]!", "Profile", and "Logout". `request.user` is now the `User` object for your superuser.
6.  **Attempt Invalid Login:** Log out first. Go back to Login. Enter incorrect credentials. The page should reload with an error message ("Please enter a correct username and password...").
7.  **Logout:** Click the "Logout" button. The `form` POSTs to `/accounts/logout/`.
8.  **Redirect & Verify:** You should be redirected to `LOGOUT_REDIRECT_URL` (e.g., the homepage `/`). The navbar should revert to showing "Login" and "Sign Up". `request.user` is `AnonymousUser` again.

You now have a working login/logout system using Django's built-in components!

---

**Part 5: User Registration (Signup) - Allowing New Users**

We need a way for _new_ users (not just admins) to create accounts. Django doesn't provide a default signup _view_, but it gives us the tools to build one easily.

**Step 5.1: Create a Signup Form**

Django provides a helpful built-in form for user creation.

1.  **Create `forms.py`:** In your `pages` app (or a dedicated `users` app if you prefer), create a `forms.py` file.
2.  **Define the Form:**

    ```python
    # src/pages/forms.py
    from django import forms
    from django.contrib.auth.forms import UserCreationForm
    from django.contrib.auth.models import User # Or your custom user model if you have one

    class SignUpForm(UserCreationForm):
        email = forms.EmailField(max_length=254, required=True, help_text='Required. Inform a valid email address.')
        first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
        last_name = forms.CharField(max_length=150, required=False, help_text='Optional.')

        class Meta(UserCreationForm.Meta):
            model = User # Specify the model it works with
            fields = ('username', 'email', 'first_name', 'last_name') # Fields to include on the form
            # Note: Password fields are handled automatically by UserCreationForm
    ```

    - **`UserCreationForm`**: This base class handles the complexity of creating a user, including password validation and hashing.
    - **Custom Fields:** We explicitly add `email`, `first_name`, `last_name` to make them part of the form and potentially require them (like `email`).
    - **`Meta` class:** We tell the form which model to use (`User`) and which fields _from that model_ should be displayed and processed (in addition to the password fields provided by the parent form).

**Step 5.2: Create the Signup View**

This view will handle displaying the form (GET request) and processing the submitted data (POST request).

1.  **Edit `pages/views.py`:**

    ```python
    # src/pages/views.py
    from django.shortcuts import render, redirect
    from django.contrib.auth import login # Import the login function
    from django.urls import reverse_lazy
    from django.views.generic.edit import CreateView
    from .forms import SignUpForm # Import your form

    # --- Option 1: Function-Based View (FBV) ---
    # def signup_view(request):
    #     if request.method == 'POST':
    #         form = SignUpForm(request.POST)
    #         if form.is_valid():
    #             user = form.save()  # Creates & saves the user, hashes password
    #             login(request, user) # Log the user in immediately after signup
    #             # messages.success(request, "Registration successful!") # Optional: add success message
    #             return redirect('pages:home') # Or LOGIN_REDIRECT_URL or profile page etc.
    #         # If form is invalid, render the page again with errors
    #     else: # GET request
    #         form = SignUpForm()
    #     return render(request, 'registration/signup.html', {'form': form})

    # --- Option 2: Class-Based View (CBV) - More concise for creation ---
    class SignUpView(CreateView):
        form_class = SignUpForm
        template_name = 'registration/signup.html' # Template to render
        success_url = reverse_lazy('pages:home') # Where to redirect on success (use reverse_lazy for CBVs)

        def form_valid(self, form):
            # This method is called when valid form data has been POSTed.
            # It should return an HttpResponse.
            user = form.save() # Save the new user object
            login(self.request, user) # Log the user in
            # messages.success(self.request, "Registration successful!") # Optional
            return super().form_valid(form) # Calls parent method which handles redirect

    # Choose ONE approach (CBV is often preferred for simple create/update views)
    ```

    - **GET Request:** If the request method is GET, we simply create an empty instance of our `SignUpForm` and pass it to the template.
    - **POST Request:**
      - We create a form instance populated with the submitted data (`request.POST`).
      - `form.is_valid()`: This triggers validation rules (e.g., username uniqueness, valid email, password confirmation matching).
      - `user = form.save()`: If valid, this creates the new `User` object in the database with a securely hashed password.
      - `login(request, user)`: This function (imported from `django.contrib.auth`) manually logs the newly created user into the current session. This is good UX.
      - `redirect(...)`: Sends the user to a success page (e.g., homepage).
    - **CBV (`CreateView`)**: Handles much of the GET/POST logic automatically. We just need to specify the form, template, and success URL. We override `form_valid` to add the `login()` call. `reverse_lazy` is used for `success_url` because URLs might not be loaded when the class is defined.

**Step 5.3: Create the Signup Template**

This template will render the form created in Step 5.1.

1.  **Create `signup.html`:** Place this inside the _same_ `registration` directory as `login.html`.

    ```html
    {# src/templates/registration/signup.html #} {% extends 'pages/base.html' %}
    {% block title %}Sign Up{% endblock %} {% block content %}
    <div class="container mx-auto px-4 py-8 max-w-lg">
      <h2 class="text-2xl font-bold text-center mb-6 text-text-secondary">
        Create an Account
      </h2>

      <form
        method="post"
        class="bg-surface p-6 rounded-lg shadow-md border border-border space-y-4"
      >
        {% csrf_token %} {# Display form errors efficiently #} {% if form.errors
        %}
        <div
          class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4"
          role="alert"
        >
          <p><strong>Please correct the errors below:</strong></p>
          {{ form.non_field_errors }}
          <ul>
            {% for field in form %} {% if field.errors %}
            <li>{{ field.label }}: {{ field.errors|striptags }}</li>
            {% endif %} {% endfor %}
          </ul>
        </div>
        {% endif %} {# Render form fields using a template tag or manually #} {{
        form.as_p }} {# Renders each form field wrapped in
        <p>
          tags - simplest way #} {# Or render manually for more control, similar
          to login.html #}

          <button
            type="submit"
            class="w-full bg-accent-primary hover:bg-accent-hover text-white font-bold py-2 px-4 rounded-lg transition-colors"
          >
            Sign Up
          </button>
        </p>
      </form>

      <p class="text-center mt-4 text-sm text-text-muted">
        Already have an account?
        <a
          href="{% url 'login' %}"
          class="text-accent-heading hover:text-accent-primary"
          >Log in</a
        >
      </p>
    </div>
    {% endblock %}
    ```

    - `{{ form.as_p }}`: A convenient way to render all form fields, labels, and errors, each wrapped in a paragraph tag. Use `form.as_ul` or `form.as_table` for different structures, or iterate through `{% for field in form %}` for full manual control.

**Step 5.4: Add URL Pattern for Signup**

Map a URL to your new signup view.

1.  **Edit `pages/urls.py`** (or wherever you want the signup URL):

    ```python
    # src/pages/urls.py
    from django.urls import path
    from . import views # Import views from the current app
    from .views import SignUpView # Import the CBV if using that

    app_name = 'pages' # Make sure you have an app_name for namespacing

    urlpatterns = [
        path('', views.home_view, name='home'),
        path('about/', views.about_view, name='about'),
        path('quizzes/', views.quizzes_view, name='quizzes'),
        path('profile/', views.profile_view, name='profile'), # Assuming you have this

        # Add the signup URL pattern
        # path('signup/', views.signup_view, name='signup'), # If using FBV
        path('signup/', SignUpView.as_view(), name='signup'), # If using CBV
    ]
    ```

    - Make sure you use `.as_view()` when adding a Class-Based View to `urlpatterns`.
    - Use a descriptive `name` like `'signup'`. We referenced this earlier in `login.html` and `base.html` using `{% url 'pages:signup' %}` (or just `{% url 'signup' %}` if not using namespaces or if signup is in the project urls.py). Adjust the `{% url %}` tags accordingly.

**Step 5.5: Test Signup**

1.  **Run Server:** `python manage.py runserver`
2.  **Visit Site:** Go to the homepage. Click the "Sign Up" link (or navigate directly to `/signup/`).
3.  **Attempt Signup:**
    - Try submitting empty form -> See validation errors.
    - Try existing username -> See validation error.
    - Try mismatched passwords -> See validation error.
    - Enter valid, unique details.
4.  **Verify:** Upon successful signup, you should be:
    - Redirected (e.g., to the homepage).
    - Automatically logged in (navbar shows "Hi, [new_username]!", "Profile", "Logout").
5.  **Check Admin:** Log out, log back in as the _superuser_, go to `/admin/`, click "Users". You should see the newly registered user listed (they will _not_ be staff or superuser by default).

You now have a complete Authentication loop: Login, Logout, and Signup!

---

**Part 6: Basic Authorization - Controlling Access**

Now that users can log in, let's restrict access to certain parts of the site.

**Step 6.1: Protecting Views with `@login_required`**

This is the simplest form of authorization: ensuring only logged-in users can access a specific view.

1.  **Choose View:** Let's protect the `profile_view` in `pages/views.py`. Only logged-in users should see their profile.
2.  **Import & Apply Decorator:**

    ```python
    # src/pages/views.py
    from django.shortcuts import render
    from django.contrib.auth.decorators import login_required # Import

    # ... other views (home, about, signup, etc.) ...

    @login_required # <<< Apply the decorator ABOVE the view function
    def profile_view(request):
        """Placeholder user profile page."""
        # In a real app, you'd fetch data specific to request.user
        # e.g., user_profile = request.user.profile
        quiz_attempts = [] # Placeholder
        context = {
            'user': request.user, # Pass the user object to the template
            'quiz_attempts': quiz_attempts
        }
        return render(request, "pages/profile.html", context)
    ```

    - **Decorator (`@login_required`):** This is Python syntax sugar. It wraps your `profile_view` function. Before your view code runs, the decorator checks `request.user.is_authenticated`.
    - **Behavior:**
      - If `True` (user is logged in): Your `profile_view` code executes normally.
      - If `False` (user is anonymous): The decorator _stops_ execution of your view and redirects the browser to the URL specified in `settings.LOGIN_URL` (which is `/accounts/login/`). Crucially, it appends a `?next=/profile/` parameter to that URL. The login view template uses this `next` value (as seen in `login.html`) so that after a successful login, the user is automatically redirected back to the `/profile/` page they originally tried to access.

3.  **Test Protection:**
    - Log out.
    - Try accessing `/profile/`.
    - You should be redirected to `/accounts/login/?next=/profile/`.
    - Log in (using any valid account).
    - You should now be redirected _back_ to `/profile/` successfully.

**Step 6.2: Conditional Logic Based on User Status**

You often need to show/hide elements or perform different actions based on user attributes.

- **In Templates (Review):** We already did this in `base.html` using `user.is_authenticated`. You can also check other flags:

  ```html
  {# Show admin link only to staff users #} {% if user.is_authenticated and
  user.is_staff %}
  <a href="/admin/">Admin Panel</a>
  {% endif %} {# Show "Edit" button only if the logged-in user owns the object
  #} {% if user.is_authenticated and user == object.author %}
  <a href="...">Edit Post</a>
  {% endif %}
  ```

- **In Views:** Check user attributes directly on the `request.user` object.

  ```python
  # src/some_app/views.py
  from django.shortcuts import render, redirect, get_object_or_404
  from django.http import HttpResponseForbidden
  from django.contrib.auth.decorators import login_required
  # from .models import SomeSensitiveData

  @login_required # Good practice to require login first
  def admin_dashboard_view(request):
      # Only allow staff users to see this dashboard
      if not request.user.is_staff:
          # Option 1: Forbidden Error
          # return HttpResponseForbidden("Access Denied: You are not authorized to view this page.")

          # Option 2: Redirect to a safe page
          # messages.error(request, "You do not have permission to access the admin dashboard.")
          # return redirect('pages:home')

          # Option 3: Render a specific "permission denied" template
          return render(request, 'errors/permission_denied.html', {'required_permission': 'Staff Access'}, status=403)

      # --- Staff-only logic proceeds here ---
      # data = SomeSensitiveData.objects.all()
      # context = {'data': data}
      # return render(request, 'some_app/admin_dashboard.html', context)
      return render(request, 'some_app/admin_dashboard.html') # Placeholder
  ```

  - Always check `is_authenticated` first (or use `@login_required`) before checking other flags like `is_staff`.
  - Decide how to handle unauthorized access: a generic 403 Forbidden error, a redirect with a message, or a user-friendly "Permission Denied" page.

---

**Part 7: Finer Control - Permissions and Groups**

Sometimes, `is_staff` is too broad. You might want "Editors" who can change quizzes but not manage users, or "Moderators" who can delete comments but not create quizzes. Django's Permissions framework handles this.

**Step 7.1: Understanding Permissions**

- **Automatic Creation:** When you run `migrate`, Django automatically creates four permissions for _each_ model you define (unless customized in the model's `Meta` options):

  - `<app_label>.add_<model_name>` (e.g., `multi_choice_quiz.add_quiz`)
  - `<app_label>.change_<model_name>` (e.g., `multi_choice_quiz.change_quiz`)
  - `<app_label>.delete_<model_name>` (e.g., `multi_choice_quiz.delete_quiz`)
  - `<app_label>.view_<model_name>` (e.g., `multi_choice_quiz.view_quiz`)
  - These permissions are stored in the `auth_permission` database table.

- **Superusers:** Remember, users with `is_superuser=True` _always_ have _all_ permissions, regardless of what's assigned.

**Step 7.2: Using Groups for Role-Based Access Control (RBAC)**

Assigning permissions individually to hundreds of users is unmanageable. **Best Practice:** Assign permissions to **Groups**, and then add users to those groups. This represents user _roles_.

1.  **Create Groups (via Admin):**

    - Log in as your superuser -> Go to `/admin/`.
    - Under "AUTHENTICATION AND AUTHORIZATION", click "Groups" -> "Add Group".
    - **Name:** Create a group named `Quiz Editors`.
    - **Permissions:** Select the relevant permissions from the list (use Ctrl/Cmd-Click or Shift-Click to select multiple). For `Quiz Editors`, you might select:
      - `multi_choice_quiz | quiz | Can add quiz`
      - `multi_choice_quiz | quiz | Can change quiz`
      - `multi_choice_quiz | quiz | Can view quiz`
      - `multi_choice_quiz | question | Can add question`
      - `multi_choice_quiz | question | Can change question`
      - `multi_choice_quiz | question | Can delete question`
      - `multi_choice_quiz | question | Can view question`
      - (And similar for `Answer` model if applicable)
    - Click "Save".

2.  **Assign Users to Groups (via Admin):**
    - Go back to "Users".
    - Click on a _non-superuser_ user you created via signup.
    - Scroll down to the "Groups" section.
    - Select "Quiz Editors" from the "Available groups" list and click the right arrow to move it to "Chosen groups".
    - Click "Save".

Now, this user inherits all the permissions granted to the `Quiz Editors` group. If you need to change the permissions for all editors, you only need to modify the group, not each user individually.

**Step 7.3: Checking Permissions in Code**

How do you enforce these permissions in your views and templates?

- **In Views (Manual Check):** Use `request.user.has_perm()`

  ```python
  # src/multi_choice_quiz/views.py
  from django.contrib.auth.decorators import login_required
  from django.http import HttpResponseForbidden
  from .models import Quiz

  @login_required # Always ensure user is logged in first!
  def edit_quiz_view(request, quiz_id):
      quiz = get_object_or_404(Quiz, pk=quiz_id)

      # Check if the user has the specific permission
      if not request.user.has_perm('multi_choice_quiz.change_quiz'):
          return HttpResponseForbidden("You do not have permission to edit quizzes.")
          # Or render('errors/permission_denied.html', ...)

      # --- Permission granted, proceed with view logic ---
      # form = QuizForm(request.POST or None, instance=quiz)
      # if request.method == 'POST' and form.is_valid():
      #     form.save()
      #     return redirect('multi_choice_quiz:detail', quiz_id=quiz.id)
      # context = {'form': form, 'quiz': quiz}
      # return render(request, 'multi_choice_quiz/edit_quiz.html', context)
      pass # Placeholder for edit logic
  ```

  - `user.has_perm('app_label.codename')`: Returns `True` if the user has the permission (either directly assigned or via a group), `False` otherwise.

- **In Views (Decorator):** Use `@permission_required` for convenience.

  ```python
  # src/multi_choice_quiz/views.py
  from django.contrib.auth.decorators import login_required, permission_required

  @login_required # Apply login_required FIRST
  @permission_required('multi_choice_quiz.add_quiz', raise_exception=False, login_url='/accounts/login/')
  def add_quiz_view(request):
      # This code only runs if the user is logged in AND has the 'add_quiz' permission.

      # If permission check fails:
      # - If raise_exception=True: Raises PermissionDenied exception (results in a 403 Forbidden).
      # - If raise_exception=False (default): Redirects to LOGIN_URL (or the specified login_url).
      #   It's often better to set raise_exception=True or handle manually for clearer feedback
      #   than just redirecting to login when the user IS logged in but lacks permissions.

      # --- Permission granted, proceed with view logic ---
      pass # Placeholder for add logic
  ```

  - **Stacking Decorators:** Order matters. `@login_required` should usually come before `@permission_required`.
  - **`raise_exception`:** Controls behavior on failure. `True` gives a 403 error; `False` redirects to login (which can be confusing if the user _is_ logged in). Consider setting `raise_exception=True` and customizing the 403 error page, or perform manual checks using `has_perm` for better control over the response.

- **In Templates:** Use the `{{ perms }}` object. Django makes permissions available in the template context if `django.contrib.auth.context_processors.auth` is included in your `settings.TEMPLATES['OPTIONS']['context_processors']` (it is by default).

  ```html
  {# src/multi_choice_quiz/templates/multi_choice_quiz/quiz_detail.html #} {#
  ... display quiz details ... #}

  <div class="mt-4 space-x-2">
    {% if perms.multi_choice_quiz.change_quiz %}
    <a
      href="{% url 'multi_choice_quiz:edit_quiz' quiz.id %}"
      class="button-secondary"
      >Edit Quiz Details</a
    >
    {% endif %} {% if perms.multi_choice_quiz.add_question %}
    <a
      href="{% url 'multi_choice_quiz:add_question' quiz.id %}"
      class="button-primary"
      >Add Question</a
    >
    {% endif %} {% if perms.multi_choice_quiz.delete_quiz %}
    <form
      method="post"
      action="{% url 'multi_choice_quiz:delete_quiz' quiz.id %}"
      class="inline"
      onsubmit="return confirm('Are you sure you want to delete this quiz?');"
    >
      {% csrf_token %}
      <button type="submit" class="button-danger">Delete Quiz</button>
    </form>
    {% endif %}
  </div>
  ```

  - `perms.<app_label>.<codename>`: Access permissions like boolean flags within the template. Show/hide buttons or links based on the user's capabilities.

**Step 7.4: Test Permissions**

1.  **Use Different Users:** Log in as:
    - The **superuser:** Should see _all_ buttons/links (Edit, Add, Delete) and be able to access protected views like `edit_quiz_view`.
    - A user in the **`Quiz Editors` group:** Should see Edit/Add buttons (based on assigned perms), be able to access corresponding views, but _not_ see the Delete button (if you didn't grant `delete_quiz`).
    - A regular user **not** in the group:\** Should *not\* see Edit/Add/Delete buttons and should get a "Forbidden" error or be redirected if they try to access the `edit_quiz_view` URL directly.
    - An **anonymous user:** Should be redirected to login if they try to access permission-protected views.

---

**Part 8: Conclusion & Next Steps**

**Congratulations!** You've journeyed from a basic Django site with no user awareness to one with a robust system for:

- **Authentication:** Secure Login, Logout, and User Signup.
- **Authorization:** Protecting views (`@login_required`), controlling access based on user roles (`is_staff`), and implementing fine-grained control using Groups and Permissions (`has_perm`, `@permission_required`, `{{ perms }}`).

You leveraged Django's built-in `django.contrib.auth` system, understanding its core components like middleware, models, views, forms, and templates.

**Where to Go From Here:**

1.  **Password Reset:** Implement the required templates (`password_reset_*.html`, etc.) in your `registration` folder and configure email settings in `settings.py` to make the password reset flow functional.
2.  **Customize Templates:** Thoroughly style `login.html`, `signup.html`, and other `registration/` templates to match your site's design using your CSS framework (e.g., Tailwind).
3.  **Profile Page Enhancement:** Make the `profile_view` actually display and allow editing of user-specific data (you might need a separate `Profile` model linked one-to-one with `User`).
4.  **Custom User Model:** If you need to fundamentally change the user model (e.g., use email as the primary identifier instead of username, add a date of birth field), explore creating a Custom User Model. **Do this early in a project if needed**, as changing later is complex.
5.  **Object-Level Permissions:** What if a user can edit _their own_ quiz, but not others? Django's built-in permissions are model-level. For object-level permissions, investigate third-party libraries like `django-guardian`.
6.  **Class-Based View Mixins:** For CBVs, explore `LoginRequiredMixin` and `PermissionRequiredMixin` as alternatives to decorators.
7.  **Social Authentication:** Integrate login via Google, GitHub, etc., using libraries like `django-allauth`.
8.  **Two-Factor Authentication (2FA):** Enhance security further with libraries like `django-otp`.

User management is fundamental to many web applications. By mastering Django's built-in system, you have a powerful and secure foundation to build upon. Remember to always prioritize security best practices when dealing with user accounts and permissions.
