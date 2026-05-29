import subprocess
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from autotrading.config import get_auto_trading_config
from autotrading.models import AutoPosition, AutoTradeLog, AutoTradeSettings


@login_required
def dashboard(request):
    config = get_auto_trading_config()
    user_bots = AutoTradeSettings.objects.filter(user=request.user).order_by('symbol')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'save_settings':
            symbol = request.POST.get('symbol', 'BTC')
            stop_loss_pct = Decimal(request.POST.get('stop_loss_pct', '0.02'))
            take_profit_pct = Decimal(request.POST.get('take_profit_pct', '0.05'))
            trade_amount_usdt = Decimal(request.POST.get('trade_amount_usdt', '100'))
            is_active = request.POST.get('is_active') == 'on'
            
            AutoTradeSettings.objects.update_or_create(
                user=request.user,
                symbol=symbol,
                defaults={
                    'stop_loss_pct': stop_loss_pct,
                    'take_profit_pct': take_profit_pct,
                    'trade_amount_usdt': trade_amount_usdt,
                    'is_active': is_active
                }
            )
            messages.success(request, f'Налаштування бота для {symbol} збережено!')
            return redirect('autotrading_dashboard')
            
        elif action == 'delete_bot':
            symbol = request.POST.get('symbol')
            if symbol:
                AutoTradeSettings.objects.filter(user=request.user, symbol=symbol).delete()
                messages.success(request, f'Бота для {symbol} видалено.')
            return redirect('autotrading_dashboard')

        elif action == 'run_cycle' and request.user.is_staff:
            try:
                # Run heavy cycle in background to avoid Gunicorn worker timeout.
                base_dir = Path(settings.BASE_DIR)
                subprocess.Popen(
                    [sys.executable, "manage.py", "run_autotrading"],
                    cwd=base_dir,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                messages.success(
                    request,
                    'Тестовий цикл запущено у фоні. Оновіть сторінку через 20-60 секунд.',
                )
            except Exception as exc:
                messages.error(request, f'Помилка циклу: {exc}')
            return redirect('autotrading_dashboard')
        elif action == 'clear_logs':
            request.session['autotrading_logs_hidden_before'] = timezone.now().isoformat()
            messages.success(request, 'Історію сигналів та угод приховано (дані в БД не видалені).')
            return redirect('autotrading_dashboard')
        elif action == 'show_all_logs':
            request.session.pop('autotrading_logs_hidden_before', None)
            messages.success(request, 'Показано всю історію сигналів та угод.')
            return redirect('autotrading_dashboard')

    logs_qs = AutoTradeLog.objects.filter(user=request.user).select_related('user')
    hidden_before = request.session.get('autotrading_logs_hidden_before')
    if hidden_before:
        try:
            cutoff = datetime.fromisoformat(hidden_before)
            if timezone.is_naive(cutoff):
                cutoff = timezone.make_aware(cutoff)
            logs_qs = logs_qs.filter(created_at__gte=cutoff)
        except Exception:
            request.session.pop('autotrading_logs_hidden_before', None)
    logs = logs_qs[:50]
    open_positions = AutoPosition.objects.filter(user=request.user, is_open=True)
    closed_positions = AutoPosition.objects.filter(user=request.user, is_open=False)[:10]

    return render(
        request,
        'autotrading/dashboard.html',
        {
            'user_bots': user_bots,
            'logs': logs,
            'open_positions': open_positions,
            'closed_positions': closed_positions,
            'supported_pairs': config.get('pairs', []),
            'models_dir': str(config.get('models_dir', '')),
            'logs_hidden_before': hidden_before,
        },
    )
