# Short Report: Requirements-Based Backend Testing and Evaluation

## 1. Test Adequacy Summary

Using the supplied Gymkhana functional requirements, the backend test design covered all 10 documented use cases, all 22 documented business rules, and all 7 documented workflows. This resulted in 30 UC tests, 44 BR tests, and 14 WF tests, which satisfies the required minimum adequacy of 100.00% in each category.

Execution outcomes were mixed but unfavorable overall. Out of 88 executed tests, 23 passed, 16 were partial, and 49 failed. The strict pass rate was 26.14%. The strongest positive signals came from direct model/view inspection, where some structural rules such as required file fields, cascade deletes, primary-key uniqueness, and category choices were confirmed. The most serious blockers came from runtime route loading and missing voting handlers.

## 2. Key Failures Found

The highest-severity issue is a backend startup failure. Importing `applications.gymkhana.urls` pulls in the API layer, which imports selector and service modules that reference a non-existent `Budget` model. This prevents Django from routing requests into the legacy Gymkhana handlers, so many use cases and workflows fail before any business logic can execute.

A second major failure is that the documented voting use cases do not currently have executable handlers. The requirement documents trace UC006 and UC007 to `voting_poll()` and `vote()`, but those functions are commented out or absent in `applications.gymkhana.views`. As a result, both voting use cases and both voting workflows are effectively not implemented.

The third major finding is that several business rules are only partially enforced or not enforced at all. Duplicate same-club membership prevention is not backed by a uniqueness constraint on `Club_member`. One-vote-per-student is not backed by any uniqueness constraint on `Voting_voters`. Non-negative budget values are not enforced because the field minimum remains the default integer floor rather than zero. The status enumeration documented in the requirements also no longer matches the broader status choices in the current model.

## 3. Major Defects

- DEF-01: Startup routing failure caused by missing `Budget` model import in the Gymkhana API dependency chain.
- DEF-02: Voting handlers `voting_poll`, `vote`, and `delete_poll` are missing/commented out despite being present in the requirements traceability.
- DEF-03: No uniqueness constraint enforces one vote per student per poll.
- DEF-04: No uniqueness constraint enforces duplicate-application prevention for the same student/club pair.
- DEF-05: Negative budget values are allowed by current model validation range.
- DEF-06: Club-member status choices exceed the documented enumeration.
- DEF-07: Minimum poll-choice validation is not enforced in the backend.

## 4. Final Module Evaluation

From a specification-based perspective, the Gymkhana backend is only partially aligned with the requirement set. The design adequacy target was met, but end-to-end execution evidence shows that most operational use cases and all workflows are blocked by routing/import failures or missing handler implementations. Some structural business rules are correctly represented at the model layer, but critical behavioral rules are either only partially enforced or not enforced by the backend itself.

The final evaluation is that the module should be treated as **not ready for submission as a fully working backend** until the startup import chain is repaired, the voting handlers are restored or implemented, and the missing database/model-level constraints are added for the documented business rules.
