import React, { useState, useEffect } from 'react';
import { X, Calendar, Clock, Stethoscope, AlertCircle, CheckCircle2, ShieldAlert } from 'lucide-react';
import { api } from '../../services/api';
import { UrgencyBadge } from '../common/Badge';

export const AppointmentBookingModal = ({ isOpen, onClose, onAppointmentBooked, urgencyScore, urgencyLevel }) => {
  if (!isOpen) return null;

  const [doctors, setDoctors] = useState([]);
  const [selectedDoctor, setSelectedDoctor] = useState('');
  const [appointmentDate, setAppointmentDate] = useState('');
  const [appointmentTime, setAppointmentTime] = useState('10:00 AM');
  const [reason, setReason] = useState('Cardiometabolic Risk Consultation & Treatment Plan');
  const [symptomsSummary, setSymptomsSummary] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDoctors = async () => {
      try {
        const data = await api.getDoctors();
        setDoctors(data);
        if (data.length > 0) {
          setSelectedDoctor(data[0].id);
        }
      } catch (err) {
        console.error("Failed to fetch doctors:", err);
      }
    };
    fetchDoctors();

    // Default date to tomorrow
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    setAppointmentDate(tomorrow.toISOString().split('T')[0]);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const payload = {
        doctor_id: selectedDoctor ? parseInt(selectedDoctor) : null,
        appointment_date: appointmentDate,
        appointment_time: appointmentTime,
        reason,
        symptoms_summary: symptomsSummary
      };

      const newAppt = await api.bookAppointment(payload);
      onAppointmentBooked(newAppt);
      onClose();
    } catch (err) {
      console.error("Failed to book appointment:", err);
      setError(err.response?.data?.detail || "Failed to schedule appointment.");
    } finally {
      setLoading(false);
    }
  };

  const timeSlots = [
    '09:00 AM', '09:30 AM', '10:00 AM', '10:30 AM', 
    '11:00 AM', '11:30 AM', '02:00 PM', '02:30 PM', 
    '03:30 PM', '04:15 PM'
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-white w-full max-w-lg rounded-3xl shadow-2xl border border-slate-200 overflow-hidden">
        
        {/* Header */}
        <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-teal-500/20 text-teal-400">
              <Calendar className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold">Book Priority Consultation</h3>
              <p className="text-[11px] text-slate-400">Urgency-triaged scheduling with specialist physician</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Auto-Triage Urgency Notice */}
        <div className="px-6 py-3 bg-teal-50/70 border-b border-teal-100/80 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-teal-900">Assigned Triage Tier:</span>
            <UrgencyBadge level={urgencyLevel || 'Routine'} score={urgencyScore} />
          </div>
          <span className="text-[11px] font-medium text-teal-700">Auto-calculated from survey</span>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Select Attending Physician</label>
            <select
              value={selectedDoctor}
              onChange={(e) => setSelectedDoctor(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs font-medium focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 bg-white"
            >
              {doctors.map(d => (
                <option key={d.id} value={d.id}>
                  {d.full_name} ({d.specialization || 'Clinical Specialist'})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Preferred Date</label>
              <input
                type="date"
                value={appointmentDate}
                onChange={(e) => setAppointmentDate(e.target.value)}
                className="w-full px-3.5 py-2 rounded-xl border border-slate-200 text-xs font-medium focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Available Time Slot</label>
              <select
                value={appointmentTime}
                onChange={(e) => setAppointmentTime(e.target.value)}
                className="w-full px-3.5 py-2 rounded-xl border border-slate-200 text-xs font-medium focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 bg-white"
              >
                {timeSlots.map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Chief Reason for Appointment</label>
            <input
              type="text"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g. Preventive cardiovascular evaluation"
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs font-medium focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Notes for the Doctor (Optional)</label>
            <textarea
              rows="2"
              value={symptomsSummary}
              onChange={(e) => setSymptomsSummary(e.target.value)}
              placeholder="Any current medications or recent acute symptoms..."
              className="w-full px-3.5 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600"
            />
          </div>

          <div className="pt-2 flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-100 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold shadow-md shadow-teal-600/20 transition disabled:opacity-50"
            >
              {loading ? 'Confirming...' : 'Confirm Appointment'}
            </button>
          </div>
        </form>

      </div>
    </div>
  );
};
