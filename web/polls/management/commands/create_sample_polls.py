from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from polls.models import Poll, PollOption, Vote

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample polls for demonstration purposes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--with-votes',
            action='store_true',
            help='Create sample votes as well',
        )

    def handle(self, *args, **options):
        # Get or create a staff user
        staff_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@svrap8.nl',
                'is_staff': True,
                'is_active': True,
                'first_name': 'Admin',
                'last_name': 'User'
            }
        )
        if created:
            staff_user.set_password('admin123')
            staff_user.save()
            self.stdout.write(f'Created staff user: {staff_user.username}')
        
        # Create sample polls
        polls_data = [
            {
                'title': 'Beste training tijd',
                'description': 'Wanneer zou je het liefst trainen?',
                'allow_multiple_choices': False,
                'options': [
                    'Maandag 19:00-20:30',
                    'Woensdag 19:00-20:30', 
                    'Vrijdag 19:00-20:30',
                    'Zaterdag 10:00-11:30'
                ]
            },
            {
                'title': 'Teamuitje activiteiten',
                'description': 'Welke activiteiten zouden leuk zijn voor het teamuitje? (meerdere keuzes mogelijk)',
                'allow_multiple_choices': True,
                'options': [
                    'Bowlen',
                    'Escape Room',
                    'Paintball',
                    'Barbecue',
                    'Lasergamen',
                    'Go-karten'
                ]
            },
            {
                'title': 'Nieuw team shirt kleur',
                'description': 'Welke kleur zou je graag zien voor het nieuwe team shirt?',
                'allow_multiple_choices': False,
                'end_date': timezone.now() + timedelta(days=7),
                'options': [
                    'Blauw/Wit',
                    'Rood/Zwart',
                    'Groen/Wit',
                    'Oranje/Blauw'
                ]
            }
        ]

        created_polls = []
        for poll_data in polls_data:
            options_data = poll_data.pop('options')
            
            poll, poll_created = Poll.objects.get_or_create(
                title=poll_data['title'],
                defaults={
                    **poll_data,
                    'created_by': staff_user
                }
            )
            
            if poll_created:
                self.stdout.write(f'Created poll: {poll.title}')
                
                # Create options
                for i, option_text in enumerate(options_data):
                    option = PollOption.objects.create(
                        poll=poll,
                        text=option_text,
                        order=i
                    )
                    self.stdout.write(f'  - Created option: {option.text}')
                
                created_polls.append(poll)
            else:
                self.stdout.write(f'Poll already exists: {poll.title}')

        # Create sample votes if requested
        if options['with_votes'] and created_polls:
            self.stdout.write('\nCreating sample votes...')
            
            # Get active players
            active_players = User.objects.filter(is_active=True)[:10]
            
            if not active_players.exists():
                # Create some sample players
                for i in range(5):
                    player = User.objects.create_user(
                        username=f'player{i+1}',
                        email=f'player{i+1}@example.com',
                        password='player123',
                        first_name=f'Speler',
                        last_name=f'{i+1}',
                        is_active=True
                    )
                    active_players = list(active_players) + [player]
                    self.stdout.write(f'Created sample player: {player.username}')
            
            # Add votes to polls
            import random
            for poll in created_polls:
                # Random number of voters (30-80% of players)
                num_voters = random.randint(
                    int(len(active_players) * 0.3),
                    int(len(active_players) * 0.8)
                )
                voters = random.sample(list(active_players), num_voters)
                
                for voter in voters:
                    options = list(poll.options.all())
                    
                    if poll.allow_multiple_choices:
                        # Vote for 1-3 random options
                        num_choices = random.randint(1, min(3, len(options)))
                        chosen_options = random.sample(options, num_choices)
                    else:
                        # Vote for one random option
                        chosen_options = [random.choice(options)]
                    
                    for option in chosen_options:
                        Vote.objects.get_or_create(
                            user=voter,
                            poll_option=option
                        )
                
                self.stdout.write(f'Added {num_voters} votes to poll: {poll.title}')

        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully created sample polls!')
        )