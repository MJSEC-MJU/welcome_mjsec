import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
from django.db.models import Sum, Case, When
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Challenge, Submission, Team
from django.db.models import Max, Min
import base64
import datetime
import pytz
import plotly.graph_objs as go
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Submission, Team
from collections import defaultdict
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.http import JsonResponse
def index(request):
    if request.user.is_authenticated:
        return redirect("challenges:feeds")  
    else:
        return redirect("accounts:login")

@login_required
def feeds(request):
    user = request.user
    team = user.team_set.first()

    if not team:
        challenges = Challenge.objects.all()
        solved_challenges = []
    else:
        challenges = Challenge.objects.all()
        solved_challenges = Submission.objects.filter(team=team, correct=True).values_list('challenge_id', flat=True)
    
    context = {
        'challenges': challenges,
        'solved_challenges': solved_challenges,
    }
    return render(request, 'challenges/feeds.html', context)

@login_required
def challenge_detail(request, challenge_id):
    user = request.user
    team = user.team_set.first()

    if not team:
        messages.error(request, 'You are not part of any team.')
        return redirect("challenges:feeds")
    
    challenge = get_object_or_404(Challenge, pk=challenge_id)
    solved = Submission.objects.filter(team=team, challenge=challenge, correct=True).exists()
    num_solvers = Submission.objects.filter(challenge=challenge, correct=True).values('team').distinct().count()

    if request.method == 'POST':
        submitted_flag = request.POST['flag']
        correct = (challenge.flag == submitted_flag)

        submission, created = Submission.objects.update_or_create(
            team=team,
            challenge=challenge,
            defaults={'submitted_flag': submitted_flag, 'correct': correct, 'user': user}
        )

        if correct:
            messages.success(request, 'Correct flag!')
            update_team_points(team)
        else:
            messages.error(request, 'Incorrect flag. Try again!')

        return redirect('challenges:challenge_detail', challenge_id=challenge.id)

    context = {
        'challenge': challenge,
        'num_solvers': num_solvers,
        'solved': solved,
    }
    return render(request, 'challenges/challenge_detail.html', context)


from django.db import transaction
from django.utils import timezone
from datetime import timedelta

@login_required
def submit_flag(request):
    user = request.user
    team = user.team_set.first()

    if not team:
        messages.error(request, 'You are not part of any team.')
        return redirect("challenges:feeds")

    if request.method == 'POST':
        challenge_id = request.POST.get('challenge_id')
        submitted_flag = request.POST.get('flag')

        if not challenge_id or not submitted_flag:
            messages.error(request, 'Challenge ID and flag must be provided.')
            return redirect('challenges:challenge_detail', challenge_id=challenge_id)

        challenge = get_object_or_404(Challenge, pk=challenge_id)

        # 팀의 최근 제출 시간 확인 (동일 챌린지에 대해)
        last_team_submission = Submission.objects.filter(team=team, challenge=challenge).order_by('-submitted_at').first()

        if last_team_submission:
            now = timezone.now()
            # 30초 이내에 제출한 경우 제출을 막음
            if last_team_submission.submitted_at and now - last_team_submission.submitted_at < timedelta(seconds=30):
                remaining_time = 30 - (now - last_team_submission.submitted_at).seconds
                messages.error(request, f'Your team has recently submitted. Please wait {remaining_time} seconds before trying again.')
                return redirect('challenges:challenge_detail', challenge_id=challenge.id)

        try:
            with transaction.atomic():  # 트랜잭션 시작
                # 동시성 문제 해결을 위해 팀의 제출 데이터를 락으로 보호
                existing_submission = Submission.objects.select_for_update().filter(team=team, challenge=challenge).first()

                if existing_submission:
                    if existing_submission.correct:
                        messages.error(request, 'You have already solved this challenge!')
                        return redirect('challenges:challenge_detail', challenge_id=challenge.id)
                    else:
                        # 제출 시간 확인 및 30초 딜레이 처리
                        now = timezone.now()
                        if existing_submission.submitted_at and now - existing_submission.submitted_at < timedelta(seconds=30):
                            remaining_time = 30 - (now - existing_submission.submitted_at).seconds
                            messages.error(request, f'Please wait {remaining_time} seconds before trying again.')
                            return redirect('challenges:challenge_detail', challenge_id=challenge.id)

                        # 정답 확인 및 제출 갱신
                        correct = (challenge.flag == submitted_flag)
                        existing_submission.submitted_flag = submitted_flag
                        existing_submission.correct = correct
                        existing_submission.submitted_at = now
                        existing_submission.user = user
                        existing_submission.save()

                        if correct:
                            messages.success(request, 'Correct flag!')
                            update_team_points(team)
                        else:
                            messages.error(request, 'Incorrect flag. Try again!')

                        # 점수 업데이트
                        challenge.update_challenge_score()  # 점수 업데이트
                        return redirect('challenges:challenge_detail', challenge_id=challenge.id)

                else:
                    correct = (challenge.flag == submitted_flag)
                    submission = Submission(
                        team=team,
                        challenge=challenge,
                        submitted_flag=submitted_flag,
                        correct=correct,
                        user=user,
                        submitted_at=timezone.now()
                    )
                    submission.save()

                    if correct:
                        messages.success(request, 'Correct flag!')
                        update_team_points(team)
                    else:
                        messages.error(request, 'Incorrect flag. Try again!')

                    # 점수 업데이트
                    challenge.update_challenge_score()  # 점수 업데이트

        except Exception as e:
            messages.error(request, f'An error occurred during submission: {e}')

        return redirect('challenges:challenge_detail', challenge_id=challenge.id)

    return redirect('challenges:index')



@receiver(post_delete, sender=Submission)
def update_team_points_on_delete(sender, instance, **kwargs):
    team = instance.team
    update_team_points(team)

def update_team_points(team):
    total_points = Submission.objects.filter(team=team, correct=True).aggregate(
        total_points=Sum('challenge__points')
    )['total_points'] or 0
    team.total_points = total_points
    team.save()
from django.db.models import Max

@login_required
def leaderboard(request):
    # Update teams to ensure they have the latest total points
    teams = Team.objects.all()
    for team in teams:
        update_team_points(team)  # Ensure points are updated before rendering

    # Sort teams by total points and name
    teams = teams.order_by('-total_points', 'name')

    user_stats = []
    team_time_series_data = {}
    submissions = Submission.objects.filter(correct=True).select_related('team')
    user_dict = defaultdict(lambda: {'count': 0, 'last_submission_time': None, 'points': 0})

    # 사용자 통계 수집
    for submission in submissions:
        user = submission.user
        user_dict[user]['count'] += 1
        user_dict[user]['points'] += submission.challenge.points
        # 첫 제출 시간
        if user_dict[user]['last_submission_time'] is None or submission.submitted_at > user_dict[user]['last_submission_time']:
            user_dict[user]['last_submission_time'] = submission.submitted_at

    for user, stats in user_dict.items():
        user_stats.append((user.username, stats['count'], stats['points'], stats['last_submission_time']))

    # 사용자 통계 정렬
    user_stats.sort(key=lambda x: (-x[2], x[3] if x[3] is not None else datetime.datetime.max))

    # 각 팀의 마지막 제출 시간 구하기
    last_submission_times = submissions.values('team').annotate(last_submission_time=Max('submitted_at'))

    team_last_submission_times = {}
    for team in teams:
        last_submission_time = next(
            (item['last_submission_time'] for item in last_submission_times if item['team'] == team.id),
            None
        )
        if last_submission_time is None:
            continue  # 이 팀은 정답 제출 기록이 없으므로 건너뜁니다.

        # 마지막 제출 시간을 기록
        team_last_submission_times[team.name] = last_submission_time

        submissions = Submission.objects.filter(team=team, correct=True, submitted_at__lte=last_submission_time).order_by('submitted_at')

        time_series_data = defaultdict(int)
        for submission in submissions:
            timestamp = submission.submitted_at
            points = submission.challenge.points
            time_series_data[timestamp] += points

        sorted_times = sorted(time_series_data.keys())
        sorted_points = [time_series_data[time] for time in sorted_times]

        cumulative_points = []
        running_total = 0
        for points in sorted_points:
            running_total += points
            cumulative_points.append(running_total)

        team_time_series_data[team.name] = (sorted_times, cumulative_points)

    # 팀을 총 점수 및 마지막 제출 시간 기준으로 정렬 (점수가 동일할 경우 마지막 제출 시간이 빠른 팀이 우선)
    sorted_teams = sorted(teams, key=lambda team: (
        -team.total_points,  # 총 점수 기준 정렬 (내림차순)
        team_last_submission_times.get(team.name)  # 마지막 성공 제출 시간 기준 정렬 (오름차순)
    ))

    # 팀별 포인트 변화 그래프 생성
    traces = []
    colors = ['#FF5733', '#33FF57', '#3357FF', '#F3FF33', '#FF33F6']

    for i, (team_name, (times, points)) in enumerate(team_time_series_data.items()):
        trace = go.Scatter(
            x=[time.isoformat() for time in times],
            y=points,
            mode='lines+markers',
            name=team_name,
            line=dict(color=colors[i % len(colors)]),
        )
        traces.append(trace)

    layout = go.Layout(
        title='Points Over Time',
        xaxis=dict(title='Time', tickformat='%H:%M:%S'),  # 초 단위 표시
        yaxis=dict(title='Total Points'),
        plot_bgcolor='#ffffff',
        paper_bgcolor='#ffffff',
        font=dict(color='#333333'),
        xaxis_title_font=dict(color='#333333'),
        yaxis_title_font=dict(color='#333333'),
    )

    fig = go.Figure(data=traces, layout=layout)
    leaderboard_graph = fig.to_json()

    # 정렬된 팀 목록을 기반으로 랭킹 생성 및 마지막 제출 시간 포함
    rankings = [
        (i + 1, team.name, team.total_points, team_last_submission_times.get(team.name)) 
        for i, team in enumerate(sorted_teams)
    ]

    context = {
        'teams': sorted_teams,
        'leaderboard_graph': leaderboard_graph,
        'rankings': rankings,
        'mvp': user_stats,
    }

    return render(request, 'challenges/leaderboard.html', context)


import pytz
KST = pytz.timezone('Asia/Seoul')

@login_required
def leaderboard_data(request):
    teams = Team.objects.all()
    for team in teams:
        update_team_points(team)
    teams = teams.order_by('-total_points', 'name')

    submissions = Submission.objects.filter(correct=True).select_related('team')
    user_dict = defaultdict(lambda: {'count': 0, 'last_submission_time': None, 'points': 0})

    for submission in submissions:
        user = submission.user
        user_dict[user]['count'] += 1
        user_dict[user]['points'] += submission.challenge.points
        if user_dict[user]['last_submission_time'] is None or submission.submitted_at > user_dict[user]['last_submission_time']:
            user_dict[user]['last_submission_time'] = submission.submitted_at

    user_stats = []
    for user, stats in user_dict.items():
        user_stats.append((user.username, stats['count'], stats['points'], stats['last_submission_time']))

    user_stats.sort(key=lambda x: (-x[2], x[3] if x[3] else datetime.datetime.max))

    last_submission_times = submissions.values('team').annotate(last_submission_time=Max('submitted_at'))
    team_last_submission_times = {}
    for team in teams:
        last_submission_time = next(
            (item['last_submission_time'] for item in last_submission_times if item['team'] == team.id),
            None
        )
        if last_submission_time is not None:
            team_last_submission_times[team.name] = last_submission_time

    sorted_teams = sorted(teams, key=lambda team: (
        -team.total_points,
        team_last_submission_times.get(team.name) or datetime.datetime.max
    ))

    rankings = [
        (i + 1, team.name, team.total_points, team_last_submission_times.get(team.name))
        for i, team in enumerate(sorted_teams)
    ]

    # 그래프용 데이터 생성
    team_time_series_data = {}
    for team in sorted_teams:
        last_submission_time = team_last_submission_times.get(team.name)
        if last_submission_time is None:
            continue
        team_subs = Submission.objects.filter(team=team, correct=True, submitted_at__lte=last_submission_time).order_by('submitted_at')
        time_series_data = defaultdict(int)
        for tsb in team_subs:
            timestamp = tsb.submitted_at
            points = tsb.challenge.points
            time_series_data[timestamp] += points

        sorted_times = sorted(time_series_data.keys())
        sorted_points = [time_series_data[t] for t in sorted_times]

        cumulative_points = []
        running_total = 0
        for p in sorted_points:
            running_total += p
            cumulative_points.append(running_total)

        team_time_series_data[team.name] = (sorted_times, cumulative_points)

    traces = []
    colors = ['#FF5733', '#33FF57', '#3357FF', '#F3FF33', '#FF33F6']
    for i, (team_name, (times, points)) in enumerate(team_time_series_data.items()):
        # times는 UTC datetime, KST로 변환 필요 시 다음과 같이 변환 가능
        # 하지만 Plotly에서는 ISO시간을 그대로 UTC로 두고, 클라이언트에서 표시를 바꿀 수도 있음.
        # 여기서는 그래프는 기존대로 UTC나 ISO로 두고, 표만 KST로 보여주도록 하겠습니다.
        # 굳이 그래프 x축도 KST로 바꾸려면 times를 KST로 변환 후 isoformat() 하면 됩니다.
        trace = go.Scatter(
            x=[t.isoformat() for t in times],
            y=points,
            mode='lines+markers',
            name=team_name,
            line=dict(color=colors[i % len(colors)]),
        )
        traces.append(trace)

    layout = go.Layout(
        title='Points Over Time',
        xaxis=dict(title='Time', tickformat='%H:%M:%S'),
        yaxis=dict(title='Total Points'),
        plot_bgcolor='#ffffff',
        paper_bgcolor='#ffffff',
        font=dict(color='#333333'),
        xaxis_title_font=dict(color='#333333'),
        yaxis_title_font=dict(color='#333333'),
        margin=dict(l=50, r=50, t=50, b=50)
    )

    fig = go.Figure(data=traces, layout=layout)
    leaderboard_graph_json = fig.to_json()

    rankings_json = []
    for r, t_name, pts, last_sub in rankings:
        if last_sub:
            # KST 변환
            last_sub_kst = last_sub.astimezone(KST)
            last_sub_str = last_sub_kst.strftime("%Y-%m-%d %H:%M:%S")
        else:
            last_sub_str = ""
        rankings_json.append([r, t_name, pts, last_sub_str])

    mvp_json = []
    for username, solved, pts, last_sub in user_stats:
        if last_sub:
            last_sub_kst = last_sub.astimezone(KST)
            last_sub_str = last_sub_kst.strftime("%Y-%m-%d %H:%M:%S")
        else:
            last_sub_str = ""
        mvp_json.append([username, solved, pts, last_sub_str])

    return JsonResponse({
        'rankings': rankings_json,
        'mvp': mvp_json,
        'graph': leaderboard_graph_json,
    })




@login_required
def problem_stats(request):
    challenges = Challenge.objects.all()
    challenge_names = [challenge.title for challenge in challenges]
    solve_counts = [Submission.objects.filter(challenge=challenge, correct=True).count() for challenge in challenges]

    fig, ax = plt.subplots()
    ax.barh(challenge_names, solve_counts, color='skyblue')
    ax.set_xlabel('Number of Correct Submissions')
    ax.set_title('Problem Solving Stats')

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    problem_stats_graph = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)

    context = {
        'problem_stats_graph': problem_stats_graph
    }

    return render(request, 'challenges/problem_stats.html', context)

@login_required
def submission_stats(request):
    user = request.user
    team = user.team_set.first()

    if not team:
        messages.error(request, 'You are not part of any team.')
        return redirect("challenges:feeds")

    submissions = Submission.objects.filter(team=team, correct=True).order_by('submitted_at')
    dates = [submission.submitted_at.date() for submission in submissions]
    date_counts = {}

    for date in dates:
        date_counts[date] = date_counts.get(date, 0) + 1

    fig, ax = plt.subplots(figsize=(12, 6))

    sorted_dates = sorted(date_counts.keys())
    sorted_counts = [date_counts[date] for date in sorted_dates]

    ax.plot(sorted_dates, sorted_counts, marker='o', linestyle='-', color='b')
    ax.set_title('Correct Submissions Over Time')
    ax.set_xlabel('Date')
    ax.set_ylabel('Number of Correct Submissions')

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator())
    fig.autofmt_xdate()

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    submission_stats_graph = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)

    context = {
        'submission_stats_graph': submission_stats_graph
    }

    return render(request, 'challenges/submission_stats.html', context)
