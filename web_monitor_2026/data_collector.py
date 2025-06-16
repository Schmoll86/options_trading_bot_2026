from datetime import datetime

def collect_portfolio_data(bot):
    """
    Collects portfolio value and P&L from the bot.
    Args:
        bot: The main OptionsTradingBot2026 instance.
    Returns:
        dict: Portfolio data.
    """
    value = bot.risk_manager.get_portfolio_value() if bot.risk_manager else 0
    risk_summary = bot.risk_manager.get_risk_summary() if bot.risk_manager else {}
    return {
        'portfolio_value': value,
        'max_trade_size': risk_summary.get('max_trade_size', 0),
        'daily_loss': risk_summary.get('daily_loss', 0),
        'daily_loss_limit': risk_summary.get('daily_loss_limit', 0),
        'trading_halted': risk_summary.get('trading_halted', False),
        'active_trailing_stops': risk_summary.get('active_trailing_stops', 0),
        'last_update': datetime.now().isoformat()
    }

def collect_active_trades(bot):
    """
    Collects active trades from the bot.
    Args:
        bot: The main OptionsTradingBot2026 instance.
    Returns:
        list: List of active trade dicts.
    """
    if bot.ibkr_client:
        try:
            return bot.ibkr_client.ib.positions()
        except Exception:
            return []
    return []

def collect_recent_actions(bot):
    """
    Returns the recent actions list from the web monitor.
    Args:
        bot: The main OptionsTradingBot2026 instance.
    Returns:
        list: List of recent actions.
    """
    if hasattr(bot, 'web_monitor'):
        return bot.web_monitor.current_data.get('recent_actions', [])
    return []

def collect_errors(bot):
    """
    Returns the error list from the web monitor.
    Args:
        bot: The main OptionsTradingBot2026 instance.
    Returns:
        list: List of errors.
    """
    if hasattr(bot, 'web_monitor'):
        return bot.web_monitor.current_data.get('errors', [])
    return []

def collect_risk_metrics(bot):
    """
    Returns the risk metrics from the risk manager.
    Args:
        bot: The main OptionsTradingBot2026 instance.
    Returns:
        dict: Risk metrics.
    """
    if bot.risk_manager:
        return bot.risk_manager.get_risk_summary()
    return {}

def collect_all_data(bot):
    """
    Aggregates all data for the dashboard.
    Args:
        bot: The main OptionsTradingBot2026 instance.
    Returns:
        dict: Aggregated dashboard data.
    """
    return {
        'portfolio': collect_portfolio_data(bot),
        'active_trades': collect_active_trades(bot),
        'recent_actions': collect_recent_actions(bot),
        'errors': collect_errors(bot),
        'risk_metrics': collect_risk_metrics(bot),
        'bot_status': getattr(bot, 'running', False),
        'last_update': datetime.now().isoformat()
    }

