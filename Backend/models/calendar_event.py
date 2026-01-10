"""
CalendarEvent Model - Stores calendar event information
"""
from tortoise.models import Model
from tortoise import fields
from datetime import datetime


class CalendarEvent(Model):
    id = fields.IntField(pk=True)
    appointment = fields.ForeignKeyField("models.Appointment", related_name="calendar_event")
    google_event_id = fields.CharField(max_length=255, unique=True)
    event_title = fields.CharField(max_length=255)
    event_description = fields.TextField()
    start_time = fields.DatetimeField()
    end_time = fields.DatetimeField()
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "calendar_events"

    def __str__(self):
        return f"Calendar Event {self.google_event_id} - {self.event_title}"

