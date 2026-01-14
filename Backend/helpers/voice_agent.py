from enum import Enum
from typing import Dict, Optional, Any
from models.intake_call import IntakeCall
from models.caller import Caller
from models.case_question import CaseQuestion
from models.appointment import Appointment
from config.lemon_law_questions import LEMON_LAW_QUESTIONS
from config.personal_injury_questions import PERSONAL_INJURY_QUESTIONS
from helpers.validators import (
    validate_email, validate_phone, normalize_phone,
    validate_practice_area, sanitize_input, extract_email
)

class CallState(Enum):
    GREETING = "GREETING"
    PRACTICE_AREA = "PRACTICE_AREA"
    PRACTICE_AREA_CLARIFY = "PRACTICE_AREA_CLARIFY"
    PERSONAL_INFO = "PERSONAL_INFO"
    CONSENT = "CONSENT"
    CASE_QUESTIONS = "CASE_QUESTIONS"
    SHOW_SLOTS = "SHOW_SLOTS"
    CONFIRM_BOOKING = "CONFIRM_BOOKING"
    END_CALL = "END_CALL"

class VoiceAgent:
    
    def __init__(self, intake_call: IntakeCall):
        self.intake_call = intake_call
        self.current_state = CallState(intake_call.current_state)
        self.personal_info = {}
        self.current_field = intake_call.current_field or None
        self.current_question_index = 0
        self.questions = []
        self.selected_slot = None
        
    async def get_next_message(self) -> str:
        if self.current_state == CallState.GREETING:
            return "Hi, this is the automated intake assistant. I can help you schedule a consultation."
        
        elif self.current_state == CallState.PRACTICE_AREA:
            return "Is this about Lemon Law or Personal Injury?"
        
        elif self.current_state == CallState.PRACTICE_AREA_CLARIFY:
            return "I didn't catch that clearly. Is this about Lemon Law, which is for vehicle defects, or Personal Injury, which is for accidents or injuries?"
        
        elif self.current_state == CallState.PERSONAL_INFO:
            if not self.current_field or self.current_field == "name":
                return "To get started, may I have your full name?"
            elif self.current_field == "phone":
                return "What is your phone number?"
            elif self.current_field == "email":
                return "What is your email address?"
            elif self.current_field == "email_confirm":
                pending_email = self.intake_call.pending_email or self.personal_info.get("email", "")
                if pending_email:
                    return f"I heard your email as {pending_email}. Is that correct? Please say yes or no."
                else:
                    return "What is your email address?"
            else:
                return "Thank you. Now I'll ask for your consent to proceed."
        
        elif self.current_state == CallState.CONSENT:
            return "May I proceed to schedule an appointment and ask a few quick questions first?"
        
        elif self.current_state == CallState.CASE_QUESTIONS:
            if not self.questions:
                if self.intake_call.practice_area == "Lemon Law":
                    self.questions = LEMON_LAW_QUESTIONS
                else:
                    self.questions = PERSONAL_INJURY_QUESTIONS
                
                try:
                    answered_records = await CaseQuestion.filter(
                        intake_call=self.intake_call
                    ).all()
                    answered_keys = {r.question_key for r in answered_records}
                    
                    self.current_question_index = len(self.questions)
                    for i, q in enumerate(self.questions):
                        if q["key"] not in answered_keys:
                            self.current_question_index = i
                            break
                except Exception:
                    import traceback
                    traceback.print_exc()
                    self.current_question_index = 0
            
            if self.current_question_index < len(self.questions):
                question = self.questions[self.current_question_index]
                return question["question"]
            else:
                await self._transition_to(CallState.SHOW_SLOTS)
                return await self.get_next_message()
        
        elif self.current_state == CallState.SHOW_SLOTS:
            return "Here are the available time slots. [Slots will be listed here]"
        
        elif self.current_state == CallState.CONFIRM_BOOKING:
            if self.selected_slot:
                return f"I have you scheduled for {self.selected_slot}. Is that correct?"
            return "Please confirm your selected time slot."
        
        elif self.current_state == CallState.END_CALL:
            return "Thank you. You will receive a confirmation email shortly. Have a great day!"
        
        return "How can I help you?"
    
    async def process_response(self, response: str) -> Dict[str, Any]:
        await self._load_caller_info()
        
        response = sanitize_input(response)
        result = {
            "message": "",
            "next_state": None,
            "action": "continue"
        }
        
        field_info = f", current_field={self.current_field}" if self.current_field else ""
        
        if self.current_state == CallState.GREETING:
            
            if not response or not response.strip():
                await self._transition_to(CallState.PRACTICE_AREA)
                result["message"] = await self.get_next_message()
            else:
                practice_area = validate_practice_area(response)
                
                if practice_area:
                    self.intake_call.practice_area = practice_area
                    await self.intake_call.save()
                    await self._transition_to(CallState.PERSONAL_INFO)
                    self.current_field = "name"
                    self.intake_call.current_field = "name"
                    await self.intake_call.save()
                    result["message"] = await self.get_next_message()
                else:
                    await self._transition_to(CallState.PRACTICE_AREA)
                    result["message"] = await self.get_next_message()
        
        elif self.current_state == CallState.PRACTICE_AREA:
            practice_area = validate_practice_area(response)
            if practice_area:
                self.intake_call.practice_area = practice_area
                await self.intake_call.save()
                await self._transition_to(CallState.PERSONAL_INFO)
                self.current_field = "name"
                self.intake_call.current_field = "name"
                await self.intake_call.save()
                result["message"] = await self.get_next_message()
            else:
                response_lower = response.lower()
                if "personal" in response_lower:
                    self.intake_call.practice_area = "Personal Injury"
                    await self.intake_call.save()
                    await self._transition_to(CallState.PERSONAL_INFO)
                    self.current_field = "name"
                    self.intake_call.current_field = "name"
                    await self.intake_call.save()
                    result["message"] = await self.get_next_message()
                elif "lemon" in response_lower:
                    self.intake_call.practice_area = "Lemon Law"
                    await self.intake_call.save()
                    await self._transition_to(CallState.PERSONAL_INFO)
                    self.current_field = "name"
                    self.intake_call.current_field = "name"
                    await self.intake_call.save()
                    result["message"] = await self.get_next_message()
                else:
                    await self._transition_to(CallState.PRACTICE_AREA_CLARIFY)
                    result["message"] = await self.get_next_message()
        
        elif self.current_state == CallState.PRACTICE_AREA_CLARIFY:
            practice_area = validate_practice_area(response)
            if practice_area:
                self.intake_call.practice_area = practice_area
                await self.intake_call.save()
                await self._transition_to(CallState.PERSONAL_INFO)
                self.current_field = "name"
                self.intake_call.current_field = "name"
                await self.intake_call.save()
                result["message"] = await self.get_next_message()
            else:
                response_lower = response.lower()
                if "lemon" in response_lower or "vehicle" in response_lower or "car" in response_lower or "defect" in response_lower:
                    self.intake_call.practice_area = "Lemon Law"
                    await self.intake_call.save()
                    await self._transition_to(CallState.PERSONAL_INFO)
                    self.current_field = "name"
                    self.intake_call.current_field = "name"
                    await self.intake_call.save()
                    result["message"] = await self.get_next_message()
                elif "personal" in response_lower or "injury" in response_lower or "accident" in response_lower or "injured" in response_lower:
                    self.intake_call.practice_area = "Personal Injury"
                    await self.intake_call.save()
                    await self._transition_to(CallState.PERSONAL_INFO)
                    self.current_field = "name"
                    self.intake_call.current_field = "name"
                    await self.intake_call.save()
                    result["message"] = await self.get_next_message()
                else:
                    self.intake_call.practice_area = "Personal Injury"
                    await self.intake_call.save()
                    await self._transition_to(CallState.PERSONAL_INFO)
                    self.current_field = "name"
                    self.intake_call.current_field = "name"
                    await self.intake_call.save()
                    result["message"] = await self.get_next_message()
        
        elif self.current_state == CallState.PERSONAL_INFO:
            if not response or not response.strip():
                if not self.current_field:
                    self.current_field = "name"
                    self.intake_call.current_field = "name"
                    await self.intake_call.save()
                result["message"] = await self.get_next_message()
                return result
            
            if not self.current_field:
                self.current_field = "name"
                self.intake_call.current_field = "name"
                await self.intake_call.save()
            
            if self.current_field == "name":
                cleaned_response = response.strip('?').strip()
                
                if not cleaned_response:
                    result["message"] = "I didn't catch that. Please provide your full name."
                    return result
                
                from helpers.validators import extract_phone_number
                extracted_phone = extract_phone_number(cleaned_response)
                if extracted_phone:
                    result["message"] = "That sounds like a phone number. I need your full name first. Please say your name."
                    return result
                
                if not any(c.isalpha() for c in cleaned_response):
                    result["message"] = "I need your full name, not just numbers. Please say your name."
                    return result
                
                self.personal_info["full_name"] = cleaned_response
                validated_input = cleaned_response
                
                try:
                    if self.intake_call.caller_id:
                        caller = await Caller.get(id=self.intake_call.caller_id)
                        if hasattr(caller, 'email') and ('temp_' in str(caller.email) or '@temp.com' in str(caller.email)):
                            caller = await Caller.create(
                                full_name=validated_input,
                                phone="",
                                email=f"pending_{self.intake_call.twilio_call_sid}@temp.com"
                            )
                            self.intake_call.caller = caller
                            await self.intake_call.save()
                        else:
                            caller.full_name = validated_input
                            await caller.save()
                    else:
                        caller = await Caller.create(
                            full_name=validated_input,
                            phone="",
                            email=f"pending_{self.intake_call.twilio_call_sid}@temp.com"
                        )
                        self.intake_call.caller = caller
                        await self.intake_call.save()
                except Exception:
                    import traceback
                    traceback.print_exc()
                self.current_field = "phone"
                self.intake_call.current_field = "phone"
                await self.intake_call.save()
                result["message"] = await self.get_next_message()
                
            elif self.current_field == "phone":
                from helpers.validators import extract_phone_number, validate_phone
                
                extracted_phone = extract_phone_number(response)
                
                if not extracted_phone or not validate_phone(extracted_phone):
                    result["message"] = "I didn't catch a valid phone number. Please say your phone number clearly, including the country code. For example, plus 9 2 3 3 3 1 2 3 4 5 6 7."
                    return result
                
                validated_input = extracted_phone
                self.personal_info["phone"] = validated_input
                
                try:
                    if self.intake_call.caller_id:
                        caller = await Caller.get(id=self.intake_call.caller_id)
                        caller.phone = validated_input
                        if "full_name" in self.personal_info:
                            caller.full_name = self.personal_info["full_name"]
                        await caller.save()
                    else:
                        caller = await Caller.create(
                            full_name=self.personal_info.get("full_name", ""),
                            phone=validated_input,
                            email=f"pending_{self.intake_call.twilio_call_sid}@temp.com"
                        )
                        self.intake_call.caller = caller
                        await self.intake_call.save()
                except Exception:
                    import traceback
                    traceback.print_exc()
                self.current_field = "email"
                self.intake_call.current_field = "email"
                await self.intake_call.save()
                result["message"] = await self.get_next_message()
                
            elif self.current_field == "email":
                extracted_email = extract_email(response)
                
                if not extracted_email:
                    result["message"] = "I didn't catch a valid email address. Please say your email address clearly, like: muhammadhassib at gmail dot com."
                    return result
                
                validated_input = extracted_email
                self.personal_info["email"] = validated_input
                self.intake_call.pending_email = validated_input
                await self.intake_call.save()
                
                self.current_field = "email_confirm"
                self.intake_call.current_field = "email_confirm"
                await self.intake_call.save()
                result["message"] = await self.get_next_message()
                
            elif self.current_field == "email_confirm":
                pending_email = self.intake_call.pending_email or self.personal_info.get("email", "")
                confirmation_response = response.lower().strip()
                
                if "yes" in confirmation_response or "correct" in confirmation_response or "right" in confirmation_response:
                    validated_input = pending_email
                    
                    try:
                        if self.intake_call.caller_id:
                            caller = await Caller.get(id=self.intake_call.caller_id)
                            if 'temp_' in str(caller.email) or '@temp.com' in str(caller.email):
                                caller, _ = await Caller.get_or_create(
                                    email=validated_input,
                                    defaults={
                                        "full_name": self.personal_info.get("full_name", ""),
                                        "phone": self.personal_info.get("phone", "")
                                    }
                                )
                                if not caller.full_name and self.personal_info.get("full_name"):
                                    caller.full_name = self.personal_info["full_name"]
                                if not caller.phone and self.personal_info.get("phone"):
                                    caller.phone = self.personal_info["phone"]
                                await caller.save()
                            else:
                                caller.email = validated_input
                                if "full_name" in self.personal_info:
                                    caller.full_name = self.personal_info["full_name"]
                                if "phone" in self.personal_info:
                                    caller.phone = self.personal_info["phone"]
                                await caller.save()
                        else:
                            caller, _ = await Caller.get_or_create(
                                email=validated_input,
                                defaults={
                                    "full_name": self.personal_info.get("full_name", ""),
                                    "phone": self.personal_info.get("phone", "")
                                }
                            )
                            if not caller.full_name and self.personal_info.get("full_name"):
                                caller.full_name = self.personal_info["full_name"]
                            if not caller.phone and self.personal_info.get("phone"):
                                caller.phone = self.personal_info["phone"]
                            await caller.save()
                        
                        self.intake_call.caller = caller
                        self.intake_call.pending_email = None
                        await self.intake_call.save()
                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                    
                    self.current_field = None
                    self.intake_call.current_field = None
                    await self.intake_call.save()
                    await self._transition_to(CallState.CONSENT)
                    result["message"] = await self.get_next_message()
                elif "no" in confirmation_response or "wrong" in confirmation_response or "incorrect" in confirmation_response:
                    self.intake_call.pending_email = None
                    self.current_field = "email"
                    self.intake_call.current_field = "email"
                    await self.intake_call.save()
                    if "email" in self.personal_info:
                        del self.personal_info["email"]
                    result["message"] = "No problem. Please say your email address again clearly."
                else:
                    result["message"] = await self.get_next_message()
            
            else:
                self.current_field = "name"
                self.intake_call.current_field = "name"
                await self.intake_call.save()
                result["message"] = await self.get_next_message()
        
        elif self.current_state == CallState.CONSENT:
            if "no" in response.lower() or "not now" in response.lower() or "later" in response.lower():
                result["action"] = "transfer"
                result["message"] = "I understand. Would you like me to transfer you to a human representative, or would you prefer to leave a message and have someone call you back?"
            elif "yes" in response.lower() or "sure" in response.lower() or "okay" in response.lower() or "ok" in response.lower() or "yes please" in response.lower():
                self.intake_call.consent_to_book = True
                await self.intake_call.save()
                await self._transition_to(CallState.CASE_QUESTIONS)
                result["message"] = await self.get_next_message()
            else:
                result["message"] = "I didn't catch that. May I proceed to schedule an appointment and ask a few quick questions first? Please say yes or no."
        
        elif self.current_state == CallState.CASE_QUESTIONS:
            if not self.questions:
                if self.intake_call.practice_area == "Lemon Law":
                    self.questions = LEMON_LAW_QUESTIONS
                else:
                    self.questions = PERSONAL_INJURY_QUESTIONS
                
                try:
                    answered_records = await CaseQuestion.filter(
                        intake_call=self.intake_call
                    ).all()
                    answered_keys = {r.question_key for r in answered_records}
                    
                    self.current_question_index = len(self.questions)
                    for i, q in enumerate(self.questions):
                        if q["key"] not in answered_keys:
                            self.current_question_index = i
                            break
                except Exception:
                    import traceback
                    traceback.print_exc()
                    self.current_question_index = 0
            
            if self.current_question_index >= len(self.questions):
                await self._transition_to(CallState.SHOW_SLOTS)
                result["message"] = await self.get_next_message()
                return result
            
            if self.current_question_index >= len(self.questions):
                await self._transition_to(CallState.SHOW_SLOTS)
                result["message"] = await self.get_next_message()
                return result
            
            question = self.questions[self.current_question_index]
            
            if not response or response.strip() == "":
                result["message"] = question["question"] + " Please provide your answer."
                return result
            
            try:
                existing_answer = await CaseQuestion.get_or_none(
                    intake_call=self.intake_call,
                    question_key=question["key"]
                )
                
                if existing_answer:
                    self.current_question_index += 1
                    
                    if self.current_question_index < len(self.questions):
                        result["message"] = await self.get_next_message()
                    else:
                        await self._transition_to(CallState.SHOW_SLOTS)
                        result["message"] = await self.get_next_message()
                    return result
            except Exception:
                pass
            
            try:
                case_question, created = await CaseQuestion.get_or_create(
                    intake_call=self.intake_call,
                    question_key=question["key"],
                    defaults={
                        "question_text": question["question"],
                        "answer": response,
                        "practice_area": self.intake_call.practice_area
                    }
                )
                
                if not created:
                    case_question.answer = response
                    case_question.question_text = question["question"]
                    await case_question.save()
                
                self.current_question_index += 1
                
                if self.current_question_index < len(self.questions):
                    result["message"] = await self.get_next_message()
                else:
                    await self._transition_to(CallState.SHOW_SLOTS)
                    result["message"] = await self.get_next_message()
            except Exception:
                import traceback
                traceback.print_exc()
                result["message"] = question["question"] + " Please try again."
        
        elif self.current_state == CallState.SHOW_SLOTS:
            result["message"] = "Please select a time slot."
        
        elif self.current_state == CallState.CONFIRM_BOOKING:
            if "yes" in response.lower() or "correct" in response.lower():
                await self._transition_to(CallState.END_CALL)
                result["message"] = await self.get_next_message()
                result["action"] = "end"
            else:
                result["message"] = "Let me show you the available slots again."
                await self._transition_to(CallState.SHOW_SLOTS)
        
        return result
    
    async def _load_caller_info(self):
        if self.current_state == CallState.PERSONAL_INFO:
            self.personal_info = {}
            return
        
        try:
            if hasattr(self.intake_call, 'caller_id') and self.intake_call.caller_id:
                try:
                    await self.intake_call.fetch_related('caller')
                    if hasattr(self.intake_call, 'caller') and self.intake_call.caller:
                        caller = self.intake_call.caller
                        if hasattr(caller, 'email') and caller.email and 'temp_' not in caller.email and '@temp.com' not in caller.email:
                            if hasattr(caller, 'full_name') and caller.full_name and caller.full_name not in ["Temporary", "Temporary Caller"]:
                                self.personal_info["full_name"] = caller.full_name
                            if hasattr(caller, 'phone') and caller.phone and caller.phone.strip():
                                self.personal_info["phone"] = caller.phone
                            if hasattr(caller, 'email') and caller.email and '@temp.com' not in caller.email:
                                self.personal_info["email"] = caller.email
                except Exception as fetch_error:
                    pass
        except Exception as e:
            pass
    
    async def _transition_to(self, new_state: CallState):
        self.current_state = new_state
        self.intake_call.current_state = new_state.value
        await self.intake_call.save()
    
    async def end_call(self):
        self.intake_call.call_status = "completed"
        await self._transition_to(CallState.END_CALL)
        await self.intake_call.save()

