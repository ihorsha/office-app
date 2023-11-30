const getDay = (date) => {
    let day = date.getDay();
    if (day == 0) day = 7;
    
    return day - 1;
};

const getMonthName = (month) => month.toLocaleString('default', { month: 'short' });

// Format date to Mongo datefield format
const getMongoDateFormat = (date) => {
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, "0");
    const day = date.getDate().toString().padStart(2, "0");
    const formattedDate = `${year}-${month}-${day}`

    return formattedDate;
};

// Get capacity for the date
const getCapacity = (date, capacity) => {
    // Find count of occupied desks for the date
    const occupied = capacity.occupied.find(item => item.date === getMongoDateFormat(date))

    return ({
        available: capacity.total_capacity - (occupied && occupied.count || 0),
        occupied: occupied && occupied.count || 0
    })
};

const makeCalendar = (target, now, {amenities, floors}) => {
    const userBooking = (date, my_active_bookings) => my_active_bookings.find(item => item.date === getMongoDateFormat(date));

    fetch(`/api/desks/schedule?amenities=${amenities}&floors=${floors}`, {
        method: 'GET',
    })
    .then(response => response.json())
    .then(({my_active_bookings, capacity}) => {
        // Create calendar
        const year = now.getFullYear();
        const month = now.getMonth()
        const calendarDate = new Date(year, month);
        
        let today = new Date();
        today.setHours(0,0,0,0);

        let container = `
            <div class="d-flex justify-content-between title">
                <div class="p-2" id="prev-month"><i class="bi bi-arrow-left" aria-hidden="true"></i></div>
                <div class="p-2"><div class="">${getMonthName(calendarDate)} ${year}</div></div>
                <div class="p-2" id="next-month"><i class="bi bi-arrow-right" aria-hidden="true"></i></div>
            </div>
            <div class="d-flex calendar-weekdays">
                <div class="col calendar-weekday">M</div>
                <div class="col calendar-weekday">T</div>
                <div class="col calendar-weekday">W</div>
                <div class="col calendar-weekday">T</div>
                <div class="col calendar-weekday">F</div>
                <div class="col calendar-weekday">S</div>
                <div class="col calendar-weekday">S</div>
            </div>
            <div class="d-flex">
        `;

        for (let i = 0; i < getDay(calendarDate); i++) {
            container += `<div class="col calendar-empty-day"></div>`;
        }

        while (calendarDate.getMonth() == month) {
            let normalizedDate = new Date(calendarDate);
            normalizedDate.setHours(0,0,0,0);

            container += `
                <div class="col calendar-day ${userBooking(calendarDate, my_active_bookings) ? 'my-booking' : ''} ${(!userBooking(calendarDate, my_active_bookings) && capacity.occupied === capacity.total_capacity) || (today >= normalizedDate) ? 'disabled' : 'selectable'}" data-date="${calendarDate}">
                    <div class="text-center">
                        <div class="badge rounded-pill text-bg-success" id="available-desks">${getCapacity(calendarDate, capacity).available}</div>
                    </div>
                    <div class="text-center">
                        <div class="badge rounded-pill text-bg-light" id="occupied-desks">${getCapacity(calendarDate, capacity).occupied}</div>
                    </div>
                    <div class="date text-end">
                        ${calendarDate.getDate()}
                    </div>
                </div>
            `;

            if (getDay(calendarDate) % 7 == 6) {
                container += `</div><div class="d-flex">`;
            }

            calendarDate.setDate(calendarDate.getDate() + 1);
        }

        if (getDay(calendarDate) != 0) {
            for (let i = getDay(calendarDate); i < 7; i++) {
                container += `<div class="col calendar-empty-day"></div>`;
            }
        }

        container += `</div>`;

        target.innerHTML = container;

        document.querySelector('#prev-month').onclick = () => {
            makeCalendar(calendar, new Date(now.getFullYear(), now.getMonth() - 1, 1), filter={amenities, floors});
        }

        document.querySelector('#next-month').onclick = () => {
            makeCalendar(calendar, new Date(now.getFullYear(), now.getMonth() + 1, 1), filter={amenities, floors});
        }

        document.querySelectorAll('.selectable').forEach(item => {
            item.onclick = (event) => {
                event.preventDefault();
                event.stopImmediatePropagation();

                fetch(`/api/desks/schedule`, {
                    method: 'POST',
                    body: JSON.stringify({
                        date: getMongoDateFormat(new Date(item.dataset.date)),
                        amenities: amenities,
                        floors: floors[0] !== '' ? floors : [],
                    })
                })
                .then(response => response.json())
                .then(({my_active_bookings, capacity, errors}) => {
                    if (!errors) {
                        // Actualize list of desks
                        document.querySelectorAll('.calendar-day').forEach(element => {
                            let normalizedDate = new Date(element.dataset.date);
                            normalizedDate.setHours(0,0,0,0);

                            // Reset dates statuses
                            element.classList.remove('my-booking', 'disabled', 'selectable');

                            // Update dates statuses
                            (!userBooking(calendarDate, my_active_bookings) && capacity.occupied === capacity.total_capacity) || (today >= normalizedDate) ?
                                element.classList.add('disabled') :
                                element.classList.add('selectable')
                            
                            // Mark booked dates of logged in user
                            userBooking(normalizedDate, my_active_bookings) &&
                                element.classList.add('my-booking');

                            // Update capacity for selected date
                            element.querySelector('#available-desks').innerHTML = getCapacity(normalizedDate, capacity).available;
                            element.querySelector('#occupied-desks').innerHTML = getCapacity(normalizedDate, capacity).occupied;
                        })
                    } else {
                        console.log(errors)
                    }
                });
            }
        })
    })
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelector('form#desk-schedule').addEventListener('change', () => {
        amenities = [...document.querySelectorAll('input[name="amenities"]:checked')].map(item => item.value);
        floors = [...document.querySelectorAll('input[name="floors"]:checked')].map(item => item.value);
        makeCalendar(calendar, new Date(), filter={amenities, floors});
    });

    default_amenities = [...document.querySelectorAll('input[name="amenities"]:checked')].map(item => item.value);
    default_floors = [...document.querySelectorAll('input[name="floors"]:checked')].map(item => item.value);
    makeCalendar(calendar, new Date(), filter={amenities: default_amenities, floors: default_floors});
});
