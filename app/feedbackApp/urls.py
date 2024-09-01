from django.urls import path

from . import views

urlpatterns = [
    path("", views.course_list, name="courses"),
    path("accounts/password_change",
         views.change_password, name="change_password"),
    path("accounts/password_change/<str:first_time>",
         views.change_password, name="change_password_first"),
    path("course/<slug:slug>", views.course_view, name="course"),
    path("course/<slug:slug>/<int:id>",
         views.assignment_view, name="assignment"),
    path("feedback/<int:id>",
         views.feedback_view, name="feedback"),
    path("comment/edit/<int:id>", views.edit_comment, name="edit_comment"),
    path("comment/delete/<int:id>",
         views.delete_comment, name="delete_comment"),
    path("grade/<str:ass_id>",
         views.ta_view_assignment, name="ta_view_all"),
    path("grade/submission/<int:sub_id>",
         views.ta_view_feedback, name="ta_view"),
    path("grade/feedback/<int:feedback_id>",
         views.grade_feedback, name="grade"),
]
