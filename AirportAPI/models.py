from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Crew(models.Model):
    # Model representing a crew member
    first_name = models.CharField(max_length=255)  # First name of the crew member
    last_name = models.CharField(max_length=255)  # Last name of the crew member

    class Meta:
        constraints = [
            # Ensuring uniqueness of the combination of first and last name
            models.UniqueConstraint(
                fields=["first_name", "last_name"],
                name="unique_crew_first_name_last_name"
            )
        ]

    def __str__(self):
        # Return the full name of the crew member
        return f"{self.first_name} {self.last_name}"

    def full_name(self, value):
        # Method to set the full name of the crew member
        self.full_name = value


class Airport(models.Model):
    # Model representing an airport
    name = models.CharField(max_length=255)  # The name of the airport
    closest_big_city = models.CharField(max_length=255)  # The closest major city to the airport

    class Meta:
        constraints = [
            # Ensuring uniqueness of the combination of name and closest big city
            models.UniqueConstraint(
                fields=["name", "closest_big_city"],
                name="unique_airport_name_closest_big_city"
            )
        ]

    def __str__(self):
        # Return the name of the airport and the closest big city
        return f"{self.name} {self.closest_big_city}"


class Route(models.Model):
    # Model representing a route between two airports
    source = models.ForeignKey(
        Airport,
        on_delete=models.CASCADE,
        related_name="source_routes"  # The related name for accessing routes originating from this airport
    )
    destination = models.ForeignKey(
        Airport,
        on_delete=models.CASCADE,
        related_name="destination_routes"  # The related name for accessing routes ending at this airport
    )
    distance = models.IntegerField()  # The distance of the route in kilometers

    def __str__(self):
        # Return a string representation of the route
        return f"{self.source} - {self.destination}"

    @staticmethod
    def validate_destination(source, destination, error_to_raise):
        # Static method to validate if the destination is different from the source
        if source == destination:
            raise error_to_raise("Destination cannot be the same as source")

    def clean(self):
        # Method to clean and validate the route instance
        Route.validate_destination(
            source=self.source,
            destination=self.destination,
            error_to_raise=ValidationError
        )

    def save(
            self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        # Save method for the Route model
        self.full_clean()
        return super(Route, self).save(
            force_insert, force_update, using, update_fields
        )


class AirplaneType(models.Model):
    # Model representing a type of airplane
    name = models.CharField(max_length=255)  # The name of the airplane type

    def __str__(self):
        # Return the name of the airplane type
        return self.name


class Airplane(models.Model):
    # Model representing an airplane
    name = models.CharField(max_length=255)  # The name of the airplane
    rows = models.IntegerField()  # The number of rows in the airplane
    seats_in_rows = models.IntegerField()  # The number of seats in each row of the airplane
    airplane_type = models.ForeignKey(
        AirplaneType,
        on_delete=models.CASCADE,
        related_name="airplanes"  # The related name for accessing airplanes of this type
    )

    def __str__(self):
        # Return a string representation of the airplane
        return f"{self.name}, Num of seats: {self.num_of_seats}"

    @property
    def num_of_seats(self):
        # Calculate and return the total number of seats in the airplane
        return self.rows * self.seats_in_rows


class Flight(models.Model):
    # Model representing a flight
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name="flights"  # The related name for accessing flights on this route
    )
    airplane = models.ForeignKey(
        Airplane,
        on_delete=models.CASCADE,
        related_name="flights"  # The related name for accessing flights operated by this airplane
    )
    departure_time = models.DateTimeField()  # The departure time of the flight
    arrival_time = models.DateTimeField()  # The arrival time of the flight
    crew = models.ManyToManyField(
        Crew,
        related_name="flights"  # The related name for accessing crew members assigned to this flight
    )

    def __str__(self):
        # Return a string representation of the flight
        return f"{self.airplane.name}, Departure time: {self.departure_time}"

    @staticmethod
    def validate_arrival(departure_time, arrival_time, error_to_raise):
        # Static method to validate if the arrival time is after the departure time
        if departure_time == arrival_time:
            raise error_to_raise("Arrival time cannot be the same as departure time")

        if departure_time > arrival_time:
            raise error_to_raise("The time and date of arrival cannot be earlier than departure")

    def clean(self):
        # Method to clean and validate the flight instance
        Flight.validate_arrival(
            departure_time=self.departure_time,
            arrival_time=self.arrival_time,
            error_to_raise=ValidationError
        )

    def save(
            self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        # Save method for the Flight model
        self.full_clean()
        return super(Flight, self).save(
            force_insert, force_update, using, update_fields
        )


class Order(models.Model):
    # Model representing an order
    created_at = models.DateTimeField(auto_now_add=True)  # The date and time the order was created
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE  # The user who placed the order
    )

    class Meta:
        ordering = ["-created_at"]  # Ordering orders by their creation date

    def __str__(self):
        # Return a string representation of the order
        return f"{self.created_at}"


class Ticket(models.Model):
    # Model representing a ticket
    row = models.IntegerField()  # The row number of the seat
    seat = models.IntegerField()  # The seat number
    flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
        related_name="tickets"  # The related name for accessing tickets booked for this flight
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="tickets"  # The related name for accessing tickets belonging to this order
    )

    class Meta:
        unique_together = ("seat", "row", "flight")  # Ensuring uniqueness of seats in a flight
        ordering = ("seat",)  # Ordering tickets by seat number

    def __str__(self):
        # Return a string representation of the ticket
        return f"{self.flight} - (seat: {self.seat})"

    @staticmethod
    def validate_seat_and_row(
            seat: int,
            row: int,
            airplane_seats_in_row: int,
            airplane_rows: int,
            error_to_raise
    ):
        # Static method to validate the seat and row of the ticket
        if not (1 <= seat <= airplane_seats_in_row):
            raise error_to_raise(
                {"seat": f"seat must be in range [1, {airplane_seats_in_row}]"}
            )

        if not (1 <= row <= airplane_rows):
            raise error_to_raise(
                {"row": f"row must be in range [1, {airplane_rows}]"}
            )

    def clean(self):
        # Method to clean and validate the ticket instance
        Ticket.validate_seat_and_row(
            seat=self.seat,
            row=self.row,
            airplane_seats_in_row=self.flight.airplane.seats_in_rows,
            airplane_rows=self.flight.airplane.rows,
            error_to_raise=ValidationError
        )

    def save(
            self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        # Save method for the Ticket model
        self.full_clean()
        return super(Ticket, self).save(
            force_insert, force_update, using, update_fields
        )
