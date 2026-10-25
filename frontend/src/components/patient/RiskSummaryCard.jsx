import React, { useState } from 'react';
import { 
  Activity, Heart, Shield, AlertTriangle, Info, Calendar, 
  Sparkles, TrendingUp, HelpCircle, AlertCircle, Database, CheckCircle2 
} from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell, ReferenceLine } from 'recharts';
import { RiskBadge, UrgencyBadge } from '../common/Badge';

export const RiskSummaryCard = ({ prediction, onOpenAppointmentModal, onRetakeSurvey }) => {
  const [selectedDisease, setSelectedDisease] = useState('cardio'); // 'cardio' or 'diabetes'

  if (!prediction) {
    return (
      <div className="p-8 text-center bg-white rounded-3xl border border-dashed border-slate-300">
        <Activity className="w-12 h-12 text-teal-600 mx-auto mb-3 opacity-40" />
        <h3 className="text-base font-bold text-slate-800">No Risk Prediction Recorded Yet</h3>
        <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
          Complete your health intake survey to generate an automated ML risk assessment and SHAP explainability insights.
        </p>
        <button
          onClick={onRetakeSurvey}
          className="px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold shadow-md transition"
        >
          Start Clinical Survey
        </button>
      </div>
    );
  }

  const activeDiseaseData = selectedDisease === 'cardio' ? prediction.cardiovascular : prediction.diabetes;
  const topFactors = activeDiseaseData?.top_factors || [];

  // Format plausible range
  const formatPlausibleRange = (diseaseData) => {
    if (diseaseData?.uncertainty_interval && diseaseData.uncertainty_interval.length === 2) {
      return `${diseaseData.uncertainty_interval[0]}% – ${diseaseData.uncertainty_interval[1]}%`;
    }
    const low = Math.max(0, Math.round(diseaseData.risk_score - 7));
    const high = Math.min(100, Math.round(diseaseData.risk_score + 7));
    return `${low}% – ${high}%`;
  };

  // Prepare data for SHAP waterfall-style horizontal bar chart
  const chartData = topFactors.map(f => ({
    name: f.feature_label.length > 22 ? f.feature_label.substring(0, 20) + '...' : f.feature_label,
    impact: f.shap_value,
    impactPct: (f.shap_value * 100).toFixed(1),
    isRisk: f.impact === 'increases_risk',
    fullLabel: f.feature_label,
    interpretation: f.interpretation,
    val: f.feature_value
  })).reverse(); // reverse so highest is top in horizontal chart

  const qualityWarning = prediction.data_quality_warning || activeDiseaseData?.data_quality_warning;

  return (
    <div className="space-y-6">

      {/* Mandatory Medical Disclaimer */}
      <div className="p-3 rounded-2xl bg-amber-50/80 border border-amber-200/80 text-[11px] text-amber-900 flex items-start gap-2.5 shadow-xs">
        <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <span className="font-bold">Medical Disclaimer:</span> This platform and its machine learning risk estimates are for demonstration and informational purposes only. They are not clinically validated diagnostic instruments and should not replace consultation with a qualified medical professional.
        </div>
      </div>

      {/* Low Data Quality Warning Banner (if survey had missing/defaulted metrics) */}
      {qualityWarning && (
        <div className="p-3.5 rounded-2xl bg-orange-50 border border-orange-200 text-xs text-orange-900 flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 text-orange-600 shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <span className="font-bold">Low Data Quality Notice:</span> {qualityWarning}
          </div>
        </div>
      )}
      
      {/* Triage Priority Banner */}
      <div className={`p-5 rounded-3xl border transition-all ${
        prediction.urgency_level === 'Critical'
          ? 'bg-rose-50/90 border-rose-200'
          : prediction.urgency_level === 'High'
          ? 'bg-orange-50/90 border-orange-200'
          : 'bg-teal-50/70 border-teal-200/80'
      }`}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start gap-3.5">
            <div className={`p-2.5 rounded-2xl ${
              prediction.urgency_level === 'Critical'
                ? 'bg-rose-600 text-white'
                : prediction.urgency_level === 'High'
                ? 'bg-orange-600 text-white'
                : 'bg-teal-600 text-white'
            }`}>
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Clinical Urgency Triage</span>
                <UrgencyBadge level={prediction.urgency_level} score={prediction.urgency_score} />
              </div>
              <h3 className="text-sm font-bold text-slate-900 mt-1">
                {prediction.recommended_action || "Schedule a consultation based on your risk metrics."}
              </h3>
              <p className="text-xs text-slate-600 mt-0.5">
                Urgency Score: <span className="font-bold text-slate-800">{prediction.urgency_score} / 100</span> (Derived from acute symptom weights + calibrated predictive probabilities)
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5 shrink-0">
            <button
              onClick={onOpenAppointmentModal}
              className="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold shadow-md transition flex items-center gap-2"
            >
              <Calendar className="w-4 h-4 text-teal-400" />
              Book Priority Appointment
            </button>
            <button
              onClick={onRetakeSurvey}
              className="px-3.5 py-2.5 rounded-xl border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold transition"
            >
              Update Survey
            </button>
          </div>
        </div>
      </div>

      {/* Dual Risk Score Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        
        {/* Cardiovascular Card */}
        <div 
          onClick={() => setSelectedDisease('cardio')}
          className={`p-6 rounded-3xl border transition-all cursor-pointer ${
            selectedDisease === 'cardio'
              ? 'bg-white border-teal-500 shadow-md ring-2 ring-teal-500/10'
              : 'bg-white border-slate-200 hover:border-slate-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-rose-50 text-rose-600 border border-rose-100">
                <Heart className="w-5 h-5 fill-rose-500/20" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-bold text-slate-800">Cardiovascular Risk</h4>
                  <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold border ${
                    prediction.cardiovascular.data_source === 'real'
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      : 'bg-amber-50 text-amber-700 border-amber-200'
                  }`}>
                    Model data: {prediction.cardiovascular.data_source || 'real'}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400">UCI Cleveland Clinic Benchmark (Isotonic Calibrated)</p>
              </div>
            </div>
            <RiskBadge category={prediction.cardiovascular.risk_category} />
          </div>

          <div className="mt-5 flex items-baseline justify-between">
            <div>
              <span className="text-3xl font-black text-slate-900">{prediction.cardiovascular.risk_score}%</span>
              <span className="text-xs text-slate-500 font-medium ml-1.5">Calibrated Probability</span>
            </div>
            <div className="text-right">
              <span className="text-[11px] font-semibold text-slate-500 block">Certainty Index</span>
              <span className="text-xs font-bold text-slate-700">
                {Math.round(prediction.cardiovascular.confidence * 100)}%
              </span>
            </div>
          </div>

          {/* Plain language explanation with 95% plausible range */}
          <div className="mt-2.5 p-2 rounded-xl bg-slate-50 border border-slate-100 text-[11px] text-slate-600">
            Estimated probability: <span className="font-bold text-slate-900">{prediction.cardiovascular.risk_score}%</span>, plausible range <span className="font-bold text-slate-900">{formatPlausibleRange(prediction.cardiovascular)}</span>
          </div>

          {/* Progress Bar */}
          <div className="mt-3 w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                prediction.cardiovascular.risk_score > 65
                  ? 'bg-red-500'
                  : prediction.cardiovascular.risk_score > 30
                  ? 'bg-amber-500'
                  : 'bg-emerald-500'
              }`}
              style={{ width: `${Math.min(100, Math.max(5, prediction.cardiovascular.risk_score))}%` }}
            />
          </div>

          <p className="mt-3 text-xs text-slate-600 line-clamp-2">
            {prediction.cardiovascular.summary_insight}
          </p>
        </div>

        {/* Diabetes Card */}
        <div 
          onClick={() => setSelectedDisease('diabetes')}
          className={`p-6 rounded-3xl border transition-all cursor-pointer ${
            selectedDisease === 'diabetes'
              ? 'bg-white border-teal-500 shadow-md ring-2 ring-teal-500/10'
              : 'bg-white border-slate-200 hover:border-slate-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-teal-50 text-teal-600 border border-teal-100">
                <Activity className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-bold text-slate-800">Diabetes Metabolic Risk</h4>
                  <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold border ${
                    prediction.diabetes.data_source === 'real'
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      : 'bg-amber-50 text-amber-700 border-amber-200'
                  }`}>
                    Model data: {prediction.diabetes.data_source || 'real'}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400">CDC BRFSS 2015 Health Indicators (Isotonic Calibrated)</p>
              </div>
            </div>
            <RiskBadge category={prediction.diabetes.risk_category} />
          </div>

          <div className="mt-5 flex items-baseline justify-between">
            <div>
              <span className="text-3xl font-black text-slate-900">{prediction.diabetes.risk_score}%</span>
              <span className="text-xs text-slate-500 font-medium ml-1.5">Calibrated Probability</span>
            </div>
            <div className="text-right">
              <span className="text-[11px] font-semibold text-slate-500 block">Certainty Index</span>
              <span className="text-xs font-bold text-slate-700">
                {Math.round(prediction.diabetes.confidence * 100)}%
              </span>
            </div>
          </div>

          {/* Plain language explanation with 95% plausible range */}
          <div className="mt-2.5 p-2 rounded-xl bg-slate-50 border border-slate-100 text-[11px] text-slate-600">
            Estimated probability: <span className="font-bold text-slate-900">{prediction.diabetes.risk_score}%</span>, plausible range <span className="font-bold text-slate-900">{formatPlausibleRange(prediction.diabetes)}</span>
          </div>

          {/* Progress Bar */}
          <div className="mt-3 w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                prediction.diabetes.risk_score > 65
                  ? 'bg-red-500'
                  : prediction.diabetes.risk_score > 30
                  ? 'bg-amber-500'
                  : 'bg-emerald-500'
              }`}
              style={{ width: `${Math.min(100, Math.max(5, prediction.diabetes.risk_score))}%` }}
            />
          </div>

          <p className="mt-3 text-xs text-slate-600 line-clamp-2">
            {prediction.diabetes.summary_insight}
          </p>
        </div>

      </div>

      {/* Explainable AI (SHAP) Insights Section */}
      <div className="p-6 bg-white rounded-3xl border border-slate-200 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded-md bg-purple-50 text-purple-700 font-bold text-[10px] tracking-wider uppercase border border-purple-200">
                SHAP Explainability
              </span>
              <h3 className="text-sm font-bold text-slate-900">
                What is Driving Your {selectedDisease === 'cardio' ? 'Cardiovascular' : 'Diabetes'} Risk?
              </h3>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Shapley Additive exPlanations quantify the exact directional impact of each biometric biomarker on your AI prediction.
            </p>
          </div>

          <div className="flex items-center gap-1.5 self-start sm:self-auto bg-slate-100 p-1 rounded-xl">
            <button
              onClick={() => setSelectedDisease('cardio')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                selectedDisease === 'cardio' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Heart Disease
            </button>
            <button
              onClick={() => setSelectedDisease('diabetes')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                selectedDisease === 'diabetes' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Diabetes
            </button>
          </div>
        </div>

        {/* Chart + Factors Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mt-6">
          
          {/* Left: Recharts Horizontal SHAP Bar Chart */}
          <div className="lg:col-span-6 bg-slate-50/60 p-4 rounded-2xl border border-slate-100">
            <div className="flex items-center justify-between text-xs mb-3 text-slate-500">
              <span className="font-semibold text-slate-700">Top 5 Clinical Feature Attributions</span>
              <div className="flex items-center gap-3 text-[11px]">
                <span className="flex items-center gap-1 text-emerald-700">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> Lowers Risk
                </span>
                <span className="flex items-center gap-1 text-rose-700">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span> Increases Risk
                </span>
              </div>
            </div>

            <div className="h-56 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
                  <XAxis type="number" tick={{ fontSize: 10, fill: '#64748b' }} unit="" />
                  <YAxis type="category" dataKey="name" width={110} tick={{ fontSize: 11, fill: '#334155', fontWeight: 600 }} />
                  <Tooltip
                    formatter={(val, name, item) => [
                      `${val > 0 ? '+' : ''}${(val * 100).toFixed(1)}% risk contribution`,
                      item.payload.fullLabel
                    ]}
                  />
                  <ReferenceLine x={0} stroke="#94a3b8" strokeDasharray="3 3" />
                  <Bar dataKey="impact" radius={[0, 4, 4, 0]}>
                    {chartData.map((entry, idx) => (
                      <Cell key={`cell-${idx}`} fill={entry.isRisk ? '#f43f5e' : '#10b981'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Right: Detailed Interpretation List */}
          <div className="lg:col-span-6 space-y-2.5">
            <span className="text-xs font-bold text-slate-700 block">Personalized Clinical Insights</span>
            {topFactors.map((f, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-2xl border text-xs flex items-start gap-3 transition-all ${
                  f.impact === 'increases_risk'
                    ? 'bg-rose-50/50 border-rose-100 hover:bg-rose-50'
                    : 'bg-emerald-50/50 border-emerald-100 hover:bg-emerald-50'
                }`}
              >
                <div className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${
                  f.impact === 'increases_risk' ? 'bg-rose-500' : 'bg-emerald-500'
                }`} />
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-800">{f.feature_label}</span>
                    <span className={`text-[11px] font-bold ${
                      f.impact === 'increases_risk' ? 'text-rose-600' : 'text-emerald-600'
                    }`}>
                      {f.shap_value > 0 ? '+' : ''}{(f.shap_value * 100).toFixed(1)}%
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-600 mt-0.5 leading-relaxed">
                    {f.interpretation}
                  </p>
                </div>
              </div>
            ))}
          </div>

        </div>
      </div>

    </div>
  );
};
