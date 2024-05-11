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

# フォントパスを正確なファイル名で指定
font_path = r"C:\Users\naoki\AppData\Local\Microsoft\Windows\Fonts\NotoSansCJKjp-Regular.otf"  # フォントファイルへの正確なパスを指定
font_prop = font_manager.FontProperties(fname=font_path)

# matplotlibのデフォルトフォントを日本語フォントに設定
plt.rcParams['font.family'] = font_prop.get_name()
plt.rcParams['axes.unicode_minus'] = False

def index(request):
    form = StudyLogForm()
    studying = False
    current_study_log = None

    if request.method == 'POST':
        if 'start_study' in request.POST:
            form = StudyLogForm(request.POST)
            if form.is_valid():
                current_study_log = form.save(commit=False)
                current_study_log.start_time = timezone.now()
                current_study_log.save()
                studying = True
        elif 'stop_study' in request.POST:
            current_study_log = StudyLog.objects.filter(end_time__isnull=True).first()
            if current_study_log:
                current_study_log.end_time = timezone.now()
                current_study_log.save()
                studying = False

    else:
        current_study_log = StudyLog.objects.filter(end_time__isnull=True).first()
        if current_study_log:
            studying = True

    return render(request, 'study/index.html', {
        'form': form,
        'studying': studying,
        'current_study_log': current_study_log
    })

def dashboard(request):
    categories = Category.objects.all()
    category_summary = {}
    for category in categories:
        logs = StudyLog.objects.filter(category=category, end_time__isnull=False)
        total_minutes = sum(log.duration_in_minutes() for log in logs)
        category_summary[category.name] = {
            'total_minutes': round(total_minutes, 2),
            'logs': logs
        }

    study_goals = StudyGoal.objects.all()
    goal_summary = {}
    for goal in study_goals:
        achieved_minutes = category_summary.get(goal.category.name, {}).get('total_minutes', 0)
        goal_summary[goal.category.name] = {
            'target_minutes': goal.target_minutes,
            'achieved_minutes': achieved_minutes,
            'remaining_minutes': max(goal.target_minutes - achieved_minutes, 0)
        }

    # グラフの描画
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

def goals(request):
    if request.method == 'POST':
        goal_form = StudyGoalForm(request.POST)
        if goal_form.is_valid():
            # Check if a goal for the category already exists
            category = goal_form.cleaned_data['category']
            existing_goal = StudyGoal.objects.filter(category=category).first()
            
            if existing_goal:
                # If a goal exists, update it
                existing_goal.target_minutes = goal_form.cleaned_data['target_minutes']
                existing_goal.save()
            else:
                # Otherwise, create a new goal
                goal_form.save()
            
            return redirect('goals')
    else:
        goal_form = StudyGoalForm()

    study_goals = StudyGoal.objects.all()
    return render(request, 'study/goals.html', {
        'goal_form': goal_form,
        'study_goals': study_goals
    })

def export_study_logs_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="study_logs.csv"'

    writer = csv.writer(response)
    writer.writerow(['Category', 'Start Time', 'End Time', 'Duration (minutes)'])

    logs = StudyLog.objects.filter(end_time__isnull=False).order_by('-start_time')
    for log in logs:
        writer.writerow([log.category.name, log.start_time, log.end_time, log.duration_in_minutes()])

    return response

def export_study_goals_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="study_goals.csv"'

    writer = csv.writer(response)
    writer.writerow(['Category', 'Target Minutes', 'Achieved Minutes', 'Remaining Minutes'])

    study_goals = StudyGoal.objects.all()
    categories = Category.objects.all()
    category_summary = {}
    for category in categories:
        logs = StudyLog.objects.filter(category=category, end_time__isnull=False)
        total_minutes = sum(log.duration_in_minutes() for log in logs)
        category_summary[category.name] = round(total_minutes, 2)

    for goal in study_goals:
        achieved_minutes = category_summary.get(goal.category.name, 0)
        remaining_minutes = max(goal.target_minutes - achieved_minutes, 0)
        writer.writerow([goal.category.name, goal.target_minutes, achieved_minutes, remaining_minutes])

    return response

def export_data(request):
    # このビューでは特に処理は行わないが、テンプレートにエクスポート用のリンクを提供する
    return render(request, 'study/export_data.html')