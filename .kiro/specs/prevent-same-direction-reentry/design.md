# Prevent Same-Direction Reentry Bugfix Design

## Overview

This design addresses a critical inefficiency in the backtest engine where positions are closed due to exit conditions (stop loss, take profit, indicator-based exits) and immediately reopened in the same direction on the same candle when the entry signal remains active. This creates unnecessary "close-reopen" cycles that generate excessive transaction costs and poor risk management.

The fix introduces a **same-direction reentry prevention mechanism** that tracks the last closed position direction and prevents reopening in that same direction on the current candle. Reverse signals (opposite direction) are explicitly allowed to maintain the existing reverse trading functionality.

**Impact**: This fix eliminates inefficient trading patterns while preserving all existing behaviors for reverse signals, normal entries, and position maintenance.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug - when a position is closed due to exit conditions and immediately reopened in the same direction on the same candle
- **Property (P)**: The desired behavior - after closing a position due to exit conditions, do NOT reopen in the same direction on that candle
- **Preservation**: Existing behaviors that must remain unchanged: reverse signals, normal entries, position maintenance, exit condition evaluation
- **run() method**: The main backtest loop in `backend/backtest/engine.py` (lines 935-1071) that processes each K-line candle sequentially
- **_check_entry_signal()**: Method that detects long/short entry signals and returns (has_signal, signal_direction)
- **_check_exit_signal()**: Method that evaluates exit conditions for the current position
- **_open_position()**: Method that creates a new position with specified direction
- **_close_position()**: Method that closes the current position and records the trade
- **current_position**: Instance variable tracking the active position (None if no position)
- **Reverse Signal**: An entry signal in the opposite direction of the current position, triggering "close current + open opposite" behavior
- **Same-Direction Reentry**: The buggy behavior where a position is closed and immediately reopened in the same direction on the same candle

## Bug Details

### Bug Condition

The bug manifests when a position is closed due to an exit condition (stop loss, take profit, or indicator-based exit) and the same-direction entry signal is still active on the same candle. The `run()` method's control flow allows the entry signal check to execute immediately after closing a position, causing an immediate reopening in the same direction.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type CandleProcessingState
  OUTPUT: boolean
  
  RETURN input.position_closed_this_candle = true
         AND input.closed_position_direction IN ['long', 'short']
         AND input.entry_signal_active = true
         AND input.entry_signal_direction = input.closed_position_direction
         AND input.position_reopened_this_candle = true
END FUNCTION
```

### Examples

**Example 1: Short position with stop loss**
- 2026/04/06 04:00: Open short position at price 50000
- 2026/04/06 08:00: Price rises to 51000, stop loss triggers (-2% loss)
- 2026/04/06 08:00: Short entry signal still active (e.g., RSI < 30)
- 2026/04/06 08:00: **BUG** - System immediately reopens short position at 51000
- Expected: System should NOT reopen short position on this candle

**Example 2: Long position with take profit**
- 2026/04/10 12:00: Open long position at price 48000
- 2026/04/10 16:00: Price rises to 49920, take profit triggers (+4% gain)
- 2026/04/10 16:00: Long entry signal still active (e.g., EMA7 > EMA25)
- 2026/04/10 16:00: **BUG** - System immediately reopens long position at 49920
- Expected: System should NOT reopen long position on this candle

**Example 3: Consecutive candles with same signal**
- 2026/04/15 08:00: Open long position at 47000
- 2026/04/15 12:00: Stop loss triggers at 46530 (-1% loss), long signal still active
- 2026/04/15 12:00: **BUG** - Reopens long at 46530
- 2026/04/15 16:00: Stop loss triggers at 46064 (-1% loss), long signal still active
- 2026/04/15 16:00: **BUG** - Reopens long at 46064
- Expected: After first close at 12:00, should wait until next candle (16:00) to evaluate new entry

**Example 4: Reverse signal (should work correctly - no bug)**
- 2026/04/20 08:00: Open long position at 50000
- 2026/04/20 12:00: Short entry signal triggers (reverse signal)
- 2026/04/20 12:00: **CORRECT** - Close long, open short (reverse trading)
- Expected: This behavior should be preserved

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- **Reverse signals must continue to work**: When a position exists and an opposite-direction entry signal triggers, the system must execute the reverse operation (close current position, open opposite direction position)
- **Normal entry signals must continue to work**: When no position exists and an entry signal triggers, the system must open a new position normally
- **Position maintenance must continue**: When a position exists with no exit conditions and no reverse signals, the system must maintain the current position
- **Exit condition evaluation must remain unchanged**: All exit conditions (stop loss, take profit, indicator-based) must continue to trigger correctly
- **Backtest end behavior must remain unchanged**: Force close any open position at the last candle
- **Insufficient capital handling must remain unchanged**: Skip entry signals when capital is insufficient and log warnings

**Scope:**
All inputs that do NOT involve closing a position due to exit conditions followed by a same-direction entry signal should be completely unaffected by this fix. This includes:
- Reverse signal execution (opposite direction entry while holding a position)
- Normal entry signal execution (entry signal when no position exists)
- Position holding (no exit, no reverse signal)
- Exit condition triggering (stop loss, take profit, indicator exits)

## Hypothesized Root Cause

Based on the bug description and code analysis, the root cause is in the `run()` method's control flow:

1. **Sequential Processing Without State Tracking**: The main loop processes each candle sequentially:
   - First checks exit conditions if position exists → closes position
   - Then checks entry conditions if no position exists → opens new position
   - No mechanism tracks whether a position was just closed on this candle

2. **Immediate Entry Check After Close**: After closing a position (lines 956-960), the code sets `self.current_position = None`, which immediately satisfies the condition `if self.current_position is None` (line 997), allowing entry signal evaluation on the same candle

3. **No Direction Tracking**: The system does not track the direction of the just-closed position, so it cannot distinguish between:
   - Same-direction reentry (should be prevented)
   - Opposite-direction entry (reverse signal, should be allowed)

4. **Reverse Signal Logic Exists But Insufficient**: The reverse signal logic (lines 968-987) only handles the case where a position exists and an opposite signal triggers. It does not prevent same-direction reentry after a position is closed due to exit conditions.

## Correctness Properties

Property 1: Bug Condition - Prevent Same-Direction Reentry

_For any_ candle where a position is closed due to exit conditions (stop loss, take profit, indicator-based exit) and the same-direction entry signal is still active, the fixed run() method SHALL NOT reopen a position in that same direction on the current candle, preventing inefficient close-reopen cycles.

**Validates: Requirements 2.1, 2.2**

Property 2: Preservation - Reverse Signal Functionality

_For any_ candle where a position exists and an opposite-direction entry signal triggers, the fixed run() method SHALL continue to execute the reverse signal (close current position and open opposite direction position), preserving the existing reverse trading functionality.

**Validates: Requirements 3.1**

Property 3: Preservation - Normal Entry Behavior

_For any_ candle where no position exists and an entry signal triggers (without a position having been closed on this candle), the fixed run() method SHALL open a new position normally, preserving the standard entry behavior.

**Validates: Requirements 3.2**

Property 4: Preservation - Position Maintenance

_For any_ candle where a position exists with no exit conditions met and no reverse signals triggered, the fixed run() method SHALL maintain the current position without any action, preserving the position holding behavior.

**Validates: Requirements 3.3, 3.4**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct, the fix requires modifying the `run()` method in `backend/backtest/engine.py`.

**File**: `backend/backtest/engine.py`

**Function**: `run()` method (lines 935-1071)

**Specific Changes**:

1. **Add State Tracking Variable**: Introduce a variable to track the direction of a position closed on the current candle
   - Variable name: `last_closed_direction`
   - Type: `Optional[Literal["long", "short"]]`
   - Scope: Local to the main loop iteration
   - Initialize to `None` at the start of each candle iteration

2. **Capture Closed Position Direction**: When closing a position due to exit conditions, capture the direction before closing
   - Location: Lines 956-960 (exit condition block)
   - Action: Store `self.current_position.direction` in `last_closed_direction` before calling `_close_position()`
   - Note: Do NOT capture direction for reverse signal closes (lines 975-977), as reverse signals should allow immediate opposite-direction entry

3. **Add Same-Direction Reentry Check**: Before opening a new position, check if it would be a same-direction reentry
   - Location: Lines 1003-1010 (entry signal block when no position exists)
   - Condition: `if has_signal and signal_direction is not None and signal_direction != last_closed_direction`
   - Logic: Only allow opening if the signal direction is different from the last closed direction (or if no position was closed this candle)
   - This allows: Normal entries (no close this candle), reverse entries (opposite direction), and entries on subsequent candles

4. **Reset State for Next Candle**: The `last_closed_direction` variable naturally resets because it's scoped to each loop iteration
   - No explicit reset needed
   - Each candle starts with `last_closed_direction = None`

5. **Preserve Reverse Signal Logic**: Ensure reverse signal handling (lines 968-987) remains unchanged
   - Reverse signals should NOT set `last_closed_direction` because they represent intentional direction changes
   - The subsequent entry in the opposite direction should be allowed

### Pseudocode

```python
def run(self) -> BacktestResult:
    # ... initialization code ...
    
    for idx, row in self.kline_data.iterrows():
        # Track if a position was closed due to exit conditions on this candle
        last_closed_direction = None
        
        # ... equity curve recording ...
        
        if self.current_position is not None:
            # Check exit conditions
            should_exit, exit_reason = self._check_exit_signal(row, self.current_position)
            
            if should_exit:
                # Capture direction before closing (for same-direction reentry prevention)
                last_closed_direction = self.current_position.direction
                
                # Close position
                trade = self._close_position(self.current_position, row, exit_reason)
                self.trades.append(trade)
                self.current_position = None
            else:
                # Check for reverse signal
                has_signal, signal_direction = self._check_entry_signal(row)
                
                if has_signal and signal_direction is not None:
                    if signal_direction != self.current_position.direction:
                        # Reverse signal - close and open opposite
                        # Do NOT set last_closed_direction here (allow immediate opposite entry)
                        trade = self._close_position(self.current_position, row, "reverse_signal")
                        self.trades.append(trade)
                        self.current_position = None
                        
                        # Open opposite direction
                        position = self._open_position(row, direction=signal_direction)
                        if position is not None:
                            self.current_position = position
        
        # Check entry conditions if no position
        if self.current_position is None:
            if not self.strategy_config.allow_multiple_positions:
                has_signal, signal_direction = self._check_entry_signal(row)
                
                # Prevent same-direction reentry on the same candle
                if has_signal and signal_direction is not None:
                    if signal_direction != last_closed_direction:
                        # Allow entry: either no close this candle, or opposite direction
                        position = self._open_position(row, direction=signal_direction)
                        if position is not None:
                            self.current_position = position
                    else:
                        # Same-direction reentry prevented
                        logger.debug(
                            f"Prevented same-direction reentry: {signal_direction} position "
                            f"was just closed on this candle"
                        )
        
        # ... rest of loop ...
    
    # ... finalization code ...
```

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that simulate scenarios where a position is closed due to exit conditions and the same-direction entry signal remains active. Run these tests on the UNFIXED code to observe the buggy behavior (immediate reopening).

**Test Cases**:
1. **Short Stop Loss Test**: Open short at 50000, trigger stop loss at 51000 with short signal still active (will fail on unfixed code - should NOT reopen, but does)
2. **Long Take Profit Test**: Open long at 48000, trigger take profit at 49920 with long signal still active (will fail on unfixed code - should NOT reopen, but does)
3. **Consecutive Candles Test**: Open long, close due to stop loss on candle 1 with signal active, verify no reopen on candle 1, allow reopen on candle 2 if signal still active (will fail on unfixed code - reopens on candle 1)
4. **Indicator Exit Test**: Open position, close due to indicator condition with same-direction signal active (will fail on unfixed code - should NOT reopen, but does)

**Expected Counterexamples**:
- Positions are immediately reopened in the same direction after exit conditions trigger
- Transaction logs show "close" followed immediately by "open" with same direction and same timestamp
- Possible causes: No state tracking between close and entry check, immediate entry evaluation after setting position to None

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**
```
FOR ALL candle WHERE isBugCondition(candle) DO
  result := run_fixed(candle)
  ASSERT NOT position_reopened_same_direction_this_candle(result)
END FOR
```

**Test Cases**:
1. **Same-Direction Prevention**: After closing due to exit conditions, verify no same-direction position is opened on that candle
2. **Next Candle Entry Allowed**: After preventing reentry on close candle, verify entry is allowed on next candle if signal still active
3. **Multiple Exit Types**: Test with stop loss, take profit, and indicator-based exits to ensure all trigger the prevention mechanism
4. **Both Directions**: Test prevention works for both long and short positions

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL candle WHERE NOT isBugCondition(candle) DO
  ASSERT run_original(candle) = run_fixed(candle)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs

**Test Plan**: Observe behavior on UNFIXED code first for reverse signals and normal entries, then write property-based tests capturing that behavior.

**Test Cases**:
1. **Reverse Signal Preservation**: Open long position, trigger short signal, verify close long + open short occurs (observe on unfixed code, then verify on fixed code)
2. **Normal Entry Preservation**: With no position, trigger entry signal, verify position opens normally (observe on unfixed code, then verify on fixed code)
3. **Position Maintenance Preservation**: With position and no exit/reverse signals, verify position is maintained (observe on unfixed code, then verify on fixed code)
4. **Exit Condition Preservation**: Verify all exit conditions (stop loss, take profit, indicator) still trigger correctly (observe on unfixed code, then verify on fixed code)
5. **Backtest End Preservation**: Verify force close at end of backtest still works (observe on unfixed code, then verify on fixed code)
6. **Insufficient Capital Preservation**: Verify insufficient capital handling still works (observe on unfixed code, then verify on fixed code)

### Unit Tests

- Test same-direction reentry prevention for long positions with stop loss
- Test same-direction reentry prevention for short positions with stop loss
- Test same-direction reentry prevention for long positions with take profit
- Test same-direction reentry prevention for short positions with take profit
- Test same-direction reentry prevention for indicator-based exits
- Test that entry is allowed on the next candle after prevention
- Test reverse signal execution (close long + open short)
- Test reverse signal execution (close short + open long)
- Test normal entry when no position exists
- Test position maintenance when no exit/reverse conditions

### Property-Based Tests

- Generate random market scenarios with exit conditions and verify no same-direction reentry occurs on the close candle
- Generate random market scenarios with reverse signals and verify reverse trading continues to work
- Generate random market scenarios with normal entries and verify entry behavior is unchanged
- Generate random sequences of candles and verify that same-direction entries are only prevented on the close candle, not subsequent candles

### Integration Tests

- Test full backtest run with multiple close-reopen scenarios and verify prevention works throughout
- Test full backtest run with mixed reverse signals and normal entries to verify preservation
- Test full backtest run with consecutive candles having same-direction signals and verify entries are allowed after the close candle
- Test full backtest run comparing trade counts and equity curves between unfixed and fixed versions to verify the fix reduces unnecessary trades
