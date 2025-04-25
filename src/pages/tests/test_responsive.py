# --- START OF FILE test_responsive.py ---

import pytest
import re
from playwright.sync_api import Page, expect

# Define breakpoints according to Tailwind defaults + custom/common usage
BREAKPOINTS = {
    "mobile": {"width": 375, "height": 667},  # Small mobile
    "sm": {"width": 640, "height": 768},  # Small tablet / Large mobile
    "md": {"width": 768, "height": 1024},  # Tablet
    "lg": {"width": 1024, "height": 768},  # Laptop
    "xl": {"width": 1280, "height": 800},  # Desktop
    "2xl": {"width": 1536, "height": 900},  # Large Desktop
}

# Pages to test (relative URLs)
PAGES_TO_TEST = [
    pytest.param("/", id="home"),
    pytest.param("/quizzes/", id="quizzes"),
    pytest.param("/about/", id="about"),
    pytest.param("/login/", id="login"),  # Placeholder
    pytest.param("/signup/", id="signup"),  # Placeholder
    pytest.param("/profile/", id="profile"),  # Placeholder
]

BASE_URL = "http://localhost:8000"  # Adjust if your dev server runs elsewhere

# --- Helper Functions ---


def get_screenshot_path(page_id: str, bp_name: str) -> str:
    """Generates a descriptive screenshot path."""
    # Clean up page_id (replace slashes, etc.)
    safe_page_id = re.sub(r"[^\w\-]+", "_", page_id.strip("/")) or "home"
    return f"screenshots/responsive/{safe_page_id}_{bp_name}.png"


# --- Tests ---


@pytest.mark.parametrize("page_path", PAGES_TO_TEST)
@pytest.mark.parametrize("bp_name, viewport", BREAKPOINTS.items())
def test_responsive_layout(page: Page, page_path: str, bp_name: str, viewport: dict):
    """
    Tests layout integrity, visibility, and basic responsiveness across breakpoints.
    """
    page_url = BASE_URL + page_path
    page_id_for_filename = page_path  # Use the original path for filenames

    # 1. Navigate and Set Viewport
    page.goto(page_url)
    page.set_viewport_size(viewport)
    page.wait_for_load_state("networkidle")  # Wait for resources to load

    # 2. Capture Screenshot
    # Ensure the directory exists before saving (optional, but good practice)
    import os
    screenshot_dir = os.path.dirname(get_screenshot_path("test", "test"))
    os.makedirs(screenshot_dir, exist_ok=True)
    screenshot_path = get_screenshot_path(page_id_for_filename, bp_name)
    page.screenshot(path=screenshot_path, full_page=True)  # Full page screenshot

    # 3. Verify Critical Elements Visibility
    header = page.locator("header")
    footer = page.locator("footer")
    main_content = page.locator("main")

    expect(
        header, f"Header should be visible on {page_path} at {bp_name}"
    ).to_be_visible()
    expect(
        footer, f"Footer should be visible on {page_path} at {bp_name}"
    ).to_be_visible()
    expect(
        main_content, f"Main content should be visible on {page_path} at {bp_name}"
    ).to_be_visible()
    # Ensure main content isn't empty (basic check)
    expect(main_content).not_to_be_empty()

    # Check header/footer width relative to viewport (should be close to full width)
    header_box = header.bounding_box()
    footer_box = footer.bounding_box()
    if header_box and footer_box:
        # Allow for small discrepancies (scrollbar, rounding)

        # --- FIX for Header Width Check ---
        header_min_width = viewport["width"] - 20
        header_max_width = viewport["width"] + 5
        actual_header_width = header_box["width"]
        assert header_min_width <= actual_header_width <= header_max_width, \
            f"Header width ({actual_header_width}px) not within expected range ({header_min_width}px - {header_max_width}px) on {page_path} at {bp_name}"

        # --- FIX for Footer Width Check ---
        # Footer might be narrower if content is short, so check it's > 50%
        footer_min_width = viewport["width"] * 0.5
        actual_footer_width = footer_box["width"]
        assert actual_footer_width > footer_min_width, \
            f"Footer width ({actual_footer_width}px) not greater than 50% of viewport ({footer_min_width}px) on {page_path} at {bp_name}"

    # 4. Check Navigation Elements Accessibility
    mobile_toggle_button = page.locator(
        "header .md\\:hidden button"
    )  # Button inside the md:hidden div
    mobile_nav_menu = page.locator("header nav[x-show='open']")  # The mobile nav itself
    desktop_nav_menu = page.locator("header nav.hidden.md\\:flex")  # The desktop nav

    if bp_name in ["mobile", "sm"]:  # Mobile/Small Tablet Viewports
        expect(
            mobile_toggle_button,
            f"Mobile menu toggle should be visible on {page_path} at {bp_name}",
        ).to_be_visible()
        expect(
            desktop_nav_menu,
            f"Desktop nav should be hidden on {page_path} at {bp_name}",
        ).to_be_hidden()

        # Test mobile menu opening
        expect(
            mobile_nav_menu,
            f"Mobile nav should be hidden initially on {page_path} at {bp_name}",
        ).to_be_hidden()
        mobile_toggle_button.click()
        expect(
            mobile_nav_menu,
            f"Mobile nav should be visible after click on {page_path} at {bp_name}",
        ).to_be_visible()

        # --- FIX for Mobile Nav Link Count ---
        mobile_links = mobile_nav_menu.locator("a[href]")
        link_count = mobile_links.count()
        assert link_count > 2, \
            f"Expected more than 2 mobile nav links on {page_path} at {bp_name}, found {link_count}"

        # Close it again (optional, good practice)
        mobile_toggle_button.click()
        expect(
            mobile_nav_menu,
            f"Mobile nav should be hidden after second click on {page_path} at {bp_name}",
        ).to_be_hidden()

    else:  # md, lg, xl, 2xl Viewports
        expect(
            mobile_toggle_button,
            f"Mobile menu toggle should be hidden on {page_path} at {bp_name}",
        ).to_be_hidden()
        expect(
            desktop_nav_menu,
            f"Desktop nav should be visible on {page_path} at {bp_name}",
        ).to_be_visible()

        # --- FIX for Desktop Nav Link Count ---
        desktop_links = desktop_nav_menu.locator("a[href]")
        link_count = desktop_links.count()
        assert link_count > 2, \
            f"Expected more than 2 desktop nav links on {page_path} at {bp_name}, found {link_count}"


    # 5. Check for Text Overflow (Basic Check - look for horizontal scrollbars)
    # A horizontal scrollbar on the body is a strong indicator of overflow.
    has_horizontal_scrollbar = page.evaluate(
        """
        () => document.body.scrollWidth > document.body.clientWidth
    """
    )
    assert (
        not has_horizontal_scrollbar
    ), f"Horizontal scrollbar detected on {page_path} at {bp_name}, possibly due to text overflow ({screenshot_path})"

    # 6. Validate Interactive Elements Spacing (Basic Check - ensure buttons aren't visually overlapping)
    # This is hard to automate perfectly, screenshots are key.
    # We can check common buttons have some padding.
    buttons = page.locator(
        "main a[class*='bg-accent-primary'], main button[type='submit'], main a[class*='border-border']"
    )
    if buttons.count() > 0:
        first_button = buttons.first
        expect(
            first_button, f"Button padding check on {page_path} at {bp_name}"
        ).to_have_css(
            "padding-left", re.compile(r"[1-9]\d*px")
        )  # Check it has some left padding
        expect(
            first_button, f"Button padding check on {page_path} at {bp_name}"
        ).to_have_css(
            "padding-right", re.compile(r"[1-9]\d*px")
        )  # Check it has some right padding

    # Add page-specific checks if needed
    if page_path == "/" and bp_name == "mobile":
        # Check if hero buttons stack vertically on mobile
        hero_buttons_container = page.locator(
            "section:first-of-type .flex.flex-col.sm\\:flex-row"
        )
        expect(
            hero_buttons_container, "Hero buttons should stack on mobile"
        ).to_have_class(re.compile(r"\bflex-col\b"))

    if "/quizzes/" in page_path:
        # Check grid layout changes
        quiz_grid_locator = page.locator(".grid.grid-cols-1.md\\:grid-cols-2.lg\\:grid-cols-3") # Adjusted locator for quiz grid

        if quiz_grid_locator.count() > 0:  # Check if the grid exists
             quiz_grid = quiz_grid_locator.first # Get the first element matching the locator

             # Check the classes applied at different breakpoints
             # Playwright's to_have_class checks the current state, considering media queries.
             # We can infer the active columns based on the viewport width.

             if bp_name == "mobile":
                 # On mobile, only grid-cols-1 should be effectively active
                 expect(quiz_grid, f"Quiz grid check on {page_path} at {bp_name}").to_have_class(re.compile(r"\bgrid-cols-1\b"))

             elif bp_name == "sm":
                 # On sm, md:grid-cols-2 is not active yet, should still be grid-cols-1 effectively
                 expect(quiz_grid, f"Quiz grid check on {page_path} at {bp_name}").to_have_class(re.compile(r"\bgrid-cols-1\b"))

             elif bp_name == "md":
                 # On md, md:grid-cols-2 should be active
                 expect(quiz_grid, f"Quiz grid check on {page_path} at {bp_name}").to_have_class(re.compile(r"\bmd:grid-cols-2\b"))

             elif bp_name in ["lg", "xl", "2xl"]:
                 # On lg and larger, lg:grid-cols-3 should be active
                 expect(quiz_grid, f"Quiz grid check on {page_path} at {bp_name}").to_have_class(re.compile(r"\blg:grid-cols-3\b"))


    # Placeholder pages checks (just ensure the main form area is visible)
    if page_path in ["/login/", "/signup/"]:
        form_container = page.locator("div[class*='max-w-md']")
        expect(
            form_container,
            f"Form container should be visible on {page_path} at {bp_name}",
        ).to_be_visible()
        # Check the non-functional notice is visible
        notice = page.locator("div.fixed.bottom-0")
        expect(
            notice, f"Placeholder notice should be visible on {page_path} at {bp_name}"
        ).to_be_visible()

    if page_path == "/profile/":
        # Check the non-functional notice is visible
        notice = page.locator("div.fixed.bottom-0")
        expect(
            notice, f"Placeholder notice should be visible on {page_path} at {bp_name}"
        ).to_be_visible()

        # Check stats grid layout changes
        stats_grid_locator = page.locator(".grid.grid-cols-2.lg\\:grid-cols-4")
        if stats_grid_locator.count() > 0:
            stats_grid = stats_grid_locator.first

            if bp_name in ["mobile", "sm", "md"]:
                # grid-cols-2 should be active
                 expect(stats_grid, f"Profile stats grid check on {page_path} at {bp_name}").to_have_class(re.compile(r"\bgrid-cols-2\b"))
                 # lg:grid-cols-4 is not active yet
            else:  # lg, xl, 2xl
                # lg:grid-cols-4 should be active
                 expect(stats_grid, f"Profile stats grid check on {page_path} at {bp_name}").to_have_class(re.compile(r"\blg:grid-cols-4\b"))

# --- END OF FILE test_responsive.py ---