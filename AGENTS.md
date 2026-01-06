# AGENT Instructions for /Users/daniel/Desktop/git

## Default Superpowers Development Workflow

For all work rooted at `/Users/daniel/Desktop/git`, use the following default workflow (phases 0–7) unless a more specific `AGENTS.md` in a subdirectory overrides or extends it.

0. **Always-on Skill Check (`using-superpowers`)**
   - Before any response, exploration, or code change, check which skills might apply (even 1%).
   - If any skill applies, invoke it and follow its instructions before acting.

1. **Task Kickoff & Orchestration (`start-workflow`)**
   - When a new feature, refactor, or bugfix task appears, use `start-workflow` to decide the overall development path and which skills to chain next.

2. **Understanding & Shaping the Solution (`brainstorming` → `writing-plans`)**
   - Use `brainstorming` to clarify goals, constraints, and candidate approaches before implementation.
   - Then use `writing-plans` to create a concrete, step-by-step implementation plan from the chosen approach.

3. **Style of Development (`test-driven-development` and/or `systematic-debugging`)**
   - For new features or behavior changes, use `test-driven-development` to drive implementation from tests.
   - For bugs, failures, or unexpected behavior, use `systematic-debugging` before proposing or implementing fixes.

4. **Parallelization (`dispatching-parallel-agents` → `subagent-driven-development`)**
   - When there are two or more independent tasks that can run without shared state or strict sequencing, use `dispatching-parallel-agents` to identify them and `subagent-driven-development` to execute them in parallel against the shared plan.

5. **Plan Execution Over Time (`executing-plans`)**
   - When executing a written plan across multiple steps or sessions, use `executing-plans` to drive implementation, track progress, and respect checkpoints.

6. **Verification Before Claiming Success (`verification-before-completion`)**
   - Before stating that any work is “done”, “fixed”, or “passing”, use `verification-before-completion` to run the plan’s verification commands and confirm outputs match expectations.

7. **Review & Integration (`requesting-code-review` → `receiving-code-review` → `finishing-a-development-branch`)**
   - Use `requesting-code-review` when work is ready for review.
   - Use `receiving-code-review` to process and respond to feedback.
   - Use `finishing-a-development-branch` to decide how to integrate the work (merge, PR, keep, or discard) and to perform any branch/worktree cleanup.

Subdirectories may define additional or stricter workflows in their own `AGENTS.md` files; those take precedence for files in their scope.
