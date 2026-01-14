import { useState, useEffect } from 'react';
import { apiService, Appointment } from '../services/api';

export default function Appointments() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAppointments = async () => {
      try {
        const data = await apiService.getAppointments();
        setAppointments(data);
      } catch (error) {
        console.error('Failed to load appointments', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAppointments();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Appointments</h2>
        <p className="mt-1 text-sm text-gray-500">All booked appointments</p>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-500">Loading appointments...</p>
        </div>
      ) : appointments.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <p className="text-gray-500">No appointments yet.</p>
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {appointments.map((appointment) => (
              <li key={appointment.id} className="px-4 py-4 sm:px-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium mr-2 ${getStatusColor(
                          appointment.booking_status
                        )}`}
                      >
                        {appointment.booking_status}
                      </span>
                      <h3 className="text-sm font-medium text-gray-900">
                        {appointment.caller.name}
                      </h3>
                    </div>
                    <div className="mt-1 text-sm text-gray-500">
                      {appointment.practice_area} • {appointment.caller.email}
                    </div>
                    <div className="mt-1 text-sm text-gray-900">
                      {new Date(appointment.appointment_date).toLocaleString()}
                    </div>
                  </div>
                  <div className="text-sm text-gray-500">
                    {appointment.confirmation_email_sent ? (
                      <span className="text-green-600">✓ Email sent</span>
                    ) : (
                      <button
                        onClick={() => apiService.sendConfirmationEmail(appointment.id)}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        Send email
                      </button>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

