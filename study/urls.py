# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # トップページ
    path('dashboard/', views.dashboard, name='dashboard'),
    path('goals/', views.goals, name='goals'),
    path('export_study_logs_csv/', views.export_study_logs_csv, name='export_study_logs_csv'),
    path('export_study_goals_csv/', views.export_study_goals_csv, name='export_study_goals_csv'),
    path('export_data/', views.export_data, name='export_data'),
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('signup/', views.signup, name='signup'),  # サインアップ用のURLパターンを追加
]