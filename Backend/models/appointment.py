"""
Appointment Model - Stores booked appointments
"""
from tortoise.models import Model
from tortoise import fields
from datetime import datetime


class Appointment(Model):
    id = fields.IntField(pk=True)
    intake_call = fields.ForeignKeyField("models.IntakeCall", related_name="appointment")
    caller = fields.ForeignKeyField("models.Caller", related_name="appointments")
    practice_area = fields.CharField(max_length=50)
    appointment_date = fields.DatetimeField()
    appointment_time = fields.TimeField()
    calendar_event_id = fields.CharField(max_length=255, null=True)
    booking_status = fields.CharField(
        max_length=20, 
        default="pending"
    )  # "pending", "confirmed", "cancelled"
    confirmation_email_sent = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "appointments"

    def __str__(self):
        return f"Appointment {self.id} - {self.appointment_date}"

