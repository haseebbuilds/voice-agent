import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { apiService, Call } from '../services/api';

export default function CallDetails() {
  const { callId } = useParams<{ callId: string }>();
  const [call, setCall] = useState<Call | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (callId) {
      apiService
        .getCall(parseInt(callId))
        .then(setCall)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [callId]);

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p className="mt-2 text-gray-500">Loading call details...</p>
      </div>
    );
  }

  if (!call) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Call not found</p>
      </div>
    );
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Call Details</h2>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
          <div>
            <dt className="text-sm font-medium text-gray-500">Call SID</dt>
            <dd className="mt-1 text-sm text-gray-900">{call.twilio_call_sid}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Practice Area</dt>
            <dd className="mt-1 text-sm text-gray-900">{call.practice_area || 'N/A'}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Call Status</dt>
            <dd className="mt-1 text-sm text-gray-900">{call.call_status}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Current State</dt>
            <dd className="mt-1 text-sm text-gray-900">{call.current_state}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Consent to Book</dt>
            <dd className="mt-1 text-sm text-gray-900">
              {call.consent_to_book ? 'Yes' : 'No'}
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Created At</dt>
            <dd className="mt-1 text-sm text-gray-900">
              {new Date(call.created_at).toLocaleString()}
            </dd>
          </div>
        </dl>
      </div>
    </div>
  );
}

