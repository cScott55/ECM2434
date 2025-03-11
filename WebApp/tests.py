from django.test import TestCase, Client
from django.urls import reverse
from django.utils.timezone import now, localtime
from .models import *
from .forms import *
from datetime import timedelta

# TESTS FOR models.py:
class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(username='testuser', password='testpass123', user_type='player')
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.user_type, 'player')

    def test_create_superuser(self):
        admin_user = User.objects.create_superuser(username='admin', password='adminpass123')
        self.assertEqual(admin_user.username, 'admin')
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_staff)

    def test_user_profile_creation(self):
        user = User.objects.create_user(username='testuser', password='testpass123', user_type='player')
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.user.username, 'testuser')
        self.assertEqual(profile.score, 0)
        self.assertEqual(profile.bio, '')
        self.assertFalse(profile.profile_picture.name)


class UserLoginStreakTest(TestCase):
    # Generate user for test purposes:
    def setUp(self):
        self.user = User.objects.create_user(username='testuser2', password='testpass123', user_type='player')
        self.profile = Profile.objects.get(user=self.user)

    # Streak on account creation must equal 1:
    def test_initial_login_streak(self):
        self.user.last_login_date = None
        self.user.calc_login_streak()
        self.user.refresh_from_db()
        self.assertEqual(self.user.login_streak, 1)

    # Logging in the next day must increment the streak by 1:
    def test_consecutive_day_login_increments_streak(self):
        self.user.last_login_date = localtime(now()).date() - timedelta(days=1)
        current_streak = self.user.login_streak
        self.user.save()
        self.user.calc_login_streak()
        self.user.refresh_from_db()
        self.assertEqual(self.user.login_streak, current_streak + 1)

    # Logging in non-consecutively should reset streak to 1:
    def test_non_consecutive_day_resets_streak(self):
        self.user.last_login_date = localtime(now()).date() - timedelta(days=2)
        self.user.calc_login_streak()
        self.user.refresh_from_db()
        self.assertEqual(self.user.login_streak, 1)

    # Multiple logins per day should not increment streak:
    def test_multiple_logins_dont_increase_streak(self):
        self.user.last_login_date = localtime(now()).date()
        initial_streak = self.user.login_streak
        self.user.refresh_from_db()
        self.assertEqual(self.user.login_streak, initial_streak)

    # Ensure reward given when 7 day login streak achieved:
    def test_reward_given_on_seven_day_streak(self):
        current_score = self.profile.score
        self.user.last_login_date = localtime(now()).date() - timedelta(days=1)
        self.user.login_streak = 6
        self.user.save()
        self.user.calc_login_streak()
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.score, current_score + 100)

    # Ensure correct reward given:
    def test_reward_user_adds_score(self):
        current_score = self.profile.score
        self.user.reward_user()
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.score, current_score + 100) # PLACEHOLDER REWARD: CHANGE IF REWARD GIVEN CHANGES.

    # Ensure rewarding user resets streak to 0:
    def test_reward_user_resets_streak(self):
        self.user.login_streak = 7
        self.user.reward_user()
        self.user.refresh_from_db()
        self.assertEqual(self.user.login_streak, 0)

# TESTS FOR forms.py:
class UserRegistrationFormTest(TestCase):
    def test_form_labels(self):
        form = UserRegistrationForm()
        self.assertEqual(form.fields['username'].label, 'Username')
        self.assertEqual(form.fields['email'].label, 'Email Address')
        self.assertEqual(form.fields['password1'].label, 'Password')
        self.assertEqual(form.fields['password2'].label, 'Confirm Password')
        self.assertEqual(form.fields['user_type'].label, 'Select user type')

    def test_form_help_text(self):
        form = UserRegistrationForm()
        self.assertEqual(form.fields['username'].help_text, '')
        self.assertEqual(form.fields['email'].help_text, '')
        self.assertEqual(form.fields['password2'].help_text, '')
        self.assertEqual(form.fields['user_type'].help_text, 'DEV SETTING - REMOVE FROM OFFICIAL RELEASE.')

    def test_form_valid_data(self):
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'user_type': 'player'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_data(self):
        form_data = {
            'username': '',
            'email': 'invalid-email',
            'password1': 'testpass123',
            'password2': 'mismatch',
            'user_type': 'player'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())

class ProfileUpdateFormTest(TestCase):
    def test_form_labels(self):
        form = ProfileUpdateForm()
        self.assertEqual(form.fields['bio'].label, 'Bio')
        self.assertEqual(form.fields['profile_picture'].label, 'Profile Picture')

    def test_form_help_text(self):
        form = ProfileUpdateForm()
        self.assertEqual(form.fields['bio'].help_text, 'Write a short bio about yourself.')
        self.assertEqual(form.fields['profile_picture'].help_text, 'Upload a profile picture.')

    def test_form_valid_data(self):
        user = User.objects.create_user(username='testuser', password='testpass123', user_type='player')
        profile = Profile.objects.get(user=user)
        form_data = {
            'bio': 'This is a test bio.',
            'profile_picture': None
        }
        form = ProfileUpdateForm(data=form_data, instance=profile)
        self.assertTrue(form.is_valid())

# TESTS FOR views.py:
class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123', user_type='player')
        self.profile = Profile.objects.get(user=self.user)

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'WebApp/home.html')

    def test_about_view(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'WebApp/about.html')

    def test_game_view_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('game'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'WebApp/game.html')

    def test_game_view_unauthenticated(self):
        response = self.client.get(reverse('game'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('game')}")

    def test_missions_view_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('missions'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'WebApp/missions.html')

    def test_missions_view_unauthenticated(self):
        response = self.client.get(reverse('missions'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('missions')}")

    def test_register_view(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'WebApp/register.html')

    def test_login_view(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'WebApp/login.html')

    def test_logout_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))

    def test_profile_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('profile', args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'WebApp/profile.html')

    def test_profile_update_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('profile_update'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'WebApp/profile_update.html')

