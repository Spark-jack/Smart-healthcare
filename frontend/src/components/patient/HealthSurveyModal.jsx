import React, { useState } from 'react';
import { X, Sparkles, Activity, Heart, Shield, AlertCircle, ArrowRight, CheckCircle2 } from 'lucide-react';
import { api } from '../../services/api';

export const HealthSurveyModal = ({ isOpen, onClose, onSurveySubmitted }) => {
  if (!isOpen) return null;

  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const [formData, setFormData] = useState({
    // Demographics
    age: 48,
    gender: 'Male',
    height_cm: 175,
    weight_kg: 82,
    // Vitals
    systolic_bp: 138,
    diastolic_bp: 88,
    total_cholesterol: 215,
    fasting_blood_sugar: 110,
    resting_ecg: 0,
    max_heart_rate: 148,
    // Lifestyle
    smoker: false,
    physical_activity: true,
    fruits_diet: true,
    veggies_diet: true,
    heavy_alcohol: false,
    // Symptoms & History
    chest_pain_type: 2, // Non-anginal
    exercise_angina: false,
    st_depression: 0.5,
    st_slope: 1, // Flat
    major_vessels: 0,
    general_health: 3, // Good
    physical_health_days: 2,
    mental_health_days: 3,
    diff_walking: false,
    stroke_history: false,
    heart_disease_history: false,
    additional_notes: ''
  });

  // Dynamic live BMI calculation
  const heightM = formData.height_cm / 100.0;
  const bmi = heightM > 0 ? (formData.weight_kg / (heightM * heightM)).toFixed(1) : 25.0;

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const payload = {
        ...formData,
        bmi: parseFloat(bmi),
        age: parseInt(formData.age),
        height_cm: parseFloat(formData.height_cm),
        weight_kg: parseFloat(formData.weight_kg),
        systolic_bp: parseInt(formData.systolic_bp),
        diastolic_bp: parseInt(formData.diastolic_bp),
        total_cholesterol: parseInt(formData.total_cholesterol),
        fasting_blood_sugar: parseFloat(formData.fasting_blood_sugar),
        resting_ecg: parseInt(formData.resting_ecg),
        max_heart_rate: parseInt(formData.max_heart_rate),
        chest_pain_type: parseInt(formData.chest_pain_type),
        st_depression: parseFloat(formData.st_depression),
        st_slope: parseInt(formData.st_slope),
        major_vessels: parseInt(formData.major_vessels),
        general_health: parseInt(formData.general_health),
        physical_health_days: parseInt(formData.physical_health_days),
        mental_health_days: parseInt(formData.mental_health_days)
      };

      const result = await api.submitSurvey(payload);
      onSurveySubmitted(result);
      onClose();
    } catch (err) {
      console.error("Survey submission error:", err);
      setError(err.response?.data?.detail || "Failed to analyze survey. Please check all fields.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-white w-full max-w-3xl rounded-3xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[92vh]">
        
        {/* Modal Header */}
        <div className="px-6 py-5 bg-gradient-to-r from-teal-700 via-teal-600 to-emerald-600 text-white flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-white/10 backdrop-blur-md">
                <Sparkles className="w-4 h-4 text-teal-200" />
              </span>
              <h2 className="text-lg font-bold">Predictive Clinical Health Intake</h2>
            </div>
            <p className="text-xs text-teal-100 mt-1">Multi-factor clinical evaluation with automatic XGBoost & SHAP explainability</p>
          </div>
          <button onClick={onClose} className="p-2 rounded-xl text-teal-100 hover:text-white hover:bg-white/10 transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Step Indicator Tabs */}
        <div className="grid grid-cols-4 border-b border-slate-200 bg-slate-50/80 text-xs font-semibold">
          {[
            { num: 1, label: 'Demographics' },
            { num: 2, label: 'Vitals & Labs' },
            { num: 3, label: 'Lifestyle' },
            { num: 4, label: 'Symptoms & History' },
          ].map(s => (
            <button
              key={s.num}
              onClick={() => setStep(s.num)}
              className={`py-3 px-2 text-center transition-all border-b-2 flex items-center justify-center gap-1.5 ${
                step === s.num
                  ? 'border-teal-600 text-teal-800 bg-white font-bold'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[11px] ${
                step === s.num ? 'bg-teal-600 text-white' : 'bg-slate-200 text-slate-600'
              }`}>
                {s.num}
              </span>
              <span className="hidden sm:inline">{s.label}</span>
            </button>
          ))}
        </div>

        {/* Modal Content Form */}
        <form onSubmit={handleSubmit} className="p-6 overflow-y-auto space-y-6 flex-1">
          {error && (
            <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}

          {/* STEP 1: Demographics */}
          {step === 1 && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Patient Age (Years)</label>
                  <input
                    type="number"
                    min="18"
                    max="105"
                    value={formData.age}
                    onChange={(e) => handleChange('age', e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 text-sm"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Biological Sex</label>
                  <select
                    value={formData.gender}
                    onChange={(e) => handleChange('gender', e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 text-sm bg-white"
                  >
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Height (cm)</label>
                  <input
                    type="number"
                    min="100"
                    max="230"
                    value={formData.height_cm}
                    onChange={(e) => handleChange('height_cm', e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 text-sm"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Weight (kg)</label>
                  <input
                    type="number"
                    min="35"
                    max="220"
                    value={formData.weight_kg}
                    onChange={(e) => handleChange('weight_kg', e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 text-sm"
                    required
                  />
                </div>
                <div className="p-3 rounded-xl bg-teal-50/70 border border-teal-100 flex flex-col justify-center">
                  <span className="text-[11px] font-semibold text-teal-800 uppercase tracking-wider">Calculated BMI</span>
                  <div className="flex items-baseline gap-2 mt-0.5">
                    <span className="text-xl font-extrabold text-teal-900">{bmi}</span>
                    <span className="text-xs text-teal-700 font-medium">
                      {bmi < 18.5 ? '(Underweight)' : bmi < 25 ? '(Normal)' : bmi < 30 ? '(Overweight)' : '(Obese)'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* STEP 2: Vitals & Labs */}
          {step === 2 && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Systolic Blood Pressure (mmHg)</label>
                  <input
                    type="number"
                    min="80"
                    max="240"
                    value={formData.systolic_bp}
                    onChange={(e) => handleChange('systolic_bp', e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 text-sm"
                    required
                  />
                  <span className="text-[11px] text-slate-400">Normal: &lt;120 mmHg | Hypertensive: &ge;140 mmHg</span>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Diastolic Blood Pressure (mmHg)</label>
                  <input
                    type="number"
                    min="50"
                    max="150"
                    value={formData.diastolic_bp}
                    onChange={(e) => handleChange('diastolic_bp', e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 text-sm"
                    required
                  />
                  <span className="text-[11px] text-slate-400">Normal: &lt;80 mmHg | Elevated: &ge;90 mmHg</span>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Serum Total Cholesterol (mg/dL)</label>
                  <input
                    type="number"
                    min="100"
                    max="500"
                    value={formData.total_cholesterol}
                    onChange={(e) => handleChange('total_cholesterol', e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 text-sm"
                    required
                  />
                  <span className="text-[11px] text-slate-400">Optimal: &lt;200 mg/dL | Borderline: 200-239 mg/dL</span>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Fasting Blood Glucose (mg/dL)</label>
                  <input
                    type="number"
                    min="60"
                    max="450"
                    value={formData.fasting_blood_sugar}
                    onChange={(e) => handleChange('fasting_blood_sugar', e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 text-sm"
                    required
                  />
                  <span className="text-[11px] text-slate-400">Normal: 70-99 mg/dL | Pre-diabetes: 100-125 | Diabetes: &ge;126</span>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Max Heart Rate Achieved (bpm)</label>
                  <input
                    type="number"
                    min="60"
                    max="220"
                    value={formData.max_heart_rate}
                    onChange={(e) => handleChange('max_heart_rate', e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 text-sm"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Resting ECG Results</label>
                  <select
                    value={formData.resting_ecg}
                    onChange={(e) => handleChange('resting_ecg', e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 text-sm bg-white"
                  >
                    <option value={0}>Normal Electrocardiogram</option>
                    <option value={1}>ST-T Wave Abnormality (T-inversion/elevation)</option>
                    <option value={2}>Left Ventricular Hypertrophy (Estes' criteria)</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: Lifestyle */}
          {step === 3 && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <label className="flex items-start gap-3 p-3.5 rounded-2xl border border-slate-200 bg-white hover:bg-slate-50 cursor-pointer transition">
                  <input
                    type="checkbox"
                    checked={formData.smoker}
                    onChange={(e) => handleChange('smoker', e.target.checked)}
                    className="mt-1 h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                  />
                  <div>
                    <span className="text-xs font-bold text-slate-800">Current or Regular Smoker</span>
                    <p className="text-[11px] text-slate-500 mt-0.5">Has smoked at least 100 cigarettes in lifetime or smokes currently.</p>
                  </div>
                </label>

                <label className="flex items-start gap-3 p-3.5 rounded-2xl border border-slate-200 bg-white hover:bg-slate-50 cursor-pointer transition">
                  <input
                    type="checkbox"
                    checked={formData.physical_activity}
                    onChange={(e) => handleChange('physical_activity', e.target.checked)}
                    className="mt-1 h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                  />
                  <div>
                    <span className="text-xs font-bold text-slate-800">Regular Physical Exercise</span>
                    <p className="text-[11px] text-slate-500 mt-0.5">Engages in 150+ minutes of moderate exercise weekly.</p>
                  </div>
                </label>

                <label className="flex items-start gap-3 p-3.5 rounded-2xl border border-slate-200 bg-white hover:bg-slate-50 cursor-pointer transition">
                  <input
                    type="checkbox"
                    checked={formData.fruits_diet}
                    onChange={(e) => handleChange('fruits_diet', e.target.checked)}
                    className="mt-1 h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                  />
                  <div>
                    <span className="text-xs font-bold text-slate-800">Daily Fruit Intake</span>
                    <p className="text-[11px] text-slate-500 mt-0.5">Consumes 1 or more servings of fruit per day.</p>
                  </div>
                </label>

                <label className="flex items-start gap-3 p-3.5 rounded-2xl border border-slate-200 bg-white hover:bg-slate-50 cursor-pointer transition">
                  <input
                    type="checkbox"
                    checked={formData.veggies_diet}
                    onChange={(e) => handleChange('veggies_diet', e.target.checked)}
                    className="mt-1 h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                  />
                  <div>
                    <span className="text-xs font-bold text-slate-800">Daily Vegetable Intake</span>
                    <p className="text-[11px] text-slate-500 mt-0.5">Consumes 1 or more servings of greens/vegetables daily.</p>
                  </div>
                </label>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Self-Reported General Health Rating</label>
                <div className="grid grid-cols-5 gap-2">
                  {[
                    { val: 1, label: 'Excellent' },
                    { val: 2, label: 'Very Good' },
                    { val: 3, label: 'Good' },
                    { val: 4, label: 'Fair' },
                    { val: 5, label: 'Poor' },
                  ].map(g => (
                    <button
                      key={g.val}
                      type="button"
                      onClick={() => handleChange('general_health', g.val)}
                      className={`py-2 px-1 text-center rounded-xl border text-xs font-semibold transition ${
                        formData.general_health === g.val
                          ? 'border-teal-600 bg-teal-50 text-teal-800 font-bold'
                          : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                      }`}
                    >
                      {g.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* STEP 4: Symptoms & Clinical History */}
          {step === 4 && (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Chest Pain Experience Profile</label>
                <select
                  value={formData.chest_pain_type}
                  onChange={(e) => handleChange('chest_pain_type', e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 text-sm bg-white"
                >
                  <option value={0}>Typical Angina (Crushing substernal pressure with exertion)</option>
                  <option value={1}>Atypical Angina (Sharp/stabbing chest discomfort)</option>
                  <option value={2}>Non-Anginal Discomfort (Pleuritic or musculoskeletal)</option>
                  <option value={3}>Asymptomatic (No current chest discomfort)</option>
                </select>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">ST Depression - Oldpeak (mm)</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="6.5"
                    value={formData.st_depression}
                    onChange={(e) => handleChange('st_depression', e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 text-sm"
                  />
                  <span className="text-[11px] text-slate-400">Values &ge;1.5mm suggest significant exercise ischemia</span>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">ST Segment Slope</label>
                  <select
                    value={formData.st_slope}
                    onChange={(e) => handleChange('st_slope', e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 text-sm bg-white"
                  >
                    <option value={0}>Upsloping (Physiological / Normal)</option>
                    <option value={1}>Flat (Borderline Ischemic)</option>
                    <option value={2}>Downsloping (High Risk Ischemic Pattern)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                <label className="flex items-center gap-3 p-3 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.exercise_angina}
                    onChange={(e) => handleChange('exercise_angina', e.target.checked)}
                    className="h-4 w-4 rounded text-teal-600 focus:ring-teal-500"
                  />
                  <span className="text-xs font-semibold text-slate-700">Exercise-Induced Angina</span>
                </label>

                <label className="flex items-center gap-3 p-3 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.diff_walking}
                    onChange={(e) => handleChange('diff_walking', e.target.checked)}
                    className="h-4 w-4 rounded text-teal-600 focus:ring-teal-500"
                  />
                  <span className="text-xs font-semibold text-slate-700">Difficulty Walking / Stairs</span>
                </label>

                <label className="flex items-center gap-3 p-3 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.stroke_history}
                    onChange={(e) => handleChange('stroke_history', e.target.checked)}
                    className="h-4 w-4 rounded text-teal-600 focus:ring-teal-500"
                  />
                  <span className="text-xs font-semibold text-slate-700">Past History of Stroke</span>
                </label>

                <label className="flex items-center gap-3 p-3 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.heart_disease_history}
                    onChange={(e) => handleChange('heart_disease_history', e.target.checked)}
                    className="h-4 w-4 rounded text-teal-600 focus:ring-teal-500"
                  />
                  <span className="text-xs font-semibold text-slate-700">Prior Heart Attack / CAD</span>
                </label>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Additional Symptoms or Clinical Notes</label>
                <textarea
                  rows="2"
                  value={formData.additional_notes}
                  onChange={(e) => handleChange('additional_notes', e.target.value)}
                  placeholder="e.g., Shortness of breath when reclining, family history of early myocardial infarction..."
                  className="w-full px-3.5 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 text-xs"
                />
              </div>
            </div>
          )}

          {/* Modal Footer with Step Controls */}
          <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
            {step > 1 ? (
              <button
                type="button"
                onClick={() => setStep(step - 1)}
                className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-100 transition"
              >
                Back
              </button>
            ) : <div />}

            {step < 4 ? (
              <button
                type="button"
                onClick={() => setStep(step + 1)}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold shadow-md shadow-teal-600/20 transition"
              >
                Continue to Step {step + 1}
                <ArrowRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={submitting}
                className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-700 hover:to-emerald-700 text-white text-xs font-bold shadow-lg shadow-teal-600/30 transition disabled:opacity-50"
              >
                {submitting ? (
                  <>Running AI Prediction...</>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    Run Risk Prediction & Triage
                  </>
                )}
              </button>
            )}
          </div>
        </form>

      </div>
    </div>
  );
};
