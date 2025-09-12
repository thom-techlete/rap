from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date, datetime, timedelta
from django.utils import timezone
from .models import InvitationCode
from events.models import Event

User = get_user_model()


class AuthenticationTestCase(TestCase):
    """Test user authentication and permissions"""
    
    def setUp(self):
        self.client = Client()
        # Create test users
        self.regular_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='staffpass123',
            first_name='Staff',
            last_name='User',
            is_staff=True
        )
    
    def test_user_login_success(self):
        """Test successful user login"""
        response = self.client.post(reverse('users:login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        # Should redirect after successful login
        self.assertEqual(response.status_code, 302)
    
    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.client.post(reverse('users:login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        # Should remain on login page
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
    
    def test_staff_permission_check(self):
        """Test staff-only areas require staff permissions"""
        # Try to access admin dashboard without login
        response = self.client.get(reverse('users:admin_dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Try with regular user
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('users:admin_dashboard'))
        self.assertEqual(response.status_code, 302)  # Should be forbidden/redirect
        
        # Try with staff user
        self.client.login(username='staffuser', password='staffpass123')
        response = self.client.get(reverse('users:admin_dashboard'))
        self.assertEqual(response.status_code, 200)  # Should succeed


class ProfileTestCase(TestCase):
    """Test user profile functionality"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_profile_view_requires_login(self):
        """Test profile view requires authentication"""
        self.client.logout()
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_profile_edit_view_loads(self):
        """Test profile edit page loads correctly"""
        response = self.client.get(reverse('users:edit_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
    
    def test_profile_edit_save_success(self):
        """Test successful profile update"""
        response = self.client.post(reverse('users:edit_profile'), {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com',
            'telefoonnummer': '0612345678',
            'geboortedatum': '01/01/1990',  # Use dd/mm/yyyy format
            'straat': 'Test Street',
            'huisnummer': '123',
            'postcode': '1234 AB',
            'plaats': 'Test City'
        })
        
        # Should redirect after successful save
        self.assertEqual(response.status_code, 302)
        
        # Verify changes were saved
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.email, 'updated@example.com')
        self.assertEqual(self.user.straat, 'Test Street')


class TeamRosterTestCase(TestCase):
    """Test team roster (user management) functionality"""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='staffpass123',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client.login(username='staffuser', password='staffpass123')
    
    def test_admin_players_list_view(self):
        """Test admin can view player list"""
        response = self.client.get(reverse('users:admin_players'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test User')
    
    def test_admin_player_detail_view(self):
        """Test admin can view individual player details"""
        response = self.client.get(
            reverse('users:admin_player_detail', kwargs={'player_id': self.regular_user.pk})
        )
        self.assertEqual(response.status_code, 200)
        # Check for user info instead of username specifically
        self.assertContains(response, 'Test User')
    
    def test_regular_user_cannot_access_admin_players(self):
        """Test regular users cannot access admin player management"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('users:admin_players'))
        self.assertEqual(response.status_code, 302)  # Should redirect/deny access
    
    def test_invitation_code_creation(self):
        """Test invitation code functionality"""
        invitation = InvitationCode.objects.create(
            code='TEST123',
            description='Test invitation',
            max_uses=5
        )
        
        self.assertTrue(invitation.is_valid()[0])
        self.assertEqual(invitation.used_count, 0)
        
        # Test using the code
        invitation.use_code()
        self.assertEqual(invitation.used_count, 1)


class InvallerTestCase(TestCase):
    """Test invaller (substitute) user functionality"""
    
    def setUp(self):
        self.client = Client()
        # Create invaller invitation code
        self.invaller_invitation = InvitationCode.objects.create(
            code='INVALLER123',
            user_type='invaller',
            description='Test invaller invitation',
        )
        # Create regular player invitation code
        self.player_invitation = InvitationCode.objects.create(
            code='PLAYER123',
            user_type='player',
            description='Test player invitation',
        )
        
    def test_invaller_registration(self):
        """Test invaller registration with invaller invitation code"""
        # Clean up any existing test data
        User.objects.filter(username='testinvaller').delete()
        
        response = self.client.post(reverse('users:register'), {
            'username': 'testinvaller',
            'first_name': 'Test',
            'last_name': 'Invaller',
            'email': 'invaller@example.com',
            'password1': 'testpass123!',
            'password2': 'testpass123!',
            'invitation_code': 'INVALLER123'
        })
        
        # Should redirect after successful registration
        self.assertEqual(response.status_code, 302)
        
        # Check user was created with correct type
        user = User.objects.get(username='testinvaller')
        self.assertEqual(user.user_type, 'invaller')
        self.assertTrue(user.is_invaller)
        self.assertFalse(user.is_player)
        
    def test_player_registration(self):
        """Test regular player registration with player invitation code"""
        # Clean up any existing test data
        User.objects.filter(username='testplayer').delete()
        
        response = self.client.post(reverse('users:register'), {
            'username': 'testplayer',
            'first_name': 'Test',
            'last_name': 'Player',
            'email': 'player@example.com',
            'password1': 'testpass123!',
            'password2': 'testpass123!',
            'invitation_code': 'PLAYER123'
        })
        
        # Should redirect after successful registration
        self.assertEqual(response.status_code, 302)
        
        # Check user was created with correct type
        user = User.objects.get(username='testplayer')
        self.assertEqual(user.user_type, 'player')
        self.assertFalse(user.is_invaller)
        self.assertTrue(user.is_player)
        
    def test_invaller_event_access_restrictions(self):
        """Test that invallers can only access matches"""
        # Create invaller user
        invaller = User.objects.create_user(
            username='testinvaller',
            email='invaller@example.com',
            password='testpass123',
            user_type='invaller',
            is_active=True
        )
        
        # Create events
        match_event = Event.objects.create(
            name='Test Match',
            event_type='wedstrijd',
            date=timezone.now() + timedelta(days=1),
            location='Test Stadium'
        )
        
        training_event = Event.objects.create(
            name='Test Training',
            event_type='training',
            date=timezone.now() + timedelta(days=2),
            location='Training Ground'
        )
        
        # Login as invaller
        self.client.login(username='testinvaller', password='testpass123')
        
        # Should be able to access match
        response = self.client.get(reverse('events:detail', kwargs={'pk': match_event.pk}))
        self.assertEqual(response.status_code, 200)
        
        # Should be redirected when trying to access training
        response = self.client.get(reverse('events:detail', kwargs={'pk': training_event.pk}))
        self.assertEqual(response.status_code, 302)  # Redirect
        
        # Should redirect to invaller matches when accessing main event list
        response = self.client.get(reverse('events:list'))
        self.assertEqual(response.status_code, 302)  # Redirect to invaller matches
        
        # Should be able to access invaller matches page
        response = self.client.get(reverse('events:invaller_matches'))
        self.assertEqual(response.status_code, 200)
        
    def test_regular_player_cannot_access_invaller_matches(self):
        """Test that regular players cannot access invaller matches page"""
        # Create regular player
        player = User.objects.create_user(
            username='testplayer',
            email='player@example.com',
            password='testpass123',
            user_type='player',
            is_active=True
        )
        
        # Login as player
        self.client.login(username='testplayer', password='testpass123')
        
        # Should be redirected when trying to access invaller matches
        response = self.client.get(reverse('events:invaller_matches'))
        self.assertEqual(response.status_code, 302)  # Redirect
