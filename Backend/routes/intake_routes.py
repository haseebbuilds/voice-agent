from fastapi import APIRouter, Request, Form, HTTPException
from typing import Optional
import os
from models.intake_call import IntakeCall
from models.appointment import Appointment
from models.caller import Caller
from controllers.twilio_controller import (
    handle_incoming_call,
    handle_caller_response,
    handle_slot_selection
)
from helpers.calendar_service import calendar_service
from helpers.email_service import send_confirmation_email
from datetime import datetime, timedelta

router = APIRouter(prefix="/api", tags=["intake"])


@router.post("/twilio/webhook")
async def twilio_webhook(request: Request):
    import sys
    from fastapi.responses import Response
    from twilio.twiml.voice_response import VoiceResponse
    
    sys.stdout.flush()
    sys.stderr.flush()
    
    print("\n" + "=" * 70, flush=True)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 📞 WEBHOOK CALLED", flush=True)
    print("=" * 70, flush=True)
    
    try:
        form = await request.form()
        form_dict = dict(form)
        call_sid = form_dict.get('CallSid', '')
        from_number = form_dict.get('From', '')
        
        print(f"CallSid: {call_sid}", flush=True)
        print(f"From: {from_number}", flush=True)
        print("-" * 70, flush=True)
        sys.stdout.flush()

        if not call_sid:
            print("❌ No CallSid", flush=True)
            resp = VoiceResponse()
            resp.say("Sorry, there was an error.", voice="alice")
            resp.hangup()
            return Response(content=str(resp), media_type="application/xml")

        intake_call = None
        try:
            print("→ Creating call record in database...", flush=True)
            from models.intake_call import IntakeCall
            from models.caller import Caller
            from helpers.voice_agent import CallState
            from tortoise.exceptions import IntegrityError, DoesNotExist, TransactionManagementError
            
            try:
                intake_call = await IntakeCall.get(twilio_call_sid=call_sid)
                print(f"→ Found existing call record: ID={intake_call.id}", flush=True)
            except (DoesNotExist, TransactionManagementError):
                print(f"→ Creating new call record with temp caller...", flush=True)
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
                if created:
                    print(f"→ Created call record: ID={intake_call.id}", flush=True)
                else:
                    print(f"→ Found existing call record after retry: ID={intake_call.id}", flush=True)
        except Exception as e:
            print(f"⚠️  Database error (will create in handle-response): {e}", flush=True)
            import traceback
            traceback.print_exc()

        resp = VoiceResponse()
        
        print("→ Adding greeting only (practice area question will come next)...", flush=True)
        from config.settings import settings
        base_url = settings.APP_URL.rstrip('/')
        action_url = f'{base_url}/api/twilio/handle-response?call_sid={call_sid}'
        
        resp.say(
            "Hi, this is the automated intake assistant. I can help you schedule a consultation.",
            voice="alice",
        )
        
        gather = resp.gather(
            input='speech',
            language='en-US',
            speech_timeout='5',
            action=action_url,
            method='POST'
        )
        
        print(f"→ Greeting Gather created (silent - no question), Action: {action_url}", flush=True)
        
        resp.redirect(action_url)

        twiml_response = str(resp)
        print(f"→ TwiML length: {len(twiml_response)} chars", flush=True)
        print("→ FULL TwiML:", flush=True)
        print(twiml_response, flush=True)
        print("=" * 70 + "\n", flush=True)
        sys.stdout.flush()

        return Response(content=twiml_response, media_type="application/xml")
        
    except Exception as e:
        print(f"\n❌❌❌ ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        
        resp = VoiceResponse()
        resp.say("Sorry, there was an error. Please try again later.", voice="alice")
        resp.hangup()
        return Response(content=str(resp), media_type="application/xml")


@router.post("/twilio/handle-response")
async def twilio_handle_response(request: Request, call_sid: str):
    from fastapi.responses import Response
    from twilio.twiml.voice_response import VoiceResponse
    import sys
    
    sys.stdout.flush()
    
    print("\n" + "=" * 70, flush=True)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🎯 HANDLING RESPONSE", flush=True)
    print(f"CallSid: {call_sid}", flush=True)
    
    try:
        form = await request.form()
        form_dict = dict(form)
        speech_result = form_dict.get("SpeechResult", "")
        
        print(f"SpeechResult: '{speech_result}'", flush=True)
        print("-" * 70, flush=True)
        sys.stdout.flush()
        
        twiml = await handle_caller_response(request, call_sid)
        print("✓ Success", flush=True)
        print("=" * 70 + "\n", flush=True)
        sys.stdout.flush()
        return Response(content=twiml, media_type="application/xml")
    except Exception as e:
        print(f"❌ ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        print("=" * 70 + "\n", flush=True)
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
    except Exception as e:
        print(f"Error handling slot selection: {e}")
        import traceback
        traceback.print_exc()
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
            response.say("I didn't catch that. Please say transfer to speak with someone, or say message to leave a message.", voice='alice')
            from config.settings import settings
            base_url = settings.APP_URL.rstrip('/')
            gather = response.gather(
                input='speech',
                language='en-US',
                speech_timeout='auto',
                action=f'{base_url}/api/twilio/handle-transfer-response?call_sid={call_sid}',
                method='POST'
            )
            gather.say("Please say transfer or message.", voice='alice')
            response.append(gather)
            response.say("Thank you for calling.", voice='alice')
            response.hangup()
        
        return Response(content=str(response), media_type="application/xml")
    except Exception as e:
        print(f"Error handling transfer response: {e}")
        import traceback
        traceback.print_exc()
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
