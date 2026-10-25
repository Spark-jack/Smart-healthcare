import React, { useState, useEffect } from 'react';
import { Activity, Plus, Calendar, Clock, AlertTriangle, FileText, CheckCircle2, RefreshCw, UserCheck, Stethoscope } from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { RiskSummaryCard } from '../components/patient/RiskSummaryCard';
import { HealthSurveyModal } from '../components/patient/HealthSurveyModal';
import { AppointmentBookingModal } from '../components/patient/AppointmentBookingModal';
import { StatusBadge, UrgencyBadge } from '../components/common/Badge';

export const PatientDashboard = () => {
  const { user } = useAuth();
  const [prediction, setPrediction] = useState(null);
  const [surveys, setSurveys] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);

  const [surveyModalOpen, setSurveyModalOpen] = useState(false);
  const [appointmentModalOpen, setAppointmentModalOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      // 1. Fetch latest prediction
      try {
        const pred = await api.getLatestPrediction();
        setPrediction(pred);
      } catch (err) {
        setPrediction(null);
      }

      // 2. Fetch past surveys
      try {
        const survs = await api.getSurveyHistory();
        setSurveys(survs);
      } catch (err) {
        setSurveys([]);
      }

      // 3. Fetch appointments
      try {
        const appts = await api.listAppointments();
        setAppointments(appts);
      } catch (err) {
        setAppointments([]);
      }
    } catch (err) {
      console.error("Error loading patient data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const handleSurveySubmitted = (newPrediction) => {
    setPrediction(newPrediction);
    loadDashboardData();
    showToast("Health survey successfully analyzed! Your risk prediction & SHAP insights have been updated.");
  };

  const handleAppointmentBooked = (newAppt) => {
    setAppointments(prev => [newAppt, ...prev]);
    showToast("Priority appointment confirmed with attending physician.");
  };

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 5000);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 p-4 rounded-2xl bg-slate-900 text-white shadow-2xl border border-teal-500/30 flex items-center gap-3 text-xs max-w-md animate-slide-up">
          <div className="p-1.5 rounded-xl bg-teal-500/20 text-teal-400">
            <CheckCircle2 className="w-4 h-4" />
          </div>
          <span className="font-medium">{toastMessage}</span>
        </div>
      )}

      {/* Top Welcome Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-extrabold text-slate-900">Welcome back, {user?.full_name}</h1>
            <span className="px-2.5 py-0.5 rounded-full bg-teal-50 text-teal-700 text-xs font-bold border border-teal-200">
              Patient Portal
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Track your cardiometabolic health indicators, view explainable AI insights, and book urgency-triaged appointments.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setSurveyModalOpen(true)}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-700 hover:to-emerald-700 text-white text-xs font-bold shadow-md shadow-teal-600/20 transition"
          >
            <Plus className="w-4 h-4" />
            {prediction ? 'Retake Clinical Survey' : 'Take Health Intake Survey'}
          </button>
        </div>
      </div>

      {/* Core Risk Prediction & Explainability Module */}
      {loading ? (
        <div className="p-12 text-center text-slate-400 text-xs">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto text-teal-600 mb-2" />
          Analyzing clinical telemetry & SHAP metrics...
        </div>
      ) : (
        <RiskSummaryCard
          prediction={prediction}
          onOpenAppointmentModal={() => setAppointmentModalOpen(true)}
          onRetakeSurvey={() => setSurveyModalOpen(true)}
        />
      )}

      {/* Two Column Grid: Appointments & Biometric Telemetry History */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Scheduled Appointments (5 cols) */}
        <div className="lg:col-span-5 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-teal-600" />
              <h3 className="text-sm font-bold text-slate-900">My Priority Consultations</h3>
            </div>
            <button
              onClick={() => setAppointmentModalOpen(true)}
              className="text-xs font-bold text-teal-600 hover:text-teal-700"
            >
              + Book New
            </button>
          </div>

          <div className="space-y-3">
            {appointments.length === 0 ? (
              <p className="text-xs text-slate-400 py-6 text-center">No upcoming appointments scheduled.</p>
            ) : (
              appointments.map((appt) => (
                <div key={appt.id} className="p-4 rounded-2xl border border-slate-200/90 hover:border-slate-300 transition bg-slate-50/50">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-bold text-slate-800">{appt.reason}</span>
                    <StatusBadge status={appt.status} />
                  </div>
                  <div className="text-[11px] text-slate-500 flex items-center gap-3">
                    <span className="flex items-center gap-1 font-medium text-slate-700">
                      <Clock className="w-3.5 h-3.5 text-slate-400" />
                      {appt.appointment_date} at {appt.appointment_time}
                    </span>
                    <span>•</span>
                    <span className="text-slate-600 truncate">{appt.doctor_name || 'Attending Physician'}</span>
                  </div>
                  <div className="mt-2.5 pt-2 border-t border-slate-200/60 flex items-center justify-between">
                    <span className="text-[10px] text-slate-400">Assigned Urgency:</span>
                    <UrgencyBadge level={appt.urgency_level} score={appt.urgency_score} />
                  </div>
                  {appt.doctor_notes && (
                    <div className="mt-2 p-2 rounded-lg bg-teal-50 border border-teal-100 text-[11px] text-teal-800">
                      <span className="font-bold">Doctor's Note:</span> {appt.doctor_notes}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Column: Historical Biomarkers Intake Table (7 cols) */}
        <div className="lg:col-span-7 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-teal-600" />
              <h3 className="text-sm font-bold text-slate-900">Health Intake Telemetry History</h3>
            </div>
            <span className="text-xs text-slate-400">{surveys.length} survey records</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-100 text-slate-400 text-[11px] font-semibold uppercase tracking-wider">
                  <th className="pb-2.5">Date</th>
                  <th className="pb-2.5">BP (mmHg)</th>
                  <th className="pb-2.5">Cholesterol</th>
                  <th className="pb-2.5">Glucose</th>
                  <th className="pb-2.5">BMI</th>
                  <th className="pb-2.5">Heart Rate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium text-slate-700">
                {surveys.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="py-6 text-center text-slate-400">
                      No health surveys submitted yet.
                    </td>
                  </tr>
                ) : (
                  surveys.map((s) => (
                    <tr key={s.id} className="hover:bg-slate-50/80 transition">
                      <td className="py-3 text-slate-900 font-semibold">
                        {new Date(s.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-3">{s.systolic_bp}/{s.diastolic_bp}</td>
                      <td className="py-3">{s.total_cholesterol} mg/dL</td>
                      <td className="py-3">{s.fasting_blood_sugar} mg/dL</td>
                      <td className="py-3">{s.bmi}</td>
                      <td className="py-3">{s.max_heart_rate} bpm</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>

      {/* Modals */}
      <HealthSurveyModal
        isOpen={surveyModalOpen}
        onClose={() => setSurveyModalOpen(false)}
        onSurveySubmitted={handleSurveySubmitted}
      />

      <AppointmentBookingModal
        isOpen={appointmentModalOpen}
        onClose={() => setAppointmentModalOpen(false)}
        onAppointmentBooked={handleAppointmentBooked}
        urgencyScore={prediction?.urgency_score || 25}
        urgencyLevel={prediction?.urgency_level || 'Routine'}
      />

    </div>
  );
};
