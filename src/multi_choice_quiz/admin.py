# src/multi_choice_quiz/admin.py

from django.contrib import admin
from django.utils.html import format_html

# Add QuizAttempt to the import
from .models import Quiz, Question, Option, Topic, QuizAttempt


# ... (Keep OptionInline, QuestionAdmin, QuestionInline, QuizAdmin, TopicAdmin) ...
class OptionInline(admin.TabularInline):
    model = Option
    extra = 4  # Show 4 empty option forms by default
    min_num = 2  # Require at least 2 options
    fields = ["text", "position", "is_correct"]


class QuestionAdmin(admin.ModelAdmin):
    list_display = [
        "text_preview",
        "quiz",
        "topic",
        "tag",
        "position",
        "option_count",
        "has_correct_answer",
    ]
    list_filter = ["quiz", "topic", "tag", "is_active"]
    search_fields = ["text", "quiz__title", "topic__name", "tag"]
    inlines = [OptionInline]

    def text_preview(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text

    text_preview.short_description = "Question"

    def option_count(self, obj):
        return obj.options.count()

    option_count.short_description = "Options"

    def has_correct_answer(self, obj):
        has_correct = obj.options.filter(is_correct=True).exists()
        icon = "✅" if has_correct else "❌"
        color = "green" if has_correct else "red"
        return format_html('<span style="color: {};">{}</span>', color, icon)

    has_correct_answer.short_description = "Correct Answer"


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ["text", "tag", "position"]
    show_change_link = True


class QuizAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "get_topics_display",
        "question_count",
        "created_at",
        "is_active",
    ]
    list_filter = ["is_active", "topics"]
    search_fields = ["title", "description", "topics__name"]
    filter_horizontal = ["topics"]
    inlines = [QuestionInline]

    def get_topics_display(self, obj):
        return obj.get_topics_display()

    get_topics_display.short_description = "Topics"


class TopicAdmin(admin.ModelAdmin):
    list_display = ["name", "question_count", "quiz_count"]
    search_fields = ["name", "description"]

    def question_count(self, obj):
        return obj.questions.count()

    question_count.short_description = "Questions"

    def quiz_count(self, obj):
        return obj.quizzes.count()

    quiz_count.short_description = "Quizzes"


# <<< START NEW ADMIN CLASS >>>
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "quiz",
        "user_display",
        "score",
        "total_questions",
        "percentage",
        "start_time",
        "end_time",
    )
    list_filter = ("quiz", "user", "start_time")
    search_fields = ("quiz__title", "user__username", "user__email")
    readonly_fields = ("start_time", "end_time")  # These are set programmatically

    def user_display(self, obj):
        return obj.user.username if obj.user else "Anonymous"

    user_display.short_description = "User"
    user_display.admin_order_field = "user"  # Allows sorting by user


# <<< END NEW ADMIN CLASS >>>

admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Topic, TopicAdmin)
admin.site.register(QuizAttempt, QuizAttemptAdmin)  # <<< Register the new model admin
# Options are managed through inline forms
