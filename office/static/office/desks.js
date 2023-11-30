const getCapacity = (capacity) => {
    document.querySelector('#capacity').innerHTML = `
        <span class="badge rounded-pill text-bg-success">${capacity.available}</span>
        <b>desks available</b>
        <span class="badge rounded-pill text-bg-light">${capacity.occupied}</span>
        <b>desks occupied</b>
    `;
}

const getDesks = (amenities, floors) => {
    fetch(`/api/desks?amenities=${amenities}&floors=${floors}`, {
        method: 'GET',
    })
    .then(response => response.json())
    .then(({desks, capacity}) => {
        document.querySelector('#desks').innerHTML = '';

        getCapacity(capacity);

        desks.forEach(desk => {
            let userBooking = desk.booked.find(item => item.my_booking);
            
            const element = document.createElement('label');

            element.classList.add('col-sm-2', 'col-lg-3');
            element.setAttribute('for', `${desk.id}`);

            element.innerHTML = `
                <input class="form-check-input" name="desk" type="radio" value="">
                <div class="facility-card ${userBooking ? 'my-booking' : ''} ${!userBooking && desk.booked.length > 0 ? 'disabled' : 'selectable'}" id="desk-${desk.id}">
                    <div class="name">
                        <i class="bi bi-geo-alt-fill" aria-hidden="true"></i>
                        Desk ${desk.name} <span>• ${desk.floor} floor</span>
                    </div>
                    <div class="peer">
                        ${desk.booked.length > 0 && !userBooking ?
                            `
                            ${!desk.booked[0].teammate ? `
                                <i class="bi bi-person-fill" aria-hidden="true"></i>
                                Booked by peer from <b>${desk.booked[0].department}</b>
                                ` : ''}
                            ${desk.booked[0].teammate ? `
                                <div class="teammate">
                                    <i class="bi bi-person-fill" aria-hidden="true"></i>
                                    <b>Booked by your teammate</b>
                                </div>` : ""}
                            ` : ""
                        }
                    </div>
                    <div class="amenities">
                        <b>Amenities:</b>
                        ${desk.amenities.map(amenity => ` ${amenity}`)}
                    </div>
                </div>
            `;

            document.querySelector('#desks').append(element);

            element.onclick = (event) => {
                event.preventDefault();

                fetch(`/api/desks`, {
                    method: 'POST',
                    body: JSON.stringify({
                        desk_id: desk.id,
                        amenities: amenities,
                        floors: floors[0] !== '' ? floors : []
                    })
                })
                .then(response => response.json())
                .then(({desks, capacity, errors}) => {
                    if (!errors) {
                        getCapacity(capacity);

                        // Actualize list of desks
                        desks.forEach(desk => {
                            // Reset desks statuses
                            document.querySelector(`#desk-${desk.id}`).classList.remove('my-booking', 'disabled', 'selectable');

                            // Change desk of logged in user
                            userBooking = desk.booked.find(item => item.my_booking);
                            userBooking && document.querySelector(`#desk-${desk.id}`).classList.add('my-booking');

                            // Update other desks statuses
                            document.querySelector(`#desk-${desk.id}`).classList.add(!userBooking && desk.booked.length > 0 ? 'disabled' : 'selectable');
                            
                            // Update peer element
                            desk_element = document.querySelector(`#desk-${desk.id}`);
                            desk_element.querySelector(`.peer`).innerHTML = '';
                            
                            desk.booked.length > 0 && !userBooking ?
                                desk_element.querySelector(`.peer`).innerHTML = `
                                    ${!desk.booked[0].teammate ? `
                                        <i class="bi bi-person-fill" aria-hidden="true"></i>
                                        Booked by peer from <b>${desk.booked[0].department}</b>
                                        ` : ''}
                                    ${desk.booked[0].teammate ? `
                                        <div class="teammate">
                                            <i class="bi bi-person-fill" aria-hidden="true"></i>
                                            <b>Booked by your teammate</b>
                                        </div>` : ""}
                                ` : ""
                        })
                    } else {
                        console.log(errors)
                    }
                });
            }
        })
    });
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelector('form#desk-today').addEventListener('change', () => {
        amenities = [...document.querySelectorAll('input[name="amenities"]:checked')].map(item => item.value);
        floors = [...document.querySelectorAll('input[name="floors"]:checked')].map(item => item.value);
        getDesks(amenities, floors);
    });

    defaultAmenities = [...document.querySelectorAll('input[name="amenities"]:checked')].map(item => item.value);
    defaultFloors = [...document.querySelectorAll('input[name="floors"]:checked')].map(item => item.value);
    getDesks(defaultAmenities, defaultFloors);
});
