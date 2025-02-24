from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import user_passes_test, login_required
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.forms import AuthenticationForm
from django.core.management import call_command
from .models import User, Profile, Mission, UserMission
from .forms import UserRegistrationForm, ProfileUpdateForm
from .leaderboard_src import generate_leaderboard_image
from .search_src import search_for_username

def home(request):
    return render(request, 'WebApp/home.html')

def about(request):
    return render(request, 'WebApp/about.html')

@login_required
def game(request):
    return render(request, 'WebApp/game.html')

@login_required
def missions(request):
    return render(request, 'WebApp/missions.html')

_NoSearchString = "NONE"
def search(request):
    username = request.GET.get('username', _NoSearchString)
    matches = search_for_username(username)
    context = { 
        "search_name" : username,
        "results" : matches,
        "anyfound" : (len(matches) > 0)
    }
    return render(request, "WebApp/search.html", context)

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')  # Redirect to home page
    else:
        form = UserRegistrationForm()
    return render(request, 'WebApp/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')  # Redirect to home page
    else:
        form = AuthenticationForm()
    return render(request, 'WebApp/login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('login')

def leaderboard(request): 
    if generate_leaderboard_image() is not None:
        # if fine and no error
        return render(request, 'WebApp/leaderboard.html')
    else:
        # if error, say so and redirect back home
        print("LEADERBOARD IMAGE GENERATION ERROR")
        return redirect('home')

@login_required
def profile(request, username=None):
    # No username provided; redirect to profile of user:
    if not username:
        if request.user.is_authenticated:
            return redirect('profile', username=request.user.username)
        else:
            # Redirect to login if the user is not authenticated:
            return redirect('login') 
        
    # Get data for provided username to display correct profile:
    user = get_object_or_404(User, username=username)
    user_profile = get_object_or_404(Profile, user=user)
    return render(request, 'WebApp/profile.html', {'profile': user_profile})

@login_required
def profile_update(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('profile', username=request.user.username)
    else:
        form = ProfileUpdateForm(instance=request.user.profile)
    return render(request, 'WebApp/profile_update.html', {'form': form})

def redirect_to_profile(request):
    if request.user.is_authenticated:
        return redirect('profile', username=request.user.username)
    else:
        # redirect to login if not logged in - no profile to show:
        return redirect('login')

# For missions:
@login_required
def missions(request):
    # Check if missions exist; if not, generate them:
    if not Mission.objects.exists():
        call_command('generate_missions')  # Run the generate_missions.py script (in WebApp/management/commands/)

    if request.method == "POST":
        mission_id = request.POST.get("mission_id")
        mission = Mission.objects.get(id=mission_id)
        today = timezone.now().date()

        # Get UserMission instance:
        user_mission, created = UserMission.objects.get_or_create(
            user=request.user,
            mission=mission,
            date_completed=today
        )

        # Toggle completion status:
        user_mission.completed = not user_mission.completed
        user_mission.save()

        # Award (and deduct, debug option) points:
        profile = request.user.profile
        if user_mission.completed:
            profile.score += mission.points
        else:
            profile.score -= mission.points
        profile.save()

        # JSON response:
        return JsonResponse({
            "status": "success",
            "completed": user_mission.completed
        })

    # Handle GET request (display missions):
    today = timezone.now().date()
    missions = Mission.objects.all()
    user_missions = UserMission.objects.filter(user=request.user, date_completed=today)

    # Create UserMission objects for any unstarted missions:
    for mission in missions:
        UserMission.objects.get_or_create(user=request.user, mission=mission, date_completed=today)

    context = {
        'missions': missions,
        'user_missions': user_missions,
    }
    return render(request, 'WebApp/missions.html', context)

def is_developer(user):
    return user.user_type == 'developer'

@user_passes_test(is_developer)
def developer_dashboard(request):
    return render(request, 'accounts/developer_dashboard.html')