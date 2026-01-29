# Approval Workflow for Organization Prompts

## Overview

Add an approval workflow for prompt changes in the organization-wide shared workspace. Users submit change requests that Approvers must review before changes go live. Personal workspaces remain unaffected (direct edits allowed).

## Key Decisions

- **Two roles**: USER and APPROVER (global, not per-workspace)
- **Organization workspace**: Auto-created on first boot, shared across all users
- **Approvers bypass approval**: Approvers can edit org prompts directly
- **Self-approval forbidden**: Users cannot approve their own change requests
- **Role management**: All Approvers can toggle any user's role (except their own)
- **Bootstrap**: First registered user becomes Approver

---

## Section 1: Data Model

### Updated Models

**User (updated):**
```
User:
  - id: UUID
  - email: str
  - created_at: datetime
  - role: UserRole (USER | APPROVER, default: USER)
```

### New Models

**ChangeRequest:**
```
ChangeRequest:
  - id: UUID
  - workspace_id: "organization"
  - prompt_type: CATEGORY_DEFINITIONS | FEW_SHOTS | SYSTEM_PROMPT
  - submitted_by: user_id
  - submitted_at: datetime
  - status: PENDING | APPROVED | REJECTED
  - description: Optional[str]
  - current_content: JSON (snapshot at submission time)
  - proposed_content: JSON (the new content)
  - reviewed_by: Optional[user_id]
  - reviewed_at: Optional[datetime]
  - review_feedback: Optional[str]
```

### Storage

- User role: Add `role` column to `users` table in `auth.db`
- Organization workspace: `data/workspaces/organization/`
- Change requests: `data/workspaces/organization/change_requests/*.json`

---

## Section 2: API Endpoints

### Change Request Endpoints

```
POST   /api/change-requests
       - Submit a change request for org workspace prompts
       - Body: { prompt_type, proposed_content, description? }
       - Returns: ChangeRequest

GET    /api/change-requests
       - List all change requests (filterable by status)
       - Query params: ?status=PENDING|APPROVED|REJECTED
       - Returns: List[ChangeRequest]

GET    /api/change-requests/{id}
       - Get single change request with diff details
       - Returns: ChangeRequest with current vs proposed content

POST   /api/change-requests/{id}/approve
       - Approver only, cannot approve own request
       - Body: { feedback? }
       - Applies proposed_content to org workspace prompts
       - Returns: ChangeRequest (status=APPROVED)

POST   /api/change-requests/{id}/reject
       - Approver only
       - Body: { feedback? }
       - Returns: ChangeRequest (status=REJECTED)

POST   /api/change-requests/{id}/revise
       - Original submitter only, only if REJECTED
       - Body: { proposed_content, description? }
       - Resets status to PENDING, refreshes current_content snapshot
       - Returns: ChangeRequest

DELETE /api/change-requests/{id}
       - Withdraw request (original submitter only, only if PENDING)
       - Returns: 204 No Content
```

### Modified Prompt Endpoints (Organization Workspace)

```
PUT    /api/workspaces/organization/prompts/categories
PUT    /api/workspaces/organization/prompts/few-shots
PUT    /api/workspaces/organization/prompts/system-prompt
       - For Users: Creates a change request (returns ChangeRequest, status=PENDING)
       - For Approvers: Direct save (existing behavior)
```

### User Management Endpoints

```
GET    /api/users/me
       - Returns current user info including role

GET    /api/users
       - Approver only
       - Returns list of all users with roles

PATCH  /api/users/{id}/role
       - Approver only, cannot change own role
       - Body: { role: "USER" | "APPROVER" }
       - Returns: Updated user
```

### Copy Prompts Endpoint

```
POST   /api/workspaces/{workspace_id}/copy-from-organization
       - Copies current org prompts to user's workspace
       - Overwrites existing prompts in target workspace
       - Returns: { success: true }
```

---

## Section 3: Authorization Rules

### Role-Based Access Matrix

| Action | USER | APPROVER |
|--------|------|----------|
| View org workspace prompts | Yes | Yes |
| Edit org workspace prompts | Creates change request | Direct save |
| Submit change request | Yes | Yes |
| View change requests | Yes | Yes |
| Approve/Reject requests | No | Yes (not own) |
| Revise rejected request | Own only | Own only |
| Withdraw pending request | Own only | Own only |
| Edit own workspace directly | Yes | Yes |
| View all users | No | Yes |
| Change user roles | No | Yes (not own) |
| Copy org prompts to own workspace | Yes | Yes |

### Business Rules

1. **Self-approval forbidden** - Approvers cannot approve their own change requests

2. **Conflict detection** - When approving, verify `current_content` matches actual current prompts. If mismatch, return error requiring revision

3. **One active request per user per prompt_type** - Cannot submit new request if user has PENDING request for same prompt type

4. **Revision refreshes snapshot** - When revising, `current_content` is updated to latest

5. **First user becomes Approver** - Bootstrap mechanism for initial setup

6. **Cannot demote last Approver** - Prevent lockout scenario

7. **Cannot delete organization workspace** - Protected from deletion

---

## Section 4: Organization Workspace Initialization

### Auto-Creation on Startup

Application startup checks for organization workspace:

1. Check if `data/workspaces/organization/` exists
2. If not, create with:
   - `metadata.json`: `{ id: "organization", name: "Organization", user_id: null, created_at: <timestamp> }`
   - `category_definitions.json`: Default template
   - `few_shot_examples.json`: Default template
   - `system_prompt.json`: Empty/default

### Workspace Listing

`GET /api/workspaces` returns:
- Organization workspace first (marked with `is_organization: true`)
- User's personal workspaces after

---

## Section 5: UI Changes

### Header/Navigation

- Badge showing count of pending change requests (visible to Approvers)
- Fetches from `GET /api/change-requests?status=PENDING`

### Organization Workspace Prompt Editor

- **For Users**: "Submit for Approval" button with optional description field
- **For Approvers**: Regular "Save" button (direct save)

### Change Request Queue (new page: `/approvals`)

- List view with columns: prompt type, submitter, submitted date, status
- Filter tabs: All / Pending / Approved / Rejected
- Click row to view details

### Change Request Detail View

- Side-by-side or inline diff (current vs proposed)
- Submitter info and description (if provided)
- **For Approvers (not own request)**: Approve/Reject buttons with optional feedback
- **For original submitter (if rejected)**: Revise button
- **For original submitter (if pending)**: Withdraw button

### User Management (new page: `/users`)

- Approver only
- Table of all users: email, role, created date
- Toggle button for role (USER <-> APPROVER)
- Disabled for current user's row

---

## Section 6: Error Handling

### Conflict Detection

When approving a change request:
- Compare `current_content` with actual current prompts
- If mismatch: `409 Conflict` - "Prompts have changed since submission. Request must be revised."

### Pending Request Limit

When submitting a change request:
- Check for existing PENDING request by same user for same prompt_type
- If exists: `409 Conflict` - "You already have a pending request for [type]. Wait for review or withdraw it."

### Last Approver Protection

When demoting an Approver:
- Count remaining Approvers
- If this is the last one: `400 Bad Request` - "Cannot demote the last Approver"

### Organization Workspace Protection

When attempting to delete organization workspace:
- `403 Forbidden` - "Organization workspace cannot be deleted"

### Self-Role Change Prevention

When Approver tries to change own role:
- `403 Forbidden` - "Cannot change your own role"

### Self-Approval Prevention

When Approver tries to approve own request:
- `403 Forbidden` - "Cannot approve your own change request"
