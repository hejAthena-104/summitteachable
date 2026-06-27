from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import AnalysisPost


@login_required
def feed(request):
    """Public feed of published, bias-coded educational analysis."""
    posts = AnalysisPost.objects.filter(status='published')
    return render(request, 'analysis/feed.html', {'posts': posts})


@login_required
def submit(request):
    """Member submission form. New posts are pending until moderated."""
    if request.method == 'POST':
        title = (request.POST.get('title') or '').strip()
        market = request.POST.get('market') or 'forex'
        symbol = (request.POST.get('symbol') or '').strip()
        bias = request.POST.get('bias') or 'neutral'
        timeframe = (request.POST.get('timeframe') or '').strip()
        tv_symbol = (request.POST.get('tv_symbol') or '').strip()
        body = (request.POST.get('body') or '').strip()

        valid_markets = dict(AnalysisPost.MARKET_CHOICES)
        valid_bias = dict(AnalysisPost.BIAS_CHOICES)

        if not title or not symbol or not timeframe or not body:
            messages.error(request, 'Please fill in the title, symbol, timeframe and analysis body.')
        elif market not in valid_markets or bias not in valid_bias:
            messages.error(request, 'Please choose a valid market and bias.')
        else:
            AnalysisPost.objects.create(
                author=request.user,
                title=title,
                market=market,
                symbol=symbol,
                bias=bias,
                timeframe=timeframe,
                tv_symbol=tv_symbol,
                body=body,
                chart_image=request.FILES.get('chart_image'),
                status='pending',
                is_house=False,
            )
            messages.success(
                request,
                'Submitted for review — our team will publish approved analysis.',
            )
            return redirect('analysis:my_posts')

    context = {
        'market_choices': AnalysisPost.MARKET_CHOICES,
        'bias_choices': AnalysisPost.BIAS_CHOICES,
    }
    return render(request, 'analysis/submit.html', context)


@login_required
def my_posts(request):
    """The signed-in member's own submissions and their review status."""
    posts = AnalysisPost.objects.filter(author=request.user)
    return render(request, 'analysis/my_posts.html', {'posts': posts})
