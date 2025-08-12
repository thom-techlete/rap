# 🎯 Managing Automatic Event Reminders via Django Admin

## Overview
Instead of hardcoding reminder schedules in settings, you can now manage all automatic reminders through the Django admin interface. This gives you full control over when and how reminders are sent.

## 🔧 Admin Interface Locations

### **Main Reminder Management**
📍 **URL:** `/admin/django_celery_beat/periodictask/`

**Here you can:**
- ✅ Enable/disable specific reminder types (1-week, 3-day, 1-day)
- ⏰ Change when reminders are sent (daily at 9 AM by default)
- 🎛️ Configure reminder-specific settings
- 📊 View execution history and statistics

### **Schedule Management**
📍 **URL:** `/admin/django_celery_beat/crontabschedule/`

**Here you can:**
- 🕘 Create custom schedules (e.g., "Every Tuesday at 2 PM")
- 🌍 Set timezone preferences
- ⚙️ Use advanced cron expressions

## 📋 Default Tasks Created

| Task Name | Type | Schedule | Status | Purpose |
|-----------|------|----------|--------|---------|
| **1-week Event Reminders** | Auto Reminder | Daily 9:00 AM | ✅ Enabled | Send reminders 7 days before events |
| **3-day Event Reminders** | Auto Reminder | Daily 9:00 AM | ❌ Disabled | Send reminders 3 days before events |
| **1-day Event Reminders** | Auto Reminder | Daily 9:00 AM | ❌ Disabled | Send reminders 1 day before events |
| **Cleanup Old Reminder Logs** | Maintenance | Monday 2:00 AM | ✅ Enabled | Clean logs older than 90 days |

## 🎮 How to Use the Admin Interface

### **1. Enable/Disable Reminders**
1. Go to `/admin/django_celery_beat/periodictask/`
2. Click on any reminder task
3. Check/uncheck the **"Enabled"** checkbox
4. Click **"Save"**

### **2. Change Reminder Timing**
1. Go to `/admin/django_celery_beat/periodictask/`
2. Click on the reminder task you want to modify
3. In the **"Reminder Settings"** section:
   - Select different **reminder type** (1_week, 3_days, 1_day)
   - Adjust **cleanup days** for maintenance tasks
4. Click **"Save"**

### **3. Modify Schedule (When Reminders are Sent)**
1. Go to `/admin/django_celery_beat/crontabschedule/`
2. Find the schedule you want to modify (e.g., "0 9 * * * (m/h/dM/MY/d)")
3. Modify the time fields:
   - **Hour:** 0-23 (9 = 9 AM)
   - **Minute:** 0-59 (0 = top of the hour)
   - **Day of week:** 0-6 (0=Sunday, 1=Monday, etc.) or * for daily
4. Click **"Save"**

### **4. Create Custom Schedules**
1. Go to `/admin/django_celery_beat/crontabschedule/`
2. Click **"Add Crontab Schedule"**
3. Set your desired timing:
   ```
   Examples:
   - Daily at 8 AM: minute=0, hour=8, day_of_week=*, day_of_month=*, month_of_year=*
   - Weekdays at 6 PM: minute=0, hour=18, day_of_week=1-5, day_of_month=*, month_of_year=*
   - Twice daily: Create two separate schedules
   ```
4. Set timezone to **"Europe/Amsterdam"**
5. Click **"Save"**

### **5. Create New Reminder Tasks**
1. Go to `/admin/django_celery_beat/periodictask/`
2. Click **"Add Periodic Task"**
3. Fill in:
   - **Name:** Descriptive name (e.g., "Weekend Event Reminders")
   - **Task:** `notifications.tasks.send_automatic_event_reminders`
   - **Enabled:** ✅ Check to activate
   - **Reminder type:** Choose from dropdown
   - **Crontab:** Select your schedule
4. Click **"Save"**

## 🛠️ Advanced Examples

### **Example 1: Weekend-Only Reminders**
```
Task: Weekend Event Reminders
Schedule: Saturday & Sunday at 10 AM
Crontab: minute=0, hour=10, day_of_week=0,6  (Sunday=0, Saturday=6)
```

### **Example 2: Multiple Daily Reminders**
```
Task: Morning Reminders
Schedule: Daily at 8 AM
Crontab: minute=0, hour=8, day_of_week=*

Task: Evening Reminders  
Schedule: Daily at 6 PM
Crontab: minute=0, hour=18, day_of_week=*
```

### **Example 3: Business Hours Only**
```
Task: Weekday Business Hour Reminders
Schedule: Monday-Friday at 9 AM
Crontab: minute=0, hour=9, day_of_week=1-5
```

## 📊 Monitoring & Logs

### **View Execution History**
1. Go to `/admin/django_celery_beat/periodictask/`
2. Check the **"Last run at"** and **"Total run count"** columns
3. Click on a task to see detailed execution info

### **View Reminder Logs**
1. Go to `/admin/notifications/automaticrreminderlog/`
2. See all sent reminders, success/failure status, and recipient counts
3. Filter by reminder type, date, or success status

## 🚨 Troubleshooting

### **Task Not Running?**
1. ✅ Check if task is **enabled**
2. ✅ Verify **Celery beat service** is running: `docker-compose logs celery_beat`
3. ✅ Check **schedule configuration** is correct
4. ✅ Look for **errors** in Celery worker logs: `docker-compose logs celery_worker`

### **No Reminders Being Sent?**
1. ✅ Verify there are **events 7 days in the future**
2. ✅ Check **players have email addresses** and are **active**
3. ✅ Look at **reminder logs** for error messages
4. ✅ Test manually: `python manage.py send_auto_reminders --dry-run`

### **Want to Test Immediately?**
```bash
# Test what would happen
python manage.py send_auto_reminders --type=1_week --dry-run

# Send reminders now
python manage.py send_auto_reminders --type=1_week
```

---

## 🎉 Benefits of Admin Management

✅ **No Code Changes Required** - Modify schedules without redeploying  
✅ **Real-time Control** - Enable/disable reminders instantly  
✅ **Multiple Schedules** - Run same reminder type at different times  
✅ **Visual Interface** - Easy to understand and manage  
✅ **Execution History** - Track when tasks run and if they succeed  
✅ **Flexible Timing** - Use cron expressions for complex schedules  

You now have complete control over your automatic reminders through a user-friendly web interface! 🚀
