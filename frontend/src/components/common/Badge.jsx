import React from 'react';
import { ShieldCheck, AlertTriangle, AlertOctagon, Clock } from 'lucide-react';

export const RiskBadge = ({ category, score }) => {
  const cat = (category || 'Low').toLowerCase();

  if (cat.includes('high')) {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-red-50 text-red-700 border border-red-200">
        <AlertOctagon className="w-3.5 h-3.5 text-red-600" />
        High Risk {score !== undefined ? `(${score}%)` : ''}
      </span>
    );
  }
  if (cat.includes('medium') || cat.includes('moderate')) {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
        <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
        Medium Risk {score !== undefined ? `(${score}%)` : ''}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
      <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
      Low Risk {score !== undefined ? `(${score}%)` : ''}
    </span>
  );
};

export const UrgencyBadge = ({ level, score }) => {
  const lvl = (level || 'Routine').toLowerCase();

  if (lvl.includes('critical')) {
    return (
      <span className="relative inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-300 shadow-sm animate-pulse">
        <span className="w-2 h-2 rounded-full bg-rose-600"></span>
        Critical Triage {score !== undefined ? `[${score}]` : ''}
      </span>
    );
  }
  if (lvl.includes('high')) {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-orange-50 text-orange-800 border border-orange-200">
        <AlertTriangle className="w-3.5 h-3.5 text-orange-600" />
        High Urgency {score !== undefined ? `[${score}]` : ''}
      </span>
    );
  }
  if (lvl.includes('moderate') || lvl.includes('medium')) {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200">
        <Clock className="w-3.5 h-3.5 text-amber-600" />
        Moderate {score !== undefined ? `[${score}]` : ''}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
      <Clock className="w-3.5 h-3.5 text-slate-500" />
      Routine {score !== undefined ? `[${score}]` : ''}
    </span>
  );
};

export const StatusBadge = ({ status }) => {
  const st = (status || 'Pending').toLowerCase();
  const styles = {
    confirmed: 'bg-teal-50 text-teal-700 border-teal-200',
    completed: 'bg-blue-50 text-blue-700 border-blue-200',
    pending: 'bg-amber-50 text-amber-700 border-amber-200',
    cancelled: 'bg-slate-100 text-slate-500 border-slate-200'
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles[st] || styles.pending}`}>
      {status}
    </span>
  );
};
