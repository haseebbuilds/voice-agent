from fastapi import Request, Form
from twilio.twiml.voice_response import VoiceResponse, Gather
from models.intake_call import IntakeCall
from models.caller import Caller
from models.appointment import Appointment
from models.calendar_event import CalendarEvent
from helpers.voice_agent import VoiceAgent, CallState
from helpers.calendar_service import calendar_service
from helpers.email_service import send_confirmation_email
from config.settings import settings
from datetime import datetime, timedelta
from typing import Optional
import json

async def handle_caller_response(request: Request, call_sid: str) -> str:
    from datetime import datetime
    
    response = VoiceResponse()

    form = await request.form()

    speech_result = form.get("SpeechResult", "")
    
    from tortoise.exceptions import DoesNotExist, IntegrityError
    
    try:
        intake_call = await IntakeCall.get(twilio_call_sid=call_sid)
        if hasattr(intake_call, 'caller_id') and intake_call.caller_id:
            try:
                await intake_call.fetch_related('caller')
            except Exception:
                pass
    except DoesNotExist:
        try:
            from_number = form.get("From", "")
            temp_caller, _ = await Caller.get_or_create(
                email=f"temp_{call_sid}@temp.com",
                defaults={
                    "full_name": "Temporary",
                    "phone": from_number or ""
                }
            )
            
            intake_call, created = await IntakeCall.get_or_create(
                twilio_call_sid=call_sid,
                defaults={
                    "caller": temp_caller,
                    "call_status": "in_progress",
                    "current_state": CallState.GREETING.value,
                    "practice_area": "",
                    "consent_to_book": False
                }
            )
        except IntegrityError:
            try:
                intake_call = await IntakeCall.get(twilio_call_sid=call_sid)
            except DoesNotExist:
                response.say("Sorry, there was an error processing your call. Please try again.", voice='alice')
                response.hangup()
                return str(response)
        except Exception:
            import traceback
            traceback.print_exc()
            response.say("Sorry, there was an error processing your call. Please try again.", voice='alice')
            response.hangup()
            return str(response)
    except Exception:
        import traceback
        traceback.print_exc()
        try:
            from_number = form.get("From", "")
            temp_caller, _ = await Caller.get_or_create(
                email=f"temp_{call_sid}@temp.com",
                defaults={
                    "full_name": "Temporary",
                    "phone": from_number or ""
                }
            )
            intake_call, created = await IntakeCall.get_or_create(
                twilio_call_sid=call_sid,
                defaults={
                    "caller": temp_caller,
                    "call_status": "in_progress",
                    "current_state": CallState.GREETING.value,
                    "practice_area": "",
                    "consent_to_book": False
                }
            )
        except Exception:
            response.say("Sorry, there was an error processing your call. Please try again.", voice='alice')
            response.hangup()
            return str(response)
    
    try:
        agent = VoiceAgent(intake_call)
    except Exception:
        import traceback
        traceback.print_exc()
        response.say("Sorry, there was an error. Please try again.", voice='alice')
        response.hangup()
        return str(response)
    
    result = await agent.process_response(speech_result)
    
    if result["action"] == "end":
        response.say(result["message"], voice='alice')
        response.hangup()
        return str(response)
    
    elif result["action"] == "transfer":
        response.say(result["message"], voice='alice')
        base_url = settings.APP_URL.rstrip('/')
        gather = Gather(
            input='speech dtmf',
            language='en-US',
            speech_timeout='auto',
            action=f'{base_url}/api/twilio/handle-transfer-response?call_sid={call_sid}',
            method='POST'
        )
        gather.say("Please say transfer to speak with someone, or say message to leave a message.", voice='alice')
        response.append(gather)
        response.say("I'll make sure someone gets back to you. Thank you for calling.", voice='alice')
        await agent.end_call()
        response.hangup()
        return str(response)
    
    if result["message"]:
        if agent.current_state == CallState.SHOW_SLOTS:
            start_date = datetime.now() + timedelta(days=1)
            end_date = start_date + timedelta(days=14)
            slots = await calendar_service.get_available_slots(start_date, end_date)
            
            if slots:
                num_slots = min(8, len(slots), 10)
                slots_message = "Here are the available time slots: "
                for i, slot in enumerate(slots[:num_slots], 1):
                    slots_message += f"Option {i}, {slot['formatted']}. "
                slots_message += f"Please choose option 1 through {num_slots}. Which option would you like?"
                
                base_url = settings.APP_URL.rstrip('/')
                gather = Gather(
                    input='speech dtmf',
                    language='en-US',
                    speech_timeout='auto',
                    action=f'{base_url}/api/twilio/handle-slot-selection?call_sid={call_sid}',
                    method='POST'
                )
                gather.say(slots_message, voice='alice')
                response.append(gather)
            else:
                response.say("I'm sorry, there are no available slots at this time. Please call back later.")
                response.hangup()
        else:
            base_url = settings.APP_URL.rstrip('/')
            gather = Gather(
                input='speech',
                language='en-US',
                speech_timeout='auto',
                action=f'{base_url}/api/twilio/handle-response?call_sid={call_sid}',
                method='POST'
            )
            gather.say(result["message"], voice='alice')
            response.append(gather)
    
    base_url = settings.APP_URL.rstrip('/')
    response.say("I didn't catch that. Could you please repeat?", voice='alice')
    response.redirect(f'{base_url}/api/twilio/handle-response?call_sid={call_sid}')
    
    return str(response)

async def handle_slot_selection(request: Request, call_sid: str, slot_datetime: Optional[str] = None) -> str:
    response = VoiceResponse()

    form = await request.form()

    speech_result = form.get("SpeechResult", "")
    digits = form.get("Digits", "")
    
    try:
        intake_call = await IntakeCall.get(twilio_call_sid=call_sid)
    except:
        response.say("Sorry, I couldn't find your call record.")
        response.hangup()
        return str(response)
    
    agent = VoiceAgent(intake_call)
    
    if slot_datetime:
        selected_slot = None
        start_date = datetime.now() + timedelta(days=1)
        end_date = start_date + timedelta(days=14)
        slots = await calendar_service.get_available_slots(start_date, end_date)
        
        for slot in slots:
            if slot["datetime"] == slot_datetime:
                selected_slot = slot
                break
        
        if selected_slot:
            confirmation_response = speech_result.lower() if speech_result else ""
            
            if "yes" in confirmation_response or "correct" in confirmation_response or "confirm" in confirmation_response:
                caller = await Caller.get(id=intake_call.caller_id)
                appointment_datetime = datetime.fromisoformat(selected_slot["datetime"])
                
                appointment = await Appointment.create(
                    intake_call=intake_call,
                    caller=caller,
                    practice_area=intake_call.practice_area,
                    appointment_date=appointment_datetime,
                    appointment_time=appointment_datetime.time(),
                    booking_status="confirmed"
                )
                
                event_data = {
                    "title": f"{intake_call.practice_area} Consultation - {caller.full_name}",
                    "description": f"Consultation for {intake_call.practice_area} case.",
                    "start_time": appointment_datetime,
                    "end_time": appointment_datetime + timedelta(minutes=30),
                    "attendees": [{"email": caller.email}]
                }
                
                google_event_id = await calendar_service.create_calendar_event(event_data)
                
                if google_event_id:
                    appointment.calendar_event_id = google_event_id
                    await appointment.save()
                    
                    await CalendarEvent.create(
                        appointment=appointment,
                        google_event_id=google_event_id,
                        event_title=event_data["title"],
                        event_description=event_data["description"],
                        start_time=appointment_datetime,
                        end_time=appointment_datetime + timedelta(minutes=30)
                    )
                
                await send_confirmation_email(appointment)
                
                confirm_message = f"Perfect! I have you scheduled for {selected_slot['formatted']}. You will receive a confirmation email shortly with all the details."
                response.say(confirm_message, voice='alice')
                response.say("Thank you for calling. Have a great day!", voice='alice')
                
                await agent.end_call()
                response.hangup()
                return str(response)
            elif "no" in confirmation_response or "wrong" in confirmation_response:
                await agent._transition_to(CallState.SHOW_SLOTS)
                response.say("No problem. Let me show you the available slots again.", voice='alice')
                response.redirect(f'{settings.APP_URL.rstrip("/")}/api/twilio/handle-response?call_sid={call_sid}')
                return str(response)
            else:
                confirm_message = f"I have you down for {selected_slot['formatted']}. Is that correct? Please say yes to confirm, or no to choose a different time."
                gather = Gather(
                    input='speech',
                    language='en-US',
                    speech_timeout='auto',
                    action=f'{settings.APP_URL.rstrip("/")}/api/twilio/handle-slot-selection?call_sid={call_sid}&slot_datetime={slot_datetime}',
                    method='POST'
                )
                gather.say(confirm_message, voice='alice')
                response.append(gather)
                return str(response)
    
    start_date = datetime.now() + timedelta(days=1)
    end_date = start_date + timedelta(days=14)
    slots = await calendar_service.get_available_slots(start_date, end_date)
    
    selected_slot = None
    
    if digits:
        try:
            option_num = int(digits) - 1
            if 0 <= option_num < len(slots):
                selected_slot = slots[option_num]
        except:
            pass
    
    if not selected_slot and speech_result:
        speech_lower = speech_result.lower()
        for i, slot in enumerate(slots, 1):
            if f"option {i}" in speech_lower or f"{i}" in speech_lower:
                selected_slot = slot
                break
    
    if selected_slot:
        await agent._transition_to(CallState.CONFIRM_BOOKING)
        agent.selected_slot = selected_slot["formatted"]
        
        slot_datetime_str = selected_slot["datetime"]
        
        confirm_message = f"I have you down for {selected_slot['formatted']}. Is that correct? Please say yes to confirm, or no to choose a different time."
        gather = Gather(
            input='speech',
            language='en-US',
            speech_timeout='auto',
            action=f'{settings.APP_URL.rstrip("/")}/api/twilio/handle-slot-selection?call_sid={call_sid}&slot_datetime={slot_datetime_str}',
            method='POST'
        )
        gather.say(confirm_message, voice='alice')
        response.append(gather)
        response.say("Please confirm your appointment time.", voice='alice')
    else:
        response.say("I didn't catch that. Let me show you the slots again.")
        response.redirect(f'{settings.APP_URL.rstrip("/")}/api/twilio/handle-response?call_sid={call_sid}')
    
    return str(response)

