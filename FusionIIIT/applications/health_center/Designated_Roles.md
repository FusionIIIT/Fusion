# Module Name: Primary Health Centre (PHC)

## Designated User Roles & Permissions

### 1. Role Name: Compounder (PHC Staff / Module Admin)

* **Description:** The primary operational administrator of the Health Centre module. The Compounder manages the day-to-day operations of the PHC including doctor management, patient consultations, pharmacy inventory, ambulance fleet, and reimbursement processing. This is the most privileged role within the module.

* **Permissions:**
    * **Doctor Management:** Full CRUD operations on doctor profiles (add, edit, activate/deactivate, delete doctors). Manage doctor schedules (create, update, delete weekly slots). Record and manage daily doctor attendance.
    * **Consultation & Prescription:** Create new patient consultations with vitals and clinical findings. Create prescriptions linked to consultations with automatic stock deduction from pharmacy inventory. View and manage all consultation records.
    * **Pharmacy & Inventory:** Full CRUD on medicine catalogue and stock entries. Manage expiry batches (add, delete, mark as returned). Create inventory requisitions for restocking. Mark requisitions as fulfilled upon receipt. View low-stock alerts and expiry warnings.
    * **Hospital Admissions:** Admit patients to the health centre ward. Record bed assignments, admission reasons, and attending doctor. Process patient discharges with discharge notes and follow-up instructions.
    * **Ambulance Fleet:** Full CRUD on ambulance vehicle records (registration, type, status). Log ambulance dispatch events with patient details, destination, and timestamps.
    * **Reimbursement Processing:** View all employee reimbursement claims. Forward claims through the approval workflow (PHC Staff → Sanction Authority → Accounts). Process claims at the PHC Staff stage (approve/reject with remarks).
    * **Announcements:** Create and broadcast health announcements to all portal users. Deactivate existing announcements.
    * **Complaints:** View and respond to all patient complaints with resolution notes and status updates.
    * **Reports & Audit:** Generate system-wide reports (consultation statistics, inventory summaries, reimbursement analytics). Access audit trail logs for all module operations.

---

### 2. Role Name: Patient (Student / Faculty / Staff — End User)

* **Description:** Any registered FusionIIIT portal user who accesses the Health Centre services as a consumer. Patients can view their medical history, file reimbursement claims, submit complaints, and access public health information.

* **Permissions:**
    * **Medical History:** Read-only access to personal consultation history, prescriptions, and clinical records.
    * **Prescriptions:** View personal prescriptions with medicine details, dosage, and instructions. Download prescription as a formatted PDF document.
    * **Health Profile:** View personal health profile (blood group, allergies, chronic conditions, emergency contacts).
    * **Doctor Schedules:** Read-only access to all doctor schedules and availability (public endpoint).
    * **Reimbursement Claims:** Submit new reimbursement claims with expense details and supporting documents. View personal claim history and track claim status through the approval workflow. Upload claim documents (receipts, bills).
    * **Complaints:** Submit new complaints/feedback about PHC services. View personal complaint history and track response status.
    * **Announcements:** Read-only access to all active health announcements.

---

### 3. Role Name: Accounts Manager (Cross-Module — Financial Authority)

* **Description:** Responsible for the final financial verification and approval of reimbursement claims that have passed through PHC Staff and Sanction Authority stages. This role operates at the accounts verification stage of the reimbursement workflow.

* **Permissions:**
    * View all reimbursement claims that have reached the `ACCOUNTS_REVIEW` stage.
    * Approve claims for final payment disbursement.
    * Reject claims with remarks at the accounts verification stage.
    * View claim documents and supporting evidence uploaded by claimants.

---

### 4. Role Name: Approving Authority (Cross-Module — Institute Admin)

* **Description:** The sanctioning authority responsible for approving high-value reimbursement claims and inventory requisitions. This role is defined at the institute level and is pending integration with the global role management system.

* **Permissions (Implemented — Pending Activation):**
    * Review and approve/reject inventory requisitions submitted by the Compounder.
    * Sanction reimbursement claims at the authority review stage.
    * **Note:** The backend API endpoints (`AuthorityInventoryRequisitionView`) are fully implemented but commented out, awaiting the cross-module `is_authority` role definition from the institute's global admin module.

---

## Role-Based Access Control (RBAC) Enforcement

| API Endpoint Group | Compounder | Patient | Accounts | Authority |
|---|---|---|---|---|
| Doctor Management (`/compounder/doctors/`) | ✅ Full CRUD | ❌ | ❌ | ❌ |
| Doctor Schedules (`/compounder/schedule/`) | ✅ Full CRUD | ✅ Read-Only | ❌ | ❌ |
| Attendance (`/compounder/attendance/`) | ✅ Full CRUD | ❌ | ❌ | ❌ |
| Consultations (`/compounder/consultation/`) | ✅ Full CRUD | ❌ | ❌ | ❌ |
| Prescriptions (`/compounder/prescription/`) | ✅ Full CRUD | ✅ Read + PDF | ❌ | ❌ |
| Medical History (`/patient/medical-history/`) | ❌ | ✅ Read-Only | ❌ | ❌ |
| Inventory & Stock (`/compounder/stock/`) | ✅ Full CRUD | ❌ | ❌ | ❌ |
| Expiry Batches (`/compounder/expiry/`) | ✅ Full CRUD | ❌ | ❌ | ❌ |
| Requisitions (`/compounder/requisition/`) | ✅ Create/Fulfill | ❌ | ❌ | ✅ Approve/Reject |
| Hospital Admissions (`/compounder/hospital-admit/`) | ✅ Full CRUD | ❌ | ❌ | ❌ |
| Ambulance Fleet (`/compounder/ambulance/`) | ✅ Full CRUD | ❌ | ❌ | ❌ |
| Ambulance Logs (`/compounder/ambulance-log/`) | ✅ Full CRUD | ❌ | ❌ | ❌ |
| Reimbursement Claims (`/reimbursement/`) | ✅ Process | ✅ Submit/View Own | ✅ Final Approve | ✅ Sanction |
| Complaints (`/complaint/`) | ✅ Respond | ✅ Submit/View Own | ❌ | ❌ |
| Announcements (`/announcements/`) | ✅ Create/Deactivate | ✅ Read-Only | ❌ | ❌ |
| System Reports (`/compounder/reports/`) | ✅ Generate | ❌ | ❌ | ❌ |
| Dashboard (`/dashboard/`) | ✅ Full Stats | ✅ Personal Stats | ❌ | ❌ |
