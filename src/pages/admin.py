# src/pages/admin.py

from django.contrib import admin
from .models import SystemCategory, UserCollection


@admin.register(SystemCategory)
class SystemCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "quiz_count")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}  # Helps auto-populate slug based on name
    filter_horizontal = ("quizzes",)  # Use a more user-friendly widget for M2M

    def quiz_count(self, obj):
        # Method to display the number of quizzes in this category
        return obj.quizzes.count()

    quiz_count.short_description = "Quiz Count"


@admin.register(UserCollection)
class UserCollectionAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "created_at", "quiz_count")
    list_filter = ("user", "created_at")
    search_fields = ("name", "description", "user__username")
    filter_horizontal = ("quizzes",)  # Use a more user-friendly widget for M2M
    readonly_fields = ("created_at", "updated_at")  # These are auto-managed

    def quiz_count(self, obj):
        # Method to display the number of quizzes in this collection
        return obj.quizzes.count()

    quiz_count.short_description = "Quiz Count"
