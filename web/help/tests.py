from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import BugReport

User = get_user_model()


class BugReportModelTest(TestCase):
    """Test the BugReport model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='staffpass123',
            is_staff=True
        )
    
    def test_bug_report_creation(self):
        """Test creating a bug report."""
        bug_report = BugReport.objects.create(
            title="Test Bug",
            description="This is a test bug",
            reported_by=self.user
        )
        
        self.assertEqual(bug_report.title, "Test Bug")
        self.assertEqual(bug_report.status, 'open')
        self.assertEqual(bug_report.priority, 'medium')
        self.assertTrue(bug_report.is_open)
        self.assertEqual(str(bug_report), f"#{bug_report.id} - Test Bug")
    
    def test_bug_report_mark_resolved(self):
        """Test marking a bug report as resolved."""
        bug_report = BugReport.objects.create(
            title="Test Bug",
            description="This is a test bug",
            reported_by=self.user
        )
        
        bug_report.mark_resolved(self.staff_user)
        
        self.assertEqual(bug_report.status, 'resolved')
        self.assertEqual(bug_report.resolved_by, self.staff_user)
        self.assertIsNotNone(bug_report.resolved_at)
        self.assertFalse(bug_report.is_open)
    
    def test_bug_report_mark_closed(self):
        """Test marking a bug report as closed."""
        bug_report = BugReport.objects.create(
            title="Test Bug",
            description="This is a test bug",
            reported_by=self.user
        )
        
        bug_report.mark_closed(self.staff_user)
        
        self.assertEqual(bug_report.status, 'closed')
        self.assertEqual(bug_report.resolved_by, self.staff_user)
        self.assertIsNotNone(bug_report.resolved_at)
        self.assertFalse(bug_report.is_open)


class BugReportViewTest(TestCase):
    """Test the bug report views."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='staffpass123',
            is_staff=True
        )
        
        self.bug_report = BugReport.objects.create(
            title="Test Bug",
            description="This is a test bug",
            reported_by=self.user
        )
    
    def test_help_index_view(self):
        """Test the help index view."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('help:index'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hulp & Ondersteuning')
        self.assertContains(response, 'Bug Rapporteren')
    
    def test_bug_report_create_view(self):
        """Test creating a bug report via the view."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(reverse('help:bug_report'), {
            'title': 'New Test Bug',
            'description': 'This is a new test bug',
            'browser_info': 'Chrome 91'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect after successful submission
        
        bug_report = BugReport.objects.get(title='New Test Bug')
        self.assertEqual(bug_report.reported_by, self.user)
        self.assertEqual(bug_report.browser_info, 'Chrome 91')
    
    def test_bug_detail_view_user_access(self):
        """Test that users can view their own bug reports."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('help:bug_detail', kwargs={'pk': self.bug_report.pk}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.bug_report.title)
    
    def test_bug_detail_view_user_cannot_access_others(self):
        """Test that users cannot view other users' bug reports."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        self.client.login(username='otheruser', password='otherpass123')
        response = self.client.get(reverse('help:bug_detail', kwargs={'pk': self.bug_report.pk}))
        
        self.assertEqual(response.status_code, 404)
    
    def test_my_bug_reports_view(self):
        """Test the user's bug reports list view."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('help:my_bug_reports'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.bug_report.title)
    
    def test_admin_bug_list_view_requires_staff(self):
        """Test that admin bug list requires staff privileges."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('help:admin_bug_list'))
        
        self.assertEqual(response.status_code, 302)  # Redirect to login or permission denied
    
    def test_admin_bug_list_view_staff_access(self):
        """Test that staff can access admin bug list."""
        self.client.login(username='staffuser', password='staffpass123')
        response = self.client.get(reverse('help:admin_bug_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bug Rapporten Beheer')
        self.assertContains(response, self.bug_report.title)
    
    def test_admin_bug_detail_view_staff_access(self):
        """Test that staff can access admin bug detail."""
        self.client.login(username='staffuser', password='staffpass123')
        response = self.client.get(reverse('help:admin_bug_detail', kwargs={'pk': self.bug_report.pk}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.bug_report.title)
        self.assertContains(response, 'Beheer Instellingen')
    
    def test_admin_bug_mark_resolved(self):
        """Test marking a bug as resolved via admin action."""
        self.client.login(username='staffuser', password='staffpass123')
        response = self.client.post(reverse('help:admin_bug_mark_resolved', kwargs={'pk': self.bug_report.pk}))
        
        self.assertEqual(response.status_code, 302)  # Redirect after action
        
        self.bug_report.refresh_from_db()
        self.assertEqual(self.bug_report.status, 'resolved')
        self.assertEqual(self.bug_report.resolved_by, self.staff_user)
    
    def test_admin_bug_mark_closed(self):
        """Test marking a bug as closed via admin action."""
        self.client.login(username='staffuser', password='staffpass123')
        response = self.client.post(reverse('help:admin_bug_mark_closed', kwargs={'pk': self.bug_report.pk}))
        
        self.assertEqual(response.status_code, 302)  # Redirect after action
        
        self.bug_report.refresh_from_db()
        self.assertEqual(self.bug_report.status, 'closed')
        self.assertEqual(self.bug_report.resolved_by, self.staff_user)
    
    def test_help_index_shows_admin_section_for_staff(self):
        """Test that staff users see admin functions on help index."""
        self.client.login(username='staffuser', password='staffpass123')
        response = self.client.get(reverse('help:index'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Beheerder Functies')
        self.assertContains(response, 'Bug Rapporten Beheren')
    
    def test_help_index_hides_admin_section_for_regular_users(self):
        """Test that regular users don't see admin functions on help index."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('help:index'))
        
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Beheerder Functies')
        self.assertNotContains(response, 'Bug Rapporten Beheren')
