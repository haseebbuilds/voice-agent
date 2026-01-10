"""
CaseQuestion Model - Stores answers to practice area questions
"""
from tortoise.models import Model
from tortoise import fields
from datetime import datetime


class CaseQuestion(Model):
    id = fields.IntField(pk=True)
    intake_call = fields.ForeignKeyField("models.IntakeCall", related_name="case_questions")
    question_key = fields.CharField(max_length=100)  # e.g., "vehicle_year", "incident_type"
    question_text = fields.TextField()
    answer = fields.TextField()
    practice_area = fields.CharField(max_length=50)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "case_questions"

    def __str__(self):
        return f"{self.question_key}: {self.answer[:50]}"

