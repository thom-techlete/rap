#!/usr/bin/env python
"""
Simple script to test the timezone fix for notifications.
This script doesn't require Django setup and can be run independently.
"""

from datetime import datetime
import pytz

def test_timezone_conversion():
    """Test timezone conversion logic"""
    
    # Simulate what Django does - store datetime in UTC
    utc_tz = pytz.UTC
    amsterdam_tz = pytz.timezone('Europe/Amsterdam')
    
    # Original time: 20:30 Amsterdam time on Dec 25, 2024
    amsterdam_time = amsterdam_tz.localize(datetime(2024, 12, 25, 20, 30))
    print(f"Original Amsterdam time: {amsterdam_time}")
    
    # Convert to UTC (this is what Django stores in the database)
    utc_time = amsterdam_time.astimezone(utc_tz)
    print(f"UTC time (stored in DB): {utc_time}")
    
    # OLD WAY (wrong): Format UTC time directly
    old_formatted = utc_time.strftime("%d-%m-%Y om %H:%M")
    print(f"OLD way (wrong): {old_formatted}")
    
    # NEW WAY (correct): Convert back to Amsterdam time before formatting
    local_time = utc_time.astimezone(amsterdam_tz)
    new_formatted = local_time.strftime("%d-%m-%Y om %H:%M")
    print(f"NEW way (correct): {new_formatted}")
    
    # Test results
    assert "18:30" in old_formatted, f"Expected 18:30 in old format, got {old_formatted}"
    assert "20:30" in new_formatted, f"Expected 20:30 in new format, got {new_formatted}"
    
    print("\n✅ All tests passed!")
    print("- Old way incorrectly shows 18:30 (UTC time)")
    print("- New way correctly shows 20:30 (Amsterdam time)")

if __name__ == "__main__":
    test_timezone_conversion()