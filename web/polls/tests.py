from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import json

from .models import Poll, PollOption, Vote

User = get_user_model()


class PollModelTestCase(TestCase):
    """Test poll model functionality"""
    
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='staffpass123',
            is_staff=True,
            is_active=True
        )
        self.active_player = User.objects.create_user(
            username='player1',
            email='player1@example.com',
            password='playerpass123',
            is_active=True
        )
        self.inactive_player = User.objects.create_user(
            username='player2',
            email='player2@example.com',
            password='playerpass123',
            is_active=False
        )
    
    def test_poll_creation(self):
        """Test basic poll creation"""
        poll = Poll.objects.create(
            title='Test Poll',
            description='Test description',
            created_by=self.staff_user,
            allow_multiple_choices=False
        )
        
        self.assertEqual(poll.title, 'Test Poll')
        self.assertEqual(poll.created_by, self.staff_user)
        self.assertTrue(poll.is_active)
        self.assertTrue(poll.is_open)
        self.assertEqual(poll.total_votes, 0)
        self.assertEqual(poll.unique_voters, 0)
    
    def test_poll_with_end_date(self):
        """Test poll with automatic end date"""
        future_date = timezone.now() + timedelta(days=1)
        past_date = timezone.now() - timedelta(days=1)
        
        # Future end date - should be open
        future_poll = Poll.objects.create(
            title='Future Poll',
            created_by=self.staff_user,
            end_date=future_date
        )
        self.assertTrue(future_poll.is_open)
        
        # Past end date - should be closed
        past_poll = Poll.objects.create(
            title='Past Poll',
            created_by=self.staff_user,
            end_date=past_date
        )
        self.assertFalse(past_poll.is_open)
    
    def test_poll_options(self):
        """Test poll options creation and ordering"""
        poll = Poll.objects.create(
            title='Options Test',
            created_by=self.staff_user
        )
        
        option1 = PollOption.objects.create(
            poll=poll,
            text='Option 1',
            order=1
        )
        option2 = PollOption.objects.create(
            poll=poll,
            text='Option 2',
            order=0
        )
        
        # Test ordering
        options = list(poll.options.all())
        self.assertEqual(options[0], option2)  # order=0 comes first
        self.assertEqual(options[1], option1)  # order=1 comes second
    
    def test_voting_single_choice(self):
        """Test single choice voting"""
        poll = Poll.objects.create(
            title='Single Choice Poll',
            created_by=self.staff_user,
            allow_multiple_choices=False
        )
        
        option1 = PollOption.objects.create(poll=poll, text='Option 1', order=0)
        option2 = PollOption.objects.create(poll=poll, text='Option 2', order=1)
        
        # Vote for option 1
        Vote.objects.create(user=self.active_player, poll_option=option1)
        
        self.assertEqual(poll.total_votes, 1)
        self.assertEqual(poll.unique_voters, 1)
        self.assertEqual(option1.vote_count, 1)
        self.assertEqual(option2.vote_count, 0)
    
    def test_voting_multiple_choice(self):
        """Test multiple choice voting"""
        poll = Poll.objects.create(
            title='Multiple Choice Poll',
            created_by=self.staff_user,
            allow_multiple_choices=True
        )
        
        option1 = PollOption.objects.create(poll=poll, text='Option 1', order=0)
        option2 = PollOption.objects.create(poll=poll, text='Option 2', order=1)
        
        # Vote for both options
        Vote.objects.create(user=self.active_player, poll_option=option1)
        Vote.objects.create(user=self.active_player, poll_option=option2)
        
        self.assertEqual(poll.total_votes, 2)
        self.assertEqual(poll.unique_voters, 1)
        self.assertEqual(option1.vote_count, 1)
        self.assertEqual(option2.vote_count, 1)
    
    def test_poll_closing(self):
        """Test manual poll closing"""
        poll = Poll.objects.create(
            title='Closable Poll',
            created_by=self.staff_user
        )
        
        self.assertTrue(poll.is_open)
        
        poll.close_poll(user=self.staff_user)
        
        self.assertFalse(poll.is_open)
        self.assertFalse(poll.is_active)
        self.assertIsNotNone(poll.closed_at)
        self.assertEqual(poll.closed_by, self.staff_user)


class PollViewTestCase(TestCase):
    """Test poll views and functionality"""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='staffpass123',
            is_staff=True,
            is_active=True
        )
        self.active_player = User.objects.create_user(
            username='player1',
            email='player1@example.com',
            password='playerpass123',
            is_active=True
        )
        
        # Create a test poll
        self.poll = Poll.objects.create(
            title='Test Poll',
            description='Test description',
            created_by=self.staff_user
        )
        self.option1 = PollOption.objects.create(
            poll=self.poll,
            text='Option 1',
            order=0
        )
        self.option2 = PollOption.objects.create(
            poll=self.poll,
            text='Option 2',
            order=1
        )
    
    def test_poll_list_view(self):
        """Test poll list view is accessible"""
        self.client.force_login(self.active_player)
        response = self.client.get(reverse('polls:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.poll.title)
    
    def test_poll_detail_view(self):
        """Test poll detail view shows poll information"""
        self.client.force_login(self.active_player)
        response = self.client.get(reverse('polls:detail', args=[self.poll.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.poll.title)
        self.assertContains(response, self.option1.text)
        self.assertContains(response, self.option2.text)
    
    def test_staff_can_create_poll(self):
        """Test staff users can access poll creation"""
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('polls:create'))
        self.assertEqual(response.status_code, 200)
    
    def test_regular_user_cannot_create_poll(self):
        """Test regular users cannot create polls"""
        self.client.force_login(self.active_player)
        response = self.client.get(reverse('polls:create'))
        self.assertEqual(response.status_code, 302)  # Redirected (permission denied)
    
    def test_voting_functionality(self):
        """Test voting via AJAX endpoint"""
        self.client.force_login(self.active_player)
        
        # Test valid vote
        response = self.client.post(
            reverse('polls:vote', args=[self.poll.pk]),
            data=json.dumps({'option_ids': [self.option1.id]}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Verify vote was recorded
        vote = Vote.objects.get(user=self.active_player, poll_option=self.option1)
        self.assertIsNotNone(vote)
    
    def test_dashboard_shows_active_polls(self):
        """Test active polls appear on dashboard"""
        self.client.force_login(self.active_player)
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        # Check if poll context is available
        self.assertIn('active_polls', response.context)


class PollPermissionTestCase(TestCase):
    """Test poll permissions and restrictions"""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='staffpass123',
            is_staff=True,
            is_active=True
        )
        self.active_player = User.objects.create_user(
            username='player1',
            email='player1@example.com',
            password='playerpass123',
            is_active=True
        )
        self.inactive_player = User.objects.create_user(
            username='player2',
            email='player2@example.com',
            password='playerpass123',
            is_active=False
        )
        
        self.poll = Poll.objects.create(
            title='Permission Test Poll',
            created_by=self.staff_user
        )
        self.option = PollOption.objects.create(
            poll=self.poll,
            text='Test Option',
            order=0
        )
    
    def test_inactive_user_cannot_vote(self):
        """Test inactive users cannot vote"""
        self.client.force_login(self.inactive_player)
        
        response = self.client.post(
            reverse('polls:vote', args=[self.poll.pk]),
            data=json.dumps({'option_ids': [self.option.id]}),
            content_type='application/json'
        )
        
        # Inactive user should be redirected due to middleware or get 403
        self.assertIn(response.status_code, [302, 403])
        if response.status_code == 200:
            data = response.json()
            self.assertFalse(data['success'])
    
    def test_cannot_vote_on_closed_poll(self):
        """Test voting is not allowed on closed polls"""
        self.poll.close_poll()
        self.client.force_login(self.active_player)
        
        response = self.client.post(
            reverse('polls:vote', args=[self.poll.pk]),
            data=json.dumps({'option_ids': [self.option.id]}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
    
    def test_only_staff_can_close_polls(self):
        """Test only staff can close polls"""
        # Regular user cannot close poll
        self.client.force_login(self.active_player)
        response = self.client.post(reverse('polls:close', args=[self.poll.pk]))
        self.assertEqual(response.status_code, 302)  # Redirected (no permission)
        
        # Staff user can close poll
        self.client.force_login(self.staff_user)
        response = self.client.post(reverse('polls:close', args=[self.poll.pk]))
        self.assertEqual(response.status_code, 302)  # Redirected to poll detail
        
        # Verify poll is closed
        self.poll.refresh_from_db()
        self.assertFalse(self.poll.is_open)
