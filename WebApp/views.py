from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import user_passes_test, login_required
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.utils import timezone
from django.contrib.auth.forms import AuthenticationForm
from django.core.management import call_command
from .models import User, Profile, Mission, UserMission
from .forms import UserRegistrationForm, ProfileUpdateForm

from .leaderboard_src import generate_leaderboard_image
from .search_src import search_for_username
from .friendsystem_src import recordFriendRequestResponse, send_friend_request, get_friend_request_list, get_friend_list
from .missions_src import get_user_missions



_IGNORE_PASSWORD_REQS = True
_NoSearchString = "NONE"





# returned by view function in order to not change the page
# active at all
def unchanged(request, *args, **kwargs):
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def acceptReq(request, accepterId, acceptedId, **kwargs):
    recordFriendRequestResponse(accepterId, acceptedId, True)
    return unchanged(request)

def rejectReq(request, rejecterId, rejectedId, **kwargs):
    recordFriendRequestResponse(rejecterId, rejectedId, False)
    return unchanged(request)


def home(request):
    return render(request, 'WebApp/home.html')

def about(request):
    return render(request, 'WebApp/about.html')

@login_required
def game(request):
    username=request.user.username
        
    # Get data for provided username to display correct profile:
    user = get_object_or_404(User, username=username)
    user_profile = get_object_or_404(Profile, user=user)

    friend_list = get_friend_list(user_profile)

    user_missions = get_user_missions(user_profile)

    context = {
        'profile': user_profile,
        'friend_list' : friend_list,
        'user_missions': user_missions
    }
    return render(request, 'WebApp/game.html', context)

@login_required
def missions(request):
    return render(request, 'WebApp/missions.html')

@login_required
def addfriend(request, idVal = None):
    send_friend_request(request.user.id, idVal)
    return unchanged(request);



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
        if form.is_valid() or _IGNORE_PASSWORD_REQS:
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

    friend_request_list = get_friend_request_list(user_profile);
    friend_list = get_friend_list(user_profile)

    context = {
        'profile': user_profile,
        'req_list' : friend_request_list,
        'friend_list' : friend_list
    };

    return render(request, 'WebApp/profile.html', context)

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