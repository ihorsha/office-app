# Office App

Office App is a web application helping employees of the specific company which uses the hybrid workplace model to quickly reserve desks and rooms in the office.

The idea came up to me from the increasing popularity of the hybrid working model giving employees the flexibility to combine remote and office work. The transition of companies to this hybrid approach will require a tool allowing employees to book a desk and rooms for certain days when they are going to work from the office. This tool will help prevent office over-booking by reserving desks and rooms by employees and improve teamwork by displaying desks booked by teammates from the same departments.

This app allows users to manage various office facilities such as desks and rooms. Users can book facilities for today or in advance, check in and out, release bookings, and view a list of available facilities. It includes features to prevent issues like double-booking and displaying outdated information. The app is also mobile-responsive, catering to employees who need to book desks and rooms on the go using their mobile devices.

Office App utilizes Django on the back-end, JavaScript on the front-end, and Bootstrap library making this app **mobile-responsive**.

Check out the [Demo](https://youtu.be/JWX24jR5kTk?feature=shared) on YouTube to see the app in action.

# Features

### Desk booking

User can:

- Find the perfect desk by filtering desks by amenity and floor
- See how many desks are available and occupied as per selected filters
- See desks booked by teammates for today (teammate is a peer from the same department as a user)
- See desks booked by colleagues from other departments for today, and see the department to which colleagues belong to
- Click on the free desk to book it for a whole day. When a user clicks on the same desk again, this booking is canceled. When a user clicks on the desk the app checks the current status of the desk (free/reserved) and shows an error if someone has already booked this desk.
- Book a desk for any date in the future in advance when clicking on the date in the calendar. The web app automatically assigns the first free desk for a specific date.
- See the updated number of available and occupied desks immediately after booking
- Check in on the day when a desk is booked, release the desk on any day before check-in, free up the desk at any time after check-in is made
- See all desks booked in advance

### Room booking

User can:

- Find the perfect room by filtering by the duration of the booking, max room capacity, amenity and floor
- Click on the date in the popup calendar to show rooms and available time intervals for a specific date
- See how many rooms are available and occupied as per selected filters
- See available time intervals for each room based on the duration selected by a user. The application checks all possible intersections of already booked intervals, finds a total period when the room is free, then split it into intervals as per preferred by user duration.
- Click on the available time interval to book a room. Once the room is booked, a user is redirected to the page with all booked rooms.
- Check in on the day when a room is booked, release the room on any day before check-in, free up the room at any time after check-in is made
- See all rooms booked in advance

### View bookings for today

User can:

- See an assigned desk and all rooms booked for today
- Check in on the day of booking, free up after check-in, or release a desk or room before check-in to free up the facility for those who need it most

### Registration

- When registering user must enter first name, last name, and select the department in which he/she works

# What’s contained in each file

### Data

- `/office/fixtures/data.json` contains initial data including all company departments, amenities, number of floors, desks and rooms in the office

### JavaScript

- `/office/static/office/index.js` contains functions to retrieve a list of booked desks and rooms, and manage their status (check-in, check-out or releasing a facility). Functions render booked desk(s) and rooms on the following URLs "/" (index.html), "desks/bookings" (desks_bookings.html) and "rooms/bookings" (rooms_bookings). Depending on the "period" value passed in the functions it can be rendered a desk and rooms booked for today (if the "period" equals "today"), or all desks and rooms booked by the logged-in user (if provided empty "period" value).

- `/office/static/office/desks.js` contains:

(1) a function to render a list of occupied and available for today desks, filter desks by floor and amenities, and reserve or release a selected desk for today

(2) a related function to get initial capacity and update it after the desk is booked by the user

- `/office/static/office/desks_schedule.js` contains:

(1) a function to render a calendar showing how many desks are occupied and available on a specific date, and book a desk on the selected date

(2) related functions to get initial capacity and update it after the desk is booked by user, format date and month and get days for the calendar

- `/office/static/office/rooms.js` contains:

(1) a function to render and book available on the selected date room, and filter rooms by duration, capacity, amenities and floor

(2) related functions to get initial capacity and update it after the room is booked by the user, convert date into Mongo format, and display time when the room is free in a more friendly way

### Third-party JavaScript library

- `/office/static/office/lib/..` folder contains third-party javascript code and stylesheet of "Datepicker" component rendering popup window on the "Book a room" page where user can select the date of booking

### Views

- `/office/views.py` contains:

(1) forms used for user login, registration, and updating user profile

(2) functions ending with "\_view" to render pages associated with each of routes mentioned in `/office/urls.py` (data is retrieved using JavaScript)

(3) functions starting with "api\_" to handle GET, POST, PUT and DELETE requests associated with each of routes mentioned in `/office/urls.py` (requests are sent using JavaScript)

### URLs

- `/config/urls.py` contains an **Admin route** and a route to the URL configuration for the `office` app

- `/office/urls.py` contains the URL configuration for the `office` app

**Employee routes** listed in the `office` app URLs configuration:

`/` shows desks and rooms booked for today

`/desks` shows all desks available and occupied today

`/desks/schedule` shows a calendar to book desks in advance for any date in the future

`/desks/bookings` shows all desks booked by the employee

`/api/desks` is API allowing to retrieve desks for today and manage them (e.g. book/change desk)

`/api/desks/schedule` is API allowing to retrieve desks available/occupied in the future and manage them (e.g. book/cancel desk)

`/api/desks/booked` is API allowing to retrieve and manage a desk for a specific period (e.g. for today)

`/rooms` shows all rooms with time slots available to book

`/rooms/bookings` shows all rooms booked by the employee

`/api/rooms` is API allowing to fetch and book free time slots

`/api/rooms/booked` is API allowing to retrieve and manage rooms for a specific period (e.g. for today)

`/profile` shows information about a logged-in employee and allows to update the department where the employee works

`/register`, `/login`, and `/logout` allows to register the employee account, log in and log out

### Settings

- `/config/settings.py` contains a list of default Django settings, enables `office` app and sets a User model `office.User`

### HTML

- `/office/templates/office/layout.html` contains the main menu showing at the top of each page and a body block to display content

- `/office/templates/office/login.html` and `/office/templates/office/register.html` renders forms to register a user and log in to the user account

- `/office/templates/office/index.html` renders the main page "Today" displaying a desk assigned to the user for today, and a list of rooms booked for today

- `/office/templates/office/desks.html` displays filters, total numbers (available, occupied), and a list of desks to book one for today

- `/office/templates/office/desks_schedule.html` displays filters and a calendar to book a desk for a specific date in the future

- `/office/templates/office/rooms.html` displays filters, total numbers (available, occupied), and a list of rooms and time slots available for booking for today or a selected date

- `/office/templates/office/desks_bookings.html` and `/office/templates/office/rooms_bookings.html` displays all desks and rooms booked by user for the next days

- `/office/templates/office/profile.html` renders the user full name, email address and department which can be changed (e.g. in case the user gets a new role in the company)

### Stylesheet

- `/office/static/office/styles.css` stylizes design of HTML documents

### Models

`/office/models.py` contains following models:

(1) **Departments** describe a department in the company

(2) **Amenities** describe an amenity (e.g. monitor, keyboard, etc.) related to a specific facility (e.g. desk or room)

(3) **Floors** describe a floor name in the office (e.g. a floor number as 1, 2, 3 or name like "Game Floor")

(4) **User** describes user data including a department user belongs to

(5) **Desks** describe desk properties enriched by additional data (user and bookings)

(6) **Rooms** describe room properties enriched by additional data (amenities and time slots when room is free)

(7 & 8) **DeskBookings** and **RoomBookings** describe desk/room bookings properties with an additional flag showing if the desk/room is available for check-in

### Other files

- `/manage.py` sets the DJANGO_SETTINGS_MODULE environment variable (`config.settings`) and executes Django-specific commands

- `/config/asgi.py` and `/config/wsgi.py` represents the default Django’s ASGI and WSGI configs

- `/office/admin.py` and `/office/tests.py` are auto-generated files intented for representing admin models and tests, and `/office/apps.py` includes an app configuration for the `office` app

- `/.gitignore` lists the files that Git should ignore and don't track

# How to run the application

In your terminal:

1. Execute `git clone git@github.com:me50/ihorsha.git office-app` to clone this Git repository

2. Go to the app directory using `cd office-app`

3. Make migrations for the Office app
   `python3 manage.py makemigrations office`

4. Apply migrations to database
   `python3 manage.py migrate`

5. Import initial data containing all company departments, amenities, floors, desks and rooms in the office
   `python3 manage.py loaddata data.json`

6. Run the app
   `python3 manage.py runserver`
