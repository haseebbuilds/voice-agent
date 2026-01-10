from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from config.settings import settings
import json
import os

class CalendarService:
    
    def __init__(self):
        self.service = None
        self.calendar_id = settings.GOOGLE_CALENDAR_ID
        
    def _get_service(self):
        if self.service:
            return self.service
        
        if not settings.GOOGLE_CALENDAR_CREDENTIALS:
            raise ValueError("GOOGLE_CALENDAR_CREDENTIALS not configured")
        
        try:
            creds_path = settings.GOOGLE_CALENDAR_CREDENTIALS
            if os.path.exists(creds_path):
                with open(creds_path, 'r') as f:
                    creds_data = json.load(f)
                
                if 'type' in creds_data and creds_data['type'] == 'service_account':
                    credentials = service_account.Credentials.from_service_account_file(
                        creds_path,
                        scopes=['https://www.googleapis.com/auth/calendar']
                    )
                elif 'web' in creds_data or 'installed' in creds_data:
                    error_msg = (
                        "OAuth client secret file provided, but service account JSON required. "
                        "Please create a service account in Google Cloud Console and download the JSON key file. "
                        "See: https://cloud.google.com/iam/docs/service-accounts"
                    )
                    print(f"[ERROR] {error_msg}")
                    raise ValueError(error_msg)
                else:
                    credentials = service_account.Credentials.from_service_account_info(
                        creds_data,
                        scopes=['https://www.googleapis.com/auth/calendar']
                    )
            else:
                creds_dict = json.loads(settings.GOOGLE_CALENDAR_CREDENTIALS)
                credentials = service_account.Credentials.from_service_account_info(
                    creds_dict,
                    scopes=['https://www.googleapis.com/auth/calendar']
                )
            
            self.service = build('calendar', 'v3', credentials=credentials)
            return self.service
        except Exception as e:
            error_msg = f"Could not initialize Google Calendar service: {e}"
            print(f"[ERROR] {error_msg}")
            print(f"[INFO] Calendar operations will use mock slots until service account is configured")
            raise ValueError(error_msg)
    
    async def get_available_slots(self, start_date: datetime, end_date: datetime, duration_minutes: int = 30) -> List[Dict]:
        try:
            service = self._get_service()
            
            freebusy_query = {
                "timeMin": start_date.isoformat() + 'Z',
                "timeMax": end_date.isoformat() + 'Z',
                "items": [{"id": self.calendar_id}]
            }
            
            freebusy_result = service.freebusy().query(body=freebusy_query).execute()
            
            busy_periods = []
            if 'calendars' in freebusy_result and self.calendar_id in freebusy_result['calendars']:
                busy_periods = freebusy_result['calendars'][self.calendar_id].get('busy', [])
            
            available_slots = []
            current = start_date
            
            business_start = 9
            business_end = 17
            
            while current < end_date:
                if business_start <= current.hour < business_end:
                    is_available = True
                    slot_end = current + timedelta(minutes=duration_minutes)
                    
                    for busy in busy_periods:
                        busy_start = datetime.fromisoformat(busy['start'].replace('Z', '+00:00'))
                        busy_end = datetime.fromisoformat(busy['end'].replace('Z', '+00:00'))
                        
                        if (current < busy_end and slot_end > busy_start):
                            is_available = False
                            break
                    
                    if is_available:
                        available_slots.append({
                            "date": current.strftime("%Y-%m-%d"),
                            "time": current.strftime("%H:%M"),
                            "datetime": current.isoformat(),
                            "formatted": current.strftime("%B %d, %Y at %I:%M %p")
                        })
                
                current += timedelta(minutes=30)
                
                if current.hour >= business_end:
                    current = current.replace(hour=business_start, minute=0) + timedelta(days=1)
            
            return available_slots[:10]
            
        except HttpError as e:
            print(f"[WARNING] Google Calendar API error: {e}")
            print(f"[WARNING] Using mock slots for development")
            return self._get_mock_slots(start_date)
        except ValueError as ve:
            print(f"[WARNING] Google Calendar credentials issue: {ve}")
            print(f"[WARNING] Using mock slots for development")
            return self._get_mock_slots(start_date)
        except Exception as e:
            print(f"[WARNING] Error in get_available_slots: {e}")
            import traceback
            traceback.print_exc()
            return self._get_mock_slots(start_date)
    
    def _get_mock_slots(self, start_date: datetime) -> List[Dict]:
        slots = []
        current = start_date.replace(hour=9, minute=0, second=0, microsecond=0)
        
        for i in range(10):
            if current.hour >= 17:
                current = current.replace(hour=9, minute=0) + timedelta(days=1)
            
            slots.append({
                "date": current.strftime("%Y-%m-%d"),
                "time": current.strftime("%H:%M"),
                "datetime": current.isoformat(),
                "formatted": current.strftime("%B %d, %Y at %I:%M %p")
            })
            
            current += timedelta(hours=1)
        
        return slots
    
    async def create_calendar_event(self, appointment_data: Dict) -> Optional[str]:
        try:
            service = self._get_service()
            
            event = {
                'summary': appointment_data.get('title', 'Legal Consultation'),
                'description': appointment_data.get('description', ''),
                'start': {
                    'dateTime': appointment_data['start_time'].isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': appointment_data['end_time'].isoformat(),
                    'timeZone': 'UTC',
                },
                'attendees': appointment_data.get('attendees', []),
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 30},
                    ],
                },
            }
            
            created_event = service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            
            return created_event.get('id')
            
        except HttpError as e:
            print(f"[WARNING] Google Calendar API error creating event: {e}")
            return None
        except ValueError as ve:
            print(f"[WARNING] Google Calendar credentials issue: {ve}")
            print(f"[WARNING] Calendar event not created - appointment will be saved but not synced to Google Calendar")
            return None
        except Exception as e:
            print(f"[WARNING] Error in create_calendar_event: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def check_slot_availability(self, date: datetime, time: datetime) -> bool:
        try:
            service = self._get_service()
            
            freebusy_query = {
                "timeMin": date.isoformat() + 'Z',
                "timeMax": (date + timedelta(minutes=30)).isoformat() + 'Z',
                "items": [{"id": self.calendar_id}]
            }
            
            freebusy_result = service.freebusy().query(body=freebusy_query).execute()
            
            if 'calendars' in freebusy_result and self.calendar_id in freebusy_result['calendars']:
                busy_periods = freebusy_result['calendars'][self.calendar_id].get('busy', [])
                return len(busy_periods) == 0
            
            return True
            
        except Exception as e:
            print(f"Error checking slot availability: {e}")
            return False

calendar_service = CalendarService()

