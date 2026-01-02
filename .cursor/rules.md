# Cursor Rules

## Project Context
This is the **TikTok Keyword Momentum Tracker** - an MVP web application that identifies newly emerging TikTok keywords with strong short-term momentum, cross-validated with Google Trends data.

## Critical Files to Read First
Before making any changes, always read:
1. `PROJECT_STATE.md` - Current project status and phase
2. `BUILD_SPEC.md` - Technical specifications and requirements
3. `TODO.md` - Current tasks and implementation order
4. `.cursor/rules.md` - This file

## Architecture Constraints
- **Backend**: Python 3.11 only
- **Frontend**: Next.js with App Router only
- **Database**: PostgreSQL only
- **No UI automation**: Never use headless browsers, Selenium, or app emulation
- **No AI scoring**: Scoring must be deterministic and reproducible
- **No real-time**: This is a daily batch processing system

## Documentation Requirements
After every meaningful action:
1. **Update PROJECT_STATE.md** - Edit existing sections, don't append endlessly
2. **Append to CURSOR_LOG.md** - Session goal, files created/modified, open questions
3. **Append to DECISIONS_LOG.md** - If a design decision or tradeoff was made

## Code Standards
- Follow Python PEP 8 style guide
- Use type hints in Python
- Use TypeScript for frontend
- Write tests for critical functionality
- Keep functions focused and single-purpose
- Add docstrings to public functions/classes

## Implementation Order
Strictly follow the order in BUILD_SPEC.md:
1. Repository structure ✅
2. Backend data models and DB schema
3. TikTok trend ingestion
4. Google Trends fetch + caching
5. Scoring algorithm
6. Daily automation
7. Frontend pages
8. Auth and Stripe
9. Final documentation

## Scoring Algorithm
Use the exact formula from BUILD_SPEC.md:
- lift = (avg(last_7) - avg(prev_21)) / (avg(prev_21) + 0.01)
- acceleration = slope(last_7) - slope(prev_21)
- novelty = 1 - percentile_rank(avg(prev_90))
- noise = stdev(last_7) / (avg(last_7) + 0.01)
- raw = 0.45*lift + 0.35*acceleration + 0.25*novelty - 0.25*noise
- score = int(100 / (1 + exp(-raw))) clamped to [1, 100]

## Error Handling
- Always handle partial failures gracefully
- Log errors with context
- Never crash the entire system due to one failure
- Implement retry logic for external APIs
- Use exponential backoff for rate limits

## Testing
- Write unit tests for scoring algorithm
- Test data ingestion with mock responses
- Test error scenarios
- Verify reproducibility of scores

## Git Workflow
- Commit frequently with clear messages
- Keep commits focused on single features
- Update documentation in same commit as code changes

## Questions
If any part of the spec is unclear or contradictory, STOP and ask before proceeding.

