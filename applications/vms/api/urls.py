from django.urls import path

from .views import (
    # Original endpoints
    ActiveVisitorsView,
    DenyEntryView,
    IssuePassView,
    RecentVisitsView,
    RecordEntryView,
    RecordExitView,
    RegisterVisitorView,
    SecurityIncidentView,
    VerifyVisitorView,
    # BR-019/020/021: Pass scan
    ScanPassView,
    # BR-023: Manual verification
    ManualVerificationView,
    # BR-024: Overstay
    OverstayView,
    # BR-025–029: Reports
    ReportGenerationView,
    # BR-030–035: Blacklist management
    BlacklistView,
    BlacklistRemoveView,
    BlacklistAuditView,
    # BR-030/031: Visitor/incident history
    VisitorHistoryView,
    VisitorHistoryByVisitView,
    IncidentHistoryView,
    # Who-am-I (role lookup for the UI)
    WhoAmIView,
    # BR-036–040: Location tracking
    VisitorLocationView,
    # BR-041–047: VIP processing
    VIPProcessView,
    VIPVisitorsView,
    VIPActivityView,
    EscortAssignView,
    EscortReleaseView,
    AvailableEscortsView,
    # BR-057–066: System config
    SystemConfigView,
    ConfigChangeHistoryView,
    # BR-063: Visiting hours
    VisitingHoursView,
    # BR-064: Access zones
    AccessZoneView,
    # BR-067–074: Data export/import
    DataExportView,
    DataImportView,
    DataOperationsView,
)

app_name = "vms"

urlpatterns = [
    # --- Role lookup (no VMS admin needed — any authenticated user) ---
    path("me/", WhoAmIView.as_view(), name="whoami"),

    # --- Core visitor workflow (WF-001, WF-003) ---
    path("register/", RegisterVisitorView.as_view(), name="register"),
    path("verify/", VerifyVisitorView.as_view(), name="verify"),
    path("pass/", IssuePassView.as_view(), name="issue-pass"),
    path("entry/", RecordEntryView.as_view(), name="record-entry"),
    path("exit/", RecordExitView.as_view(), name="record-exit"),
    path("deny/", DenyEntryView.as_view(), name="deny-entry"),
    path("active/", ActiveVisitorsView.as_view(), name="active"),
    path("recent/", RecentVisitsView.as_view(), name="recent"),

    # --- Pass scan & validation (WF-003) ---
    path("scan/", ScanPassView.as_view(), name="scan-pass"),
    path("manual-check/", ManualVerificationView.as_view(), name="manual-check"),

    # --- Incidents (WF-008) ---
    path("incidents/", SecurityIncidentView.as_view(), name="incidents"),

    # --- Overstay detection (BR-024) ---
    path("overstay/", OverstayView.as_view(), name="overstay"),

    # --- Reports (WF-004) ---
    path("reports/", ReportGenerationView.as_view(), name="reports"),

    # --- Blacklist management (WF-005) ---
    path("blacklist/", BlacklistView.as_view(), name="blacklist"),
    path("blacklist/<int:entry_id>/remove/", BlacklistRemoveView.as_view(), name="blacklist-remove"),
    path("blacklist/audit/<str:id_number>/", BlacklistAuditView.as_view(), name="blacklist-audit"),

    # --- Visitor / incident history (BR-030/031) ---
    path("history/<str:id_number>/", VisitorHistoryView.as_view(), name="visitor-history"),
    path("history/<str:id_number>/incidents/", IncidentHistoryView.as_view(), name="incident-history"),
    path("visit-history/<int:visit_id>/", VisitorHistoryByVisitView.as_view(), name="visit-history"),

    # --- Location tracking (WF-006) ---
    path("location/<int:visit_id>/", VisitorLocationView.as_view(), name="visitor-location"),

    # --- VIP processing (WF-007) ---
    path("vip/process/", VIPProcessView.as_view(), name="vip-process"),
    path("vip/", VIPVisitorsView.as_view(), name="vip-visitors"),
    path("vip/<int:visit_id>/activity/", VIPActivityView.as_view(), name="vip-activity"),
    path("escorts/", EscortAssignView.as_view(), name="escorts"),
    path("escorts/available/", AvailableEscortsView.as_view(), name="escorts-available"),
    path("escorts/<int:assignment_id>/release/", EscortReleaseView.as_view(), name="escort-release"),

    # --- System config (WF-009) ---
    path("config/", SystemConfigView.as_view(), name="config"),
    path("config/history/", ConfigChangeHistoryView.as_view(), name="config-history"),

    # --- Visiting hours (BR-063) ---
    path("visiting-hours/", VisitingHoursView.as_view(), name="visiting-hours"),

    # --- Access zones (BR-064) ---
    path("zones/", AccessZoneView.as_view(), name="zones"),

    # --- Data export/import (WF-010) ---
    path("export/", DataExportView.as_view(), name="data-export"),
    path("import/", DataImportView.as_view(), name="data-import"),
    path("data-operations/", DataOperationsView.as_view(), name="data-operations"),
]
