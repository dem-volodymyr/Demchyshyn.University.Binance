from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

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
                from autotrading.services.auto_trading_service import build_auto_trading_service
                active_bots = AutoTradeSettings.objects.filter(user=request.user, is_active=True)
                results_len = 0
                for bot_setting in active_bots:
                    service = build_auto_trading_service(bot_setting)
                    results = service.run_cycle()
                    results_len += len(results)
                messages.success(
                    request,
                    f'Тестовий цикл виконано: {results_len} записів у журналі.',
                )
            except Exception as exc:
                messages.error(request, f'Помилка циклу: {exc}')
            return redirect('autotrading_dashboard')

    logs = AutoTradeLog.objects.filter(user=request.user).select_related('user')[:50]
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
        },
    )
