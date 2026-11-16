
# CourtVision — Manual Testing and Validation

**Course:** CSCE 4110 — Algorithms  
**Project:** NBA Analytics & Lineup Optimizer  
**Contribution:** Member 3 — Dashboard, Integration, Testing and Debugging  
**Date:** November 15, 2026

## TC-01: Normal Lineup Optimization

Input:
- Salary budget: $150M
- Requested lineup: 5 players
- Untouchable player: Jayson Tatum

Expected:
- Five unique players within the salary cap.
- Locked player included.

Actual:
- Total performance: 344.3
- Total salary: $141.4M
- Remaining cap: $8.6M
- Dashboard reported all constraints passed.

Result: PRELIMINARY PASS.
Individual lineup rows were not independently verified.

## TC-02: Insufficient Budget

Input:
- Salary budget: $20M
- Requested lineup: 5 players
- Untouchable player: Jayson Tatum

Expected:
- Reject an infeasible lineup without exceeding the budget.

Actual:
- Application displayed:
  "Untouchable players cost $54.1M, which is over the $20M budget."

Result: PASS.

## TC-03: Full Roster Builder

Input:
- Team salary cap: $165M
- Bench importance: 0.40
- Five starters and five bench players

Expected:
- Ten unique players.
- Salary within the cap.
- Jayson Tatum retained once.

Actual:
- Weighted score: 444.4
- Total salary: $164.0M
- Remaining cap: $1.0M
- Roster size: 10
- Five starters and five bench players.
- No duplicate players observed.

Result: PASS.

## TC-04: Player Search

Input:
- Search term: Jokic

Expected:
- Find Nikola Jokić without requiring accented characters.

Actual:
- Before debugging: 0 matching players.
- After debugging: 1 matching player.
- Average performance: 91.3.

Result: PASS, assuming matching row is Nikola Jokić.

Debugging:
- Updated player-name filtering with Unicode normalization.
- Improved accent-insensitive search.

## TC-05: Locked-Player Validation

Input:
- Salary budget: $165M
- Requested lineup: 5 players
- Untouchable: Jayson Tatum

Expected:
- Retain Jayson Tatum.
- Respect the budget and lineup constraints.

Actual:
- Total performance: 352.6
- Total salary: $157.9M
- Remaining cap: $7.1M
- Dashboard reported all constraints passed.
- Dashboard reported Jayson Tatum retained.

Result: PASS based on dashboard-reported constraints.

## Automated Testing

- Original automated test suite: 37 passed.
- New integration tests: 4 passed.
- Full combined 41-test suite : 41 tests passed.

## Summary

The dashboard handled normal optimization,
infeasible budgets, locked-player constraints,
roster building, and player search.

Manual testing identified an accented-name search
issue. The search logic was updated and retested.
