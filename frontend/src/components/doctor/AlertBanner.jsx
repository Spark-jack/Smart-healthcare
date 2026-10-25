import React from 'react';
import { AlertOctagon, ArrowRight, Bell, ShieldAlert, Sparkles } from 'lucide-react';

export const AlertBanner = ({ alerts, onSelectPatient }) => {
  if (!alerts || alerts.length === 0) return null;

  return (
    <div className="bg-gradient-to-r from-rose-950 via-slate-900 to-rose-900 border border-rose-500/30 rounded-3xl p-4 sm:p-5 text-white shadow-xl shadow-rose-950/20 relative overflow-hidden">
      
      {/* Decorative pulse blur */}
      <div className="absolute top-0 right-0 -mt-6 -mr-6 w-32 h-32 rounded-full bg-rose-500/10 blur-2xl pointer-events-none" />

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        
        <div className="flex items-start gap-3.5">
          <div className="p-2.5 rounded-2xl bg-rose-600/30 border border-rose-500/40 text-rose-300 shrink-0 animate-pulse">
            <AlertOctagon className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-bold tracking-wider uppercase px-2 py-0.5 rounded-md bg-rose-500/30 text-rose-200 border border-rose-500/40">
                Critical Clinical Alerts
              </span>
              <span className="text-xs text-rose-300 font-medium">
                {alerts.length} high-urgency patient{alerts.length > 1 ? 's' : ''} require immediate triage review
              </span>
            </div>
            
            {/* Carousel / Quick Action Badges */}
            <div className="flex flex-wrap items-center gap-2 mt-2.5">
              {alerts.slice(0, 3).map((alert, idx) => (
                <button
                  key={idx}
                  onClick={() => onSelectPatient(alert.patient_id)}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/10 hover:bg-rose-600/40 border border-white/10 hover:border-rose-400/40 text-xs text-white transition text-left"
                >
                  <span className="font-bold">{alert.patient_name}</span>
                  <span className="text-rose-300 font-semibold">[{alert.overall_risk_score}% Risk]</span>
                  <span className="text-[10px] text-slate-300 hidden sm:inline">• {alert.key_drivers[0]}</span>
                  <ArrowRight className="w-3 h-3 text-rose-300" />
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="text-right shrink-0">
          <span className="text-[11px] text-rose-200/80 block">Real-time XGBoost Risk Monitor</span>
          <span className="text-xs font-mono text-emerald-400 flex items-center justify-end gap-1 mt-0.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span> Live Active
          </span>
        </div>

      </div>
    </div>
  );
};
