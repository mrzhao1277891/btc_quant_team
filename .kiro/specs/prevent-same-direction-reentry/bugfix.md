# Bugfix Requirements Document

## Introduction

This document specifies the requirements for fixing inefficient trading behavior in the backtest engine where consecutive K-line candles satisfying the same direction entry signal cause the system to close and immediately reopen positions in the same direction, resulting in unnecessary transaction costs.

The bug occurs when:
- A position is closed due to an exit condition (e.g., stop loss, take profit)
- On the same candle, the entry signal for the same direction is still active
- The system immediately reopens a position in the same direction

This creates a "close-reopen" cycle that is inefficient and generates unnecessary transaction costs.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN a position is closed due to an exit condition (stop loss, take profit, or indicator-based exit) AND the same-direction entry signal is still active on the same candle THEN the system immediately reopens a position in the same direction

1.2 WHEN consecutive K-line candles continuously satisfy the same direction entry conditions (e.g., multiple candles satisfy long entry conditions) AND a position is closed due to exit conditions THEN the system creates a "close-reopen" cycle on each candle where exit conditions are met

1.3 WHEN a short position is closed at 2026/04/06 08:00 due to stop loss AND the short entry signal is still active at 2026/04/06 08:00 THEN the system immediately reopens a short position at the same timestamp

### Expected Behavior (Correct)

2.1 WHEN a position is closed due to an exit condition (stop loss, take profit, or indicator-based exit) AND the same-direction entry signal is still active on the same candle THEN the system SHALL NOT reopen a position in the same direction on that candle

2.2 WHEN consecutive K-line candles continuously satisfy the same direction entry conditions AND a position is closed due to exit conditions THEN the system SHALL wait for the next candle before evaluating new entry signals in the same direction

2.3 WHEN a position is closed due to an exit condition THEN the system SHALL only reopen a position if an opposite-direction entry signal is triggered (reverse signal)

### Unchanged Behavior (Regression Prevention)

3.1 WHEN a position is closed due to an exit condition AND an opposite-direction entry signal is active THEN the system SHALL CONTINUE TO execute the reverse signal (close current position and open opposite direction position)

3.2 WHEN no position exists AND an entry signal is triggered THEN the system SHALL CONTINUE TO open a new position normally

3.3 WHEN a position exists AND no exit conditions are met AND no reverse signals are triggered THEN the system SHALL CONTINUE TO maintain the current position

3.4 WHEN a position exists AND the same-direction entry signal triggers again (without any exit) THEN the system SHALL CONTINUE TO maintain the current position without any action

3.5 WHEN the backtest ends with an open position THEN the system SHALL CONTINUE TO force close the position at the last candle

3.6 WHEN insufficient capital exists to open a position THEN the system SHALL CONTINUE TO skip the entry signal and log a warning

## Bug Condition and Property

### Bug Condition Function

```pascal
FUNCTION isBugCondition(candle, prev_candle, position_history)
  INPUT: 
    candle - Current K-line candle data
    prev_candle - Previous K-line candle data  
    position_history - List of position open/close events
  OUTPUT: boolean
  
  // Check if a position was closed on the previous candle
  position_closed_prev := EXISTS event IN position_history WHERE
    event.type = "close" AND 
    event.timestamp = prev_candle.timestamp
  
  IF NOT position_closed_prev THEN
    RETURN false
  END IF
  
  // Get the direction of the closed position
  closed_direction := GET direction FROM position_history WHERE
    event.type = "close" AND
    event.timestamp = prev_candle.timestamp
  
  // Check if same-direction entry signal is active on current candle
  same_direction_signal := (
    (closed_direction = "long" AND long_entry_signal_active(candle)) OR
    (closed_direction = "short" AND short_entry_signal_active(candle))
  )
  
  // Check if a new position was opened on current candle in same direction
  position_opened_current := EXISTS event IN position_history WHERE
    event.type = "open" AND
    event.timestamp = candle.timestamp AND
    event.direction = closed_direction
  
  // Bug condition: position closed, same signal active, position reopened
  RETURN same_direction_signal AND position_opened_current
END FUNCTION
```

### Property Specification

```pascal
// Property: Fix Checking - Prevent Same-Direction Reentry
FOR ALL candle, prev_candle, position_history WHERE isBugCondition(candle, prev_candle, position_history) DO
  
  // Get the closed position direction
  closed_direction := GET direction FROM position_history WHERE
    event.type = "close" AND
    event.timestamp = prev_candle.timestamp
  
  // After fix, no same-direction position should be opened on current candle
  no_same_direction_reentry := NOT EXISTS event IN position_history WHERE
    event.type = "open" AND
    event.timestamp = candle.timestamp AND
    event.direction = closed_direction
  
  ASSERT no_same_direction_reentry
END FOR
```

### Preservation Goal

```pascal
// Property: Preservation Checking - Maintain Other Trading Behaviors
FOR ALL candle, position_history WHERE NOT isBugCondition(candle, prev_candle, position_history) DO
  
  // Original behavior F: The unfixed backtest engine
  // Fixed behavior F': The fixed backtest engine
  
  // For non-buggy scenarios, behavior should remain unchanged
  ASSERT F(candle, position_history) = F'(candle, position_history)
  
  // Specifically:
  // 1. Reverse signals still work
  // 2. Normal entry signals (when no position exists) still work
  // 3. Position maintenance (when no exit/reverse) still works
  // 4. Exit conditions still trigger correctly
END FOR
```

## Counterexample

**Concrete example demonstrating the bug:**

```
Scenario: Short position with stop loss
- 2026/04/06 04:00: Open short position at price 50000
- 2026/04/06 08:00: Price rises to 51000, stop loss triggers (-2% loss)
- 2026/04/06 08:00: Short entry signal still active (e.g., RSI < 30)
- 2026/04/06 08:00: System immediately reopens short position at 51000

Expected behavior:
- 2026/04/06 04:00: Open short position at price 50000
- 2026/04/06 08:00: Price rises to 51000, stop loss triggers (-2% loss)
- 2026/04/06 08:00: System does NOT reopen short position
- 2026/04/06 12:00: If short entry signal still active, system may open new short position
```

The bug creates unnecessary transaction costs and poor risk management by immediately re-entering a position that just hit a stop loss.
