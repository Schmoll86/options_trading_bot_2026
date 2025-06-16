# bear_module_2026/bear.py
import logging
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from ib_insync import Option, ComboLeg, Contract, Order, Stock
import numpy as np

class BearModule2026:
    """
    Professional Bear Put Spread Strategy Implementation
    
    Strategy focuses on:
    - High probability setups in downtrending stocks
    - Optimal risk/reward ratios (minimum 2:1)
    - Sentiment-driven entry signals
    - Dynamic position sizing based on volatility
    """
    
    def __init__(self, ibkr_client, portfolio_provider):
        self.ibkr_client = ibkr_client
        self.portfolio_provider = portfolio_provider
        self.logger = logging.getLogger(__name__)
        self.active_trades = {}
        self.max_trades = 3
        self.min_days_to_expiry = 30
        self.max_days_to_expiry = 60
        self.optimal_days_to_expiry = 45
        self.long_put_delta_target = -0.40  # -40 delta for long put
        self.short_put_delta_target = -0.25  # -25 delta for short put
        self.min_probability_profit = 0.65  # 65% probability of profit
        self.max_iv_percentile = 70  # Higher IV acceptable for puts
        self.max_spread_cost_pct = 0.02  # Max 2% of portfolio per spread
        self.profit_target_pct = 0.50  # Take profits at 50% of max profit
        self.stop_loss_pct = 0.30  # Stop loss at 30% of debit paid
        self.max_concurrent_trades = 5
        self.min_volume = 1000  # Minimum daily volume
        self.min_open_interest = 100  # Minimum open interest
        self.max_bid_ask_spread_pct = 0.03  # Max 3% bid-ask spread
        self.max_rsi = 60  # RSI below 60 (not overbought)
        self.min_rsi = 30  # RSI above 30 (not oversold yet)
        self.require_below_20ma = True  # Price below 20-day MA
        self.require_below_50ma = True  # Price below 50-day MA
        self.min_down_trend_days = 5  # Minimum days in downtrend

    async def scan_opportunities(self, symbols: List[str]) -> List[Dict]:
        """
        Scan for bear put spread opportunities with professional criteria
        
        This method integrates with:
        1. Sentiment analysis (bearish market required)
        2. Stock screener (provides pre-filtered bearish symbols)
        3. Technical analysis for downtrends
        4. Options analysis for optimal spreads
        """
        opportunities = []
        
        self.logger.info(f"Bear module scanning {len(symbols)} pre-screened bearish symbols")
        
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
        
        self.logger.info(f"Found {len(opportunities)} bear put spread opportunities")
        
        return opportunities[:3]  # Return top 3 opportunities

    async def _analyze_symbol(self, symbol: str) -> Optional[Dict]:
        """Analyze a single symbol for bear put spread opportunity"""
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
            
            if hist_data is None or hist_data.empty:
                return None
            
            # Calculate technical indicators
            tech_signals = self._calculate_technical_indicators(hist_data, current_price)
            if not tech_signals['bearish']:
                return None
            
            # Get options chain
            expiry = self._get_optimal_expiry()
            options_chain = await self.ibkr_client.get_options_chain(symbol, expiry)
            
            if not options_chain:
                return None
            
            # Find optimal strikes for bear put spread
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
                    'type': 'bear_put_spread',
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
        """Calculate technical indicators for bearish confirmation"""
        try:
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
            
            # Check downtrend duration
            down_trend_days = self._count_downtrend_days(closes)
            
            # Support level detection
            support_level = self._find_support_level(closes[-20:])
            distance_to_support = (current_price - support_level) / current_price
            
            # Bearish signals
            bearish = (
                current_price < sma_20 and
                current_price < sma_50 and
                self.min_rsi <= rsi <= self.max_rsi and
                trend_strength < -0.02 and  # At least 2% below 50MA
                down_trend_days >= self.min_down_trend_days
            )
            
            return {
                'bearish': bearish,
                'rsi': rsi,
                'sma_20': sma_20,
                'sma_50': sma_50,
                'volatility': volatility,
                'trend_strength': trend_strength,
                'price_below_20ma': current_price < sma_20,
                'price_below_50ma': current_price < sma_50,
                'down_trend_days': down_trend_days,
                'support_level': support_level,
                'distance_to_support': distance_to_support
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating technical indicators: {e}")
            return {'bearish': False, 'volatility': 0.3}

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

    def _count_downtrend_days(self, prices) -> int:
        """Count consecutive days of lower highs and lower lows"""
        if len(prices) < 2:
            return 0
        
        count = 0
        for i in range(len(prices) - 1, 0, -1):
            if prices[i] < prices[i-1]:
                count += 1
            else:
                break
        
        return count

    def _find_support_level(self, prices) -> float:
        """Find the nearest support level"""
        # Simple approach: use the minimum of recent lows
        return np.min(prices)

    def _get_optimal_expiry(self) -> str:
        """Get optimal expiration date for the spread"""
        target_date = datetime.now() + timedelta(days=self.optimal_days_to_expiry)
        # Format as YYYYMMDD
        return target_date.strftime('%Y%m%d')

    def _find_optimal_spread(self, options_chain: List[Dict], 
                           current_price: float, volatility: float) -> Optional[Dict]:
        """Find optimal strikes for bear put spread"""
        try:
            # Calculate target strikes based on expected move
            expected_move = current_price * volatility * np.sqrt(self.optimal_days_to_expiry / 365)
            
            # Long put strike: slightly OTM (around -40 delta)
            target_long_strike = current_price - (0.2 * expected_move)
            
            # Short put strike: further OTM (around -25 delta)
            target_short_strike = current_price - (0.8 * expected_move)
            
            # Find closest available strikes
            long_strike = None
            short_strike = None
            long_put_data = None
            short_put_data = None
            
            for option in options_chain:
                strike = option['strike']
                
                # Find long strike
                if long_strike is None or abs(strike - target_long_strike) < abs(long_strike - target_long_strike):
                    if option['put']['bid'] and option['put']['ask']:
                        long_strike = strike
                        long_put_data = option['put']
                
                # Find short strike (must be lower than long strike)
                if strike < target_long_strike:
                    if short_strike is None or abs(strike - target_short_strike) < abs(short_strike - target_short_strike):
                        if option['put']['bid'] and option['put']['ask']:
                            short_strike = strike
                            short_put_data = option['put']
            
            if not all([long_strike, short_strike, long_put_data, short_put_data]):
                return None
            
            # Calculate net debit
            long_put_mid = (long_put_data['bid'] + long_put_data['ask']) / 2
            short_put_mid = (short_put_data['bid'] + short_put_data['ask']) / 2
            debit = long_put_mid - short_put_mid
            
            # Validate spread width
            spread_width = long_strike - short_strike
            if spread_width < expected_move * 0.3:  # Too narrow
                return None
            
            return {
                'long_strike': long_strike,
                'short_strike': short_strike,
                'debit': debit,
                'spread_width': spread_width,
                'long_put_data': long_put_data,
                'short_put_data': short_put_data
            }
            
        except Exception as e:
            self.logger.error(f"Error finding optimal spread: {e}")
            return None

    def _calculate_spread_metrics(self, spread_params: Dict, 
                                current_price: float, tech_signals: Dict) -> Dict:
        """Calculate comprehensive metrics for the bear put spread"""
        debit = spread_params['debit']
        spread_width = spread_params['spread_width']
        long_strike = spread_params['long_strike']
        
        # Basic spread calculations
        max_profit = spread_width - debit
        max_loss = debit
        breakeven = long_strike - debit
        
        # Risk/reward ratio
        risk_reward_ratio = max_profit / max_loss if max_loss > 0 else 0
        
        # Probability calculations (simplified Black-Scholes approximation)
        volatility = tech_signals['volatility']
        days_to_expiry = self.optimal_days_to_expiry
        
        # Distance to breakeven in standard deviations
        expected_move = current_price * volatility * np.sqrt(days_to_expiry / 365)
        distance_to_breakeven = (current_price - breakeven) / expected_move
        
        # Rough probability estimate using normal distribution
        from scipy.stats import norm
        probability_profit = norm.cdf(distance_to_breakeven)
        
        # Adjust probability based on trend strength
        if tech_signals['trend_strength'] < -0.05:  # Strong downtrend
            probability_profit *= 1.1  # Increase probability
        
        # Score calculation (weighted combination of factors)
        score = (
            probability_profit * 0.4 +
            min(risk_reward_ratio / 3, 1) * 0.3 +  # Normalize RR ratio
            abs(tech_signals['trend_strength']) * 0.2 +
            min(tech_signals['down_trend_days'] / 10, 1) * 0.1
        )
        
        return {
            'max_profit': max_profit,
            'max_loss': max_loss,
            'breakeven': breakeven,
            'risk_reward_ratio': risk_reward_ratio,
            'probability_profit': min(probability_profit, 0.95),  # Cap at 95%
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
        """Execute the bear put spread trade"""
        try:
            symbol = opportunity['symbol']
            
            # Final risk check
            if not self.portfolio_provider.can_trade(opportunity['debit'] * opportunity['position_size'] * 100):
                self.logger.warning(f"Risk check failed for {symbol}")
                return None
            
            # Create option contracts
            long_put = Option(
                symbol=symbol,
                lastTradeDateOrContractMonth=opportunity['expiry'],
                strike=opportunity['long_strike'],
                right='P',
                exchange='SMART'
            )
            
            short_put = Option(
                symbol=symbol,
                lastTradeDateOrContractMonth=opportunity['expiry'],
                strike=opportunity['short_strike'],
                right='P',
                exchange='SMART'
            )
            
            # Qualify contracts
            long_details = await self.ibkr_client.reqContractDetails(long_put)
            short_details = await self.ibkr_client.reqContractDetails(short_put)
            
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
            self.logger.info(f"Placing bear put spread order for {symbol}")
            order_id = await self.ibkr_client.place_order(combo, order)
            
            if order_id:
                self.logger.info(f"✅ Bear put spread order placed: {order_id} for {symbol}")
                
                # Log trade details
                self.logger.info(f"Trade details: Long {opportunity['long_strike']}P, "
                               f"Short {opportunity['short_strike']}P, "
                               f"Debit: ${opportunity['debit']:.2f}, "
                               f"Size: {opportunity['position_size']} contracts")
                
                return order_id
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error executing bear put spread: {e}")
            return None

    async def manage_positions(self, positions: List) -> List[Dict]:
        """Monitor and manage existing bear put spread positions"""
        management_actions = []
        
        for position in positions:
            if position.contract.secType != 'BAG':
                continue
            
            try:
                # Get current value
                current_value = position.marketValue
                entry_cost = position.avgCost * position.position
                pnl_pct = (current_value - entry_cost) / entry_cost if entry_cost != 0 else 0
                
                # Check profit target
                if pnl_pct >= self.profit_target_pct:
                    management_actions.append({
                        'action': 'close',
                        'position': position,
                        'reason': 'profit_target',
                        'pnl_pct': pnl_pct
                    })
                
                # Check stop loss
                elif pnl_pct <= -self.stop_loss_pct:
                    management_actions.append({
                        'action': 'close',
                        'position': position,
                        'reason': 'stop_loss',
                        'pnl_pct': pnl_pct
                    })
                
            except Exception as e:
                self.logger.error(f"Error managing position: {e}")
        
        return management_actions
