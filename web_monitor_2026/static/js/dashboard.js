class TradingBotMonitor {
    constructor() {
        this.socket = io();
        this.portfolioChart = null;
        this.portfolioHistory = [];
        this.setupSocketEvents();
        this.initializeChart();
    }

    setupSocketEvents() {
        this.socket.on('connect', () => {
            console.log('Connected to bot monitor');
            this.updateBotStatus('Connected', 'connecting');
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from bot monitor');
            this.updateBotStatus('Disconnected', 'stopped');
        });

        this.socket.on('status_update', (data) => {
            this.updateDashboard(data);
        });

        // Request initial update
        this.socket.emit('request_update');
    }

    updateDashboard(data) {
        // Update portfolio metrics
        this.updatePortfolioMetrics(data);
        
        // Update risk metrics
        this.updateRiskMetrics(data);
        
        // Update active trades
        this.updateActiveTrades(data.active_trades);
        
        // Update recent actions
        this.updateRecentActions(data.recent_actions);
        
        // Update errors
        this.updateErrors(data.errors);
        
        // Update bot status
        this.updateBotStatus(data.bot_status, 'running');
        
        // Update last update time
        this.updateLastUpdateTime(data.last_update);
        
        // Update chart
        this.updateChart(data.portfolio_value);
    }

    updatePortfolioMetrics(data) {
        document.getElementById('portfolio-value').textContent = 
            this.formatCurrency(data.portfolio_value);
        
        const dailyPnlElement = document.getElementById('daily-pnl');
        dailyPnlElement.textContent = this.formatCurrency(data.daily_pnl);
        dailyPnlElement.className = `metric-value ${data.daily_pnl >= 0 ? 'positive' : 'negative'}`;
        
        const totalPnlElement = document.getElementById('total-pnl');
        totalPnlElement.textContent = this.formatCurrency(data.total_pnl);
        totalPnlElement.className = `metric-value ${data.total_pnl >= 0 ? 'positive' : 'negative'}`;
        
        document.getElementById('active-trades-count').textContent = 
            data.active_trades.length;
    }

    updateRiskMetrics(data) {
        const riskMetrics = data.risk_metrics || {};
        
        document.getElementById('daily-loss').textContent = 
            this.formatCurrency(riskMetrics.daily_loss || 0);
        
        document.getElementById('daily-limit').textContent = 
            this.formatCurrency(riskMetrics.daily_loss_limit || 1000);
        
        const tradingStatus = riskMetrics.trading_halted ? 'HALTED' : 'ACTIVE';
        const statusElement = document.getElementById('trading-status');
        statusElement.textContent = tradingStatus;
        statusElement.style.color = riskMetrics.trading_halted ? '#e74c3c' : '#27ae60';
    }

    updateActiveTrades(trades) {
        const container = document.getElementById('active-trades-list');
        
        if (!trades || trades.length === 0) {
            container.innerHTML = '<p class="no-data">No active trades</p>';
            return;
        }

        container.innerHTML = trades.map(trade => `
            <div class="trade-item">
                <div class="item-header">
                    <span>${trade.symbol} - ${trade.strategy}</span>
                    <span>${this.formatCurrency(trade.unrealized_pnl || 0)}</span>
                </div>
                <div class="item-details">
                    Entry: ${this.formatCurrency(trade.entry_price || 0)} | 
                    Current: ${this.formatCurrency(trade.current_price || 0)} | 
                    Size: ${trade.size || 0}
                </div>
            </div>
        `).join('');
    }

    updateRecentActions(actions) {
        const container = document.getElementById('recent-actions');
        
        if (!actions || actions.length === 0) {
            container.innerHTML = '<p class="no-data">No recent actions</p>';
            return;
        }

        container.innerHTML = actions.slice(0, 10).map(action => `
            <div class="action-item">
                <div class="item-header">
                    <span>${action.type}: ${action.symbol}</span>
                    <span>${this.formatTime(action.timestamp)}</span>
                </div>
                <div class="item-details">
                    Strategy: ${action.strategy} | ${JSON.stringify(action.details)}
                </div>
            </div>
        `).join('');
    }

    updateErrors(errors) {
        const container = document.getElementById('errors-list');
        
        if (!errors || errors.length === 0) {
            container.innerHTML = '<p class="no-data">No errors</p>';
            return;
        }

        container.innerHTML = errors.slice(0, 5).map(error => `
            <div class="error-item">
                <div class="item-header">
                    <span>${error.type}</span>
                    <span>${this.formatTime(error.timestamp)}</span>
                </div>
                <div class="item-details">
                    ${error.message}
                </div>
            </div>
        `).join('');
    }

    updateBotStatus(status, className) {
        const statusElement = document.getElementById('bot-status');
        statusElement.textContent = status;
        statusElement.className = `status-badge ${className}`;
    }

    updateLastUpdateTime(timestamp) {
        const timeElement = document.getElementById('last-update');
        timeElement.textContent = `Last Update: ${this.formatTime(timestamp)}`;
    }

    initializeChart() {
        const ctx = document.getElementById('performance-chart').getContext('2d');
        this.portfolioChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Portfolio Value',
                    data: [],
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    updateChart(portfolioValue) {
        const now = new Date();
        this.portfolioHistory.push({
            time: now,
            value: portfolioValue
        });

        // Keep only last 50 data points
        if (this.portfolioHistory.length > 50) {
            this.portfolioHistory.shift();
        }

        this.portfolioChart.data.labels = this.portfolioHistory.map(point => 
            point.time.toLocaleTimeString()
        );
        this.portfolioChart.data.datasets[0].data = this.portfolioHistory.map(point => 
            point.value
        );
        this.portfolioChart.update('none');
    }

    formatCurrency(value) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(value || 0);
    }

    formatTime(timestamp) {
        return new Date(timestamp).toLocaleTimeString();
    }
}

// Initialize monitor when page loads
document.addEventListener('DOMContentLoaded', () => {
    new TradingBotMonitor();
});
