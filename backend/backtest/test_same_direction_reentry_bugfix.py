#!/usr/bin/env python3
"""
Same-Direction Reentry Bugfix Tests
使用Hypothesis进行基于属性的测试，验证同方向重入防护功能

Bug Condition Exploration Test (Task 1):
- Property 1: Bug Condition - Same-Direction Reentry After Exit
- CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists
- DO NOT attempt to fix the test or the code when it fails
- GOAL: Surface counterexamples that demonstrate the bug exists
"""

import pytest
import pandas as pd
import numpy as np
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta

from backend.backtest.engine import BacktestEngine
from backend.backtest.models import (
    StrategyConfig,
    EntryConditions,
    ExitConditions,
    IndicatorCondition,
    ComparisonOperator,
    LogicOperator,
    Position
)


# ============================================================================
# Property 1: Bug Condition - Same-Direction Reentry After Exit
# ============================================================================

class TestBugConditionExploration:
    """
    Bug Condition Exploration Tests
    
    These tests are EXPECTED TO FAIL on unfixed code.
    Failure confirms the bug exists.
    """
    
    def test_property_1_short_stop_loss_same_direction_signal(self):
        """
        **Validates: Requirements 2.1, 2.2**
        
        Property 1: Bug Condition - Same-Direction Reentry After Exit
        
        CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.
        
        Scenario: Short position with stop loss
        - Open short position at price 50000
        - Price rises to 51000, stop loss triggers (-2% loss)
        - Short entry signal still active (RSI < 30)
        - Expected: System should NOT reopen short position on the same candle
        - Bug: System immediately reopens short position at 51000
        """
        # Create K-line data with 3 candles
        # Candle 1: Short entry signal active, open short position
        # Candle 2: Price rises, stop loss triggers, short signal still active
        # Candle 3: Continue monitoring
        
        kline_data = pd.DataFrame([
            {
                'timestamp': datetime(2026, 4, 6, 4, 0),
                'open': 50000.0,
                'high': 50200.0,
                'low': 49800.0,
                'close': 50000.0,
                'volume': 100.0,
                'RSI14': 25.0,  # Short signal active (RSI < 30)
                'EMA7': 50500.0,
                'EMA25': 51000.0,
            },
            {
                'timestamp': datetime(2026, 4, 6, 8, 0),
                'open': 50000.0,
                'high': 51500.0,
                'low': 50000.0,
                'close': 51000.0,  # Price rises, triggers stop loss
                'volume': 150.0,
                'RSI14': 28.0,  # Short signal STILL active (RSI < 30)
                'EMA7': 50600.0,
                'EMA25': 51000.0,
            },
            {
                'timestamp': datetime(2026, 4, 6, 12, 0),
                'open': 51000.0,
                'high': 51200.0,
                'low': 50800.0,
                'close': 51000.0,
                'volume': 120.0,
                'RSI14': 29.0,  # Short signal still active
                'EMA7': 50700.0,
                'EMA25': 51000.0,
            }
        ])
        
        # Strategy: Short entry when RSI < 30, exit with 2% stop loss
        strategy = StrategyConfig(
            name="Short Stop Loss Test",
            description="Test same-direction reentry bug with short position",
            timeframe="4h",
            position_size_type="percentage",
            position_size_value=100.0,  # Use 100% of capital
            initial_capital=10000.0,
            leverage=1.0,
            short_entry_conditions=EntryConditions(
                conditions=[
                    IndicatorCondition(
                        indicator='RSI14',
                        operator=ComparisonOperator.LT,
                        value=30.0
                    )
                ],
                logic_operator=LogicOperator.AND
            ),
            short_exit_conditions=ExitConditions(
                indicator_conditions=[],
                stop_loss_pct=2.0,  # 2% stop loss
                take_profit_pct=None,
                logic_operator=LogicOperator.OR
            )
        )
        
        # Run backtest
        engine = BacktestEngine(strategy, kline_data)
        result = engine.run()
        
        # Analyze trades to detect bug condition
        trades = result.trades
        
        # Expected behavior: 1 trade (open short on candle 1, close on candle 2)
        # Bug behavior: 2+ trades (open short on candle 1, close on candle 2, 
        #                          immediately reopen short on candle 2)
        
        print("\n" + "=" * 80)
        print("Bug Condition Exploration - Short Stop Loss Test")
        print("=" * 80)
        print(f"Total trades: {len(trades)}")
        
        for i, trade in enumerate(trades, 1):
            print(f"\nTrade {i}:")
            print(f"  Direction: {trade.direction}")
            print(f"  Entry Time: {trade.entry_time}")
            print(f"  Exit Time: {trade.exit_time}")
            print(f"  Entry Price: {trade.entry_price:.2f}")
            print(f"  Exit Price: {trade.exit_price:.2f}")
            print(f"  Exit Reason: {trade.exit_reason}")
            print(f"  P/L: {trade.profit_loss:.2f} ({trade.profit_loss_pct:.2f}%)")
        
        # Check for same-direction reentry bug
        # Bug condition: Multiple trades with same direction and same exit timestamp
        bug_detected = False
        for i in range(len(trades) - 1):
            current_trade = trades[i]
            next_trade = trades[i + 1]
            
            # Check if next trade opens at the same time current trade closes
            # and in the same direction
            if (current_trade.exit_time == next_trade.entry_time and
                current_trade.direction == next_trade.direction):
                bug_detected = True
                print("\n" + "!" * 80)
                print("BUG DETECTED: Same-direction reentry on same candle!")
                print("!" * 80)
                print(f"Trade {i+1} closed at {current_trade.exit_time} (direction: {current_trade.direction})")
                print(f"Trade {i+2} opened at {next_trade.entry_time} (direction: {next_trade.direction})")
                print(f"Exit reason: {current_trade.exit_reason}")
                print("Expected: No reentry in same direction on same candle")
                print("Actual: Position immediately reopened in same direction")
                print("!" * 80)
        
        print("\n" + "=" * 80)
        print(f"Bug Condition Result: {'DETECTED' if bug_detected else 'NOT DETECTED'}")
        print("=" * 80)
        
        # ASSERTION: This test encodes the EXPECTED behavior
        # On unfixed code, this assertion will FAIL (bug exists)
        # On fixed code, this assertion will PASS (bug fixed)
        
        # Expected behavior: No same-direction reentry on the same candle
        # The key check is that NO consecutive trades have the same exit_time and entry_time
        # (i.e., no same-candle reentry)
        
        # Verify no consecutive trades with same direction at same time (same-candle reentry)
        for i in range(len(trades) - 1):
            current_trade = trades[i]
            next_trade = trades[i + 1]
            
            assert not (
                current_trade.exit_time == next_trade.entry_time and
                current_trade.direction == next_trade.direction
            ), (
                f"Bug detected: Trade {i+1} closed at {current_trade.exit_time} "
                f"(direction: {current_trade.direction}, reason: {current_trade.exit_reason}) "
                f"and Trade {i+2} immediately opened at {next_trade.entry_time} "
                f"in the same direction. This is the same-direction reentry bug."
            )
        
        # If we reach here, no same-candle reentry occurred - the fix is working!
        print("\n✓ Fix verified: No same-direction reentry on the same candle")
        print("✓ Entry on subsequent candles is allowed (correct behavior)")
    
    def test_property_1_long_take_profit_same_direction_signal(self):
        """
        **Validates: Requirements 2.1, 2.2**
        
        Property 1: Bug Condition - Same-Direction Reentry After Exit
        
        CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.
        
        Scenario: Long position with take profit
        - Open long position at price 48000
        - Price rises to 49920, take profit triggers (+4% gain)
        - Long entry signal still active (EMA7 > EMA25)
        - Expected: System should NOT reopen long position on the same candle
        - Bug: System immediately reopens long position at 49920
        """
        kline_data = pd.DataFrame([
            {
                'timestamp': datetime(2026, 4, 10, 12, 0),
                'open': 48000.0,
                'high': 48200.0,
                'low': 47800.0,
                'close': 48000.0,
                'volume': 100.0,
                'EMA7': 48500.0,  # Long signal active (EMA7 > EMA25)
                'EMA25': 47500.0,
                'RSI14': 55.0,
            },
            {
                'timestamp': datetime(2026, 4, 10, 16, 0),
                'open': 48000.0,
                'high': 50000.0,
                'low': 48000.0,
                'close': 49920.0,  # Price rises, triggers take profit
                'volume': 150.0,
                'EMA7': 49000.0,  # Long signal STILL active (EMA7 > EMA25)
                'EMA25': 47800.0,
                'RSI14': 60.0,
            },
            {
                'timestamp': datetime(2026, 4, 10, 20, 0),
                'open': 49920.0,
                'high': 50100.0,
                'low': 49800.0,
                'close': 50000.0,
                'volume': 120.0,
                'EMA7': 49500.0,  # Long signal still active
                'EMA25': 48000.0,
                'RSI14': 62.0,
            }
        ])
        
        # Strategy: Long entry when EMA7 > EMA25, exit with 4% take profit
        strategy = StrategyConfig(
            name="Long Take Profit Test",
            description="Test same-direction reentry bug with long position",
            timeframe="4h",
            position_size_type="percentage",
            position_size_value=100.0,
            initial_capital=10000.0,
            leverage=1.0,
            long_entry_conditions=EntryConditions(
                conditions=[
                    IndicatorCondition(
                        indicator='EMA7',
                        operator=ComparisonOperator.GT,
                        value='EMA25'  # EMA7 > EMA25
                    )
                ],
                logic_operator=LogicOperator.AND
            ),
            long_exit_conditions=ExitConditions(
                indicator_conditions=[],
                take_profit_pct=4.0,  # 4% take profit
                stop_loss_pct=None,
                logic_operator=LogicOperator.OR
            )
        )
        
        # Run backtest
        engine = BacktestEngine(strategy, kline_data)
        result = engine.run()
        
        # Analyze trades
        trades = result.trades
        
        print("\n" + "=" * 80)
        print("Bug Condition Exploration - Long Take Profit Test")
        print("=" * 80)
        print(f"Total trades: {len(trades)}")
        
        for i, trade in enumerate(trades, 1):
            print(f"\nTrade {i}:")
            print(f"  Direction: {trade.direction}")
            print(f"  Entry Time: {trade.entry_time}")
            print(f"  Exit Time: {trade.exit_time}")
            print(f"  Entry Price: {trade.entry_price:.2f}")
            print(f"  Exit Price: {trade.exit_price:.2f}")
            print(f"  Exit Reason: {trade.exit_reason}")
            print(f"  P/L: {trade.profit_loss:.2f} ({trade.profit_loss_pct:.2f}%)")
        
        # Check for bug
        bug_detected = False
        for i in range(len(trades) - 1):
            current_trade = trades[i]
            next_trade = trades[i + 1]
            
            if (current_trade.exit_time == next_trade.entry_time and
                current_trade.direction == next_trade.direction):
                bug_detected = True
                print("\n" + "!" * 80)
                print("BUG DETECTED: Same-direction reentry on same candle!")
                print("!" * 80)
                print(f"Trade {i+1} closed at {current_trade.exit_time} (direction: {current_trade.direction})")
                print(f"Trade {i+2} opened at {next_trade.entry_time} (direction: {next_trade.direction})")
                print(f"Exit reason: {current_trade.exit_reason}")
                print("!" * 80)
        
        print("\n" + "=" * 80)
        print(f"Bug Condition Result: {'DETECTED' if bug_detected else 'NOT DETECTED'}")
        print("=" * 80)
        
        # ASSERTION: Expected behavior - no same-direction reentry on same candle
        # The key check is that NO consecutive trades have the same exit_time and entry_time
        for i in range(len(trades) - 1):
            current_trade = trades[i]
            next_trade = trades[i + 1]
            
            assert not (
                current_trade.exit_time == next_trade.entry_time and
                current_trade.direction == next_trade.direction
            ), (
                f"Bug detected: Same-direction reentry at {next_trade.entry_time}"
            )
        
        # If we reach here, no same-candle reentry occurred - the fix is working!
        print("\n✓ Fix verified: No same-direction reentry on the same candle")
        print("✓ Entry on subsequent candles is allowed (correct behavior)")
    
    def test_property_1_consecutive_candles_same_signal(self):
        """
        **Validates: Requirements 2.1, 2.2**
        
        Property 1: Bug Condition - Same-Direction Reentry After Exit
        
        CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.
        
        Scenario: Consecutive candles with same signal
        - Candle 1: Open long position at 47000
        - Candle 2: Stop loss triggers at 46530 (-1% loss), long signal still active
        - Expected: Should NOT reopen long on candle 2
        - Bug: Reopens long at 46530
        - Candle 3: Stop loss triggers at 46064 (-1% loss), long signal still active
        - Expected: Should NOT reopen long on candle 3
        - Bug: Reopens long at 46064
        """
        kline_data = pd.DataFrame([
            {
                'timestamp': datetime(2026, 4, 15, 8, 0),
                'open': 47000.0,
                'high': 47200.0,
                'low': 46800.0,
                'close': 47000.0,
                'volume': 100.0,
                'RSI14': 45.0,  # Long signal active (RSI > 40)
                'EMA7': 47000.0,
                'EMA25': 46000.0,
            },
            {
                'timestamp': datetime(2026, 4, 15, 12, 0),
                'open': 47000.0,
                'high': 47000.0,
                'low': 46400.0,
                'close': 46530.0,  # Price drops, triggers stop loss
                'volume': 150.0,
                'RSI14': 42.0,  # Long signal STILL active (RSI > 40)
                'EMA7': 46800.0,
                'EMA25': 46000.0,
            },
            {
                'timestamp': datetime(2026, 4, 15, 16, 0),
                'open': 46530.0,
                'high': 46530.0,
                'low': 46000.0,
                'close': 46064.0,  # Price drops again, triggers stop loss
                'volume': 160.0,
                'RSI14': 41.0,  # Long signal STILL active (RSI > 40)
                'EMA7': 46500.0,
                'EMA25': 46000.0,
            },
            {
                'timestamp': datetime(2026, 4, 15, 20, 0),
                'open': 46064.0,
                'high': 46200.0,
                'low': 45900.0,
                'close': 46000.0,
                'volume': 140.0,
                'RSI14': 43.0,  # Long signal still active
                'EMA7': 46200.0,
                'EMA25': 46000.0,
            }
        ])
        
        # Strategy: Long entry when RSI > 40, exit with 1% stop loss
        strategy = StrategyConfig(
            name="Consecutive Candles Test",
            description="Test same-direction reentry bug with consecutive candles",
            timeframe="4h",
            position_size_type="percentage",
            position_size_value=100.0,
            initial_capital=10000.0,
            leverage=1.0,
            long_entry_conditions=EntryConditions(
                conditions=[
                    IndicatorCondition(
                        indicator='RSI14',
                        operator=ComparisonOperator.GT,
                        value=40.0
                    )
                ],
                logic_operator=LogicOperator.AND
            ),
            long_exit_conditions=ExitConditions(
                indicator_conditions=[],
                stop_loss_pct=1.0,  # 1% stop loss (tight to trigger multiple times)
                take_profit_pct=None,
                logic_operator=LogicOperator.OR
            )
        )
        
        # Run backtest
        engine = BacktestEngine(strategy, kline_data)
        result = engine.run()
        
        # Analyze trades
        trades = result.trades
        
        print("\n" + "=" * 80)
        print("Bug Condition Exploration - Consecutive Candles Test")
        print("=" * 80)
        print(f"Total trades: {len(trades)}")
        
        for i, trade in enumerate(trades, 1):
            print(f"\nTrade {i}:")
            print(f"  Direction: {trade.direction}")
            print(f"  Entry Time: {trade.entry_time}")
            print(f"  Exit Time: {trade.exit_time}")
            print(f"  Entry Price: {trade.entry_price:.2f}")
            print(f"  Exit Price: {trade.exit_price:.2f}")
            print(f"  Exit Reason: {trade.exit_reason}")
            print(f"  P/L: {trade.profit_loss:.2f} ({trade.profit_loss_pct:.2f}%)")
        
        # Check for bug - count same-direction reentries
        same_direction_reentries = 0
        for i in range(len(trades) - 1):
            current_trade = trades[i]
            next_trade = trades[i + 1]
            
            if (current_trade.exit_time == next_trade.entry_time and
                current_trade.direction == next_trade.direction):
                same_direction_reentries += 1
                print(f"\nBUG: Same-direction reentry detected between Trade {i+1} and Trade {i+2}")
                print(f"  Closed at: {current_trade.exit_time}")
                print(f"  Reopened at: {next_trade.entry_time}")
                print(f"  Direction: {current_trade.direction}")
        
        print("\n" + "=" * 80)
        print(f"Same-direction reentries detected: {same_direction_reentries}")
        print("=" * 80)
        
        # ASSERTION: Expected behavior
        # Should NOT reopen on the same candle where position was closed
        # Should allow reopen on subsequent candles
        # The key check: NO consecutive trades with same exit_time and entry_time
        for i in range(len(trades) - 1):
            current_trade = trades[i]
            next_trade = trades[i + 1]
            
            assert not (
                current_trade.exit_time == next_trade.entry_time and
                current_trade.direction == next_trade.direction
            ), (
                f"Bug detected: Same-direction reentry on same candle. "
                f"Trade {i+1} closed at {current_trade.exit_time}, "
                f"Trade {i+2} opened at {next_trade.entry_time} in same direction."
            )
        
        # Verify that same_direction_reentries count is 0
        assert same_direction_reentries == 0, (
            f"Expected 0 same-direction reentries on same candle, but detected {same_direction_reentries}. "
            f"Bug: system reopened positions in same direction on same candle after exit."
        )
        
        # If we reach here, no same-candle reentry occurred - the fix is working!
        print("\n✓ Fix verified: No same-direction reentry on the same candle")
        print("✓ Entry on subsequent candles is allowed (correct behavior)")


# ============================================================================
# Property 2: Preservation - Reverse Signals and Normal Entry Behavior
# ============================================================================

class TestPreservation:
    """
    Preservation Tests
    
    These tests validate existing correct behaviors that must be preserved.
    They should PASS on both unfixed and fixed code.
    
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
    """
    
    def test_property_2_reverse_signal_long_to_short(self):
        """
        **Validates: Requirement 3.1**
        
        Property 2: Preservation - Reverse Signal Functionality
        
        Scenario: Reverse signal from long to short
        - Open long position
        - Short entry signal triggers (reverse signal)
        - Expected: Close long, open short (reverse trading)
        - This behavior must be preserved after the fix
        """
        kline_data = pd.DataFrame([
            {
                'timestamp': datetime(2026, 4, 20, 8, 0),
                'open': 50000.0,
                'high': 50200.0,
                'low': 49800.0,
                'close': 50000.0,
                'volume': 100.0,
                'RSI14': 65.0,  # Long signal active (RSI > 60)
                'EMA7': 50000.0,
                'EMA25': 49000.0,
            },
            {
                'timestamp': datetime(2026, 4, 20, 12, 0),
                'open': 50000.0,
                'high': 50500.0,
                'low': 49500.0,
                'close': 49800.0,
                'volume': 150.0,
                'RSI14': 25.0,  # Short signal active (RSI < 30) - REVERSE SIGNAL
                'EMA7': 49500.0,
                'EMA25': 49000.0,
            },
            {
                'timestamp': datetime(2026, 4, 20, 16, 0),
                'open': 49800.0,
                'high': 50000.0,
                'low': 49500.0,
                'close': 49700.0,
                'volume': 120.0,
                'RSI14': 28.0,  # Short signal still active
                'EMA7': 49400.0,
                'EMA25': 49000.0,
            }
        ])
        
        # Strategy: Long when RSI > 60, Short when RSI < 30
        strategy = StrategyConfig(
            name="Reverse Signal Long to Short Test",
            description="Test reverse signal preservation",
            timeframe="4h",
            position_size_type="percentage",
            position_size_value=100.0,
            initial_capital=10000.0,
            leverage=1.0,
            long_entry_conditions=EntryConditions(
                conditions=[
                    IndicatorCondition(
                        indicator='RSI14',
                        operator=ComparisonOperator.GT,
                        value=60.0
                    )
                ],
                logic_operator=LogicOperator.AND
            ),
            short_entry_conditions=EntryConditions(
                conditions=[
                    IndicatorCondition(
                        indicator='RSI14',
                        operator=ComparisonOperator.LT,
                        value=30.0
                    )
                ],
                logic_operator=LogicOperator.AND
            ),
            long_exit_conditions=ExitConditions(
                indicator_conditions=[],
                stop_loss_pct=None,
                take_profit_pct=None,
                logic_operator=LogicOperator.OR
            ),
            short_exit_conditions=ExitConditions(
                indicator_conditions=[],
                stop_loss_pct=None,
                take_profit_pct=None,
                logic_operator=LogicOperator.OR
            )
        )
        
        # Run backtest
        engine = BacktestEngine(strategy, kline_data)
        result = engine.run()
        
        trades = result.trades
        
        print("\n" + "=" * 80)
        print("Preservation Test - Reverse Signal Long to Short")
        print("=" * 80)
        print(f"Total trades: {len(trades)}")
        
        for i, trade in enumerate(trades, 1):
            print(f"\nTrade {i}:")
            print(f"  Direction: {trade.direction}")
            print(f"  Entry Time: {trade.entry_time}")
            print(f"  Exit Time: {trade.exit_time}")
            print(f"  Exit Reason: {trade.exit_reason}")
        
        # Expected: 2 trades
        # Trade 1: Long position opened on candle 1, closed on candle 2 (reverse_signal)
        # Trade 2: Short position opened on candle 2, still open at end
        assert len(trades) >= 2, (
            f"Expected at least 2 trades (long closed, short opened), but got {len(trades)}"
        )
        
        # Verify first trade is long and closed due to reverse signal
        assert trades[0].direction == "long", "First trade should be long"
        assert trades[0].exit_reason == "reverse_signal", (
            f"First trade should be closed due to reverse_signal, but got {trades[0].exit_reason}"
        )
        
        # Verify second trade is short and opened at same time as first trade closed
        assert trades[1].direction == "short", "Second trade should be short"
        assert trades[0].exit_time == trades[1].entry_time, (
            "Short position should open at same time long position closes (reverse signal)"
        )
        
        print("\n✓ Reverse signal (long to short) works correctly")
        print("=" * 80)
    
    def test_property_2_reverse_signal_short_to_long(self):
        """
        **Validates: Requirement 3.1**
        
        Property 2: Preservation - Reverse Signal Functionality
        
        Scenario: Reverse signal from short to long
        - Open short position
        - Long entry signal triggers (reverse signal)
        - Expected: Close short, open long (reverse trading)
        - This behavior must be preserved after the fix
        """
        kline_data = pd.DataFrame([
            {
                'timestamp': datetime(2026, 4, 21, 8, 0),
                'open': 50000.0,
                'high': 50200.0,
                'low': 49800.0,
                'close': 50000.0,
                'volume': 100.0,
                'RSI14': 25.0,  # Short signal active (RSI < 30)
                'EMA7': 50000.0,
                'EMA25': 51000.0,
            },
            {
                'timestamp': datetime(2026, 4, 21, 12, 0),
                'open': 50000.0,
                'high': 51000.0,
                'low': 49500.0,
                'close': 50800.0,
                'volume': 150.0,
                'RSI14': 65.0,  # Long signal active (RSI > 60) - REVERSE SIGNAL
                'EMA7': 50800.0,
                'EMA25': 51000.0,
            },
            {
                'timestamp': datetime(2026, 4, 21, 16, 0),
                'open': 50800.0,
                'high': 51200.0,
                'low': 50500.0,
                'close': 51000.0,
                'volume': 120.0,
                'RSI14': 68.0,  # Long signal still active
                'EMA7': 51000.0,
                'EMA25': 51000.0,
            }
        ])
        
        # Strategy: Short when RSI < 30, Long when RSI > 60
        strategy = StrategyConfig(
            name="Reverse Signal Short to Long Test",
            description="Test reverse signal preservation",
            timeframe="4h",
            position_size_type="percentage",
            position_size_value=100.0,
            initial_capital=10000.0,
            leverage=1.0,
            short_entry_conditions=EntryConditions(
                conditions=[
                    IndicatorCondition(
                        indicator='RSI14',
                        operator=ComparisonOperator.LT,
                        value=30.0
                    )
                ],
                logic_operator=LogicOperator.AND
            ),
            long_entry_conditions=EntryConditions(
                conditions=[
                    IndicatorCondition(
                        indicator='RSI14',
                        operator=ComparisonOperator.GT,
                        value=60.0
                    )
                ],
                logic_operator=LogicOperator.AND
            ),
            short_exit_conditions=ExitConditions(
                indicator_conditions=[],
                stop_loss_pct=None,
                take_profit_pct=None,
                logic_operator=LogicOperator.OR
            ),
            long_exit_conditions=ExitConditions(
                indicator_conditions=[],
                stop_loss_pct=None,
                take_profit_pct=None,
                logic_operator=LogicOperator.OR
            )
        )
        
        # Run backtest
        engine = BacktestEngine(strategy, kline_data)
        result = engine.run()
        
        trades = result.trades
        
        print("\n" + "=" * 80)
        print("Preservation Test - Reverse Signal Short to Long")
        print("=" * 80)
        print(f"Total trades: {len(trades)}")
        
        for i, trade in enumerate(trades, 1):
            print(f"\nTrade {i}:")
            print(f"  Direction: {trade.direction}")
            print(f"  Entry Time: {trade.entry_time}")
            print(f"  Exit Time: {trade.exit_time}")
            print(f"  Exit Reason: {trade.exit_reason}")
        
        # Expected: 2 trades
        # Trade 1: Short position opened on candle 1, closed on candle 2 (reverse_signal)
        # Trade 2: Long position opened on candle 2
        assert len(trades) >= 2, (
            f"Expected at least 2 trades (short closed, long opened), but got {len(trades)}"
        )
        
        # Verify first trade is short and closed due to reverse signal
        assert trades[0].direction == "short", "First trade should be short"
        assert trades[0].exit_reason == "reverse_signal", (
            f"First trade should be closed due to reverse_signal, but got {trades[0].exit_reason}"
        )
        
        # Verify second trade is long and opened at same time as first trade closed
        assert trades[1].direction == "long", "Second trade should be long"
        assert trades[0].exit_time == trades[1].entry_time, (
            "Long position should open at same time short position closes (reverse signal)"
        )
        
        print("\n✓ Reverse signal (short to long) works correctly")
        print("=" * 80)
    
    def test_property_2_normal_entry_no_position(self):
        """
        **Validates: Requirement 3.2**
        
        Property 2: Preservation - Normal Entry Behavior
        
        Scenario: Normal entry when no position exists
        - No position exists
        - Entry signal triggers
        - Expected: Position opens normally
        - This behavior must be preserved after the fix
        """
        kline_data = pd.DataFrame([
            {
                'timestamp': datetime(2026, 4, 22, 8, 0),
                'open': 50000.0,
                'high': 50200.0,
                'low': 49800.0,
                'close': 50000.0,
                'volume': 100.0,
                'RSI14': 50.0,  # No signal (neutral)
                'EMA7': 50000.0,
                'EMA25': 50000.0,
            },
            {
                'timestamp': datetime(2026, 4, 22, 12, 0),
                'open': 50000.0,
                'high': 50500.0,
                'low': 49800.0,
                'close': 50300.0,
                'volume': 150.0,
                'RSI14': 65.0,  # Long signal active (RSI > 60)
                'EMA7': 50300.0,
                'EMA25': 50000.0,
            },
            {
                'timestamp': datetime(2026, 4, 22, 16, 0),
                'open': 50300.0,
                'high': 50800.0,
                'low': 50200.0,
                'close': 50600.0,
                'volume': 120.0,
                'RSI14': 68.0,  # Long signal still active
                'EMA7': 50600.0,
                'EMA25': 50200.0,
            }
        ])
        
        # Strategy: Long when RSI > 60
        strategy = StrategyConfig(
            name="Normal Entry Test",
            description="Test normal entry preservation",
            timeframe="4h",
            position_size_type="percentage",
            position_size_value=100.0,
            initial_capital=10000.0,
            leverage=1.0,
            long_entry_conditions=EntryConditions(
                conditions=[
                    IndicatorCondition(
                        indicator='RSI14',
                        operator=ComparisonOperator.GT,
                        value=60.0
                    )
                ],
                logic_operator=LogicOperator.AND
            ),
            long_exit_conditions=ExitConditions(
                indicator_conditions=[],
                stop_loss_pct=None,
                take_profit_pct=None,
                logic_operator=LogicOperator.OR
            )
        )
        
        # Run backtest
        engine = BacktestEngine(strategy, kline_data)
        result = engine.run()
        
        trades = result.trades
        
        print("\n" + "=" * 80)
        print("Preservation Test - Normal Entry (No Position)")
        print("=" * 80)
        print(f"Total trades: {len(trades)}")
        
        for i, trade in enumerate(trades, 1):
            print(f"\nTrade {i}:")
            print(f"  Direction: {trade.direction}")
            print(f"  Entry Time: {trade.entry_time}")
            print(f"  Exit Time: {trade.exit_time}")
        
        # Expected: 1 trade (long position opened on candle 2)
        assert len(trades) >= 1, (
            f"Expected at least 1 trade (normal entry), but got {len(trades)}"
        )
        
        # Verify first trade is long and opened on candle 2
        assert trades[0].direction == "long", "First trade should be long"
        assert trades[0].entry_time == datetime(2026, 4, 22, 12, 0), (
            "Long position should open on candle 2 when signal triggers"
        )
        
        print("\n✓ Normal entry (no position) works correctly")
        print("=" * 80)
    
    def test_property_2_position_maintenance_no_exit(self):
        """
        **Validates: Requirements 3.3, 3.4**
        
        Property 2: Preservation - Position Maintenance
        
        Scenario: Position maintenance when no exit/reverse conditions
        - Position exists
        - No exit conditions met
        - No reverse signals
        - Expected: Position is maintained
        - This behavior must be preserved after the fix
        """
        kline_data = pd.DataFrame([
            {
                'timestamp': datetime(2026, 4, 23, 8, 0),
                'open': 50000.0,
                'high': 50200.0,
                'low': 49800.0,
                'close': 50000.0,
                'volume': 100.0,
                'RSI14': 65.0,  # Long signal active (RSI > 60)
                'EMA7': 50000.0,
                'EMA25': 49000.0,
            },
            {
                'timestamp': datetime(2026, 4, 23, 12, 0),
                'open': 50000.0,
                'high': 50300.0,
                'low': 49900.0,
                'close': 50100.0,
                'volume': 150.0,
                'RSI14': 66.0,  # Long signal still active, no exit conditions
                'EMA7': 50100.0,
                'EMA25': 49200.0,
            },
            {
                'timestamp': datetime(2026, 4, 23, 16, 0),
                'open': 50100.0,
                'high': 50400.0,
                'low': 50000.0,
                'close': 50200.0,
                'volume': 120.0,
                'RSI14': 67.0,  # Long signal still active, no exit conditions
                'EMA7': 50200.0,
                'EMA25': 49400.0,
            }
        ])
        
        # Strategy: Long when RSI > 60, no exit conditions
        strategy = StrategyConfig(
            name="Position Maintenance Test",
            description="Test position maintenance preservation",
            timeframe="4h",
            position_size_type="percentage",
            position_size_value=100.0,
            initial_capital=10000.0,
            leverage=1.0,
            long_entry_conditions=EntryConditions(
                conditions=[
                    IndicatorCondition(
                        indicator='RSI14',
                        operator=ComparisonOperator.GT,
                        value=60.0
                    )
                ],
                logic_operator=LogicOperator.AND
            ),
            long_exit_conditions=ExitConditions(
                indicator_conditions=[],
                stop_loss_pct=None,  # No stop loss
                take_profit_pct=None,  # No take profit
                logic_operator=LogicOperator.OR
            )
        )
        
        # Run backtest
        engine = BacktestEngine(strategy, kline_data)
        result = engine.run()
        
        trades = result.trades
        
        print("\n" + "=" * 80)
        print("Preservation Test - Position Maintenance")
        print("=" * 80)
        print(f"Total trades: {len(trades)}")
        
        for i, trade in enumerate(trades, 1):
            print(f"\nTrade {i}:")
            print(f"  Direction: {trade.direction}")
            print(f"  Entry Time: {trade.entry_time}")
            print(f"  Exit Time: {trade.exit_time}")
            print(f"  Exit Reason: {trade.exit_reason}")
        
        # Expected: 1 trade (long position opened on candle 1, closed at backtest end)
        assert len(trades) == 1, (
            f"Expected 1 trade (position maintained), but got {len(trades)}"
        )
        
        # Verify position was opened on candle 1
        assert trades[0].direction == "long", "Trade should be long"
        assert trades[0].entry_time == datetime(2026, 4, 23, 8, 0), (
            "Position should open on candle 1"
        )
        
        # Verify position was closed at backtest end (candle 3)
        assert trades[0].exit_time == datetime(2026, 4, 23, 16, 0), (
            "Position should be held until backtest end"
        )
        assert trades[0].exit_reason == "backtest_end", (
            f"Position should be closed at backtest end, but got {trades[0].exit_reason}"
        )
        
        print("\n✓ Position maintenance works correctly")
        print("=" * 80)
    
    def test_property_2_same_direction_signal_during_position_ignored(self):
        """
        **Validates: Requirement 3.4**
        
        Property 2: Preservation - Same-Direction Signal Ignored During Position
        
        Scenario: Same-direction signal during open position
        - Long position exists
        - Long entry signal triggers again (without any exit)
        - Expected: Position is maintained, no action taken
        - This behavior must be preserved after the fix
        """
        kline_data = pd.DataFrame([
            {
                'timestamp': datetime(2026, 4, 24, 8, 0),
                'open': 50000.0,
                'high': 50200.0,
                'low': 49800.0,
                'close': 50000.0,
                'volume': 100.0,
                'RSI14': 65.0,  # Long signal active (RSI > 60)
                'EMA7': 50000.0,
                'EMA25': 49000.0,
            },
            {
                'timestamp': datetime(2026, 4, 24, 12, 0),
                'open': 50000.0,
                'high': 50500.0,
                'low': 49900.0,
                'close': 50300.0,
                'volume': 150.0,
                'RSI14': 70.0,  # Long signal STILL active (RSI > 60) - SAME DIRECTION
                'EMA7': 50300.0,
                'EMA25': 49200.0,
            },
            {
                'timestamp': datetime(2026, 4, 24, 16, 0),
                'open': 50300.0,
                'high': 50800.0,
                'low': 50200.0,
                'close': 50600.0,
                'volume': 120.0,
                'RSI14': 72.0,  # Long signal STILL active (RSI > 60) - SAME DIRECTION
                'EMA7': 50600.0,
                'EMA25': 49400.0,
            }
        ])
        
        # Strategy: Long when RSI > 60, no exit conditions
        strategy = StrategyConfig(
            name="Same Direction Signal Ignored Test",
            description="Test same-direction signal ignored during position",
            timeframe="4h",
            position_size_type="percentage",
            position_size_value=100.0,
            initial_capital=10000.0,
            leverage=1.0,
            long_entry_conditions=EntryConditions(
                conditions=[
                    IndicatorCondition(
                        indicator='RSI14',
                        operator=ComparisonOperator.GT,
                        value=60.0
                    )
                ],
                logic_operator=LogicOperator.AND
            ),
            long_exit_conditions=ExitConditions(
                indicator_conditions=[],
                stop_loss_pct=None,
                take_profit_pct=None,
                logic_operator=LogicOperator.OR
            )
        )
        
        # Run backtest
        engine = BacktestEngine(strategy, kline_data)
        result = engine.run()
        
        trades = result.trades
        
        print("\n" + "=" * 80)
        print("Preservation Test - Same-Direction Signal Ignored")
        print("=" * 80)
        print(f"Total trades: {len(trades)}")
        
        for i, trade in enumerate(trades, 1):
            print(f"\nTrade {i}:")
            print(f"  Direction: {trade.direction}")
            print(f"  Entry Time: {trade.entry_time}")
            print(f"  Exit Time: {trade.exit_time}")
        
        # Expected: 1 trade (long position opened on candle 1, maintained through candles 2-3)
        assert len(trades) == 1, (
            f"Expected 1 trade (same-direction signals ignored), but got {len(trades)}"
        )
        
        # Verify position was opened on candle 1 and held until end
        assert trades[0].direction == "long", "Trade should be long"
        assert trades[0].entry_time == datetime(2026, 4, 24, 8, 0), (
            "Position should open on candle 1"
        )
        assert trades[0].exit_time == datetime(2026, 4, 24, 16, 0), (
            "Position should be held until backtest end (same-direction signals ignored)"
        )
        
        print("\n✓ Same-direction signals during position are correctly ignored")
        print("=" * 80)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
