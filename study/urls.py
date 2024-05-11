from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('goals/', views.goals, name='goals'),
    path('export_data/', views.export_data, name='export_data'),  # 追加
    path('export_study_logs_csv/', views.export_study_logs_csv, name='export_study_logs_csv'),
    path('export_study_goals_csv/', views.export_study_goals_csv, name='export_study_goals_csv'),
]