from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta, date

class Departments(models.Model):
    name = models.CharField(max_length=128, blank=False, null=False)

    def __str__(self):
        return self.name


class Amenities(models.Model):
    class Facility(models.TextChoices):
        desk = 'Desk'
        room = 'Room'

    name = models.CharField(max_length=128, blank=False, null=False)
    facility = models.CharField(max_length=4, choices=Facility.choices, blank=False, null=False)

    def __str__(self):
        return self.name


class Floors(models.Model):
    name = models.CharField(max_length=128, blank=False, null=False)
    
    def __str__(self):
        return self.name


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True, blank=False, null=False)
    first_name = models.CharField(max_length=128, blank=False, null=False)
    last_name = models.CharField(max_length=128, blank=False, null=False)
    department = models.ForeignKey(Departments, blank=False, null=False, on_delete=models.CASCADE)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []


class Desks(models.Model):
    name = models.CharField(max_length=128, blank=False, null=False)
    floor = models.ForeignKey(Floors, on_delete=models.CASCADE)
    amenities = models.ManyToManyField(Amenities)

    def serialize(self, request, booked):
        booked = booked.filter(desk_id=self.id).values('user', 'date')

        for booking in booked:
            # Check if the desk is booked by logged in user
            booking['my_booking'] = booking['user'] == request.user.id
            # Check if the desk is booked by teammate
            booking['teammate'] = list(User.objects.filter(pk=booking['user']).values_list('department_id', flat=True))[0] == request.user.department_id
            # Add department
            department_id = list(User.objects.filter(pk=booking['user']).values_list('department', flat=True))[0]
            booking['department'] = list(Departments.objects.filter(pk=department_id).values_list('name', flat=True))[0]

        return {
            "id": self.id,
            "name": self.name,
            "floor": self.floor.name,
            "amenities": [amenity.name for amenity in self.amenities.all()],
            "booked": [booked for booked in booked]
        }


class DeskBookings(models.Model):
    user = models.ForeignKey(User, blank=False, null=False, on_delete=models.CASCADE)
    desk = models.ForeignKey(Desks, blank=False, null=False, on_delete=models.CASCADE)
    date = models.DateField(blank=False, null=False)
    checked_in = models.DateTimeField(blank=True, null=True)
    checked_out = models.DateTimeField(blank=True, null=True)

    def serialize(self):
        return {
            "id": self.id,
            "name": self.desk.name,
            "floor": self.desk.floor.name,
            "amenities": [amenity.name for amenity in self.desk.amenities.all()],
            "date": self.date,
            "checked_in": self.checked_in,
            "checked_out": self.checked_out,
            # Validate if check-in is open
            "check_in": self.date == date.today()
        }


class Rooms(models.Model):
    name = models.CharField(max_length=128, blank=False, null=False)
    floor = models.ForeignKey(Floors, on_delete=models.CASCADE)
    capacity = models.IntegerField(blank=False, null=False)
    amenities = models.ManyToManyField(Amenities)

    def serialize(self, request, booked, selected_date, duration):
        booked = booked.filter(room_id=self.id).values('user', 'start', 'end').order_by('start')

        # Set office working hours for selected date
        office_hours = [
            datetime(selected_date.year, selected_date.month, selected_date.day, 7, 00, tzinfo=timezone.utc),
            datetime(selected_date.year, selected_date.month, selected_date.day, 20, 00, tzinfo=timezone.utc)
        ]
        
        # Set selected duration
        interval = timedelta(minutes=duration)

        # Get available slots and split by interval
        available_slots = []

        booked_time = [list(time) for time in list(booked.values_list('start', 'end'))]

        available_slots_by_interval = []
        def split_slots(slot):
            period_start2 = slot[0]
            while period_start2 < slot[1]:
                period_end2 = min(period_start2 + interval, slot[1])
                if interval <= period_end2 - period_start2:
                    available_slots_by_interval.append((period_start2, period_end2))
                period_start2 = period_end2 + timedelta(minutes=5) # Add 5 minutes between bookings
        
        if len(booked_time) > 0:
            available_slots.append([office_hours[0], booked_time[0][0]])
            
            index = 0
            for i in booked_time:
                if len(booked_time) > index + 1:
                    available_slots.append([booked_time[index][1], booked_time[index+1][0]])

                index += 1

            available_slots.append([booked_time[len(booked_time)-1][1], office_hours[1]])

            for available_slot in available_slots:
                split_slots(available_slot)
        else:
            split_slots(office_hours)

        available_slots_formatted = [[start, end] for start, end in available_slots_by_interval]

        # Check if the desk is booked by logged in user
        for booking in booked:
            booking['my_booking'] = booking['user'] == request.user.id

        return {
            "id": self.id,
            "name": self.name,
            "floor": self.floor.name,
            "capacity": self.capacity,
            "amenities": [amenity.name for amenity in self.amenities.all()],
            "available_slots": available_slots_formatted,
        }


class RoomBookings(models.Model):
    user = models.ForeignKey(User, blank=False, null=False, on_delete=models.CASCADE)
    room = models.ForeignKey(Rooms, blank=False, null=False, on_delete=models.CASCADE)
    start = models.DateTimeField(blank=False, null=False)
    end = models.DateTimeField(blank=False, null=False)
    checked_in = models.DateTimeField(blank=True, null=True)
    checked_out = models.DateTimeField(blank=True, null=True)

    def serialize(self):
        today = date.today()

        return {
            "id": self.id,
            "name": self.room.name,
            "floor": self.room.floor.name,
            "amenities": [amenity.name for amenity in self.room.amenities.all()],
            "user": self.user.get_full_name(),
            "start": self.start,
            "end": self.end,
            "checked_in": self.checked_in,
            "checked_out": self.checked_out,
            # Validate if check-in is open
            "check_in": datetime(today.year, today.month, today.day + 1, tzinfo=timezone.utc) > self.start >= datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
        }

