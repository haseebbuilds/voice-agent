import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Call {
  id: number;
  twilio_call_sid: string;
  practice_area: string;
  call_status: string;
  current_state: string;
  consent_to_book: boolean;
  created_at: string;
}

export interface Appointment {
  id: number;
  caller: {
    name: string;
    email: string;
    phone: string;
  };
  practice_area: string;
  appointment_date: string;
  appointment_time: string;
  booking_status: string;
  confirmation_email_sent: boolean;
}

export interface CalendarSlot {
  date: string;
  time: string;
  datetime: string;
  formatted: string;
}

export const apiService = {
  getCall: async (callId: number): Promise<Call> => {
    const response = await api.get(`/api/calls/${callId}`);
    return response.data;
  },

  getCallState: async (callId: number) => {
    const response = await api.get(`/api/calls/${callId}/state`);
    return response.data;
  },

  getAvailability: async (daysAhead: number = 14): Promise<{ available_slots: CalendarSlot[] }> => {
    const response = await api.get(`/api/calendar/availability?days_ahead=${daysAhead}`);
    return response.data;
  },

  getAppointment: async (appointmentId: number): Promise<Appointment> => {
    const response = await api.get(`/api/appointments/${appointmentId}`);
    return response.data;
  },

  sendConfirmationEmail: async (appointmentId: number) => {
    const response = await api.post(`/api/email/send-confirmation`, null, {
      params: { appointment_id: appointmentId },
    });
    return response.data;
  },
};

export default api;

