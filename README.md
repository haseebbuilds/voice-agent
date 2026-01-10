# Voice Intake Agent - Legal Intake System

A complete voice-based legal intake system that answers calls, collects case information, and books appointments automatically.

## Features

- Voice Call Handling: Automated call answering and processing via Twilio
- Intake Forms: Collects practice area information (Lemon Law / Personal Injury)
- Case Questions: Dynamic question sets based on practice area
- Calendar Integration: Google Calendar integration for appointment booking
- Email Confirmation: Automatic confirmation emails sent to callers
- Dashboard: React frontend to view calls, appointments, and settings

## Tech Stack

### Backend
- Python 3.10+
- FastAPI - REST API framework
- Tortoise ORM - Async ORM for PostgreSQL
- PostgreSQL - Database
- Twilio - Voice call handling
- Deepgram - Speech-to-Text
- ElevenLabs - Text-to-Speech
- Google Calendar API - Calendar integration
- Gmail SMTP - Email sending

### Frontend
- React 19 - UI library
- TypeScript - Type safety
- Vite - Build tool
- TailwindCSS - Styling
- React Router - Navigation

## Project Structure

```
Shah-project/
├── Backend/
│   ├── config/          # Configuration files
│   ├── controllers/     # Request handlers
│   ├── models/          # Database models
│   ├── helpers/         # Helper functions
│   ├── routes/          # API routes
│   ├── main.py          # FastAPI app
│   └── requirements.txt
└── Frontend/
    ├── src/
    │   ├── components/  # React components
    │   ├── pages/       # Page components
    │   ├── services/    # API services
    │   ├── App.tsx
    │   └── main.tsx
    └── package.json
```

## Setup Instructions

### Backend Setup

1. Navigate to Backend directory:
```bash
cd Backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file and configure environment variables:
```env
DATABASE_URL=postgres://user:password@localhost:5432/voice_intake
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890
DEEPGRAM_API_KEY=your_deepgram_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
GOOGLE_CALENDAR_CREDENTIALS=path/to/credentials.json
GOOGLE_CALENDAR_ID=primary
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
SENDER_NAME=Legal Intake Team
APP_URL=http://localhost:8000
DEBUG=True
```

5. Initialize database:
```bash
aerich init -t config.database.TORTOISE_ORM
aerich init-db
```

6. Run migrations (if needed):
```bash
aerich upgrade
```

7. Start the server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to Frontend directory:
```bash
cd Frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env` file:
```env
VITE_API_URL=http://localhost:8000
```

4. Start development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Environment Variables

### Backend (.env)

- `DATABASE_URL` - PostgreSQL connection string
- `TWILIO_ACCOUNT_SID` - Twilio account SID
- `TWILIO_AUTH_TOKEN` - Twilio auth token
- `TWILIO_PHONE_NUMBER` - Twilio phone number
- `DEEPGRAM_API_KEY` - Deepgram API key for speech-to-text
- `ELEVENLABS_API_KEY` - ElevenLabs API key for text-to-speech
- `GOOGLE_CALENDAR_CREDENTIALS` - Path to Google Calendar service account JSON
- `GOOGLE_CALENDAR_ID` - Google Calendar ID
- `SENDER_EMAIL` - Email address for sending confirmations
- `SENDER_PASSWORD` - Email app password
- `SENDER_NAME` - Email sender display name
- `APP_URL` - Application URL (for webhooks)
- `DEBUG` - Debug mode (True/False)

### Frontend (.env)

- `VITE_API_URL` - Backend API URL

## API Endpoints

### Twilio Webhooks
- `POST /api/twilio/webhook` - Handle incoming calls
- `POST /api/twilio/handle-response` - Handle caller responses
- `POST /api/twilio/handle-slot-selection` - Handle slot selection

### Calls
- `GET /api/calls/{call_id}` - Get call details
- `GET /api/calls/{call_id}/state` - Get current call state

### Calendar
- `GET /api/calendar/availability` - Get available time slots

### Appointments
- `GET /api/appointments/{appointment_id}` - Get appointment details
- `POST /api/email/send-confirmation` - Send confirmation email

## Call Flow

1. Greeting - Initial greeting message
2. Practice Area - Select Lemon Law or Personal Injury
3. Personal Info - Collect name, phone, email
4. Consent - Ask permission to proceed
5. Case Questions - Ask practice-area specific questions
6. Show Slots - Display available time slots
7. Confirm Booking - Confirm selected slot
8. End Call - Send confirmation email and end call

## Database Models

- Caller - Caller personal information
- IntakeCall - Call tracking and state
- CaseQuestion - Answers to practice area questions
- Appointment - Booked appointments
- CalendarEvent - Calendar event records

## Practice Area Questions

### Lemon Law
1. Vehicle year, make, and model
2. Purchase/lease date
3. Registration state
4. Vehicle problems
5. Repair attempts
6. Days in shop
7. Has repair invoices/receipts

### Personal Injury
1. Incident type
2. Incident date
3. Incident location
4. Injuries description
5. Medical treatment
6. Police report
7. Insurance involved

## Development

### Running Backend
```bash
cd Backend
python main.py
```

### Running Frontend
```bash
cd Frontend
npm run dev
```

### Database Migrations
```bash
cd Backend
aerich upgrade
```

## Testing

To test the system:
1. Configure Twilio phone number webhook to point to `/api/twilio/webhook`
2. Make a test call to your Twilio number
3. Follow the voice prompts
4. Check the dashboard for call records and appointments

