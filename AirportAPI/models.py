from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Crew(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["first_name", "last_name"],
                name="unique_crew_first_name_last_name"
            )
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def full_name(self, value):
        self.full_name = value


class Airport(models.Model):
    name = models.CharField(max_length=255)
    closest_big_city = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "closest_big_city"],
                name="unique_airport_name_closest_big_city"
            )
        ]

    def __str__(self):
        return f"{self.name} {self.closest_big_city}"


class Route(models.Model):
    source = models.ForeignKey(
        Airport,
        on_delete=models.CASCADE,
        related_name="source_routes"
    )
    destination = models.ForeignKey(
        Airport,
        on_delete=models.CASCADE,
        related_name="destination_routes"
    )
    distance = models.IntegerField()

    def __str__(self):
        return f"{self.source} - {self.destination}"

    @staticmethod
    def validate_destination(source, destination, error_to_raise):
        if source == destination:
            raise error_to_raise("Destination cannot be the same as source")

    def clean(self):
        Route.validate_destination(
            source=self.source,
            destination=self.destination,
            error_to_raise=ValidationError
        )

    def save(
            self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        self.full_clean()
        return super(Route, self).save(
            force_insert, force_update, using, update_fields
        )


class AirplaneType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Airplane(models.Model):
    name = models.CharField(max_length=255)
    rows = models.IntegerField()
    seats_in_rows = models.IntegerField()
    airplane_type = models.ForeignKey(
        AirplaneType,
        on_delete=models.CASCADE,
        related_name="airplanes"
    )

    def __str__(self):
        return f"{self.name}, Num of seats: {self.num_of_seats}"

    @property
    def num_of_seats(self):
        return self.rows * self.seats_in_rows


class Flight(models.Model):
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name="flights"
    )
    airplane = models.ForeignKey(
        Airplane,
        on_delete=models.CASCADE,
        related_name="flights"
    )
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    crew = models.ManyToManyField(
        Crew,
        related_name="flights"
    )

    def __str__(self):
        return f"{self.airplane.name}, Departure time: {self.departure_time}"

    @staticmethod
    def validate_arrival(departure_time, arrival_time, error_to_raise):
        if departure_time == arrival_time:
            raise error_to_raise("Arrival time cannot be the same as departure time")

        if departure_time > arrival_time:
            raise error_to_raise("The time and date of arrival cannot be earlier than departure")

    def clean(self):
        Flight.validate_arrival(
            departure_time=self.departure_time,
            arrival_time=self.arrival_time,
            error_to_raise=ValidationError
        )

    def save(
            self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        self.full_clean()
        return super(Flight, self).save(
            force_insert, force_update, using, update_fields
        )


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.created_at}"


class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
        related_name="tickets"
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="tickets"
    )

    class Meta:
        unique_together = ("seat", "row", "flight")
        ordering = ("seat",)

    def __str__(self):
        return f"{self.flight} - (seat: {self.seat})"

    @staticmethod
    def validate_seat_and_row(
            seat: int,
            row: int,
            airplane_seats_in_row: int,
            airplane_rows: int,
            error_to_raise
    ):
        if not (1 <= seat <= airplane_seats_in_row):
            raise error_to_raise(
                {"seat": f"seat must be in range [1, {airplane_seats_in_row}]"}
            )

        if not (1 <= row <= airplane_rows):
            raise error_to_raise(
                {"row": f"row must be in range [1, {airplane_rows}]"}
            )

    def clean(self):
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
        self.full_clean()
        return super(Ticket, self).save(
            force_insert, force_update, using, update_fields
        )
