import React, { useState, useEffect } from 'react';
import { 
  Users, AlertOctagon, Heart, Activity, Search, Filter, 
  ArrowUpDown, ExternalLink, Calendar, BarChart2, ShieldAlert, 
  RefreshCw, TrendingUp, CheckCircle, Clock, LineChart as LineChartIcon
} from 'lucide-react';
import { 
  ResponsiveContainer, BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, 
  CartesianGrid, Legend 
} from 'recharts';
import { api } from '../services/api';
import { AlertBanner } from '../components/doctor/AlertBanner';
import { PatientDeepDiveModal } from '../components/doctor/PatientDeepDiveModal';
import { RiskBadge, UrgencyBadge } from '../components/common/Badge';

export const DoctorDashboard = () => {
  const [queue, setQueue] = useState([]);
  const [population, setPopulation] = useState(null);
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(true);
  const [trendsLoading, setTrendsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterUrgency, setFilterUrgency] = useState('ALL');
  
  // Demographic and Trend Filters
  const [trendPeriod, setTrendPeriod] = useState('month');
  const [filterAgeGroup, setFilterAgeGroup] = useState('ALL');
  const [filterSex, setFilterSex] = useState('ALL');

  const [selectedPatientId, setSelectedPatientId] = useState(null);
  const [deepDiveOpen, setDeepDiveOpen] = useState(false);

  const loadDoctorData = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filterAgeGroup !== 'ALL') params.age_group = filterAgeGroup;
      if (filterSex !== 'ALL') params.sex = filterSex;

      const [queueData, popData] = await Promise.all([
        api.getTriageQueue(),
        api.getPopulationInsights(params)
      ]);
      setQueue(queueData);
      setPopulation(popData);
    } catch (err) {
      console.error("Failed to fetch doctor dashboard data:", err);
    } finally {
      setLoading(false);
    }
  };

  const loadTrendData = async () => {
    setTrendsLoading(true);
    try {
      const params = { period: trendPeriod };
      if (filterAgeGroup !== 'ALL') params.age_group = filterAgeGroup;
      if (filterSex !== 'ALL') params.sex = filterSex;

      const trendRes = await api.getPopulationTrends(params);
      setTrends(trendRes?.trends || []);
    } catch (err) {
      console.error("Failed to load population trend data:", err);
      setTrends([]);
    } finally {
      setTrendsLoading(false);
    }
  };

  useEffect(() => {
    loadDoctorData();
  }, [filterAgeGroup, filterSex]);

  useEffect(() => {
    loadTrendData();
  }, [trendPeriod, filterAgeGroup, filterSex]);

  const handleOpenDeepDive = (patientId) => {
    setSelectedPatientId(patientId);
    setDeepDiveOpen(true);
  };

  // Filtered queue
  const filteredQueue = queue.filter(item => {
    const matchesSearch = item.patient_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          item.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesUrgency = filterUrgency === 'ALL' || item.urgency_level === filterUrgency;
    return matchesSearch && matchesUrgency;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      
      {/* Alert Banner for Critical Patients */}
      <AlertBanner
        alerts={population?.recent_alerts || []}
        onSelectPatient={handleOpenDeepDive}
      />

      {/* Top Clinical Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        <div className="bg-white p-5 rounded-3xl border border-slate-200/90 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Active Patient Cohort</span>
            <div className="text-2xl font-black text-slate-900 mt-1">{population?.total_patients || 0}</div>
            <span className="text-[11px] text-teal-600 font-semibold">Triage monitored</span>
          </div>
          <div className="p-3 rounded-2xl bg-teal-50 text-teal-600">
            <Users className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-3xl border border-slate-200/90 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">High Risk Flagged</span>
            <div className="text-2xl font-black text-rose-600 mt-1">{population?.high_risk_count || 0}</div>
            <span className="text-[11px] text-rose-500 font-semibold">&gt;65% disease probability</span>
          </div>
          <div className="p-3 rounded-2xl bg-rose-50 text-rose-600">
            <AlertOctagon className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-3xl border border-slate-200/90 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Critical/High Urgency</span>
            <div className="text-2xl font-black text-amber-600 mt-1">{population?.critical_triage_count || 0}</div>
            <span className="text-[11px] text-amber-600 font-semibold">Needs 24-72h consult</span>
          </div>
          <div className="p-3 rounded-2xl bg-amber-50 text-amber-600">
            <Clock className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-3xl border border-slate-200/90 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Mean Population Risk</span>
            <div className="text-2xl font-black text-slate-900 mt-1">{population?.avg_cardio_risk || 0}%</div>
            <span className="text-[11px] text-slate-500 font-semibold">Cardio: {population?.avg_cardio_risk}% | Diab: {population?.avg_diabetes_risk}%</span>
          </div>
          <div className="p-3 rounded-2xl bg-indigo-50 text-indigo-600">
            <Activity className="w-5 h-5" />
          </div>
        </div>

      </div>

      {/* Main Section: Patient Triage Queue Table */}
      <div className="bg-white rounded-3xl border border-slate-200/90 shadow-xs overflow-hidden">
        
        {/* Table Header Controls */}
        <div className="p-6 border-b border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-base font-bold text-slate-900">Patient Risk Triage Queue</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Prioritized clinical queue ranked by Urgency Score and Machine Learning Risk Projections.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Search Input */}
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search patient name or email..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9 pr-3.5 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 w-56"
              />
            </div>

            {/* Urgency Filter Dropdown */}
            <select
              value={filterUrgency}
              onChange={(e) => setFilterUrgency(e.target.value)}
              className="px-3 py-2 rounded-xl border border-slate-200 text-xs font-semibold focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 bg-white"
            >
              <option value="ALL">All Triage Tiers</option>
              <option value="Critical">Critical Only</option>
              <option value="High">High Urgency</option>
              <option value="Moderate">Moderate</option>
              <option value="Routine">Routine</option>
            </select>

            <button
              onClick={loadDoctorData}
              title="Refresh queue"
              className="p-2 rounded-xl border border-slate-200 text-slate-500 hover:text-slate-900 hover:bg-slate-50 transition"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-50/70 border-b border-slate-100 text-slate-500 text-[11px] font-semibold uppercase tracking-wider">
                <th className="py-3.5 px-6">Patient Name</th>
                <th className="py-3.5 px-4">Urgency Triage Tier</th>
                <th className="py-3.5 px-4">Combined Risk</th>
                <th className="py-3.5 px-4">Cardio Risk</th>
                <th className="py-3.5 px-4">Diabetes Risk</th>
                <th className="py-3.5 px-4">Top SHAP Feature Driver</th>
                <th className="py-3.5 px-4">Appointment</th>
                <th className="py-3.5 px-6 text-right">Clinical Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium text-slate-700">
              {loading ? (
                <tr>
                  <td colSpan="8" className="py-12 text-center text-slate-400">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto text-teal-600 mb-2" />
                    Loading prioritized triage queue...
                  </td>
                </tr>
              ) : filteredQueue.length === 0 ? (
                <tr>
                  <td colSpan="8" className="py-12 text-center text-slate-400">
                    No patients match your search criteria.
                  </td>
                </tr>
              ) : (
                filteredQueue.map((patient) => (
                  <tr 
                    key={patient.patient_id}
                    className="hover:bg-teal-50/30 transition cursor-pointer"
                    onClick={() => handleOpenDeepDive(patient.patient_id)}
                  >
                    <td className="py-4 px-6">
                      <div className="font-bold text-slate-900">{patient.patient_name}</div>
                      <div className="text-[11px] text-slate-400">
                        {patient.age} yrs • {patient.gender} • BMI: {patient.bmi}
                      </div>
                    </td>

                    <td className="py-4 px-4">
                      <UrgencyBadge level={patient.urgency_level} score={patient.urgency_score} />
                    </td>

                    <td className="py-4 px-4">
                      <RiskBadge category={patient.overall_risk_category} score={patient.overall_risk_score} />
                    </td>

                    <td className="py-4 px-4">
                      <span className={`font-bold ${patient.cardio_risk_score > 60 ? 'text-rose-600' : 'text-slate-700'}`}>
                        {patient.cardio_risk_score}%
                      </span>
                    </td>

                    <td className="py-4 px-4">
                      <span className={`font-bold ${patient.diabetes_risk_score > 60 ? 'text-amber-600' : 'text-slate-700'}`}>
                        {patient.diabetes_risk_score}%
                      </span>
                    </td>

                    <td className="py-4 px-4">
                      <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 text-[11px] font-semibold border border-slate-200">
                        {patient.top_concern}
                      </span>
                    </td>

                    <td className="py-4 px-4 text-slate-600">
                      {patient.appointment_status}
                    </td>

                    <td className="py-4 px-6 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenDeepDive(patient.patient_id);
                        }}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-teal-600 hover:text-white text-slate-700 text-xs font-bold transition"
                      >
                        Deep Dive
                        <ExternalLink className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* POPULATION TRENDS SECTION (Task 6) */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200/90 shadow-xs space-y-6">
        
        {/* Header & Filter Controls Bar */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-100 pb-5">
          <div>
            <div className="flex items-center gap-2">
              <LineChartIcon className="w-5 h-5 text-teal-600" />
              <h2 className="text-base font-bold text-slate-900">Population Health Trends & Temporal Analytics</h2>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Longitudinal tracking of average cardiometabolic risk and triage severity distributions aggregated via SQL.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Period Selector */}
            <div className="flex items-center rounded-xl bg-slate-100 p-1 border border-slate-200 text-xs font-semibold">
              <button
                onClick={() => setTrendPeriod('month')}
                className={`px-3 py-1 rounded-lg transition ${
                  trendPeriod === 'month' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                Monthly
              </button>
              <button
                onClick={() => setTrendPeriod('week')}
                className={`px-3 py-1 rounded-lg transition ${
                  trendPeriod === 'week' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                Weekly
              </button>
            </div>

            {/* Age Group Filter */}
            <select
              value={filterAgeGroup}
              onChange={(e) => setFilterAgeGroup(e.target.value)}
              className="px-3 py-1.5 rounded-xl border border-slate-200 text-xs font-semibold bg-white"
            >
              <option value="ALL">All Age Cohorts</option>
              <option value="18-35">18–35 yrs</option>
              <option value="36-50">36–50 yrs</option>
              <option value="51-65">51–65 yrs</option>
              <option value="65+">65+ yrs</option>
            </select>

            {/* Sex Filter */}
            <select
              value={filterSex}
              onChange={(e) => setFilterSex(e.target.value)}
              className="px-3 py-1.5 rounded-xl border border-slate-200 text-xs font-semibold bg-white"
            >
              <option value="ALL">All Biological Sexes</option>
              <option value="Male">Male</option>
              <option value="Female">Female</option>
            </select>

            <button
              onClick={() => { loadDoctorData(); loadTrendData(); }}
              title="Refresh trends"
              className="p-2 rounded-xl border border-slate-200 text-slate-500 hover:text-slate-900 hover:bg-slate-50 transition"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {trendsLoading ? (
          <div className="py-16 text-center text-slate-400">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-teal-600 mb-2" />
            Aggregating longitudinal cohort trends...
          </div>
        ) : trends.length === 0 ? (
          <div className="py-12 text-center text-slate-400 bg-slate-50 rounded-2xl border border-dashed border-slate-200">
            <Calendar className="w-8 h-8 mx-auto text-slate-300 mb-2" />
            <span className="text-xs font-semibold block">No trend records found for the selected demographic filters.</span>
            <span className="text-[11px] text-slate-400">Adjust the age or sex filters above to broaden the cohort.</span>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* Chart 1: Line Chart of Average Risk Over Time */}
            <div className="p-4 rounded-2xl bg-slate-50/60 border border-slate-100 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-800">Average Risk Projections Over Time</span>
                <span className="text-[11px] text-slate-400 font-mono">Diabetes & Cardiovascular (%)</span>
              </div>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trends} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="period_label" tick={{ fontSize: 11, fill: '#64748b' }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#64748b' }} />
                    <Tooltip 
                      formatter={(val, name) => [`${val}%`, name]}
                      contentStyle={{ borderRadius: '12px', fontSize: '11px', border: '1px solid #e2e8f0' }}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                    <Line 
                      type="monotone" 
                      dataKey="avg_cardio_risk" 
                      name="Cardiovascular Risk (%)" 
                      stroke="#ef4444" 
                      strokeWidth={2.5} 
                      dot={{ r: 4, fill: '#ef4444' }} 
                    />
                    <Line 
                      type="monotone" 
                      dataKey="avg_diabetes_risk" 
                      name="Diabetes Risk (%)" 
                      stroke="#f59e0b" 
                      strokeWidth={2.5} 
                      dot={{ r: 4, fill: '#f59e0b' }} 
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Chart 2: Stacked Bar Chart of Triage Level Counts Per Period */}
            <div className="p-4 rounded-2xl bg-slate-50/60 border border-slate-100 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-800">Triage Severity Distributions by Period</span>
                <span className="text-[11px] text-slate-400 font-mono">Patient Urgency Count</span>
              </div>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={trends} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="period_label" tick={{ fontSize: 11, fill: '#64748b' }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#64748b' }} />
                    <Tooltip 
                      contentStyle={{ borderRadius: '12px', fontSize: '11px', border: '1px solid #e2e8f0' }}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                    <Bar dataKey="critical_triage_count" name="Critical (Urgent)" stackId="triage" fill="#dc2626" />
                    <Bar dataKey="high_triage_count" name="High Urgency" stackId="triage" fill="#ea580c" />
                    <Bar dataKey="moderate_triage_count" name="Moderate" stackId="triage" fill="#f59e0b" />
                    <Bar dataKey="routine_triage_count" name="Routine" stackId="triage" fill="#10b981" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

          </div>
        )}

      </div>

      {/* Population Health Demographic Breakdown Charts (Recharts) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Risk Distribution Donut & Age Groups (7 cols) */}
        <div className="lg:col-span-7 bg-white p-6 rounded-3xl border border-slate-200/90 shadow-xs space-y-6">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Demographic Risk Distribution by Age Bracket</h3>
              <p className="text-xs text-slate-400">Low, Medium, and High Risk breakdown across demographic age cohorts</p>
            </div>
            <BarChart2 className="w-4 h-4 text-teal-600" />
          </div>

          <div className="h-64 w-full">
            {population?.age_group_risks && (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={population.age_group_risks} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="age_group" tick={{ fontSize: 11, fill: '#64748b' }} />
                  <YAxis tick={{ fontSize: 11, fill: '#64748b' }} allowDecimals={false} />
                  <Tooltip />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                  <Bar dataKey="low_risk" name="Low Risk (<30%)" fill="#10b981" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="medium_risk" name="Medium Risk (30-65%)" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="high_risk" name="High Risk (>65%)" fill="#ef4444" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Common Clinical Risk Drivers & Urgency Load (5 cols) */}
        <div className="lg:col-span-5 bg-white p-6 rounded-3xl border border-slate-200/90 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Prevalent Clinical Biomarker Drivers</h3>
              <p className="text-xs text-slate-400">Prevalence & risk multiplication across cohort</p>
            </div>
            <TrendingUp className="w-4 h-4 text-rose-500" />
          </div>

          <div className="space-y-3 pt-1">
            {population?.common_risk_factors?.map((f, idx) => (
              <div key={idx} className="p-3 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold text-slate-800 block">{f.factor_name}</span>
                  <span className="text-[11px] text-slate-400">Adds ~{f.avg_risk_increase}% to predictive probability</span>
                </div>
                <div className="text-right">
                  <span className="text-xs font-extrabold text-teal-700 bg-teal-50 px-2.5 py-1 rounded-lg border border-teal-200">
                    {f.prevalence_pct}% Cohort
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Patient Deep Dive Modal */}
      <PatientDeepDiveModal
        patientId={selectedPatientId}
        isOpen={deepDiveOpen}
        onClose={() => setDeepDiveOpen(false)}
        onRefreshQueue={loadDoctorData}
      />

    </div>
  );
};
