from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def index(request):
    return render(request, 'news/index.html')


@login_required
def markets(request):
    """Live Markets — TradingView market widgets."""
    return render(request, 'news/markets.html')
