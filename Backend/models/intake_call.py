"""
IntakeCall Model - Tracks voice intake calls and their state
"""
from tortoise.models import Model
from tortoise import fields
from datetime import datetime


class IntakeCall(Model):
    id = fields.IntField(pk=True)
    caller = fields.ForeignKeyField("models.Caller", related_name="calls", null=True)
    twilio_call_sid = fields.CharField(max_length=100, unique=True)
    practice_area = fields.CharField(max_length=50)  # "Lemon Law" or "Personal Injury"
    call_status = fields.CharField(
        max_length=20, 
        default="in_progress"
    )  # "in_progress", "completed", "failed"
    current_state = fields.CharField(
        max_length=50, 
        default="GREETING"
    )  # State machine state
    current_field = fields.CharField(
        max_length=20,
        null=True
    )  # Current field being collected in PERSONAL_INFO: "name", "phone", "email", "email_confirm"
    pending_email = fields.CharField(
        max_length=255,
        null=True
    )  # Temporary storage for email before confirmation
    consent_to_book = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "intake_calls"

    def __str__(self):
        return f"Call {self.twilio_call_sid} - {self.practice_area}"

