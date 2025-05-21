# User Story: Rule Promotion and Hierarchical Scopes

## Motivation
To support organization-wide, team, and project-specific best practices, rules can now be promoted from project or machine scope to higher levels (team, global, etc.). This enables scalable governance and flexible rule management across distributed teams and systems.

## Actors
- Project Maintainer
- Team Lead
- System Administrator
- API Client (automation)

## Preconditions
- A rule exists at a lower scope (e.g., project or machine).
- The user has permission to promote rules (enforced externally or by workflow).

## Step-by-Step Actions
1. **Identify the Rule:**
   - Fetch the rule to be promoted using the `/rules` endpoint, filtering by `scope_level` and `scope_id` if needed.
2. **Prepare Promotion Request:**
   - Decide the new `scope_level` (e.g., `team`, `global`) and, if required, the `scope_id` (e.g., team identifier).
3. **Call the Promotion Endpoint:**
   - Make a `POST` request to `/rules/{rule_id}/promote` with a JSON body:
     ```json
     {
       "scope_level": "team",
       "scope_id": "team-123"  // optional, as needed
     }
     ```
4. **API Validates Transition:**
   - The API only allows upward promotions (e.g., project → team, team → global).
   - If the transition is valid, the rule's `scope_level` and `scope_id` are updated.
5. **Receive Updated Rule:**
   - The API returns the updated rule object, now at the higher scope.

## Expected Outcomes
- The rule is now visible to all users/systems at the new scope (e.g., all projects in a team, or globally).
- The rule's `scope_level` and `scope_id` fields reflect the new scope.
- Downward transitions (demotions) are not allowed via this endpoint.

## Best Practices
- Use promotion to share proven rules upward in the organization.
- Always verify the rule's content and impact before promoting.
- Document the rationale for promotion in the rule's `user_story` or `description` fields.
- Use the `/rules` endpoint with `scope_level` and `scope_id` filters to audit rules at each level.

## References
- **API Endpoint:** `POST /rules/{rule_id}/promote`
- **Model Fields:** `scope_level`, `scope_id`, `parent_rule_id` (see API schema)
- **Related:** [project_scoped_rules_and_multiuser.md](project_scoped_rules_and_multiuser.md) 