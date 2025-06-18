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
            'activity_log': [],
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
        
        @self.app.route('/api/simulate')
        def simulate_trading():
            """Simulate a complete trading cycle and return what would happen"""
            try:
                if not self.bot_instance or not hasattr(self.bot_instance, 'execution_engine'):
                    return jsonify({
                        'success': False,
                        'error': 'Bot not running or execution engine unavailable'
                    })
                
                execution_engine = self.bot_instance.execution_engine
                
                # Run simulation without executing actual trades
                simulation_results = self._run_simulation(execution_engine)
                
                return jsonify({
                    'success': True,
                    'simulation': simulation_results,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"Error in simulation: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })

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

    def log_activity(self, component: str, level: str, message: str, details: dict = None):
        """Log an activity entry to the real-time activity log"""
        try:
            activity_entry = {
                'timestamp': datetime.now().isoformat(),
                'component': component.upper(),
                'level': level.lower(),
                'message': message,
                'details': details or {}
            }
            
            # Add to activity log (keep last 200 entries)
            self.current_data['activity_log'].insert(0, activity_entry)
            self.current_data['activity_log'] = self.current_data['activity_log'][:200]
            
            # Emit immediately to connected clients
            self.socketio.emit('activity_log', activity_entry)
            
        except Exception as e:
            self.logger.error(f"Error logging activity: {e}")

    def _broadcast_update(self):
        """Broadcast updates to all connected clients"""
        try:
            self.socketio.emit('status_update', self.current_data)
        except Exception as e:
            self.logger.error(f"Error broadcasting update: {e}")

    def _run_simulation(self, execution_engine):
        """Run a complete trading simulation using real market data"""
        simulation_results = {
            'sentiment_analysis': None,
            'market_data': {},
            'stock_screening': None,
            'options_analysis': [],
            'execution_plan': [],
            'errors': []
        }
        
        try:
            import asyncio
            import nest_asyncio
            
            # Create event loop for async operations
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Step 1: Get real market sentiment using news handler
                self.logger.info("🔍 SIMULATION: Getting real market sentiment...")
                sentiment = loop.run_until_complete(
                    execution_engine.news_analyzer.get_market_sentiment()
                )
                simulation_results['sentiment_analysis'] = sentiment
                
                # Extract market data from sentiment for display
                if sentiment:
                    tech_sentiment = sentiment.get('technical_sentiment', {})
                    simulation_results['market_data'] = {
                        'vix_level': tech_sentiment.get('vix_level', 20.0),
                        'spy_momentum': tech_sentiment.get('market_momentum', 0.0),
                        'bull_bear_ratio': tech_sentiment.get('bull_bear_ratio', 0.5),
                        'sector_sentiment': sentiment.get('sector_sentiment', {}),
                        'overall_sentiment': sentiment.get('overall_sentiment', 'neutral'),
                        'confidence': sentiment.get('confidence', 0.5)
                    }
                
                # Step 2: Convert sentiment to market condition
                overall_sentiment = sentiment.get('overall_sentiment', 'neutral') if sentiment else 'neutral'
                sentiment_score = sentiment.get('sentiment_score', 0.0) if sentiment else 0.0
                volatility_expected = sentiment.get('volatility_expected', 0.5) if sentiment else 0.5
                
                # Determine market condition (same logic as execution engine)
                if volatility_expected > 0.7:
                    market_condition = 'HIGH_VOLATILITY'
                elif overall_sentiment == 'bullish' or sentiment_score > 0.2:
                    market_condition = 'BULLISH'
                elif overall_sentiment == 'bearish' or sentiment_score < -0.2:
                    market_condition = 'BEARISH'
                else:
                    market_condition = 'NEUTRAL'
                
                simulation_results['market_condition'] = market_condition
                self.logger.info(f"🎯 SIMULATION: Market condition determined as {market_condition}")
                
                # Step 3: Screen stocks using real market data
                self.logger.info("📊 SIMULATION: Screening stocks with real data...")
                market_sentiment_dict = {
                    'sentiment_score': sentiment_score,
                    'bullish': market_condition == 'BULLISH',
                    'bearish': market_condition == 'BEARISH', 
                    'volatile': market_condition in ['VOLATILE', 'HIGH_VOLATILITY'],
                    'neutral': market_condition == 'NEUTRAL',
                    'volatility_expected': volatility_expected
                }
                
                # Use the sophisticated screener with real data
                candidates = loop.run_until_complete(
                    execution_engine.stock_screener.screen_stocks(market_sentiment_dict)
                )
                
                # Get full screening results for display
                full_screening = loop.run_until_complete(
                    execution_engine._get_full_screening_results_sync(market_sentiment_dict)
                )
                
                simulation_results['stock_screening'] = {
                    'candidates': candidates,
                    'full_results': full_screening,
                    'total_candidates': len(candidates)
                }
                
                self.logger.info(f"📈 SIMULATION: Found {len(candidates)} stock candidates")
                
                # Step 4: Analyze options for top candidates (SIMULATION ONLY)
                if candidates:
                    strategy_map = {
                        'BULLISH': (0, 'bull'),
                        'BEARISH': (1, 'bear'), 
                        'VOLATILE': (2, 'volatility'),
                        'HIGH_VOLATILITY': (2, 'volatility'),
                        'NEUTRAL': (0, 'bull')  # Default to bull for neutral
                    }
                    
                    strategy_idx, strategy_name = strategy_map.get(market_condition, (0, 'bull'))
                    strategy = execution_engine.strategies[strategy_idx]
                    
                    self.logger.info(f"⚡ SIMULATION: Analyzing {strategy_name} options for top candidates...")
                    
                    # Analyze top 3 candidates for options opportunities
                    from async_sync_adapter import AsyncSyncAdapter
                    async_client = AsyncSyncAdapter(execution_engine.ibkr_client)
                    original_client = strategy.ibkr_client
                    strategy.ibkr_client = async_client
                    
                    try:
                        for symbol in candidates[:3]:  # Top 3 only for simulation
                            try:
                                self.logger.info(f"🔎 SIMULATION: Analyzing {symbol} for {strategy_name} strategy...")
                                
                                # Scan for opportunities (no execution)
                                if strategy_name == 'volatility':
                                    opportunities = loop.run_until_complete(
                                        strategy.scan_opportunities([symbol], market_sentiment_dict)
                                    )
                                else:
                                    opportunities = loop.run_until_complete(
                                        strategy.scan_opportunities([symbol])
                                    )
                                
                                if opportunities:
                                    opportunity = opportunities[0]
                                    simulation_results['options_analysis'].append({
                                        'symbol': symbol,
                                        'strategy': strategy_name,
                                        'opportunity': {
                                            'score': opportunity.get('score', 0),
                                            'probability_profit': opportunity.get('probability_profit', 0),
                                            'max_profit': opportunity.get('max_profit', 0),
                                            'max_loss': opportunity.get('max_loss', 0),
                                            'risk_reward_ratio': opportunity.get('risk_reward_ratio', 0),
                                            'current_price': opportunity.get('current_price', 0),
                                            'position_size': opportunity.get('position_size', 0),
                                            'long_strike': opportunity.get('long_strike'),
                                            'short_strike': opportunity.get('short_strike'),
                                            'expiry': opportunity.get('expiry'),
                                            'debit': opportunity.get('debit'),
                                            'details': opportunity.get('setup', {})
                                        },
                                        'execution_ready': True
                                    })
                                    
                                    # Add to execution plan
                                    simulation_results['execution_plan'].append({
                                        'action': 'BUY',
                                        'symbol': symbol,
                                        'strategy': strategy_name,
                                        'estimated_cost': opportunity.get('debit', opportunity.get('max_loss', 0)),
                                        'max_profit': opportunity.get('max_profit', 0),
                                        'probability_profit': opportunity.get('probability_profit', 0),
                                        'confidence': 'HIGH' if opportunity.get('score', 0) > 0.7 else 'MEDIUM'
                                    })
                                    
                                    self.logger.info(f"✅ SIMULATION: Found viable {strategy_name} opportunity for {symbol}")
                                else:
                                    simulation_results['options_analysis'].append({
                                        'symbol': symbol,
                                        'strategy': strategy_name,
                                        'opportunity': None,
                                        'execution_ready': False,
                                        'reason': 'No viable options opportunity found'
                                    })
                                    self.logger.info(f"❌ SIMULATION: No {strategy_name} opportunity for {symbol}")
                                    
                            except Exception as e:
                                error_msg = f"Error analyzing {symbol}: {str(e)}"
                                simulation_results['errors'].append(error_msg)
                                self.logger.error(f"🚨 SIMULATION ERROR: {error_msg}")
                    
                    finally:
                        strategy.ibkr_client = original_client
                
                # Step 5: Summary
                simulation_results['summary'] = {
                    'market_condition': market_condition,
                    'total_stocks_screened': len(candidates) if candidates else 0,
                    'options_opportunities': len([x for x in simulation_results['options_analysis'] if x['execution_ready']]),
                    'total_execution_plans': len(simulation_results['execution_plan']),
                    'estimated_total_cost': sum(plan.get('estimated_cost', 0) for plan in simulation_results['execution_plan']),
                    'data_sources': sentiment.get('data_sources', []) if sentiment else ['fallback']
                }
                
                self.logger.info(f"🎯 SIMULATION COMPLETE: {simulation_results['summary']}")
                
            finally:
                loop.close()
                
        except Exception as e:
            error_msg = f"Simulation failed: {str(e)}"
            simulation_results['errors'].append(error_msg)
            self.logger.error(f"🚨 SIMULATION FAILED: {error_msg}")
            
        return simulation_results

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
