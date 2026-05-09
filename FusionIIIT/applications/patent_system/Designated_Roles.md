# Module Name: Patent Management System

## Designated User Roles & Permissions

### 1. Role Name: PCC Admin

* **Description:** Central module administrator responsible for operational control, workflow routing, and compliance handling.

* **Permissions:**

    * Full CRUD on patent applications and related module records.

    * Review new submissions and forward applications to Director.

    * Request modifications, manage workflow state transitions, and monitor pending actions.

    * Manage budget entries, communication logs, attorney assignment, filing records, and analytics dashboards.

    * Access audit logs and module-wide reporting views.


### 2. Role Name: Director

* **Description:** Decision authority for review, approval/rejection, appeal decisions, and escalated budget approvals.

* **Permissions:**

    * View applications assigned for Director review.

    * Approve, reject, or mark applications for revision with mandatory feedback.

    * Approve or deny escalated budgets.

    * Review and decide appeals.

    * View notifications and decision-linked records relevant to assigned workflows.


### 3. Role Name: Applicant / Inventor

* **Description:** Primary end-user who submits, tracks, and updates patent applications and inventor consent data.

* **Permissions:**

    * Create and submit patent applications.

    * View personal/associated applications and status timeline.

    * Revise and resubmit applications when revision is requested.

    * Withdraw applications (subject to workflow/state restrictions).

    * Provide/revoke inventor consent where applicable.

    * Lodge appeal for rejected applications within defined timeline constraints.


### 4. Role Name: External Attorney (Recorded Entity)

* **Description:** External legal expert tracked by the module for legal assessment and filing lifecycle stages.

* **Permissions:**

    * Not a direct portal-authenticated role in current implementation.

    * Assignment details, legal assessment inputs, and filing details are recorded by PCC Admin.

    * Actions are represented through module records (assessment, filing, communication logs).
