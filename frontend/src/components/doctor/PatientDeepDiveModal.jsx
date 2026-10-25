import React, { useState, useEffect } from 'react';
import { X, Activity, Heart, Shield, AlertOctagon, User, Phone, Mail, Calendar, FileText, CheckCircle2, TrendingUp, Sparkles } from 'lucide-react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, BarChart, Bar, Cell, ReferenceLine } from 'recharts';
import { api } from '../../services/api';
import { RiskBadge, UrgencyBadge, StatusBadge } from '../common/Badge';

export const PatientDeepDiveModal = ({ patientId, isOpen, onClose, onRefreshQueue }) => {
  if (!isOpen || !patientId) return null;

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('clinical'); // 'clinical' | 'shap' | 'history'
  const [doctorNote, setDoctorNote] = useState('');
  const [selectedApptId, setSelectedApptId] = useState(null);
  const [updatingAppt, setUpdatingAppt] = useState(false);

  useEffect(() => {
    const fetchPatientData = async () => {
      setLoading(true);
      try {
        const res = await api.getPatientDeepDive(patientId);
        setData(res);
        if (res.appointments && res.appointments.length > 0) {
          setSelectedApptId(res.appointments[0].id);
          setDoctorNote(res.appointments[0].notes || '');
        }
      } catch (err) {
        console.error("Failed to fetch patient deep-dive:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchPatientData();
  }, [patientId]);

  const handleUpdateStatus = async (status) => {
    if (!selectedApptId) return;
    setUpdatingAppt(true);
    try {
      await api.updateAppointmentStatus(selectedApptId, {
        status,
        doctor_notes: doctorNote
      });
      // Refresh local data
      const refreshed = await api.getPatientDeepDive(patientId);
      setData(refreshed);
      if (onRefreshQueue) onRefreshQueue();
    } catch (err) {
      console.error("Failed to update status:", err);
    } finally {
      setUpdatingAppt(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-white w-full max-w-4xl rounded-3xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[92vh]">
        
        {/* Header */}
        <div className="px-6 py-5 bg-slate-900 text-white flex items-center justify-between border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-teal-500/20 border border-teal-500/30 flex items-center justify-center text-teal-400 font-bold text-base">
              {data?.patient?.name?.charAt(0) || 'P'}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white">{data?.patient?.name || 'Loading Patient...'}</h3>
                {data?.latest_prediction && (
                  <RiskBadge category={data.latest_prediction.overall_risk_category} score={data.latest_prediction.overall_risk_score} />
                )}
                {data?.latest_prediction && (
                  <UrgencyBadge level={data.latest_prediction.urgency_level} score={data.latest_prediction.urgency_score} />
                )}
              </div>
              <div className="flex items-center gap-4 text-xs text-slate-400 mt-1">
                <span className="flex items-center gap-1"><Mail className="w-3.5 h-3.5" /> {data?.patient?.email}</span>
                {data?.patient?.phone && (
                  <span className="flex items-center gap-1"><Phone className="w-3.5 h-3.5" /> {data?.patient?.phone}</span>
                )}
              </div>
            </div>
          </div>

          <button onClick={onClose} className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Strip */}
        <div className="flex border-b border-slate-200 bg-slate-50 px-6 gap-6 text-xs font-semibold">
          {[
            { id: 'clinical', label: 'Biometrics & Risk Breakdown' },
            { id: 'shap', label: 'SHAP Feature Attributions' },
            { id: 'history', label: 'Longitudinal Trajectory & Appointments' },
          ].map(t => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`py-3.5 border-b-2 transition-all ${
                activeTab === t.id
                  ? 'border-teal-600 text-teal-800 font-bold'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {loading ? (
            <div className="py-16 text-center text-slate-400 text-xs">
              <Activity className="w-8 h-8 animate-spin mx-auto text-teal-600 mb-2" />
              Loading Clinical Patient Record...
            </div>
          ) : data ? (
            <>
              {/* TAB 1: Biometrics & Risk Overview */}
              {activeTab === 'clinical' && (
                <div className="space-y-6">
                  {/* Vitals Summary Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
                    <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80">
                      <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Blood Pressure</span>
                      <div className="text-base font-extrabold text-slate-800 mt-0.5">{data.latest_vitals.blood_pressure || 'N/A'}</div>
                    </div>
                    <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80">
                      <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Serum Cholesterol</span>
                      <div className="text-base font-extrabold text-slate-800 mt-0.5">{data.latest_vitals.cholesterol || 'N/A'}</div>
                    </div>
                    <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80">
                      <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Fasting Glucose</span>
                      <div className="text-base font-extrabold text-slate-800 mt-0.5">{data.latest_vitals.fasting_glucose || 'N/A'}</div>
                    </div>
                    <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80">
                      <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Body Mass Index</span>
                      <div className="text-base font-extrabold text-slate-800 mt-0.5">{data.latest_vitals.bmi || 'N/A'} kg/m²</div>
                    </div>
                  </div>

                  {/* Dual Disease Risk Meters */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="p-5 rounded-2xl border border-slate-200 bg-white">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <Heart className="w-4 h-4 text-rose-500" />
                          <h4 className="text-xs font-bold text-slate-800">Cardiovascular Risk Score</h4>
                        </div>
                        <RiskBadge category={data.latest_prediction.cardio.category} />
                      </div>
                      <div className="text-2xl font-black text-slate-900 mb-2">
                        {data.latest_prediction.cardio.score}%
                      </div>
                      <p className="text-[11px] text-slate-600">
                        {data.latest_prediction.cardio.shap?.summary_insight || 'Risk evaluation complete.'}
                      </p>
                    </div>

                    <div className="p-5 rounded-2xl border border-slate-200 bg-white">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <Activity className="w-4 h-4 text-teal-600" />
                          <h4 className="text-xs font-bold text-slate-800">Diabetes Risk Score</h4>
                        </div>
                        <RiskBadge category={data.latest_prediction.diabetes.category} />
                      </div>
                      <div className="text-2xl font-black text-slate-900 mb-2">
                        {data.latest_prediction.diabetes.score}%
                      </div>
                      <p className="text-[11px] text-slate-600">
                        {data.latest_prediction.diabetes.shap?.summary_insight || 'Risk evaluation complete.'}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: SHAP Feature Attributions */}
              {activeTab === 'shap' && (
                <div className="space-y-6">
                  {/* Cardio SHAP Table */}
                  <div className="border border-slate-200 rounded-2xl overflow-hidden bg-white">
                    <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-800 flex items-center gap-2">
                        <Heart className="w-4 h-4 text-rose-500" />
                        Cardiovascular Disease Driving Factors (SHAP TreeExplainer)
                      </span>
                    </div>
                    <div className="p-4 space-y-2.5">
                      {data.latest_prediction.cardio.shap?.top_factors?.map((f, i) => (
                        <div key={i} className="flex items-center justify-between text-xs p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                          <div>
                            <span className="font-bold text-slate-800">{f.feature_label}</span>
                            <span className="text-slate-400 ml-2">(Recorded: {f.feature_value})</span>
                            <p className="text-[11px] text-slate-500 mt-0.5">{f.interpretation}</p>
                          </div>
                          <span className={`font-bold px-2.5 py-1 rounded-lg text-xs ${
                            f.impact === 'increases_risk' ? 'bg-rose-50 text-rose-700' : 'bg-emerald-50 text-emerald-700'
                          }`}>
                            {f.shap_value > 0 ? '+' : ''}{(f.shap_value * 100).toFixed(1)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Diabetes SHAP Table */}
                  <div className="border border-slate-200 rounded-2xl overflow-hidden bg-white">
                    <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-800 flex items-center gap-2">
                        <Activity className="w-4 h-4 text-teal-600" />
                        Diabetes Metabolic Driving Factors (SHAP TreeExplainer)
                      </span>
                    </div>
                    <div className="p-4 space-y-2.5">
                      {data.latest_prediction.diabetes.shap?.top_factors?.map((f, i) => (
                        <div key={i} className="flex items-center justify-between text-xs p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                          <div>
                            <span className="font-bold text-slate-800">{f.feature_label}</span>
                            <span className="text-slate-400 ml-2">(Recorded: {f.feature_value})</span>
                            <p className="text-[11px] text-slate-500 mt-0.5">{f.interpretation}</p>
                          </div>
                          <span className={`font-bold px-2.5 py-1 rounded-lg text-xs ${
                            f.impact === 'increases_risk' ? 'bg-rose-50 text-rose-700' : 'bg-emerald-50 text-emerald-700'
                          }`}>
                            {f.shap_value > 0 ? '+' : ''}{(f.shap_value * 100).toFixed(1)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 3: Longitudinal Risk Trajectory & Notes */}
              {activeTab === 'history' && (
                <div className="space-y-6">
                  {/* Recharts Longitudinal Risk Trajectory */}
                  <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200">
                    <h4 className="text-xs font-bold text-slate-800 mb-3 flex items-center gap-2">
                      <TrendingUp className="w-4 h-4 text-teal-600" />
                      Longitudinal Patient Risk Trajectory Over Time
                    </h4>
                    <div className="h-48 w-full">
                      {data.trajectory && data.trajectory.length > 0 ? (
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={data.trajectory}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                            <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748b' }} />
                            <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#64748b' }} />
                            <Tooltip />
                            <Line type="monotone" dataKey="cardio_risk" name="Cardiovascular Risk %" stroke="#ef4444" strokeWidth={2} dot={{ r: 4 }} />
                            <Line type="monotone" dataKey="diabetes_risk" name="Diabetes Risk %" stroke="#0d9488" strokeWidth={2} dot={{ r: 4 }} />
                            <Line type="monotone" dataKey="urgency_score" name="Urgency Score" stroke="#8b5cf6" strokeWidth={2} strokeDasharray="4 4" dot={{ r: 3 }} />
                          </LineChart>
                        </ResponsiveContainer>
                      ) : (
                        <div className="h-full flex items-center justify-center text-xs text-slate-400">
                          Single survey baseline recorded. Longitudinal trend will plot as new surveys arrive.
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Doctor Clinical Notes and Appointment Status */}
                  <div className="p-4 bg-white rounded-2xl border border-slate-200 space-y-3">
                    <h4 className="text-xs font-bold text-slate-800 flex items-center gap-2">
                      <FileText className="w-4 h-4 text-teal-600" />
                      Doctor Consultation Notes & Triage Decision
                    </h4>
                    
                    {data.appointments && data.appointments.length > 0 ? (
                      <div className="space-y-3">
                        <div className="flex items-center gap-2 text-xs">
                          <span className="font-semibold text-slate-700">Scheduled:</span>
                          <span className="text-slate-900 font-bold">{data.appointments[0].date} at {data.appointments[0].time}</span>
                          <StatusBadge status={data.appointments[0].status} />
                        </div>

                        <textarea
                          rows="3"
                          value={doctorNote}
                          onChange={(e) => setDoctorNote(e.target.value)}
                          placeholder="Record physician clinical notes, diagnostic orders, or prescription guidance..."
                          className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600"
                        />

                        <div className="flex items-center justify-between pt-1">
                          <span className="text-[11px] text-slate-400">Update appointment clinical status:</span>
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleUpdateStatus('Confirmed')}
                              disabled={updatingAppt}
                              className="px-3 py-1.5 rounded-lg bg-teal-50 text-teal-700 hover:bg-teal-100 text-xs font-semibold border border-teal-200"
                            >
                              Confirm
                            </button>
                            <button
                              onClick={() => handleUpdateStatus('Completed')}
                              disabled={updatingAppt}
                              className="px-3 py-1.5 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 text-xs font-semibold border border-blue-200"
                            >
                              Mark Completed
                            </button>
                            <button
                              onClick={() => handleUpdateStatus('Cancelled')}
                              disabled={updatingAppt}
                              className="px-3 py-1.5 rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 text-xs font-semibold"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <p className="text-xs text-slate-400">No scheduled appointments for this patient yet.</p>
                    )}
                  </div>
                </div>
              )}
            </>
          ) : null}
        </div>

      </div>
    </div>
  );
};
