# views.py
import csv
import matplotlib.pyplot as plt
import io
import base64
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from .models import StudyLog, Category, StudyGoal
from .forms import StudyLogForm, StudyGoalForm
from matplotlib import font_manager
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
import matplotlib
matplotlib.use('Agg') 


# フォントパスを正確なファイル名で指定
font_path = r"C:\Users\naoki\AppData\Local\Microsoft\Windows\Fonts\NotoSansCJKjp-Regular.otf"  # フォントファイルへの正確なパスを指定
font_prop = font_manager.FontProperties(fname=font_path)

# matplotlibのデフォルトフォントを日本語フォントに設定
plt.rcParams['font.family'] = font_prop.get_name()
plt.rcParams['axes.unicode_minus'] = False

def index(request):
    if request.user.is_authenticated:
        form = StudyLogForm()
        studying = False
        current_study_log = None

        if request.method == 'POST':
            if 'start_study' in request.POST:
                form = StudyLogForm(request.POST)
                if form.is_valid():
                    current_study_log = form.save(commit=False)
                    current_study_log.user = request.user  # ユーザーを紐付け
                    current_study_log.start_time = timezone.now()
                    current_study_log.save()
                    studying = True
            elif 'stop_study' in request.POST:
                current_study_log = StudyLog.objects.filter(user=request.user, end_time__isnull=True).first()
                if current_study_log:
                    current_study_log.end_time = timezone.now()
                    current_study_log.save()
                    studying = False
        else:
            current_study_log = StudyLog.objects.filter(user=request.user, end_time__isnull=True).first()
            if current_study_log:
                studying = True

        return render(request, 'study/index.html', {
            'form': form,
            'studying': studying,
            'current_study_log': current_study_log
        })
    else:
        return render(request, 'study/welcome.html')

def user_login(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('index')
            else:
                return render(request, 'study/login.html', {'form': form, 'error': 'Invalid username or password'})
        else:
            return render(request, 'study/login.html', {'form': form})
    else:
        form = AuthenticationForm()
        return render(request, 'study/login.html', {'form': form})

def signup(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
        else:
            return render(request, 'study/signup.html', {'form': form, 'error': 'Please correct the error below.'})
    else:
        form = UserCreationForm()
        return render(request, 'study/signup.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    return redirect('user_login')

@login_required
def dashboard(request):
    categories = Category.objects.all()
    category_summary = {}
    for category in categories:
        logs = StudyLog.objects.filter(user=request.user, category=category, end_time__isnull=False)
        total_minutes = sum(log.duration_in_minutes() for log in logs)
        category_summary[category.name] = {
            'total_minutes': round(total_minutes, 2),
            'logs': logs
        }

    study_goals = StudyGoal.objects.filter(user=request.user)
    goal_summary = {}
    for goal in study_goals:
        achieved_minutes = category_summary.get(goal.category.name, {}).get('total_minutes', 0)
        goal_summary[goal.category.name] = {
            'target_minutes': goal.target_minutes,
            'achieved_minutes': achieved_minutes,
            'remaining_minutes': max(goal.target_minutes - achieved_minutes, 0)
        }

    categories = list(goal_summary.keys())
    target_minutes = [goal_summary[cat]['target_minutes'] for cat in categories]
    achieved_minutes = [goal_summary[cat]['achieved_minutes'] for cat in categories]

    fig, ax = plt.subplots()
    index = range(len(categories))
    bar_width = 0.35

    ax.bar(index, target_minutes, bar_width, label='目標 (分)', color='grey')
    ax.bar([i + bar_width for i in index], achieved_minutes, bar_width, label='達成 (分)', color='blue')

    ax.set_xlabel('カテゴリー', fontproperties=font_prop)
    ax.set_ylabel('分', fontproperties=font_prop)
    ax.set_title('勉強進捗', fontproperties=font_prop)
    ax.set_xticks([i + bar_width / 2 for i in index])
    ax.set_xticklabels(categories, rotation=45, fontproperties=font_prop)
    ax.legend()

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    graph = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()

    return render(request, 'study/dashboard.html', {
        'category_summary': category_summary,
        'goal_summary': goal_summary,
        'graph': f'data:image/png;base64,{graph}'
    })

@login_required
def goals(request):
    if request.method == 'POST':
        goal_form = StudyGoalForm(request.POST)
        if goal_form.is_valid():
            category = goal_form.cleaned_data['category']
            existing_goal = StudyGoal.objects.filter(user=request.user, category=category).first()
            
            if existing_goal:
                existing_goal.target_minutes = goal_form.cleaned_data['target_minutes']
                existing_goal.save()
            else:
                goal = goal_form.save(commit=False)
                goal.user = request.user  # ユーザーを紐付け
                goal.save()
            
            return redirect('goals')
    else:
        goal_form = StudyGoalForm()

    study_goals = StudyGoal.objects.filter(user=request.user)
    return render(request, 'study/goals.html', {
        'goal_form': goal_form,
        'study_goals': study_goals
    })

@login_required
def export_study_logs_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="study_logs.csv"'

    writer = csv.writer(response)
    writer.writerow(['Category', 'Start Time', 'End Time', 'Duration (minutes)'])

    logs = StudyLog.objects.filter(user=request.user, end_time__isnull=False).order_by('-start_time')
    for log in logs:
        writer.writerow([log.category.name, log.start_time, log.end_time, log.duration_in_minutes()])

    return response

@login_required
def export_study_goals_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="study_goals.csv"'

    writer = csv.writer(response)
    writer.writerow(['Category', 'Target Minutes', 'Achieved Minutes', 'Remaining Minutes'])

    study_goals = StudyGoal.objects.filter(user=request.user)
    categories = Category.objects.all()
    category_summary = {}
    for category in categories:
        logs = StudyLog.objects.filter(user=request.user, category=category, end_time__isnull=False)
        total_minutes = sum(log.duration_in_minutes() for log in logs)
        category_summary[category.name] = round(total_minutes, 2)

    for goal in study_goals:
        achieved_minutes = category_summary.get(goal.category.name, 0)
        remaining_minutes = max(goal.target_minutes - achieved_minutes, 0)
        writer.writerow([goal.category.name, goal.target_minutes, achieved_minutes, remaining_minutes])

    return response

@login_required
def export_data(request):
    return render(request, 'study/export_data.html')