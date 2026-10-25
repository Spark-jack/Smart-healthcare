import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, User, LogOut, Shield, Stethoscope, HeartPulse, 
  Bell, CheckCheck, AlertOctagon, Calendar, ArrowRight, X 
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';

export const Navbar = ({ activeTab, setActiveTab }) => {
  const { user, logout, isDoctor, isPatient, isAdmin } = useAuth();
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [loadingNotifs, setLoadingNotifs] = useState(false);
  const dropdownRef = useRef(null);

  // Poll unread count every 30 seconds
  const fetchUnreadCount = async () => {
    try {
      const data = await api.getUnreadNotificationCount();
      setUnreadCount(data.unread_count || 0);
    } catch (err) {
      // Ignore polling errors
    }
  };

  const fetchNotifications = async () => {
    setLoadingNotifs(true);
    try {
      const data = await api.getNotifications(1, 15);
      setNotifications(data.items || []);
      setUnreadCount(data.unread_count || 0);
    } catch (err) {
      console.error("Failed to load notifications:", err);
    } finally {
      setLoadingNotifs(false);
    }
  };

  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 30000); // 30s polling
    return () => clearInterval(interval);
  }, []);

  const handleToggleDropdown = () => {
    if (!dropdownOpen) {
      fetchNotifications();
    }
    setDropdownOpen(!dropdownOpen);
  };

  const handleMarkAsRead = async (id, e) => {
    e.stopPropagation();
    try {
      await api.markNotificationRead(id);
      setNotifications(notifications.map(n => n.id === id ? { ...n, is_read: true } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (err) {
      console.error("Failed to mark notification read:", err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.markAllNotificationsRead();
      setNotifications(notifications.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error("Failed to mark all notifications read:", err);
    }
  };

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <header className="sticky top-0 z-40 bg-white/90 backdrop-blur-md border-b border-slate-200/80 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand Logo & Name */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-600 to-emerald-500 flex items-center justify-center text-white shadow-md shadow-teal-500/20">
            <HeartPulse className="w-6 h-6 stroke-[2.2]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold tracking-tight text-slate-900">SmartHealth<span className="text-teal-600">.AI</span></span>
              <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-md bg-teal-50 text-teal-700 border border-teal-200/60">
                PRJ-02
              </span>
            </div>
            <p className="text-xs text-slate-500 font-medium hidden sm:block">Predictive Clinical Risk & Urgency Triage</p>
          </div>
        </div>

        {/* Navigation Tabs based on Role */}
        <div className="hidden md:flex items-center gap-1 bg-slate-100/80 p-1 rounded-xl border border-slate-200/60">
          {(isPatient || isAdmin) && (
            <button
              onClick={() => setActiveTab('patient')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'patient'
                  ? 'bg-white text-teal-700 shadow-xs font-bold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <User className="w-3.5 h-3.5" />
              Patient Health Portal
            </button>
          )}

          {(isDoctor || isAdmin) && (
            <button
              onClick={() => setActiveTab('doctor')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'doctor'
                  ? 'bg-white text-teal-700 shadow-xs font-bold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Stethoscope className="w-3.5 h-3.5" />
              Doctor Analytics & Triage
            </button>
          )}

          {isAdmin && (
            <button
              onClick={() => setActiveTab('admin')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'admin'
                  ? 'bg-white text-teal-700 shadow-xs font-bold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Shield className="w-3.5 h-3.5" />
              System Admin
            </button>
          )}
        </div>

        {/* User Info & Actions */}
        <div className="flex items-center gap-3">
          
          {/* Notifications Bell with Dropdown */}
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={handleToggleDropdown}
              title="Notifications & Clinical Alerts"
              className="relative p-2 rounded-xl text-slate-500 hover:text-teal-700 hover:bg-teal-50 border border-transparent hover:border-teal-200 transition-all"
            >
              <Bell className="w-4 h-4" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 flex h-4 min-w-[16px] px-1 items-center justify-center rounded-full bg-rose-500 text-[9px] font-bold text-white shadow-xs animate-pulse">
                  {unreadCount > 99 ? '99+' : unreadCount}
                </span>
              )}
            </button>

            {/* Dropdown Panel */}
            {dropdownOpen && (
              <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden z-50 animate-fade-in">
                <div className="p-3.5 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-800">Notifications</span>
                    {unreadCount > 0 && (
                      <span className="px-2 py-0.5 rounded-full bg-rose-50 text-rose-600 text-[10px] font-bold border border-rose-200">
                        {unreadCount} unread
                      </span>
                    )}
                  </div>
                  {unreadCount > 0 && (
                    <button
                      onClick={handleMarkAllRead}
                      className="text-[11px] font-bold text-teal-600 hover:text-teal-700 flex items-center gap-1 hover:underline"
                    >
                      <CheckCheck className="w-3.5 h-3.5" /> Mark all read
                    </button>
                  )}
                </div>

                <div className="max-h-80 overflow-y-auto divide-y divide-slate-100">
                  {loadingNotifs ? (
                    <div className="p-6 text-center text-xs text-slate-400">Loading alerts...</div>
                  ) : notifications.length === 0 ? (
                    <div className="p-6 text-center text-xs text-slate-400">
                      No notifications yet
                    </div>
                  ) : (
                    notifications.map((notif) => {
                      const isHighRisk = notif.type === "HIGH_RISK_FLAG";
                      const isReminder = notif.type === "APPOINTMENT_REMINDER";
                      return (
                        <div
                          key={notif.id}
                          className={`p-3.5 transition flex gap-3 items-start ${
                            notif.is_read ? 'bg-white opacity-80' : isHighRisk ? 'bg-rose-50/60' : 'bg-teal-50/30'
                          } hover:bg-slate-50`}
                        >
                          <div className={`p-1.5 rounded-lg shrink-0 mt-0.5 ${
                            isHighRisk ? 'bg-rose-100 text-rose-600' : isReminder ? 'bg-amber-100 text-amber-700' : 'bg-teal-100 text-teal-700'
                          }`}>
                            {isHighRisk ? <AlertOctagon className="w-3.5 h-3.5" /> : <Calendar className="w-3.5 h-3.5" />}
                          </div>

                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between gap-1">
                              <span className={`text-xs font-bold truncate ${isHighRisk ? 'text-rose-900' : 'text-slate-800'}`}>
                                {notif.title}
                              </span>
                              {!notif.is_read && (
                                <button
                                  onClick={(e) => handleMarkAsRead(notif.id, e)}
                                  title="Mark as read"
                                  className="text-[10px] text-teal-600 hover:underline shrink-0 font-semibold"
                                >
                                  Read
                                </button>
                              )}
                            </div>
                            <p className="text-[11px] text-slate-600 mt-0.5 line-clamp-2 leading-relaxed">
                              {notif.body}
                            </p>
                            <span className="text-[9px] text-slate-400 mt-1 block">
                              {new Date(notif.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} • {new Date(notif.created_at).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>

                <div className="p-2.5 bg-slate-50/60 border-t border-slate-100 text-center">
                  <span className="text-[10px] text-slate-400">
                    Clinical alerts updated live
                  </span>
                </div>
              </div>
            )}
          </div>

          <div className="text-right hidden sm:block">
            <div className="text-xs font-bold text-slate-800">{user?.full_name}</div>
            <div className="text-[11px] font-medium text-slate-500 capitalize flex items-center justify-end gap-1">
              <span className={`w-1.5 h-1.5 rounded-full ${isDoctor ? 'bg-indigo-500' : isAdmin ? 'bg-purple-500' : 'bg-teal-500'}`}></span>
              {user?.role} {user?.specialization ? `• ${user.specialization}` : ''}
            </div>
          </div>

          <button
            onClick={logout}
            title="Sign Out"
            className="p-2 rounded-xl text-slate-500 hover:text-red-600 hover:bg-red-50 border border-transparent hover:border-red-200 transition-all"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>

      </div>
    </header>
  );
};
