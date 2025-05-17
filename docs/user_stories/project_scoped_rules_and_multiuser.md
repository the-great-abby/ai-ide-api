# Project-Scoped Rules, Dynamic Inheritance, and Multi-User Collaboration

## Motivation
Enable multiple users to collaborate on projects, with project-specific and globally-inherited rules, and clear access control. For now, all users are admins by default for simplicity.

## Actors
- Project Admin (all users, for now)
- Project Editor (future)
- Project Viewer (future)

## Preconditions
- Users and projects exist in the system.
- Some rules are defined globally (default project).

## Steps
1. Admin creates a new project.
2. On creation, the project automatically inherits all global rules (linked, not copied).
3. Admin invites users to the project; all users are assigned the 'admin' role by default.
4. Users access the project:
   - All see inherited rules from the default project.
   - Admins can add custom rules to the project.
   - Admins can update project settings and manage users.
5. If a global rule is updated, all projects inheriting it see the update immediately.
6. Users can distinguish between inherited and custom rules in the UI/API.

## Expected Outcomes
- Projects have both inherited and custom rules.
- Multiple users can collaborate with full permissions.
- Legacy data is accessible via the default project.

## Best Practices
- Use roles to control access and prevent accidental changes (future).
- Regularly review inherited rules for relevance.

## Notes
- For now, all users added to a project are assigned the 'admin' role, granting them full permissions. This simplifies collaboration during early development. Role-based access control will be introduced in a future update as requirements evolve. 