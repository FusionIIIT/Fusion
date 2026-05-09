VMS Integration Map (concise)

Globals: Uses applications.globals.models.ExtraInfo to tie actions to staff; reuse Departments/Designations for role-based permissions.
Notifications: Hook VMS events (blacklist hit, denial, overstay, incident) into notification/notifications for alerts to supervisors/admins and hosts.
Filetracking: For escalations or incident reports, auto-create tracking files so investigations follow an auditable workflow.
HR2 / Recruitment: Onboard/offboard security staff; synchronize User/ExtraInfo and role assignments for VMS operators.
Academic Information / Department: Resolve host departments when registering visits; validate host users/contacts against authoritative staff/faculty records.
Inventory / Estate / Central Mess / Hostel / Library: Use authorized zones to mirror physical areas; deny entry if zone doesn’t match module-managed access policies.
Gymkhana / Event Modules: Pre-register event visitors and apply VIP/fast-track rules; monitor crowd limits via VMS active/inside counts.
Health Center: Flag health-related restrictions or escort requirements; log incidents involving medical emergencies.
Security/Compliance Reporting: Feed VMS movement and incident logs into reporting modules (or scheduled jobs) for audits, overstays, and hotspot analysis.
How to extend

Emit signals/webhooks from VMS events to notification and reporting modules.
Add DRF endpoints to fetch authorized zones from estate/inventory.
Add host lookup autocomplete that queries faculty/staff (globals/academic_information).
Create scheduled tasks to flag unclosed visits and push alerts via notifications.
Integrate incident creation with filetracking so high-severity issues open investigation files automatically.