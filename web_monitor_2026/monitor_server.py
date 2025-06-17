# web_monitor_2026/monitor_server.py
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import threading
from datetime import datetime
import logging
import asyncio
from typing import Dict, Any

class BotMonitorServer:
    """Real-time web monitor for Options Trading Bot 2026"""

    def __init__(self, bot_instance=None, port=5000):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'options_bot_2026_monitor'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.bot_instance = bot_instance
        self.port = port
        self.running = False
        self.current_data = {
            'portfolio_value': 0,
            'daily_pnl': 0,
            'total_pnl': 0,
            'active_trades': [],
            'recent_actions': [],
            'errors': [],
            'bot_status': 'Stopped',
            'risk_metrics': {},
            'market_sentiment': {},
            'screening_results': {
                'bull': [],
                'bear': [],
                'volatile': [],
                'last_update': None
            },
            'health_metrics': {
                'ibkr_connection': False,
                'portfolio_provider': False,
                'execution_engine': False,
                'risk_manager': False,
                'news_handler': False,
                'stock_screener': False
            },
            'last_update': datetime.now().isoformat()
        }
        self.logger = logging.getLogger(__name__)
        self._setup_routes()
        self._setup_socketio_events()

    def _setup_routes(self):
        @self.app.route('/')
        def dashboard():
            return render_template('dashboard.html')
        
        @self.app.route('/api/status')
        def get_status():
            return jsonify(self.current_data)
        
        @self.app.route('/api/trades')
        def get_trades():
            return jsonify({
                'active_trades': self.current_data['active_trades'],
                'trade_count': len(self.current_data['active_trades'])
            })
        
        @self.app.route('/api/health')
        def get_health():
            return jsonify(self.current_data['health_metrics'])

    def _setup_socketio_events(self):
        @self.socketio.on('connect')
        def handle_connect():
            emit('status_update', self.current_data)
            self.logger.info("Client connected to monitor")
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            self.logger.info("Client disconnected from monitor")
        
        @self.socketio.on('request_update')
        def handle_update_request():
            emit('status_update', self.current_data)

    async def _update_loop(self):
        """Background task to update monitor data"""
        while self.running:
            try:
                if self.bot_instance:
                    # Update portfolio value
                    portfolio_value = await self.bot_instance.get_portfolio_value()
                    self.update_portfolio_value(portfolio_value)
                    
                    # Update active trades
                    active_trades = await self.bot_instance.get_active_trades()
                    self.update_active_trades(active_trades)
                    
                    # Update risk metrics
                    risk_metrics = await self.bot_instance.get_risk_metrics()
                    self.update_risk_metrics(risk_metrics)
                    
                    # Update health status
                    health_status = await self.bot_instance.get_health_status()
                    self.update_health_status(health_status)
                
                await asyncio.sleep(5)  # Update every 5 seconds
            except Exception as e:
                self.logger.error(f"Error in update loop: {e}")
                await asyncio.sleep(5)

    def update_portfolio_value(self, value: float):
        """Update portfolio value and calculate PnL"""
        old_value = self.current_data['portfolio_value']
        self.current_data['portfolio_value'] = value
        self.current_data['daily_pnl'] = value - old_value if old_value > 0 else 0
        self.current_data['last_update'] = datetime.now().isoformat()
        self._broadcast_update()

    def add_trade_action(self, action_type: str, symbol: str, strategy: str, details: dict):
        """Add a new trade action to the recent actions list"""
        action = {
            'timestamp': datetime.now().isoformat(),
            'type': action_type,
            'symbol': symbol,
            'strategy': strategy,
            'details': details
        }
        self.current_data['recent_actions'].insert(0, action)
        self.current_data['recent_actions'] = self.current_data['recent_actions'][:50]
        self.current_data['last_update'] = datetime.now().isoformat()
        self._broadcast_update()

    def update_active_trades(self, trades: list):
        """Update the list of active trades"""
        self.current_data['active_trades'] = trades
        self.current_data['last_update'] = datetime.now().isoformat()
        self._broadcast_update()

    def add_error(self, error_type: str, message: str, details: dict = None):
        """Add a new error to the error list"""
        error = {
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'message': message,
            'details': details or {}
        }
        self.current_data['errors'].insert(0, error)
        self.current_data['errors'] = self.current_data['errors'][:20]
        self.current_data['last_update'] = datetime.now().isoformat()
        self._broadcast_update()

    def update_risk_metrics(self, metrics: dict):
        """Update risk metrics"""
        self.current_data['risk_metrics'] = metrics
        self.current_data['last_update'] = datetime.now().isoformat()
        self._broadcast_update()

    def update_bot_status(self, status: str):
        """Update bot status"""
        self.current_data['bot_status'] = status
        self.current_data['last_update'] = datetime.now().isoformat()
        self._broadcast_update()

    def update_health_status(self, health_data: dict):
        """Update the health status of the bot components"""
        if not isinstance(health_data, dict):
            self.logger.error(f"Invalid health data format: {health_data}")
            return
            
        # Update only valid health metrics
        for component, status in health_data.items():
            if component in self.current_data['health_metrics']:
                self.current_data['health_metrics'][component] = bool(status)
        
        self.current_data['last_update'] = datetime.now().isoformat()
        self._broadcast_update()

    def update_market_sentiment(self, sentiment_data: dict):
        """Update the market sentiment data"""
        if not isinstance(sentiment_data, dict):
            self.logger.error(f"Invalid sentiment data format: {sentiment_data}")
            return
        
        # Store sentiment data
        self.current_data['market_sentiment'] = sentiment_data
        self.current_data['last_update'] = datetime.now().isoformat()
        self._broadcast_update()

    def update_screening_results(self, screening_results: dict):
        """Update the stock screening results"""
        if not isinstance(screening_results, dict):
            self.logger.error(f"Invalid screening results format: {screening_results}")
            return
        
        # Update screening results
        self.current_data['screening_results']['bull'] = screening_results.get('bull', [])
        self.current_data['screening_results']['bear'] = screening_results.get('bear', [])
        self.current_data['screening_results']['volatile'] = screening_results.get('volatile', [])
        self.current_data['screening_results']['last_update'] = datetime.now().isoformat()
        self.current_data['last_update'] = datetime.now().isoformat()
        self._broadcast_update()
        
        # Log summary
        total_stocks = (
            len(self.current_data['screening_results']['bull']) +
            len(self.current_data['screening_results']['bear']) +
            len(self.current_data['screening_results']['volatile'])
        )
        self.logger.info(f"📊 Updated screening results: {total_stocks} stocks across categories")

    def _broadcast_update(self):
        """Broadcast updates to all connected clients"""
        try:
            self.socketio.emit('status_update', self.current_data)
        except Exception as e:
            self.logger.error(f"Error broadcasting update: {e}")

    def start_server(self):
        """Start the web monitor server"""
        self.running = True
        self.logger.info(f"🖥️ Starting web monitor on http://localhost:{self.port}")
        
        # Start the update loop in a separate thread
        def run_update_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._update_loop())
        
        update_thread = threading.Thread(target=run_update_loop, daemon=True)
        update_thread.start()
        
        # Start the Flask server
        self.socketio.run(self.app, host='0.0.0.0', port=self.port, debug=False)

    def stop_server(self):
        """Stop the web monitor server"""
        self.running = False
        self.logger.info("Web monitor stopped")
