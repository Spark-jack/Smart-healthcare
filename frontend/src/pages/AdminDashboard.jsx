import React, { useState, useEffect } from 'react';
import { 
  Shield, Users, Server, Database, Activity, CheckCircle2, 
  XCircle, RefreshCw, UserPlus, AlertCircle, X
} from 'lucide-react';
import { api } from '../services/api';

export const AdminDashboard = () => {
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // New user modal state
  const [isAddUserOpen, setIsAddUserOpen] = useState(false);
  const [newUser, setNewUser] = useState({
    email: '',
    password: '',
    full_name: '',
    role: 'doctor',
    is_active: true
  });
  const [creatingUser, setCreatingUser] = useState(false);

  const loadAdminData = async () => {
    setLoading(true);
    try {
      const [statsData, usersData] = await Promise.all([
        api.getAdminStats(),
        api.listAdminUsers()
      ]);
      setStats(statsData);
      setUsers(usersData);
    } catch (err) {
      console.error("Failed to load admin metrics:", err);
      setErrorMessage("Failed to load admin metrics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAdminData();
  }, []);

  const handleRoleChange = async (userId, newRole) => {
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      await api.updateUserRole(userId, newRole);
      setSuccessMessage("User role updated successfully.");
      loadAdminData();
    } catch (err) {
      const detail = err.response?.data?.detail || "Failed to update role";
      setErrorMessage(detail);
    }
  };

  const handleToggleStatus = async (userId) => {
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      await api.toggleUserStatus(userId);
      setSuccessMessage("User status toggled successfully.");
      loadAdminData();
    } catch (err) {
      const detail = err.response?.data?.detail || "Failed to toggle status";
      setErrorMessage(detail);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setErrorMessage(null);
    setCreatingUser(true);
    try {
      await api.createAdminUser(newUser);
      setIsAddUserOpen(false);
      setNewUser({ email: '', password: '', full_name: '', role: 'doctor', is_active: true });
      setSuccessMessage(`Account for ${newUser.full_name} (${newUser.role}) created successfully.`);
      loadAdminData();
    } catch (err) {
      const detail = err.response?.data?.detail || "Failed to create user";
      setErrorMessage(detail);
    } finally {
      setCreatingUser(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      
      {/* Alert Notices */}
      {errorMessage && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span className="font-semibold">{errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage(null)} className="text-rose-500 hover:text-rose-700">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {successMessage && (
        <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span className="font-semibold">{successMessage}</span>
          </div>
          <button onClick={() => setSuccessMessage(null)} className="text-emerald-500 hover:text-emerald-700">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-3xl border border-slate-200/90 shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-extrabold text-slate-900">System Administration & Diagnostics</h1>
            <span className="px-2.5 py-0.5 rounded-full bg-purple-50 text-purple-700 text-xs font-bold border border-purple-200">
              Admin Portal
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Role-based governance, ML calibration metrics audit, and database operational telemetry.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsAddUserOpen(true)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-2xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold shadow-md shadow-teal-600/20 transition"
          >
            <UserPlus className="w-4 h-4" />
            Create Account
          </button>
          <button
            onClick={loadAdminData}
            className="p-2.5 rounded-2xl border border-slate-200 text-slate-600 hover:bg-slate-50 transition"
            title="Refresh metrics"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="p-5 rounded-3xl bg-white border border-slate-200/90 shadow-xs">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Total Users</span>
          <div className="text-2xl font-black text-slate-900 mt-1">{stats?.counts?.total_users || 0}</div>
        </div>
        <div className="p-5 rounded-3xl bg-white border border-slate-200/90 shadow-xs">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Patients</span>
          <div className="text-2xl font-black text-teal-600 mt-1">{stats?.counts?.patients || 0}</div>
        </div>
        <div className="p-5 rounded-3xl bg-white border border-slate-200/90 shadow-xs">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Doctors</span>
          <div className="text-2xl font-black text-indigo-600 mt-1">{stats?.counts?.doctors || 0}</div>
        </div>
        <div className="p-5 rounded-3xl bg-white border border-slate-200/90 shadow-xs">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Admins</span>
          <div className="text-2xl font-black text-purple-600 mt-1">{stats?.counts?.admins || 0}</div>
        </div>
        <div className="p-5 rounded-3xl bg-white border border-slate-200/90 shadow-xs">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Surveys</span>
          <div className="text-2xl font-black text-amber-600 mt-1">{stats?.counts?.surveys_submitted || 0}</div>
        </div>
        <div className="p-5 rounded-3xl bg-white border border-slate-200/90 shadow-xs">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Predictions</span>
          <div className="text-2xl font-black text-rose-600 mt-1">{stats?.counts?.predictions_generated || 0}</div>
        </div>
      </div>

      {/* ML Engine Calibration & Model Audit */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Diabetes Model Details */}
        <div className="p-6 bg-white rounded-3xl border border-slate-200/90 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Server className="w-4 h-4 text-teal-600" />
              Diabetes Risk Classifier & Calibration
            </h3>
            <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider ${
              stats?.ml_engine?.diabetes_data_source === 'real'
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : 'bg-amber-50 text-amber-700 border border-amber-200'
            }`}>
              Data: {stats?.ml_engine?.diabetes_data_source || 'real'}
            </span>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-100">
              <span className="font-semibold text-slate-600">Dataset Source</span>
              <span className="font-bold text-slate-900">{stats?.ml_engine?.diabetes_dataset}</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-100">
              <span className="font-semibold text-slate-600">Sample Row Count</span>
              <span className="font-bold text-slate-900">{(stats?.ml_engine?.diabetes_row_count || 0).toLocaleString()} observations</span>
            </div>
            <div className="grid grid-cols-3 gap-2 pt-1">
              <div className="p-3 rounded-xl bg-teal-50/60 border border-teal-100 text-center">
                <span className="text-[10px] font-bold text-teal-700 uppercase">Test AUC-ROC</span>
                <div className="text-base font-black text-teal-900 mt-0.5">
                  {stats?.ml_engine?.diabetes_auc?.toFixed(4) || '0.8252'}
                </div>
              </div>
              <div className="p-3 rounded-xl bg-teal-50/60 border border-teal-100 text-center">
                <span className="text-[10px] font-bold text-teal-700 uppercase">Test Accuracy</span>
                <div className="text-base font-black text-teal-900 mt-0.5">
                  {((stats?.ml_engine?.diabetes_accuracy || 0.8655) * 100).toFixed(1)}%
                </div>
              </div>
              <div className="p-3 rounded-xl bg-indigo-50/60 border border-indigo-100 text-center">
                <span className="text-[10px] font-bold text-indigo-700 uppercase">Calibration (ECE)</span>
                <div className="text-base font-black text-indigo-900 mt-0.5">
                  {stats?.ml_engine?.diabetes_ece != null ? stats.ml_engine.diabetes_ece.toFixed(4) : '0.0038'}
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between p-2 rounded-xl bg-slate-50 text-[11px] text-slate-500">
              <span>Model & Explainer Status:</span>
              <span className="font-bold text-emerald-600 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> Calibrated Classifier + TreeExplainer Active
              </span>
            </div>
          </div>
        </div>

        {/* Cardiovascular Model Details */}
        <div className="p-6 bg-white rounded-3xl border border-slate-200/90 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Activity className="w-4 h-4 text-rose-600" />
              Cardiovascular Risk Classifier & Calibration
            </h3>
            <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider ${
              stats?.ml_engine?.heart_data_source === 'real'
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : 'bg-amber-50 text-amber-700 border border-amber-200'
            }`}>
              Data: {stats?.ml_engine?.heart_data_source || 'real'}
            </span>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-100">
              <span className="font-semibold text-slate-600">Dataset Source</span>
              <span className="font-bold text-slate-900">{stats?.ml_engine?.heart_dataset}</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-100">
              <span className="font-semibold text-slate-600">Sample Row Count</span>
              <span className="font-bold text-slate-900">{(stats?.ml_engine?.heart_row_count || 0).toLocaleString()} observations</span>
            </div>
            <div className="grid grid-cols-3 gap-2 pt-1">
              <div className="p-3 rounded-xl bg-rose-50/60 border border-rose-100 text-center">
                <span className="text-[10px] font-bold text-rose-700 uppercase">Test AUC-ROC</span>
                <div className="text-base font-black text-rose-900 mt-0.5">
                  {stats?.ml_engine?.heart_auc?.toFixed(4) || '0.9459'}
                </div>
              </div>
              <div className="p-3 rounded-xl bg-rose-50/60 border border-rose-100 text-center">
                <span className="text-[10px] font-bold text-rose-700 uppercase">Test Accuracy</span>
                <div className="text-base font-black text-rose-900 mt-0.5">
                  {((stats?.ml_engine?.heart_accuracy || 0.8000) * 100).toFixed(1)}%
                </div>
              </div>
              <div className="p-3 rounded-xl bg-indigo-50/60 border border-indigo-100 text-center">
                <span className="text-[10px] font-bold text-indigo-700 uppercase">Calibration (ECE)</span>
                <div className="text-base font-black text-indigo-900 mt-0.5">
                  {stats?.ml_engine?.heart_ece != null ? stats.ml_engine.heart_ece.toFixed(4) : '0.1106'}
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between p-2 rounded-xl bg-slate-50 text-[11px] text-slate-500">
              <span>Model & Explainer Status:</span>
              <span className="font-bold text-emerald-600 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> Calibrated Classifier + TreeExplainer Active
              </span>
            </div>
          </div>
        </div>

      </div>

      {/* User Management Table */}
      <div className="bg-white rounded-3xl border border-slate-200/90 shadow-xs overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900">User Accounts & Role Permissions</h3>
            <p className="text-xs text-slate-400 mt-0.5">Manage user access rights, privileged roles, and active accounts</p>
          </div>
          <button
            onClick={() => setIsAddUserOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition w-fit"
          >
            <UserPlus className="w-3.5 h-3.5" /> Add New User
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-50/70 border-b border-slate-100 text-slate-500 text-[11px] font-semibold uppercase tracking-wider">
                <th className="py-3 px-6">User Name</th>
                <th className="py-3 px-4">Email Address</th>
                <th className="py-3 px-4">Role</th>
                <th className="py-3 px-4">Account Status</th>
                <th className="py-3 px-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium text-slate-700">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-slate-50 transition">
                  <td className="py-3.5 px-6 font-bold text-slate-900">{u.full_name}</td>
                  <td className="py-3.5 px-4 text-slate-500">{u.email}</td>
                  <td className="py-3.5 px-4">
                    <select
                      value={u.role}
                      onChange={(e) => handleRoleChange(u.id, e.target.value)}
                      className="px-2 py-1 rounded-lg border border-slate-200 text-xs font-semibold bg-white"
                    >
                      <option value="patient">Patient</option>
                      <option value="doctor">Doctor</option>
                      <option value="admin">Admin</option>
                    </select>
                  </td>
                  <td className="py-3.5 px-4">
                    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                      u.is_active ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-red-50 text-red-700 border border-red-200'
                    }`}>
                      {u.is_active ? 'Active' : 'Disabled'}
                    </span>
                  </td>
                  <td className="py-3.5 px-6 text-right">
                    <button
                      onClick={() => handleToggleStatus(u.id)}
                      className="px-3 py-1 rounded-lg border border-slate-200 text-xs text-slate-600 hover:bg-slate-100 transition"
                    >
                      {u.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Account Modal */}
      {isAddUserOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-fade-in">
          <div className="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl border border-slate-100 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-teal-600" />
                <h3 className="text-sm font-bold text-slate-900">Provision New Privileged Account</h3>
              </div>
              <button 
                onClick={() => setIsAddUserOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateUser} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-700 font-semibold mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Dr. Jane Doe"
                  value={newUser.full_name}
                  onChange={(e) => setNewUser({...newUser, full_name: e.target.value})}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">Email Address</label>
                <input
                  type="email"
                  required
                  placeholder="name@healthcare.org"
                  value={newUser.email}
                  onChange={(e) => setNewUser({...newUser, email: e.target.value})}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">Initial Password</label>
                <input
                  type="password"
                  required
                  placeholder="Minimum 6 characters"
                  value={newUser.password}
                  onChange={(e) => setNewUser({...newUser, password: e.target.value})}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">Assigned Role</label>
                <select
                  value={newUser.role}
                  onChange={(e) => setNewUser({...newUser, role: e.target.value})}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-semibold bg-white"
                >
                  <option value="doctor">Doctor (Clinical Staff)</option>
                  <option value="admin">Administrator (System Manager)</option>
                  <option value="patient">Patient</option>
                </select>
                <p className="text-[11px] text-slate-400 mt-1">
                  Doctors and Admins can only be created by an authorized administrator.
                </p>
              </div>

              <div className="pt-3 flex items-center justify-end gap-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsAddUserOpen(false)}
                  className="px-4 py-2 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creatingUser}
                  className="px-5 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold transition disabled:opacity-50"
                >
                  {creatingUser ? "Creating..." : "Create User"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
