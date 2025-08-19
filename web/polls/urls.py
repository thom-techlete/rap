from django.urls import path
from . import views

app_name = 'polls'

urlpatterns = [
    # Poll listing and detail
    path('', views.poll_list, name='list'),
    path('<int:pk>/', views.poll_detail, name='detail'),
    
    # Poll management (staff only)
    path('create/', views.poll_create, name='create'),
    path('<int:pk>/edit/', views.poll_edit, name='edit'),
    path('<int:pk>/close/', views.poll_close, name='close'),
    path('<int:pk>/reopen/', views.poll_reopen, name='reopen'),
    
    # Voting and results
    path('<int:pk>/vote/', views.vote, name='vote'),
    path('<int:pk>/results/', views.poll_results, name='results'),
]