const getCapacity = (capacity) => {
    document.querySelector('#capacity').innerHTML = `
        <span class="badge rounded-pill text-bg-success">${capacity.available}</span>
        <b>rooms available</b>
        <span class="badge rounded-pill text-bg-light">${capacity.occupied}</span>
        <b>rooms occupied</b>
    `;
}

// Format date to Mongo datefield format
const getMongoDateFormat = (date) => {
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, "0");
    const day = date.getDate().toString().padStart(2, "0");
    const formattedDate = `${year}-${month}-${day}`

    return formattedDate;
};

const getTime = (date) => {
    const time = new Date(date).toLocaleTimeString('en', { timeStyle: 'short', hour12: false, timeZone: 'UTC' });
    return time;
};

const getRooms = (date, duration, roomCapacity, amenities, floors) => {
    fetch(`/api/rooms?date=${date}&duration=${duration}&roomCapacity=${roomCapacity}&amenities=${amenities}&floors=${floors}`, {
        method: 'GET',
    })
    .then(response => response.json())
    .then(({rooms, capacity}) => {
        document.querySelector('#rooms').innerHTML = '';

        getCapacity(capacity);

        rooms.forEach(room => {
            if (room.available_slots.length > 0) {
                const element = document.createElement('label');

                element.classList.add('col-sm-2', 'col-lg-3');
                element.setAttribute('for', `${room.id}`);

                element.innerHTML = `
                    <div class="facility-card">
                        <div class="name">
                            <i class="bi bi-geo-alt-fill" aria-hidden="true"></i>
                            Room ${room.name} <span>• ${room.floor} floor</span>
                        </div>
                        
                        <div class="capacity">
                            <i class="bi bi-people" aria-hidden="true"></i>
                            Max. ${room.capacity}
                        </div>
                        <div class="amenities">
                            <b>Amenities:</b>
                            ${room.amenities.map(amenity => ` ${amenity}`)}
                        </div>
                        <div class="availability">
                            <i class="bi bi-clock" aria-hidden="true"></i>
                            Available
                            <div class="slots">
                                ${room.available_slots.map((slot, index) => (
                                    `
                                        <input class="btn-check" type="radio"
                                            name="slot"
                                            id="${room.id}-${index}"
                                            value=${index}
                                            data-room_id=${room.id}
                                            data-start=${slot[0]}
                                            data-end=${slot[1]}
                                        >
                                        <label class="btn btn-outline-primary" for="${room.id}-${index}">
                                            ${getTime(slot[0])}-${getTime(slot[1])}
                                        </label>
                                    `
                                )).join(' ')}
                            </div>
                        </div>
                    </div>
                `;

                document.querySelector('#rooms').append(element);
            }
        })
    });
}

document.addEventListener('DOMContentLoaded', () => {
    // Render an initial list of rooms
    date = getMongoDateFormat(new Date());
    duration = [...document.querySelectorAll('input[name="duration"]:checked')].map(item => item.value);
    roomCapacity = [...document.querySelectorAll('input[name="room-capacity"]:checked')].map(item => item.value);
    amenities = [...document.querySelectorAll('input[name="amenities"]:checked')].map(item => item.value);
    floors = [...document.querySelectorAll('input[name="floors"]:checked')].map(item => item.value);

    getRooms(date, duration, roomCapacity, amenities, floors);
    
    // Update a list of rooms if filter is changed
    document.querySelector('form#book-room').addEventListener('change', (event) => {
        filter = ['date', 'duration', 'room-capacity', 'amenities', 'floors'];

        if (filter.includes(event.target.name)) {
            duration = [...document.querySelectorAll('input[name="duration"]:checked')].map(item => item.value);
            roomCapacity = [...document.querySelectorAll('input[name="room-capacity"]:checked')].map(item => item.value);
            amenities = [...document.querySelectorAll('input[name="amenities"]:checked')].map(item => item.value);
            floors = [...document.querySelectorAll('input[name="floors"]:checked')].map(item => item.value);

            getRooms(date, duration, roomCapacity, amenities, floors);
        } else {
            document.querySelector('.form-submit-container').style.display = 'initial';
        }
    });

    // Handle a click on date later
    document.querySelector('#date-later').onclick = () => {
        // Switch to custom date selection
        document.querySelector('#date-later').remove();
        document.querySelector('#date-today').remove();
        document.querySelector('#date-custom').style.display = 'initial';

        // Render datepicker from the third-party lib
        datepicker('#datepicker', {
            onSelect: instance => {
                document.querySelector('.form-submit-container').style.display = 'none';
                date = getMongoDateFormat(instance.dateSelected);
                getRooms(date, duration, roomCapacity, amenities, floors);
            },
            dateSelected: new Date(),
            disabler: date => new Date() >= date
        });
    };

    // Book a room
    document.querySelector('form#book-room').addEventListener('submit', (event) => {
        event.preventDefault();

        // Get params
        selectedSlot = document.querySelector('input[name=slot]:checked');
        roomId = selectedSlot.dataset.room_id;
        start = selectedSlot.dataset.start;
        end = selectedSlot.dataset.end;

        // Book a room
        fetch(`/api/rooms`, {
            method: 'POST',
            body: JSON.stringify({roomId, start, end})
        })
        .then(response => response.json())
        .then(({errors}) => {
            if (!errors) {
                window.location.href = "/rooms/bookings";
            } else {
                console.log(errors);
            }
        });
    });
});
