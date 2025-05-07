import datetime
import base64
import pytz
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
from collections import defaultdict
from datetime import timedelta

import plotly.graph_objs as go
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Max
from django.utils import timezone
from django.http import JsonResponse
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Challenge, Submission

KST = pytz.timezone('Asia/Seoul')


def index(request):
    if request.user.is_authenticated:
        return redirect("challenges:feeds")
    return redirect("accounts:login")


@login_required
def feeds(request):
    user = request.user

    ALL = 'all'
    categories = [(ALL, 'All')] + list(Challenge.CATEGORY_CHOICES)
    selected_category = request.GET.get('category', ALL)

    qs = Challenge.objects.all()
    if selected_category != ALL:
        qs = qs.filter(category=selected_category)

    solved_qs = Submission.objects.filter(user=user, correct=True)
    solved_challenges = solved_qs.values_list('challenge_id', flat=True)
    solved_any = solved_qs.exists()
    return render(request, 'challenges/feeds.html', {
        'categories': categories,
        'selected_category': selected_category,
        'challenges': qs,
        'solved_challenges':solved_challenges,
        'solved_any': solved_any,
    })


@login_required
def challenge_detail(request, challenge_id):
    user = request.user
    ch = get_object_or_404(Challenge, pk=challenge_id)

    solved = Submission.objects.filter(
        user=user, challenge=ch, correct=True
    ).exists()
    num_solvers = Submission.objects.filter(
        challenge=ch, correct=True
    ).values('user').distinct().count()

    if request.method == 'POST':
        flag = request.POST.get('flag', '')
        correct = (ch.flag == flag)

        Submission.objects.update_or_create(
            user=user,
            challenge=ch,
            defaults={'submitted_flag': flag, 'correct': correct}
        )
        messages.success(request, 'Correct flag!' if correct else 'Incorrect flag.')
        ch.update_challenge_score()
        return redirect('challenges:challenge_detail', challenge_id=challenge_id)

    return render(request, 'challenges/challenge_detail.html', {
        'challenge': ch,
        'solved': solved,
        'num_solvers': num_solvers,
    })


@login_required
def submit_flag(request):
    user = request.user
    if request.method != 'POST':
        return redirect('challenges:feeds')

    cid = request.POST.get('challenge_id')
    flag = request.POST.get('flag')
    ch = get_object_or_404(Challenge, pk=cid)

    last = Submission.objects.filter(user=user, challenge=ch)\
                             .order_by('-submitted_at').first()
    if last and timezone.now() - last.submitted_at < timedelta(seconds=30):
        rem = 30 - (timezone.now() - last.submitted_at).seconds
        messages.error(request, f'Please wait {rem}s before retry.')
        return redirect('challenges:challenge_detail', challenge_id=cid)

    try:
        with transaction.atomic():
            now = timezone.now()
            ex = Submission.objects.select_for_update()\
                                   .filter(user=user, challenge=ch)\
                                   .first()
            if ex:
                if ex.correct:
                    messages.error(request, 'Already solved!')
                    return redirect('challenges:challenge_detail', challenge_id=cid)
                if now - ex.submitted_at < timedelta(seconds=30):
                    rem = 30 - (now - ex.submitted_at).seconds
                    messages.error(request, f'Please wait {rem}s before retry.')
                    return redirect('challenges:challenge_detail', challenge_id=cid)

                ex.submitted_flag = flag
                ex.correct = (ch.flag == flag)
                ex.submitted_at = now
                ex.save()
                messages.success(request, 'Correct flag!' if ex.correct else 'Incorrect flag.')
            else:
                correct = (ch.flag == flag)
                Submission.objects.create(
                    user=user, challenge=ch,
                    submitted_flag=flag, correct=correct,
                    submitted_at=now
                )
                messages.success(request, 'Correct flag!' if correct else 'Incorrect flag.')

            ch.update_challenge_score()
    except Exception as e:
        messages.error(request, f'Error during submission: {e}')

    return redirect('challenges:challenge_detail', challenge_id=cid)


@receiver(post_delete, sender=Submission)
def noop_on_delete(sender, instance, **kwargs):
    pass


@login_required
def leaderboard(request):
    # 단순히 페이지 렌더링: JS가 leaderboard_data 로딩 후 그래프/테이블 그리도록 합니다.
    return render(request, 'challenges/leaderboard.html')


@login_required
def leaderboard_data(request):
    # 1) 개인 통계 집계
    subs = Submission.objects.filter(correct=True).select_related('user')
    user_stats = defaultdict(lambda: {'count': 0, 'points': 0, 'last': None})
    user_events = defaultdict(list)

    for s in subs:
        u = s.user.username
        pts = s.challenge.points
        tm  = s.submitted_at
        user_stats[u]['count'] += 1
        user_stats[u]['points'] += pts
        if not user_stats[u]['last'] or tm > user_stats[u]['last']:
            user_stats[u]['last'] = tm
        user_events[u].append((tm, pts))

    # 2) 사용자별 제출 시간순 누적 점수 데이터 생성
    traces = []
    for i, (u, events) in enumerate(user_events.items()):
        events.sort(key=lambda x: x[0])
        times, cum = [], []
        total = 0
        for tm, pts in events:
            total += pts
            times.append(tm.isoformat())
            cum.append(total)
        traces.append(
            go.Scatter(
                x=times,
                y=cum,
                mode='lines+markers',
                name=u
            )
        )

    layout = go.Layout(
        title='Score Over Time',
        xaxis=dict(title='Time'),
        yaxis=dict(title='Cumulative Points'),
        plot_bgcolor='#fff', paper_bgcolor='#fff'
    )
    fig = go.Figure(data=traces, layout=layout)
    graph_json = fig.to_json()

    # 3) 랭킹 & MVP JSON
    ranking = sorted(
        [(u, d['count'], d['points'], d['last'].astimezone(KST).strftime("%Y-%m-%d %H:%M:%S"))
         for u, d in user_stats.items()],
        key=lambda x: (-x[2], x[3])
    )
    ranking_json = [[i+1, *r] for i, r in enumerate(ranking)]

    mvp_json = [
        [u, d['count'], d['points'], d['last'].astimezone(KST).strftime("%Y-%m-%d %H:%M:%S")]
        for u, d in sorted(
            user_stats.items(),
            key=lambda x: (-x[1]['points'], x[1]['last'])
        )
    ]

    return JsonResponse({
        'graph': graph_json,
        'rankings': ranking_json,
#        'mvp': mvp_json,
    })


@login_required
def problem_stats(request):
    challenges = Challenge.objects.all()
    names = [c.title for c in challenges]
    counts = [Submission.objects.filter(challenge=c, correct=True).count()
              for c in challenges]

    fig, ax = plt.subplots()
    ax.barh(names, counts)
    ax.set_xlabel('Correct Submissions')
    ax.set_title('Problem Solving Stats')

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img = base64.b64encode(buf.getvalue()).decode()
    plt.close(fig)

    return render(request, 'challenges/problem_stats.html', {
        'problem_stats_graph': img
    })


@login_required
def submission_stats(request):
    subs = Submission.objects.filter(correct=True, user=request.user)
    date_counts = defaultdict(int)
    for s in subs:
        date_counts[s.submitted_at.date()] += 1

    dates = sorted(date_counts)
    counts = [date_counts[d] for d in dates]

    fig, ax = plt.subplots()
    ax.plot(dates, counts, marker='o')
    ax.set_title('Your Correct Submissions Over Time')
    ax.set_xlabel('Date')
    ax.set_ylabel('Count')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate()

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img = base64.b64encode(buf.getvalue()).decode()
    plt.close(fig)

    return render(request, 'challenges/submission_stats.html', {
        'submission_stats_graph': img
    })

@login_required
def flag_page(request):
    # 한 문제라도 맞췄는지 확인
    solved_any = Submission.objects.filter(user=request.user, correct=True).exists()
    if not solved_any:
        messages.error(request, "문제를 하나 이상 풀어야 비밀번호를 확인할 수 있습니다.")
        return redirect('challenges:feeds')

    # 설정에서 가져온 오픈카톡 정보
    chat_url = settings.MJSEC_KAKAO_CHAT_URL
    password = settings.MJSEC_KAKAO_CHAT_PASSWORD

    return render(request, 'challenges/flag.html', {
        'kakao_chat_url': chat_url,
        'kakao_password': password,
    })