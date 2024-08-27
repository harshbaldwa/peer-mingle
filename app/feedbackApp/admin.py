from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import Assignment, Course, Feedback, GTUser, Submission


class GTUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = GTUser
    list_display = ["email", "first_name", "gt_id",
                    "is_staff", "is_active", "should_change_password"]
    fieldsets = UserAdmin.fieldsets + (
        (None, {"fields": ("is_student", "gt_id")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {"fields": ("is_student", "gt_id")}),
    )
    ordering = ["email"]
    search_fields = ["email"]


class CourseAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "semester", "year"]
    ordering = ["name"]
    search_fields = ["name", "code"]
    actions = ["create_roster", "download_passwords"]

    @admin.action(description="Create Roster")
    def create_roster(self, request, queryset):
        for course in queryset:
            course.create_roster()
        self.message_user(request, "Roster(s) created successfully")


class AssignmentAdmin(admin.ModelAdmin):
    list_display = ["name", "course"]
    ordering = ["name"]
    actions = ["make_submissions", "create_feedbacks"]

    @admin.action(description="Make submissions")
    def make_submissions(self, request, queryset):
        for assignment in queryset:
            assignment.make_submissions()
        self.message_user(request, "Submission(s) created successfully")

    @admin.action(description="Create feedbacks")
    def create_feedbacks(self, request, queryset):
        for assignment in queryset:
            assignment.create_feedbacks()
        self.message_user(request, "Feedback(s) created successfully")


class SubmissionAdmin(admin.ModelAdmin):
    list_display = ["assignment", "student", "is_late"]
    ordering = ["assignment", "student"]
    actions = ["assign_submissions"]
    list_filter = ["is_late", "assignment"]

    @admin.action(description="Assign submissions for review")
    def assign_submissions(self, request, queryset):
        for submission in queryset:
            submission.assign_submissions()
        self.message_user(request, "Submission(s) assigned successfully")


class FeedbackAdmin(admin.ModelAdmin):
    list_display = ["assignment", "student", "reviewer", "issued", "graded"]


# Register your models here.
admin.site.register(Course, CourseAdmin)
admin.site.register(GTUser, GTUserAdmin)
admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(Feedback, FeedbackAdmin)
