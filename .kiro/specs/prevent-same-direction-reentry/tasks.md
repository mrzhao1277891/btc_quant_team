# Implementation Plan

## Overview

This task list implements the fix for preventing same-direction reentry after exit conditions. The workflow follows the exploratory bugfix methodology:
1. **Explore** - Write bug condition test BEFORE fix to understand the bug
2. **Preserve** - Write preservation tests for non-buggy behavior
3. **Implement** - Apply the fix with understanding
4. **Validate** - Verify fix works and doesn't break anything

## Tasks

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Same-Direction Reentry After Exit
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists
  - **Scoped PBT Approach**: Scope the property to concrete failing cases: position closed due to exit condition with same-direction signal still active
  - Test implementation details from Bug Condition in design:
    - Create scenario where position is closed due to stop loss/take profit
    - Ensure same-direction entry signal is still active on the same candle
    - Assert that NO position is reopened in the same direction on that candle
  - The test assertions should match the Expected Behavior Properties from design (Requirements 2.1, 2.2)
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists)
  - Document counterexamples found to understand root cause:
    - Record timestamps where close-reopen cycles occur
    - Record position directions and entry/exit prices
    - Record the entry signal conditions that were active
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Reverse Signals and Normal Entry Behavior
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for non-buggy inputs:
    - Test reverse signal execution (close long + open short, close short + open long)
    - Test normal entry when no position exists
    - Test position maintenance when no exit/reverse conditions
    - Test that same-direction signals during an open position are ignored (no action)
  - Write property-based tests capturing observed behavior patterns from Preservation Requirements:
    - For all reverse signal scenarios, verify close + open opposite occurs
    - For all normal entry scenarios (no position), verify position opens
    - For all position maintenance scenarios, verify position is held
    - For all same-direction signals during open position, verify no action
  - Property-based testing generates many test cases for stronger guarantees
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3. Fix for same-direction reentry prevention

  - [x] 3.1 Implement the fix in backend/backtest/engine.py
    - Add `last_closed_direction` variable at the start of each candle iteration in run() method
    - Initialize to `None` at the beginning of the loop (line ~950)
    - When closing position due to exit conditions (lines 956-960):
      - Capture `self.current_position.direction` into `last_closed_direction` BEFORE calling `_close_position()`
      - Do NOT capture for reverse signal closes (lines 975-977) - reverse signals should allow immediate opposite entry
    - Before opening new position (lines 1003-1010):
      - Add condition: `if has_signal and signal_direction is not None and signal_direction != last_closed_direction`
      - Only allow opening if signal direction differs from last closed direction
      - Add debug log when same-direction reentry is prevented
    - Variable naturally resets each iteration (scoped to loop)
    - _Bug_Condition: isBugCondition(input) where position_closed_this_candle = true AND closed_position_direction = entry_signal_direction_
    - _Expected_Behavior: After closing due to exit conditions, do NOT reopen in same direction on current candle (Requirements 2.1, 2.2)_
    - _Preservation: Reverse signals (3.1), normal entries (3.2), position maintenance (3.3, 3.4) must remain unchanged_
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4_

  - [x] 3.2 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Same-Direction Reentry Prevented
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - Verify that positions are NOT reopened in the same direction on the close candle
    - Verify that debug logs show "Prevented same-direction reentry" messages
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.3 Verify preservation tests still pass
    - **Property 2: Preservation** - No Regressions in Other Behaviors
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix:
      - Reverse signals still execute correctly
      - Normal entries still work when no position exists
      - Position maintenance still works
      - Same-direction signals during open position still ignored
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 4. Checkpoint - Ensure all tests pass
  - Run complete test suite for backtest engine
  - Verify all bug condition tests pass (same-direction reentry prevented)
  - Verify all preservation tests pass (no regressions)
  - Verify integration tests pass (full backtest scenarios)
  - Review test coverage for edge cases
  - If any tests fail, investigate and fix before proceeding
  - Ask the user if questions arise about test failures or unexpected behavior

## Test File Organization

**Test Location**: `backend/tests/test_backtest_engine_same_direction_reentry.py`

**Test Structure**:
```python
# Bug Condition Tests (Property 1)
class TestBugConditionExploration:
    def test_short_stop_loss_same_direction_signal()
    def test_long_take_profit_same_direction_signal()
    def test_consecutive_candles_same_signal()
    def test_indicator_exit_same_direction_signal()

# Preservation Tests (Property 2)
class TestPreservation:
    def test_reverse_signal_long_to_short()
    def test_reverse_signal_short_to_long()
    def test_normal_entry_no_position()
    def test_position_maintenance_no_exit()
    def test_same_direction_signal_during_position_ignored()
    def test_backtest_end_force_close()
    def test_insufficient_capital_handling()

# Integration Tests
class TestIntegration:
    def test_full_backtest_with_multiple_scenarios()
    def test_trade_count_reduction_after_fix()
```

## Implementation Notes

**Key Points**:
- The `last_closed_direction` variable is the core mechanism for tracking closed positions
- It's scoped to each loop iteration, so it naturally resets for each candle
- Reverse signals do NOT set this variable, allowing immediate opposite-direction entry
- The fix only affects the entry signal check when no position exists
- All other logic (exit conditions, reverse signals, position maintenance) remains unchanged

**Testing Strategy**:
- Write tests BEFORE implementing the fix (exploratory testing)
- Run tests on unfixed code to confirm the bug exists
- Implement the fix
- Re-run the same tests to confirm the fix works
- Ensure preservation tests pass to confirm no regressions

**Success Criteria**:
- Bug condition tests pass (same-direction reentry prevented)
- Preservation tests pass (no regressions in other behaviors)
- Integration tests pass (full backtest scenarios work correctly)
- Trade counts are reduced in scenarios with consecutive same-direction signals
- No new bugs introduced
