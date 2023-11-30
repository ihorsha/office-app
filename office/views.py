import json

from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, date
from django.utils import timezone
from django.db.models import Count, Q

from .models import Amenities, Floors, User, Departments, Desks, DeskBookings, Rooms, RoomBookings


class LoginUserForm(forms.ModelForm):
    email = forms.CharField(
        widget=forms.EmailInput(attrs={"autofocus": True, "class": "form-control", "placeholder": "Email (e.g. name@example.com)"})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"})
    )

    class Meta:
        model = User
        fields = ["email", "password1"]
    
        
class RegisterUserForm(UserCreationForm):
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={"autofocus": True, "class": "form-control", "placeholder": "First Name"})
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Last Name"})
    )
    department = forms.ModelChoiceField(
        widget=forms.Select(attrs={"class": "form-control"}),
        queryset=Departments.objects.all(), empty_label="Select department..."
    )
    email = forms.CharField(
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email (e.g. name@example.com)"})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"})
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "department", "email", "password1"]

    def __init__(self, *args, **kwargs):
        super(RegisterUserForm, self).__init__(*args, **kwargs)
        del self.fields['password2']
        self.fields['password1'].help_text = None


class UpdateProfileForm(forms.ModelForm):
    department = forms.ModelChoiceField(
        widget=forms.Select(attrs={"class": "form-control"}),
        queryset=Departments.objects.all(), empty_label="Select department..."
    )

    class Meta:
        model = User
        fields = ["department"]


def index_view(request):
    title = "Today"

    if request.user.is_authenticated:
        return render(request, "office/index.html", {
            "title": title
        })
    else:
        return HttpResponseRedirect(reverse("login"))


def desks_view(request):
    title = "Book a desk"
    amenities = Amenities.objects.filter(facility="desk")
    floors = Floors.objects.all()
    
    if request.user.is_authenticated:
        return render(request, "office/desks.html", {
            "title": title,
            "amenities": amenities,
            "floors": floors,
        })
    else:
        return HttpResponseRedirect(reverse("login"))


@csrf_exempt
@login_required
def api_desks(request):
    # Get available desks for today
    if request.method == 'GET':
        # Normalize amenities
        amenities = request.GET['amenities']
        if amenities: amenities_array = [int(amenity) for amenity in amenities.split(',')]
        else: amenities_array = []

        # Normalize floors
        floors = request.GET['floors']
        if floors: floors_array = [int(floor) for floor in floors.split(',')]
        else: floors_array = [id for id in list(Floors.objects.all().values_list('pk', flat=True))]

        # Query
        desks = Desks.objects.filter(
                    amenities__in=amenities_array,
                    floor__in=floors_array
                ).distinct()
        booked = DeskBookings.objects.filter(date=date.today(), checked_out__isnull=True)

        # Normalize result
        desks_normalized = [desk.serialize(request, booked) for desk in desks]
        
        # Get capacity
        available_capacity = len([value for desk in desks_normalized for key, value in desk.items() if key == 'booked' and len(value) == 0])
        total_capacity = len(desks_normalized)

        return JsonResponse({
            "desks": desks_normalized,
            "capacity": {
                "available": available_capacity,
                "occupied": total_capacity - available_capacity
            }
        }, safe=False)

    # Book a desk
    if request.method == 'POST':
        body = json.loads(request.body)
        desk_id = body['desk_id']

        # Normalize amenities
        amenities = body['amenities']
        if amenities: amenities_array = [int(amenity) for amenity in amenities]
        else: amenities_array = []

        # Normalize floors
        floors = body['floors']
        if floors: floors_array = [int(floor) for floor in floors]
        else: floors_array = [id for id in list(Floors.objects.all().values_list('pk', flat=True))]

        # Query
        desks = Desks.objects.filter(
                    amenities__in=amenities_array,
                    floor__in=floors_array
                ).distinct()
        booked = DeskBookings.objects.filter(date=date.today(), checked_out__isnull=True)

        # Check if selected desk is already booked by another user
        booked_by_someone = DeskBookings.objects.filter(
                                desk_id=desk_id,
                                date=date.today(),
                                checked_out__isnull=True
                            ).exclude(user=request.user)
        if booked_by_someone:
            return JsonResponse({"errors": "Selected desk is already booked."}, safe=False)

        # Else proceed with booking for logged in user
        try:
            desk = DeskBookings.objects.get(user=request.user, date=date.today(), checked_out__isnull=True)
            
            # Check if desk is already checked in
            if desk.checked_in:
                return JsonResponse({"errors": "Can't change already checked-in desk. Free up the desk first."}, safe=False)
            # Cancel previosly booked desk (without changing to another one)
            elif desk.desk_id == desk_id:
                desk.delete()
            # Change previosly booked desk
            else:
                desk.desk_id = desk_id
                desk.save()
        except DeskBookings.DoesNotExist:
            # Book if no desk booked
            DeskBookings(user=request.user, desk_id=desk_id, date=date.today()).save()

        # Normalize result
        desks_normalized = [desk.serialize(request, booked) for desk in desks]
        
        # Get capacity
        available_capacity = len([value for desk in desks_normalized for key, value in desk.items() if key == 'booked' and len(value) == 0])
        total_capacity = len(desks_normalized)

        return JsonResponse({
            "desks": desks_normalized,
            "capacity": {
                "available": available_capacity,
                "occupied": total_capacity - available_capacity
            }
        }, safe=False)


@csrf_exempt
@login_required
def api_desks_schedule(request):
    # Get date available to book
    if request.method == 'GET':
        # Normalize amenities
        amenities = request.GET['amenities']
        if amenities: amenities_array = [int(amenity) for amenity in amenities.split(',')]
        else: amenities_array = []

        # Normalize floors
        floors = request.GET['floors']
        if floors: floors_array = [int(floor) for floor in floors.split(',')]
        else: floors_array = [id for id in list(Floors.objects.all().values_list('pk', flat=True))]

        # Query
        desks = Desks.objects.filter(
                    amenities__in=amenities_array,
                    floor__in=floors_array
                ).distinct()
        booked = DeskBookings.objects.filter(
                    desk__in=[id for id in list(desks.values_list('pk', flat=True))],
                    checked_out__isnull=True
                ).values('date').annotate(count=Count('date')).order_by()

        # Get all active bookings for logged in user
        my_active_bookings = DeskBookings.objects.filter(
                    user=request.user,
                    checked_out__isnull=True
                )

        # Normalize result
        my_active_bookings_normalized = [my_active_booking.serialize() for my_active_booking in my_active_bookings]

        # Get capacity
        occupied = list(booked)
        total_capacity = len(desks)

        return JsonResponse({
            "my_active_bookings": list(my_active_bookings_normalized),
            "capacity": {
                "total_capacity": total_capacity,
                "occupied": occupied
            }
        }, safe=False)

    # Book a desk
    if request.method == 'POST':
        body = json.loads(request.body)
        selected_date = body['date']

        # Normalize amenities
        amenities = body['amenities']
        if amenities: amenities_array = [int(amenity) for amenity in amenities]
        else: amenities_array = []

        # Normalize floors
        floors = body['floors']
        if floors: floors_array = [int(floor) for floor in floors]
        else: floors_array = [id for id in list(Floors.objects.all().values_list('pk', flat=True))]

        # Query
        desks = Desks.objects.filter(
                    amenities__in=amenities_array,
                    floor__in=floors_array
                ).distinct()
        booked = DeskBookings.objects.filter(
                    desk__in=[id for id in list(desks.values_list('pk', flat=True))],
                    date=selected_date,
                    checked_out__isnull=True
                )

        if len(booked) > 0:
            available_desks = desks.exclude(pk__in=[id for id in list(booked.values_list('desk_id', flat=True))])
            user_desk = booked.filter(user=request.user)
        else:
            available_desks = desks.all()

        # Check if no desks available for selected date
        if not available_desks and not user_desk:
            return JsonResponse({"errors": "No desks available for this day."}, safe=False)
        # Check if the selected date in the past or equals today
        if datetime.strptime(selected_date, '%Y-%m-%d').date() <= date.today():
            return JsonResponse({"errors": "The selected date must be later than today."}, safe=False)

        # Else proceed with booking for logged in user
        try:
            desk = DeskBookings.objects.get(user=request.user, date=selected_date, checked_out__isnull=True)
            
            # Check if desk is already checked in
            if desk.checked_in:
                return JsonResponse({"errors": "Can't cancel already checked-in desk. Free up the desk first."}, safe=False)
            # Cancel previosly booked desk
            elif desk:
                desk.delete()
        except DeskBookings.DoesNotExist:
            # Choose desk
            desk = available_desks[0]
            # Book if no desk booked
            DeskBookings(user=request.user, desk=desk, date=selected_date).save()

        # Get all active bookings for logged in user
        my_active_bookings = DeskBookings.objects.filter(
                    user=request.user,
                    checked_out__isnull=True
                )

        # Normalize result
        my_active_bookings_normalized = [my_active_booking.serialize() for my_active_booking in my_active_bookings]

        # Get capacity
        booked = DeskBookings.objects.filter(
                    desk__in=[id for id in list(desks.values_list('pk', flat=True))],
                    checked_out__isnull=True
                ).values('date').annotate(count=Count('date')).order_by()

        occupied = list(booked)
        total_capacity = len(desks)

        return JsonResponse({
            "my_active_bookings": list(my_active_bookings_normalized),
            "capacity": {
                "total_capacity": total_capacity,
                "occupied": occupied
            }
        }, safe=False)


@csrf_exempt
@login_required
def api_desks_booked(request):
    # Get booked desk
    if request.method == 'GET':
        period = request.GET['period']

        desks = DeskBookings.objects.filter(
                    Q(user=request.user) & 
                    (Q(date=date.today()) if period == 'today' else Q(date__gte=date.today())) &
                    Q(checked_out__isnull=True)
                ).order_by('date')

        if desks:
            return JsonResponse({
                "desks": [desk.serialize() for desk in desks]
            }, safe=False)
            
        return JsonResponse({"errors": "No booked desk for today."}, safe=False)

    # Check in / Check out
    if request.method == 'PUT':
        data = json.loads(request.body)

        try:
            desk = DeskBookings.objects.get(pk=data.get('desk_id'), user=request.user, checked_out__isnull=True)

            if not desk.serialize()['check_in']:
                return JsonResponse({"errors": "Check-in isn't open yet."}, safe=False)
        except DeskBookings.DoesNotExist:
            return JsonResponse({"errors": "No booked desk or no permission to edit."}, safe=False)

        desk.checked_in = timezone.now() if data.get('check_in') else getattr(desk, "checked_in")
        desk.checked_out = timezone.now() if data.get('check_out') else getattr(desk, "checked_out")
        desk.save()

        if data.get('check_out'):
            total_bookings = DeskBookings.objects.filter(
                        Q(user=request.user) & 
                        (Q(date=date.today()) if data.get('period') == 'today' else Q(date__gte=date.today())) &
                        Q(checked_out__isnull=True)
                    ).count()

            return JsonResponse({
                "status": 204,
                "total_bookings": total_bookings,
            }, safe=False)

        return JsonResponse({"status": 204}, safe=False)

    # Release a desk before check-in
    if request.method == 'DELETE':
        data = json.loads(request.body)
        
        try:
            desk = DeskBookings.objects.get(pk=data.get('desk_id'), user=request.user, checked_out__isnull=True)
            desk.delete()
        except DeskBookings.DoesNotExist:
            return JsonResponse({"errors": "No booked desk or no permission to edit."}, status=404)

        total_bookings = DeskBookings.objects.filter(
                        Q(user=request.user) & 
                        (Q(date=date.today()) if data.get('period') == 'today' else Q(date__gte=date.today())) &
                        Q(checked_out__isnull=True)
                    ).count()

        return JsonResponse({
            "status": 204,
            "total_bookings": total_bookings,
        }, safe=False)


def desks_schedule_view(request):
    title = "Book a desk"
    amenities = Amenities.objects.filter(facility="desk")
    floors = Floors.objects.all()
    
    if request.user.is_authenticated:
        return render(request, "office/desks_schedule.html", {
            "title": title,
            "amenities": amenities,
            "floors": floors,
        })
    else:
        return HttpResponseRedirect(reverse("login"))


def desks_bookings_view(request):
    title = "My booked desks"
    
    if request.user.is_authenticated:
        return render(request, "office/desks_bookings.html", {
            "title": title,
        })
    else:
        return HttpResponseRedirect(reverse("login"))


def rooms_view(request):
    title = "Book a room"
    amenities = Amenities.objects.filter(facility="room")
    floors = Floors.objects.all()
    
    if request.user.is_authenticated:
        return render(request, "office/rooms.html", {
            "title": title,
            "amenities": amenities,
            "floors": floors,
        })
    else:
        return HttpResponseRedirect(reverse("login"))


@csrf_exempt
@login_required
def api_rooms(request):
    # Get available rooms to book
    if request.method == 'GET':
        # Normalize date
        selected_date = request.GET['date']
        if selected_date: selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        else: selected_date = date.today()

        # Normalize duration
        duration = request.GET['duration']
        if duration: duration = int(duration)
        else: duration = 25 # 25 minutes by default

        # Normalize room capacity
        room_capacity = request.GET['roomCapacity']
        if room_capacity: room_capacity_array = [int(capacity) for capacity in room_capacity.split(',')]
        else: room_capacity_array = [id for id in list(Rooms.objects.all().values_list('capacity', flat=True))]

        # Normalize amenities
        amenities = request.GET['amenities']
        if amenities: amenities_array = [int(amenity) for amenity in amenities.split(',')]
        else: amenities_array = []

        # Normalize floors
        floors = request.GET['floors']
        if floors: floors_array = [int(floor) for floor in floors.split(',')]
        else: floors_array = [id for id in list(Floors.objects.all().values_list('pk', flat=True))]

        # Query
        rooms = Rooms.objects.filter(
                    capacity__in=room_capacity_array,
                    amenities__in=amenities_array,
                    floor__in=floors_array
                ).distinct()
        booked = RoomBookings.objects.filter(
                    start__year=selected_date.year,
                    start__month=selected_date.month,
                    start__day=selected_date.day,
                    checked_out__isnull=True
                )

        # Normalize result
        rooms_normalized = [room.serialize(request, booked, selected_date, duration) for room in rooms]

        # Get capacity
        available_capacity = len([value for room in rooms_normalized for key, value in room.items() if key == 'available_slots' and len(value) > 0])
        total_capacity = len(rooms_normalized)

        return JsonResponse({
            "rooms": rooms_normalized,
            "capacity": {
                "available": available_capacity,
                "occupied": total_capacity - available_capacity
            }
        }, safe=False)

    # Book a room
    if request.method == 'POST':
        body = json.loads(request.body)
        room_id = body['roomId']
        start = body['start']
        end = body['end']

        # Check if the selected room and time is already booked (time has intersections)
        booked = RoomBookings.objects.filter(
                    Q(room_id=room_id) & (
                        Q(
                            Q(Q(start=start) | Q(end=end)) |
                            Q(Q(start__lt=start) & Q(end__gt=start)) |
                            Q(Q(start__lt=end) & Q(end__gt=end))
                    )) &
                    Q(checked_out__isnull=True)
                )

        if booked:
            return JsonResponse({"errors": "Selected slot is already booked."}, safe=False)

        # Book if selected room and time is free
        RoomBookings(
            user=request.user,
            room_id=room_id,
            start = start,
            end = end,
        ).save()

        return JsonResponse({"status": 204}, safe=False)
        

@csrf_exempt
@login_required
def api_rooms_booked(request):
    today = date.today()

    # Get booked rooms
    if request.method == 'GET':
        period = request.GET['period']

        rooms = RoomBookings.objects.filter(
                    Q(user=request.user) & 
                    (
                        Q(Q(start__gte=datetime(today.year, today.month, today.day, tzinfo=timezone.utc)) & Q(end__lt=datetime(today.year, today.month, today.day + 1, tzinfo=timezone.utc))) if period == 'today' else 
                        Q(start__gte=datetime(today.year, today.month, today.day, tzinfo=timezone.utc))
                    ) &
                    Q(checked_out__isnull=True)
                ).order_by('start')

        if rooms:
            return JsonResponse({
                "rooms": [room.serialize() for room in rooms]
            }, safe=False)

        return JsonResponse({"errors": "No booked rooms for today."}, safe=False)

    # Check in / Check out
    if request.method == 'PUT':
        data = json.loads(request.body)

        try:
            room = RoomBookings.objects.get(pk=data.get('room_id'), user=request.user, checked_out__isnull=True)
        except RoomBookings.DoesNotExist:
            return JsonResponse({"errors": "No booked rooms or no permission to edit."}, status=404)

        # Check if booking within the day
        if room.serialize()['check_in']:
            room.checked_in = timezone.now() if data.get('check_in') else getattr(room, "checked_in")
            room.checked_out = timezone.now() if data.get('check_out') else getattr(room, "checked_out")
            room.save()

            if data.get('check_out'):
                total_bookings = RoomBookings.objects.filter(
                                    Q(user=request.user) & 
                                    (
                                        Q(Q(start__gte=datetime(today.year, today.month, today.day, tzinfo=timezone.utc)) & Q(end__lt=datetime(today.year, today.month, today.day + 1, tzinfo=timezone.utc))) if data.get('period') == 'today' else 
                                        Q(start__gte=datetime(today.year, today.month, today.day, tzinfo=timezone.utc))
                                    ) &
                                    Q(checked_out__isnull=True)
                                ).count()

                return JsonResponse({
                    "status": 204,
                    "total_bookings": total_bookings,
                }, safe=False)

            return JsonResponse({"status": 204}, safe=False)
            
        return JsonResponse({"errors": "Check-in isn't open yet."}, safe=False)
        
    # Release a desk before check-in
    if request.method == 'DELETE':
        data = json.loads(request.body)
        
        try:
            room = RoomBookings.objects.get(pk=data.get('room_id'), user=request.user, checked_out__isnull=True)
            room.delete()
        except RoomBookings.DoesNotExist:
            return JsonResponse({"errors": "No booked desk or no permission to edit."}, status=404)

        total_bookings = RoomBookings.objects.filter(
                                Q(user=request.user) & 
                                (
                                    Q(Q(start__gte=datetime(today.year, today.month, today.day, tzinfo=timezone.utc)) & Q(end__lt=datetime(today.year, today.month, today.day + 1, tzinfo=timezone.utc))) if data.get('period') == 'today' else 
                                    Q(start__gte=datetime(today.year, today.month, today.day, tzinfo=timezone.utc))
                                ) &
                                Q(checked_out__isnull=True)
                            ).count()

        return JsonResponse({
            "status": 204,
            "total_bookings": total_bookings,
        }, safe=False)
        

def rooms_bookings_view(request):
    title = "My booked rooms"
    
    if request.user.is_authenticated:
        return render(request, "office/rooms_bookings.html", {
            "title": title,
        })
    else:
        return HttpResponseRedirect(reverse("login"))


def profile_view(request):
    title = "My profile"

    if request.user.is_authenticated:
        if request.method == "POST":
            form = UpdateProfileForm(request.POST, instance=get_user(request))

            if form.is_valid():
                form.save()

            else:
                return render(request, "office/profile.html", {
                    "title": title,
                    "form": form
                })
        else:
            form = UpdateProfileForm(instance=get_user(request))
    
        return render(request, "office/profile.html", {
            "title": title,
            "form": form
        })
    else:
        return HttpResponseRedirect(reverse("login"))


def login_view(request):
    form = LoginUserForm()

    if request.method == "POST":
        email = request.POST["email"]
        password1 = request.POST["password1"]
        user = authenticate(request, username=email, password=password1)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            messages.add_message(request, messages.INFO, "Invalid email or password.")

    return render(request, "office/login.html", {
        "form": form,
    })


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register_view(request):
    if request.method == "POST":
        form = RegisterUserForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "office/register.html", {
                "form": form,
            })

    return render(request, "office/register.html", {
        "form": RegisterUserForm(),
    })
