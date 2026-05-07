#!/usr/bin/env python3
"""
Visual explanation of quiz start/end time calculation
"""

def calculate_quiz_duration(start_time_str, end_time_str):
    """Calculate quiz duration from ISO datetime strings"""
    from datetime import datetime
    
    # Parse ISO formatted datetimes
    start = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
    end = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
    
    # Calculate difference
    delta = end - start
    total_minutes = int(delta.total_seconds() // 60)
    
    # Breakdown
    days = total_minutes // (60 * 24)
    hours = (total_minutes % (60 * 24)) // 60
    minutes = total_minutes % 60
    
    return {
        'start': start,
        'end': end,
        'total_minutes': total_minutes,
        'days': days,
        'hours': hours,
        'minutes': minutes,
        'total_seconds': int(delta.total_seconds())
    }

# Example 1: Short quiz (same day)
print("="*70)
print("EXAMPLE 1: Short Quiz (Same Day)")
print("="*70)
result1 = calculate_quiz_duration(
    "2026-03-26T10:00:00Z",
    "2026-03-26T11:30:00Z"
)
print(f"Start: {result1['start']}")
print(f"End:   {result1['end']}")
print(f"\nDuration:")
print(f"  Days:    {result1['days']:02d}")
print(f"  Hours:   {result1['hours']:02d}")
print(f"  Minutes: {result1['minutes']:02d}")
print(f"\nTotal: {result1['total_minutes']} minutes ({result1['total_seconds']} seconds)")

# Example 2: Multi-day quiz (what we used earlier)
print("\n" + "="*70)
print("EXAMPLE 2: Multi-Day Quiz")
print("="*70)
result2 = calculate_quiz_duration(
    "2026-03-26T10:00:00Z",
    "2026-03-31T14:30:00Z"
)
print(f"Start: {result2['start']}")
print(f"End:   {result2['end']}")
print(f"\nDuration:")
print(f"  Days:    {result2['days']:02d}")
print(f"  Hours:   {result2['hours']:02d}")
print(f"  Minutes: {result2['minutes']:02d}")
print(f"\nTotal: {result2['total_minutes']} minutes ({result2['total_seconds']} seconds)")

# Example 3: Exactly 1 day
print("\n" + "="*70)
print("EXAMPLE 3: Exactly 1 Day")
print("="*70)
result3 = calculate_quiz_duration(
    "2026-03-26T10:00:00Z",
    "2026-03-27T10:00:00Z"
)
print(f"Start: {result3['start']}")
print(f"End:   {result3['end']}")
print(f"\nDuration:")
print(f"  Days:    {result3['days']:02d}")
print(f"  Hours:   {result3['hours']:02d}")
print(f"  Minutes: {result3['minutes']:02d}")
print(f"\nTotal: {result3['total_minutes']} minutes ({result3['total_seconds']} seconds)")

# Example 4: What happens in database
print("\n" + "="*70)
print("WHAT GETS STORED IN DATABASE")
print("="*70)
print("\nFor Example 2 (Multi-Day Quiz):")
print(f"  d_day    = '{result2['days']:02d}'")
print(f"  d_hour   = '{result2['hours']:02d}'")
print(f"  d_minute = '{result2['minutes']:02d}'")
print(f"  start_time = '{result2['start'].isoformat()}'")
print(f"  end_time   = '{result2['end'].isoformat()}'")

# Visual timeline
print("\n" + "="*70)
print("VISUAL TIMELINE")
print("="*70)
print("""
Quiz Duration Timeline:
                    
    2026-03-26 10:00 UTC
    │
    ├─── Day 1 (24 hours)
    │
    ├─── Day 2 (24 hours)
    │
    ├─── Day 3 (24 hours)
    │
    ├─── Day 4 (24 hours)
    │
    ├─── Day 5 (24 hours)
    │
    └─── Plus 4 hours 30 minutes
         │
         2026-03-31 14:30 UTC

Total Duration: 5 days + 4 hours + 30 minutes
              = 129 hours 30 minutes
              = 7770 minutes
""")

print("="*70)
