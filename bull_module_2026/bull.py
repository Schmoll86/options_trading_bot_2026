# bull_module_2026/bull.py
import logging
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from ib_insync import Option, ComboLeg, Contract, Order, Stock
import numpy as np

class BullModule2026:
    """
    Professional Bull Call Spread Strategy Implementation
    
    Strategy focuses on:
    - High probability setups in uptrending stocks
    - Optimal risk/reward ratios (minimum 2:1)
    - Sentiment-driven entry signals
    - Dynamic position sizing based on volatility
    """
    
    def __init__(self, ibkr_client, portfolio_provider):
        self.ibkr_client = ibkr_client
        self.portfolio_provider = portfolio_provider
        self.logger = logging.getLogger(__name__)
        
        # Strategy Parameters (based on historical profitability)
        self.min_days_to_expiry = 30
        self.max_days_to_expiry = 60
        self.optimal_days_to_expiry = 45
        
        # Greeks and probability thresholds
        self.long_call_delta_target = 0.40  # 40 delta for long call
        self.short_call_delta_target = 0.25  # 25 delta for short call
        self.min_probability_profit = 0.65  # 65% probability of profit
        self.max_iv_percentile = 50  # Don't buy when IV is too high
        
        # Risk management
        self.max_spread_cost_pct = 0.02  # Max 2% of portfolio per spread
        self.profit_target_pct = 0.50  # Take profits at 50% of max profit
        self.stop_loss_pct = 0.30  # Stop loss at 30% of debit paid
        self.max_concurrent_trades = 5
        
        # Entry criteria
        self.min_volume = 1000  # Minimum daily volume
        self.min_open_interest = 100  # Minimum open interest
        self.max_bid_ask_spread_pct = 0.03  # Max 3% bid-ask spread
        
        # Technical requirements
        self.min_rsi = 40  # RSI above 40 (not oversold)
        self.max_rsi = 70  # RSI below 70 (not overbought yet)
        self.require_above_20ma = True  # Price above 20-day MA
        self.require_above_50ma = True  # Price above 50-day MA

    async def scan_opportunities(self, symbols: List[str]) -> List[Dict]:
        """
        Scan for bull call spread opportunities with professional criteria
        
        This method integrates with:
        1. Sentiment analysis (bullish market required)
        2. Stock screener (provides pre-filtered symbols)
        3. Technical analysis
        4. Options analysis
        """
        opportunities = []
        
        self.logger.info(f"Bull module scanning {len(symbols)} pre-screened bullish symbols")
        
        # Process symbols concurrently for efficiency
        tasks = []
        for symbol in symbols[:10]:  # Limit to top 10 to avoid overloading
            tasks.append(self._analyze_symbol(symbol))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Error analyzing symbol: {result}")
                continue
            if result:
                opportunities.append(result)
        
        # Sort by score (combination of probability and risk/reward)
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        self.logger.info(f"Found {len(opportunities)} bull call spread opportunities")
        
        return opportunities[:3]  # Return top 3 opportunities

    async def _analyze_symbol(self, symbol: str) -> Optional[Dict]:
        """Analyze a single symbol for bull call spread opportunity"""
        try:
            # Get current price and historical data
            stock_data = await self.ibkr_client.get_market_data(symbol)
            if not stock_data or not stock_data.get('last'):
                return None
            
            current_price = stock_data['last']
            
            # Get historical data for technical analysis
            hist_data = await self.ibkr_client.get_historical_data(
                symbol, duration='60 D', bar_size='1 day'
            )
            
            if hist_data is None or len(hist_data) == 0:
                return None
            
            # Calculate technical indicators
            tech_signals = self._calculate_technical_indicators(hist_data, current_price)
            if not tech_signals['bullish']:
                return None
            
            # Get options chain
            expiry = self._get_optimal_expiry()
            options_chain = await self.ibkr_client.get_options_chain(symbol, expiry)
            
            if not options_chain:
                return None
            
            # Find optimal strikes for bull call spread
            spread_params = self._find_optimal_spread(
                options_chain, current_price, tech_signals['volatility']
            )
            
            if not spread_params:
                return None
            
            # Calculate spread metrics
            spread_metrics = self._calculate_spread_metrics(
                spread_params, current_price, tech_signals
            )
            
            if self._validate_opportunity(spread_metrics):
                return {
                    'type': 'bull_call_spread',
                    'symbol': symbol,
                    'current_price': current_price,
                    'expiry': expiry,
                    'long_strike': spread_params['long_strike'],
                    'short_strike': spread_params['short_strike'],
                    'debit': spread_params['debit'],
                    'max_profit': spread_metrics['max_profit'],
                    'max_loss': spread_metrics['max_loss'],
                    'breakeven': spread_metrics['breakeven'],
                    'probability_profit': spread_metrics['probability_profit'],
                    'risk_reward_ratio': spread_metrics['risk_reward_ratio'],
                    'score': spread_metrics['score'],
                    'technical_signals': tech_signals,
                    'position_size': self._calculate_position_size(spread_metrics)
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {e}")
            return None

    def _calculate_technical_indicators(self, hist_data, current_price) -> Dict:
        """Calculate technical indicators for bullish confirmation"""
        try:
            # Handle BarDataList from ib_insync
            if hasattr(hist_data, '__iter__') and not hasattr(hist_data, 'values'):
                # Convert BarDataList to array of closes
                closes = np.array([bar.close for bar in hist_data])
            else:
                # Handle pandas DataFrame (if converted)
                closes = hist_data['close'].values
            
            # Simple Moving Averages
            sma_20 = np.mean(closes[-20:])
            sma_50 = np.mean(closes[-50:]) if len(closes) >= 50 else sma_20
            
            # RSI
            rsi = self._calculate_rsi(closes)
            
            # Historical Volatility (20-day)
            returns = np.diff(closes) / closes[:-1]
            volatility = np.std(returns[-20:]) * np.sqrt(252)  # Annualized
            
            # Trend strength (price relative to moving averages)
            trend_strength = (current_price - sma_50) / sma_50
            
            # Bullish signals
            bullish = (
                current_price > sma_20 and
                current_price > sma_50 and
                self.min_rsi <= rsi <= self.max_rsi and
                trend_strength > 0.02  # At least 2% above 50MA
            )
            
            return {
                'bullish': bullish,
                'rsi': rsi,
                'sma_20': sma_20,
                'sma_50': sma_50,
                'volatility': volatility,
                'trend_strength': trend_strength,
                'price_above_20ma': current_price > sma_20,
                'price_above_50ma': current_price > sma_50
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating technical indicators: {e}")
            return {'bullish': False, 'volatility': 0.3}  # Default volatility

    def _calculate_rsi(self, prices, period=14) -> float:
        """Calculate RSI indicator"""
        if len(prices) < period + 1:
            return 50  # Neutral RSI if not enough data
        
        deltas = np.diff(prices)
        gains = deltas.copy()
        losses = deltas.copy()
        gains[gains < 0] = 0
        losses[losses > 0] = 0
        losses = abs(losses)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi

    def _get_optimal_expiry(self) -> str:
        """Get optimal expiration date for the spread"""
        target_date = datetime.now() + timedelta(days=self.optimal_days_to_expiry)
        # Format as YYYYMMDD
        return target_date.strftime('%Y%m%d')

    def _find_optimal_spread(self, options_chain: List[Dict], 
                           current_price: float, volatility: float) -> Optional[Dict]:
        """Find optimal strikes for bull call spread"""
        try:
            # Calculate target strikes based on expected move
            expected_move = current_price * volatility * np.sqrt(self.optimal_days_to_expiry / 365)
            
            # Long call strike: slightly OTM (around 40 delta)
            target_long_strike = current_price + (0.2 * expected_move)
            
            # Short call strike: further OTM (around 25 delta)
            target_short_strike = current_price + (0.8 * expected_move)
            
            # Find closest available strikes
            long_strike = None
            short_strike = None
            long_call_data = None
            short_call_data = None
            
            for option in options_chain:
                strike = option['strike']
                
                # Find long strike
                if long_strike is None or abs(strike - target_long_strike) < abs(long_strike - target_long_strike):
                    if option['call']['bid'] and option['call']['ask']:
                        long_strike = strike
                        long_call_data = option['call']
                
                # Find short strike
                if strike > target_long_strike:  # Must be higher than long strike
                    if short_strike is None or abs(strike - target_short_strike) < abs(short_strike - target_short_strike):
                        if option['call']['bid'] and option['call']['ask']:
                            short_strike = strike
                            short_call_data = option['call']
            
            if not all([long_strike, short_strike, long_call_data, short_call_data]):
                return None
            
            # Calculate net debit
            long_call_mid = (long_call_data['bid'] + long_call_data['ask']) / 2
            short_call_mid = (short_call_data['bid'] + short_call_data['ask']) / 2
            debit = long_call_mid - short_call_mid
            
            # Validate spread width
            spread_width = short_strike - long_strike
            if spread_width < expected_move * 0.3:  # Too narrow
                return None
            
            return {
                'long_strike': long_strike,
                'short_strike': short_strike,
                'debit': debit,
                'spread_width': spread_width,
                'long_call_data': long_call_data,
                'short_call_data': short_call_data
            }
            
        except Exception as e:
            self.logger.error(f"Error finding optimal spread: {e}")
            return None

    def _calculate_spread_metrics(self, spread_params: Dict, 
                                current_price: float, tech_signals: Dict) -> Dict:
        """Calculate comprehensive metrics for the bull call spread"""
        debit = spread_params['debit']
        spread_width = spread_params['spread_width']
        long_strike = spread_params['long_strike']
        
        # Basic spread calculations
        max_profit = spread_width - debit
        max_loss = debit
        breakeven = long_strike + debit
        
        # Risk/reward ratio
        risk_reward_ratio = max_profit / max_loss if max_loss > 0 else 0
        
        # Probability calculations (simplified Black-Scholes approximation)
        volatility = tech_signals['volatility']
        days_to_expiry = self.optimal_days_to_expiry
        
        # Distance to breakeven in standard deviations
        expected_move = current_price * volatility * np.sqrt(days_to_expiry / 365)
        distance_to_breakeven = (breakeven - current_price) / expected_move
        
        # Rough probability estimate using normal distribution
        from scipy.stats import norm
        probability_profit = 1 - norm.cdf(distance_to_breakeven)
        
        # Score calculation (weighted combination of factors)
        score = (
            probability_profit * 0.4 +
            min(risk_reward_ratio / 3, 1) * 0.3 +  # Normalize RR ratio
            tech_signals['trend_strength'] * 0.2 +
            (1 - tech_signals['volatility']) * 0.1  # Lower volatility is better
        )
        
        return {
            'max_profit': max_profit,
            'max_loss': max_loss,
            'breakeven': breakeven,
            'risk_reward_ratio': risk_reward_ratio,
            'probability_profit': probability_profit,
            'score': score,
            'return_on_risk': (max_profit / max_loss) * probability_profit
        }

    def _validate_opportunity(self, metrics: Dict) -> bool:
        """Validate if the opportunity meets our strict criteria"""
        return (
            metrics['risk_reward_ratio'] >= 2.0 and
            metrics['probability_profit'] >= self.min_probability_profit and
            metrics['return_on_risk'] >= 1.5  # Expected value must be positive
        )

    def _calculate_position_size(self, metrics: Dict) -> int:
        """Calculate optimal position size based on Kelly Criterion and risk limits"""
        try:
            # Get available capital
            available_capital = self.portfolio_provider.get_available_capital()
            
            # Maximum risk per trade (2% of portfolio)
            max_risk = available_capital * self.max_spread_cost_pct
            
            # Kelly Criterion (simplified)
            win_prob = metrics['probability_profit']
            loss_prob = 1 - win_prob
            win_amount = metrics['max_profit']
            loss_amount = metrics['max_loss']
            
            kelly_fraction = (win_prob * win_amount - loss_prob * loss_amount) / win_amount
            kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%
            
            # Position size based on max risk
            contracts_by_risk = int(max_risk / metrics['max_loss'])
            
            # Position size based on Kelly
            contracts_by_kelly = int((available_capital * kelly_fraction) / metrics['max_loss'])
            
            # Use the smaller of the two
            position_size = min(contracts_by_risk, contracts_by_kelly, 10)  # Cap at 10 contracts
            
            return max(1, position_size)  # At least 1 contract
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 1

    async def execute_trade(self, opportunity: Dict) -> Optional[str]:
        """Execute the bull call spread trade"""
        try:
            symbol = opportunity['symbol']
            
            # Final risk check
            if not self.portfolio_provider.can_trade(opportunity['debit'] * opportunity['position_size'] * 100):
                self.logger.warning(f"Risk check failed for {symbol}")
                return None
            
            # Create option contracts
            long_call = Option(
                symbol=symbol,
                lastTradeDateOrContractMonth=opportunity['expiry'],
                strike=opportunity['long_strike'],
                right='C',
                exchange='SMART'
            )
            
            short_call = Option(
                symbol=symbol,
                lastTradeDateOrContractMonth=opportunity['expiry'],
                strike=opportunity['short_strike'],
                right='C',
                exchange='SMART'
            )
            
            # Qualify contracts
            long_details = await self.ibkr_client.reqContractDetails(long_call)
            short_details = await self.ibkr_client.reqContractDetails(short_call)
            
            if not long_details or not short_details:
                self.logger.error(f"Could not qualify option contracts for {symbol}")
                return None
            
            # Create combo order
            combo = Contract()
            combo.symbol = symbol
            combo.secType = 'BAG'
            combo.currency = 'USD'
            combo.exchange = 'SMART'
            
            leg1 = ComboLeg()
            leg1.conId = long_details[0].contract.conId
            leg1.ratio = 1
            leg1.action = 'BUY'
            leg1.exchange = 'SMART'
            
            leg2 = ComboLeg()
            leg2.conId = short_details[0].contract.conId
            leg2.ratio = 1
            leg2.action = 'SELL'
            leg2.exchange = 'SMART'
            
            combo.comboLegs = [leg1, leg2]
            
            # Create order
            order = Order()
            order.action = 'BUY'
            order.totalQuantity = opportunity['position_size']
            order.orderType = 'LMT'
            order.lmtPrice = opportunity['debit'] * 1.02  # Allow 2% slippage
            order.tif = 'GTC'
            order.transmit = True
            
            # Place order
            self.logger.info(f"Placing bull call spread order for {symbol}")
            order_id = await self.ibkr_client.place_order(combo, order)
            
            if order_id:
                self.logger.info(f"✅ Bull call spread order placed: {order_id} for {symbol}")
                
                # Log trade details
                self.logger.info(f"Trade details: Long {opportunity['long_strike']}C, "
                               f"Short {opportunity['short_strike']}C, "
                               f"Debit: ${opportunity['debit']:.2f}, "
                               f"Size: {opportunity['position_size']} contracts")
                
                return order_id
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error executing bull call spread: {e}")
            return None

    async def manage_positions(self, positions: List[Any]) -> List[Dict]:
        """
        Manage existing bull positions for profit taking or stop loss.
        Returns a list of actions to take for each position.
        """
        actions = []
        
        for position in positions:
            try:
                symbol = position.contract.symbol
                entry_price = position.avgCost
                current_price = position.marketValue / abs(position.position) if position.position != 0 else 0
                
                # Calculate P&L percentage
                pnl_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price != 0 else 0
                
                # Bull strategy specific exits
                # Take profit at 50% of max profit
                if pnl_pct >= 50:
                    self.logger.info(f"🎯 BULL: Take profit target hit for {symbol} at {pnl_pct:.1f}%")
                    actions.append({
                        'action': 'close',
                        'position': position,
                        'reason': 'take_profit_50pct'
                    })
                    continue
                
                # Stop loss at 30% of debit paid
                if pnl_pct <= -30:
                    self.logger.warning(f"🛑 BULL: Stop loss hit for {symbol} at {pnl_pct:.1f}%")
                    actions.append({
                        'action': 'close',
                        'position': position,
                        'reason': 'stop_loss_30pct'
                    })
                    continue
                
                # Additional bull-specific exit conditions
                
                # Exit if underlying has broken below support
                stock_data = await self.ibkr_client.get_market_data(symbol)
                if stock_data and stock_data.get('last', 0) > 0:
                    # Calculate simple support level (20-day low)
                    # In production, this would use more sophisticated technical analysis
                    current_price = stock_data.get('last')
                    close_price = stock_data.get('close', current_price)
                    
                    # Exit if stock drops more than 5% from close
                    if current_price < close_price * 0.95:
                        self.logger.warning(f"⚠️ BULL: Underlying {symbol} breaking down")
                        actions.append({
                            'action': 'close',
                            'position': position,
                            'reason': 'underlying_breakdown'
                        })
                        continue
                
                # Time-based exit for weeklies near expiration
                if hasattr(position.contract, 'lastTradeDateOrContractMonth'):
                    days_to_expiry = self._calculate_days_to_expiry(
                        position.contract.lastTradeDateOrContractMonth
                    )
                    
                    # Close if less than 2 days to expiry and in profit
                    if days_to_expiry <= 2 and pnl_pct > 10:
                        self.logger.info(f"⏰ BULL: Closing {symbol} near expiry with {pnl_pct:.1f}% profit")
                        actions.append({
                            'action': 'close',
                            'position': position,
                            'reason': 'near_expiry_profit'
                        })
                        continue
                
                # Log position status if no action
                if not any(a['position'] == position for a in actions):
                    self.logger.debug(f"BULL position {symbol}: {pnl_pct:.1f}% P&L, holding")
                    
            except Exception as e:
                self.logger.error(f"Error managing bull position {position.contract.symbol}: {e}")
        
        return actions
    
    def _calculate_days_to_expiry(self, expiry_date: str) -> int:
        """Calculate days remaining to expiry"""
        try:
            from datetime import datetime
            # Parse expiry date (format: YYYYMMDD)
            expiry = datetime.strptime(str(expiry_date)[:8], '%Y%m%d')
            today = datetime.now()
            days_remaining = (expiry - today).days
            return max(0, days_remaining)
        except Exception:
            return 30  # Default to 30 days if parsing fails
