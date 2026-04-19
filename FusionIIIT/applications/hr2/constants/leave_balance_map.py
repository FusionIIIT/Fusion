"""Maps normalized leave-type keys to ``LeaveBalance`` allotted/used field names."""

LEAVE_TYPE_TO_ALLOTTED_USED = {
    "casual": ("casual_leave_allotted", "casual_leave_used"),
    "special casual leave": ("special_casual_leave_allotted", "special_casual_leave_used"),
    "special casual": ("special_casual_leave_allotted", "special_casual_leave_used"),
    "earned": ("earned_leave_allotted", "earned_leave_used"),
    "earned leave": ("earned_leave_allotted", "earned_leave_used"),
    "commuted": ("commuted_leave_allotted", "commuted_leave_used"),
    "commuted leave": ("commuted_leave_allotted", "commuted_leave_used"),
    "restricted holiday": ("restricted_holiday_allotted", "restricted_holiday_used"),
    "station leave": ("station_leave_allotted", "station_leave_used"),
    "vacation": ("vacation_leave_allotted", "vacation_leave_used"),
    "vacation leave": ("vacation_leave_allotted", "vacation_leave_used"),
}
