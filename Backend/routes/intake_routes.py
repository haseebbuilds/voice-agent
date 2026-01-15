from fastapi import APIRouter, Request, Form, HTTPException
from typing import Optional
import os
from models.intake_call import IntakeCall
from models.appointment import Appointment
from models.caller import Caller
from controllers.twilio_controller import (
    handle_caller_response,
    handle_slot_selection
)
from helpers.calendar_service import calendar_service
from helpers.email_service import send_confirmation_email
from datetime import datetime, timedelta

router = APIRouter(prefix="/api", tags=["intake"])


@router.post("/twilio/webhook")
async def twilio_webhook(request: Request):
    from fastapi.responses import Response
    from twilio.twiml.voice_response import VoiceResponse
    try:
        form = await request.form()
        form_dict = dict(form)
        call_sid = form_dict.get('CallSid', '')
        from_number = form_dict.get('From', '')

        if not call_sid:
            resp = VoiceResponse()
            resp.say("Sorry, there was an error.", voice="alice")
            resp.hangup()
            return Response(content=str(resp), media_type="application/xml")

        from models.intake_call import IntakeCall
        from models.caller import Caller
        from helpers.voice_agent import CallState
        from tortoise.exceptions import IntegrityError, DoesNotExist, TransactionManagementError

        try:
            intake_call = await IntakeCall.get(twilio_call_sid=call_sid)
        except (DoesNotExist, TransactionManagementError):
            temp_caller, _ = await Caller.get_or_create(
                email=f"temp_{call_sid}@temp.com",
                defaults={
                    "full_name": "Temporary",
                    "phone": from_number or ""
                }
            )
            intake_call, _ = await IntakeCall.get_or_create(
                twilio_call_sid=call_sid,
                defaults={
                    "caller": temp_caller,
                    "call_status": "in_progress",
                    "current_state": CallState.GREETING.value,
                    "practice_area": "",
                    "consent_to_book": False
                }
            )
        resp = VoiceResponse()
        from config.settings import settings
        base_url = settings.APP_URL.rstrip('/')
        action_url = f'{base_url}/api/twilio/handle-response?call_sid={call_sid}'
        resp.say(
            "Hi, this is the automated intake assistant. I can help you schedule a consultation.",
            voice="alice",
        )
        resp.gather(
            input='speech',
            language='en-US',
            speech_timeout='5',
            action=action_url,
            method='POST'
        )
        resp.redirect(action_url)
        return Response(content=str(resp), media_type="application/xml")
    except Exception:
        resp = VoiceResponse()
        resp.say("Sorry, there is an error. Please try again later.", voice="alice")
        resp.hangup()
        return Response(content=str(resp), media_type="application/xml")


@router.post("/twilio/handle-response")
async def twilio_handle_response(request: Request, call_sid: str):
    from fastapi.responses import Response
    from twilio.twiml.voice_response import VoiceResponse
    try:
        form = await request.form()
        form_dict = dict(form)
        _ = form_dict.get("SpeechResult", "")
        twiml = await handle_caller_response(request, call_sid)
        return Response(content=twiml, media_type="application/xml")
    except Exception:
        response = VoiceResponse()
        response.say("Sorry, there was an error. Please try again.", voice='alice')
        from config.settings import settings
        base_url = settings.APP_URL.rstrip('/')
        gather = response.gather(
            input='speech',
            language='en-US',
            speech_timeout='3',
            action=f'{base_url}/api/twilio/handle-response?call_sid={call_sid}',
            method='POST'
        )
        gather.say("Please try again. Is this about Lemon Law or Personal Injury?", voice='alice')
        return Response(content=str(response), media_type="application/xml")


@router.post("/twilio/handle-slot-selection")
async def twilio_handle_slot_selection(request: Request, call_sid: str, slot_datetime: Optional[str] = None):
    from fastapi.responses import Response
    try:
        twiml = await handle_slot_selection(request, call_sid, slot_datetime)
        return Response(content=twiml, media_type="application/xml")
    except Exception:
        from twilio.twiml.voice_response import VoiceResponse
        response = VoiceResponse()
        response.say("Sorry, there was an error selecting the slot.", voice='alice')
        return Response(content=str(response), media_type="application/xml")


@router.post("/twilio/handle-transfer-response")
async def twilio_handle_transfer_response(request: Request, call_sid: str):
    from fastapi.responses import Response
    from twilio.twiml.voice_response import VoiceResponse
    from models.intake_call import IntakeCall
    from helpers.voice_agent import VoiceAgent, CallState
    
    try:
        form = await request.form()
        speech_result = form.get("SpeechResult", "").lower()
        
        intake_call = await IntakeCall.get(twilio_call_sid=call_sid)
        agent = VoiceAgent(intake_call)
        
        response = VoiceResponse()
        
        if "transfer" in speech_result or "speak" in speech_result or "human" in speech_result:
            response.say("I'll transfer you to a human representative now. Please hold.", voice='alice')
            response.say("I'm sorry, but I cannot transfer you at this time. Please call back during business hours to speak with someone.", voice='alice')
            await agent.end_call()
            response.hangup()
        elif "message" in speech_result or "leave" in speech_result:
            response.say("I've noted your information and someone will call you back soon. Thank you for calling.", voice='alice')
            await agent.end_call()
            response.hangup()
        else:
            from config.settings import settings
            base_url = settings.APP_URL.rstrip('/')
            gather = response.gather(
                input='speech',
                language='en-US',
                speech_timeout='auto',
                action=f'{base_url}/api/twilio/handle-transfer-response?call_sid={call_sid}',
                method='POST'
            )
            gather.say("Please say transfer to speak with someone, or say message to leave a message.", voice='alice')
            response.append(gather)
        
        return Response(content=str(response), media_type="application/xml")
    except Exception:
        response = VoiceResponse()
        response.say("Thank you for calling. Someone will contact you soon.", voice='alice')
        response.hangup()
        return Response(content=str(response), media_type="application/xml")


@router.get("/calls/{call_id}")
async def get_call_details(call_id: int):
    try:
        call = await IntakeCall.get(id=call_id)
        return {
            "id": call.id,
            "twilio_call_sid": call.twilio_call_sid,
            "practice_area": call.practice_area,
            "call_status": call.call_status,
            "current_state": call.current_state,
            "consent_to_book": call.consent_to_book,
            "created_at": call.created_at.isoformat()
        }
    except:
        raise HTTPException(status_code=404, detail="Call not found")


@router.get("/calls")
async def list_calls():
    calls = await IntakeCall.all().order_by("-created_at")
    return [
        {
            "id": call.id,
            "twilio_call_sid": call.twilio_call_sid,
            "practice_area": call.practice_area,
            "call_status": call.call_status,
            "current_state": call.current_state,
            "consent_to_book": call.consent_to_book,
            "created_at": call.created_at.isoformat(),
        }
        for call in calls
    ]


@router.get("/calls/{call_id}/state")
async def get_call_state(call_id: int):
    try:
        call = await IntakeCall.get(id=call_id)
        return {
            "call_id": call.id,
            "current_state": call.current_state,
            "call_status": call.call_status
        }
    except:
        raise HTTPException(status_code=404, detail="Call not found")


@router.get("/calendar/availability")
async def get_availability(days_ahead: int = 14):
    start_date = datetime.now() + timedelta(days=1)
    end_date = start_date + timedelta(days=days_ahead)
    slots = await calendar_service.get_available_slots(start_date, end_date)
    return {"available_slots": slots}


@router.get("/appointments")
async def list_appointments():
    appointments = await Appointment.all().order_by("-appointment_date")
    result = []
    for appointment in appointments:
        caller = await Caller.get(id=appointment.caller_id)
        result.append(
            {
                "id": appointment.id,
                "caller": {
                    "name": caller.full_name,
                    "email": caller.email,
                    "phone": caller.phone,
                },
                "practice_area": appointment.practice_area,
                "appointment_date": appointment.appointment_date.isoformat(),
                "appointment_time": appointment.appointment_time.isoformat(),
                "booking_status": appointment.booking_status,
                "confirmation_email_sent": appointment.confirmation_email_sent,
            }
        )
    return result


@router.get("/appointments/{appointment_id}")
async def get_appointment(appointment_id: int):
    try:
        appointment = await Appointment.get(id=appointment_id)
        caller = await Caller.get(id=appointment.caller_id)
        return {
            "id": appointment.id,
            "caller": {
                "name": caller.full_name,
                "email": caller.email,
                "phone": caller.phone
            },
            "practice_area": appointment.practice_area,
            "appointment_date": appointment.appointment_date.isoformat(),
            "appointment_time": appointment.appointment_time.isoformat(),
            "booking_status": appointment.booking_status,
            "confirmation_email_sent": appointment.confirmation_email_sent
        }
    except:
        raise HTTPException(status_code=404, detail="Appointment not found")


@router.post("/email/send-confirmation")
async def send_email_confirmation(appointment_id: int):
    try:
        appointment = await Appointment.get(id=appointment_id)
        success = await send_confirmation_email(appointment)
        if success:
            return {"message": "Confirmation email sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send email")
    except:
        raise HTTPException(status_code=404, detail="Appointment not found")
