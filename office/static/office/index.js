const url = new URL(window.location.href);

const noBooking = (type) => {
    const container = document.createElement('div');
    container.classList.add('col-sm-2', 'col-lg-3');
    container.innerHTML = `
        <div class="facility-card">
            <div class="py-3 text-center">
                Not booked yet
            </div>
            <div class="actions py-2">
                <a class="btn w-100 btn-primary" href="/${type}">Book now</a>
            </div>
        </div>
    `

    document.querySelector(`#${type}`).append(container);
}

const getFilteredDesks = (period) => {
    // Get booked desk
    fetch(`/api/desks/booked?period=${period}`, {
        method: 'GET',
    })
    .then(response => response.json())
    .then(({desks}) => {
        if (!desks) {
            noBooking('desks');
        } else {
            desks.forEach(desk => {
                const element = document.createElement('div');
                element.classList.add('col-sm-2', 'col-lg-3', 'mb-2');

                element.innerHTML = `
                    <div class="facility-card">
                        <div class="name">
                            <i class="bi bi-geo-alt-fill" aria-hidden="true"></i>
                            Desk ${desk.name} <span>• ${desk.floor} floor</span>
                        </div>
                        ${url.pathname !== '/' ? `
                            <div class="duration">
                                <i class="bi bi-clock" aria-hidden="true"></i>
                                ${new Date(desk.date).toLocaleDateString('en', {
                                    weekday: 'short', year: 'numeric', month: 'long', day: 'numeric'
                                })}
                            </div>` : ''
                        }
                        ${!desk.check_in ? 
                            `
                                <div class="alert alert-warning" role="alert">
                                    💡 Check-in is available on the day of booking
                                </div>
                            ` :
                            ''
                        }
                        <div class="amenities">
                            <b>Amenities:</b>
                            ${desk.amenities.map(amenity => ` ${amenity}`)}
                        </div>
                        <div class="check-in success" style="display: ${desk.checked_in ? 'block' : 'none'}">
                            <i class="bi bi-check-circle-fill" aria-hidden="true"></i>
                            Checked in
                        </div>
                        <div class="actions py-2">
                            <a class="btn btn-outline-secondary" id="release" style="display: ${desk.checked_in ? 'none' : 'inline-block'}">Release</a>
                            <button type="button" class="btn btn-success" ${!desk.check_in ? 'disabled' : ''} id="check-in" style="display: ${desk.checked_in ? 'none' : 'initial'}">
                                ✅ Check in
                            </button>
                            <button type="button" class="w-100 btn btn-outline-danger" id="check-out" style="display: ${desk.checked_in ? 'initial' : 'none'}">
                                ❌ Free up
                            </button>
                        </div>
                    </div>
                `;

                document.querySelector('#desks').append(element);

                element.querySelector('#check-in').onclick = (event) => {
                    event.preventDefault();

                    fetch(`/api/desks/booked`, {
                        method: 'PUT',
                        body: JSON.stringify({
                            desk_id: desk.id,
                            check_in: true,
                        })
                    })
                    .then(response => response.json())
                    .then(({status, errors}) => {
                        if (!errors && status === 204) {
                            element.querySelector('#release').style.display = 'none';
                            element.querySelector('#check-in').style.display = 'none';
                            element.querySelector('#check-out').style.display = 'initial';
                            element.querySelector('.check-in').style.display = 'block';
                        }

                        if (errors) {
                            console.log(errors)
                        }
                    })
                }

                element.querySelector('#check-out').onclick = (event) => {
                    event.preventDefault();

                    fetch(`/api/desks/booked`, {
                        method: 'PUT',
                        body: JSON.stringify({
                            desk_id: desk.id,
                            check_out: true,
                            period: period
                        })
                    })
                    .then(response => response.json())
                    .then(({status, total_bookings, errors}) => {
                        if (!errors && status === 204) {
                            element.remove();

                            if (total_bookings === 0) {
                                noBooking('desks');
                            }
                        }

                        if (errors) {
                            console.log(errors)
                        }
                    })
                }

                element.querySelector('#release').onclick = (event) => {
                    event.preventDefault();

                    fetch(`/api/desks/booked`, {
                        method: 'DELETE',
                        body: JSON.stringify({
                            desk_id: desk.id,
                            period: period
                        })
                    })
                    .then(response => response.json())
                    .then(({status, total_bookings, errors}) => {
                        if (!errors && status === 204) {
                            element.remove();

                            if (total_bookings === 0) {
                                noBooking('desks');
                            }
                        }

                        if (errors) {
                            console.log(errors)
                        }
                    })
                }
            });
        }
    });
};

const getFilteredRooms = (period) => {
    // Get booked rooms
    fetch(`/api/rooms/booked?period=${period}`, {
        method: 'GET',
    })
    .then(response => response.json())
    .then(({rooms}) => {
        if (!rooms) {
            noBooking('rooms');
        } else {
            rooms.forEach(room => {
                const element = document.createElement('div');
                element.classList.add('col-sm-2', 'col-lg-3', 'mb-2');

                element.innerHTML = `
                    <div class="facility-card">
                        <div class="name">
                            <i class="bi bi-geo-alt-fill" aria-hidden="true"></i>
                            Room ${room.name} <span>• ${room.floor} floor</span>
                        </div>
                        <div class="duration">
                            <i class="bi bi-clock" aria-hidden="true"></i>
                            ${url.pathname !== '/' ? 
                                new Date(room.start).toLocaleDateString('en', {
                                    weekday: 'short', year: 'numeric', month: 'long', day: 'numeric'
                                }) : ''
                            }
                            ${new Date(room.start).toLocaleTimeString('en', { timeStyle: 'short', hour12: false, timeZone: 'UTC' })}-${new Date(room.end).toLocaleTimeString('en', { timeStyle: 'short', hour12: false, timeZone: 'UTC' })}
                        </div>
                        ${!room.check_in ? 
                            `
                                <div class="alert alert-warning" role="alert">
                                    💡 Check-in is available on the day of booking
                                </div>
                            ` :
                            ''
                        }
                        <div class="amenities">
                            <b>Amenities:</b>
                            ${room.amenities.map(amenity => ` ${amenity}`)}
                        </div>
                        <div class="check-in success" style="display: ${room.checked_in ? 'block' : 'none'}">
                            <i class="bi bi-check-circle-fill" aria-hidden="true"></i>
                            Checked in
                        </div>
                        <div class="actions py-2">
                            <a class="btn btn-outline-secondary" id="release" style="display: ${room.checked_in ? 'none' : 'inline-block'}">Release</a>
                            <button type="button" class="btn btn-success" ${!room.check_in ? 'disabled' : ''} id="check-in" style="display: ${room.checked_in ? 'none' : 'initial'}">
                                ✅ Check in
                            </button>
                            <button type="button" class="w-100 btn btn-outline-danger" id="check-out" style="display: ${room.checked_in ? 'initial' : 'none'}">
                                ❌ Free up
                            </button>
                        </div>
                    </div>
                `;

                document.querySelector('#rooms').append(element);

                element.querySelector('#check-in').onclick = (event) => {
                    event.preventDefault();

                    fetch(`/api/rooms/booked`, {
                        method: 'PUT',
                        body: JSON.stringify({
                            room_id: room.id,
                            check_in: true,
                        })
                    })
                    .then(response => response.json())
                    .then(({status, errors}) => {
                        if (!errors && status === 204) {
                            element.querySelector('#release').style.display = 'none';
                            element.querySelector('#check-in').style.display = 'none';
                            element.querySelector('#check-out').style.display = 'initial';
                            element.querySelector('.check-in').style.display = 'block';
                        }

                        if (errors) {
                            console.log(errors)
                        }
                    })
                }

                element.querySelector('#check-out').onclick = (event) => {
                    event.preventDefault();

                    fetch(`/api/rooms/booked`, {
                        method: 'PUT',
                        body: JSON.stringify({
                            room_id: room.id,
                            check_out: true,
                            period: period
                        })
                    })
                    .then(response => response.json())
                    .then(({status, total_bookings, errors}) => {
                        if (!errors && status === 204) {
                            element.remove();

                            if (total_bookings === 0) {
                                noBooking('rooms');
                            }
                        }

                        if (errors) {
                            console.log(errors)
                        }
                    })
                }

                element.querySelector('#release').onclick = (event) => {
                    event.preventDefault();

                    fetch(`/api/rooms/booked`, {
                        method: 'DELETE',
                        body: JSON.stringify({
                            room_id: room.id,
                            period: period
                        })
                    })
                    .then(response => response.json())
                    .then(({status, total_bookings, errors}) => {
                        if (!errors && status === 204) {
                            element.remove();

                            if (total_bookings === 0) {
                                noBooking('rooms');
                            }
                        }

                        if (errors) {
                            console.log(errors)
                        }
                    })
                }
            })
        }
    });
};

document.addEventListener('DOMContentLoaded', () => {
    if (url.pathname === '/') {
        getFilteredDesks('today');
    } else if (url.pathname !== '/rooms/bookings') {
        getFilteredDesks();
    }

    if (url.pathname === '/') {
        getFilteredRooms('today');
    } else if (url.pathname !== '/desks/bookings') {
        getFilteredRooms();
    }
});
