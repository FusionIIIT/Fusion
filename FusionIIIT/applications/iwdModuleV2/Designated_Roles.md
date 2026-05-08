# Module Name: IWD Module V2

## Designated User Roles & Permissions

### 1. Role Name: Request Initiator (Engineer / HOD / Dean)

* **Description:** Creates maintenance requests and starts the workflow. Students are explicitly blocked from creating requests.

* **Permissions:**

    * Create new IWD requests (non-student authenticated users only).

    * Must use a held designation as sender role.

    * New requests can only be forwarded to `Admin IWD` at creation time.

    * View own created requests and file/request status views.

### 2. Role Name: IWD Admin

* **Description:** Primary operational approver and workflow controller for IWD requests.

* **Permissions:**

    * Approve or reject requests at the first approval stage (`handle-admin-approval`).

    * Set next stage to HOD/Dean after approval.

    * Issue work orders (along with allowed roles configured in API).

    * Add vendors, process bills, and participate in financial flow.

    * Access request/budget/inventory/SLA views used for module operations.

### 3. Role Name: HOD / Dean Approver

* **Description:** Second-level approver in the mandatory sequential approval chain.

* **Permissions:**

    * Can process requests only if user holds one of configured HOD/Dean designations.

    * Approve/reject at dean/HOD stage (`handle-dean-process-request`).

    * On approve, can forward only to `Director` designation.

    * On reject, request is marked rejected at dean/HOD stage.

### 4. Role Name: Director

* **Description:** Final approver for the request approval workflow.

* **Permissions:**

    * Approve or reject requests at director stage (`handle-director-approval`).

    * Director approval requires prior IWD Admin approval and dean/HOD processing.

    * Final approval marks request fully approved for work order issuance.

### 5. Role Name: Engineer (Execution Role)

* **Description:** Execution-side role responsible for proposal/work progress updates.

* **Permissions:**

    * Create proposals and submit updates tied to requests.

    * Mark work as completed (`work-completed`).

    * Access engineer-facing workflow endpoints (processed/in-progress views).

### 6. Role Name: Auditor

* **Description:** Audits generated bills before settlement.

* **Permissions:**

    * Audit bill documents (`audit-document`).

    * Forward audited items to `Accounts Admin` stage.

    * Audit must occur after bill generation.

### 7. Role Name: Accounts Admin

* **Description:** Financial closure role for bill processing and settlement.

* **Permissions:**

    * Process bills (`handle-process-bills`) and move them through payment workflow.

    * Settle final bills (`handle-settle-bill-request`).

    * Participate in work order issuance and vendor/billing operations where permitted.

### 8. Role Name: Authenticated End User (General Access)

* **Description:** Logged-in module user with baseline read/access actions.

* **Permissions:**

    * Access common read endpoints (file views, status lists, generated bill views, feedback history, SLA/inventory dashboards).

    * Submit feedback and reopen requests where workflow conditions permit.

    * Read-only usage does not grant stage-approval authority.
