from django.urls import path
from . import views

app_name = 'help'

urlpatterns = [
    # Help section main page
    path('', views.help_index, name='index'),
    
    # Bug reporting for users
    path('bug-report/', views.bug_report_create, name='bug_report'),
    path('bug/<int:pk>/', views.bug_detail, name='bug_detail'),
    path('my-bugs/', views.my_bug_reports, name='my_bug_reports'),
    
    # Admin bug management
    path('admin/', views.admin_bug_list, name='admin_bug_list'),
    path('admin/bug/<int:pk>/', views.admin_bug_detail, name='admin_bug_detail'),
    path('admin/bug/<int:pk>/resolve/', views.admin_bug_mark_resolved, name='admin_bug_mark_resolved'),
    path('admin/bug/<int:pk>/close/', views.admin_bug_mark_closed, name='admin_bug_mark_closed'),
]