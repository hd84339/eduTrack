import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../api/client';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import AlertBanner from '../../components/common/AlertBanner';
import {
  Users,
  CalendarCheck,
  BookOpen,
  ArrowRightLeft,
  Building2,
  TrendingUp,
  Award,
  PlusCircle,
  Clock,
} from 'lucide-react';

export const DashboardPage = () => {
  const { user, activeCenter, isSuperAdmin, isCenterManager, isTeacher } = useAuth();
  const [metrics, setMetrics] = useState(null);
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDashboardData = async () => {
      setLoading(true);
      setError('');
      try {
        if (isSuperAdmin) {
          try {
            const { data: ov } = await api.get('/analytics/overview');
            setOverview(ov);
          } catch (e) {
            console.error('Overview analytics error', e);
          }
        }

        if (activeCenter && (isSuperAdmin || isCenterManager)) {
          try {
            const { data: cm } = await api.get(`/analytics/centers/${activeCenter.id}`);
            setMetrics(cm);
          } catch (e) {
            console.error('Center analytics error', e);
          }
        } else if (activeCenter && isTeacher) {
          // Teacher quick roster summary
          try {
            const { data: studs } = await api.get('/students?status=ACTIVE&page_size=1');
            const { data: sess } = await api.get('/sessions?page_size=5');
            setMetrics({
              active_student_count: studs.total || 0,
              recent_sessions: sess.items || [],
            });
          } catch (e) {
            console.error('Teacher dashboard fetch error', e);
          }
        }
      } catch (err) {
        setError('Failed to load dashboard metrics.');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [activeCenter, isSuperAdmin, isCenterManager, isTeacher]);

  if (loading) {
    return <LoadingSpinner fullPage text="Loading dashboard metrics..." />;
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white rounded-xl shadow-xs border border-slate-200 p-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">
            Welcome back, {user?.full_name}
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            {activeCenter ? (
              <span>
                Active Center:{' '}
                <strong className="text-slate-800">
                  {activeCenter.name} ({activeCenter.code})
                </strong>
              </span>
            ) : (
              'All Centers Overview'
            )}
          </p>
        </div>

        {/* Quick actions */}
        <div className="flex flex-wrap items-center gap-2">
          {(isSuperAdmin || isCenterManager) && (
            <Link
              to="/students/new"
              className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-lg hover:bg-indigo-700 shadow-xs transition-colors"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Enroll Student</span>
            </Link>
          )}
          <Link
            to="/attendance"
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-white border border-slate-300 text-slate-700 text-sm font-semibold rounded-lg hover:bg-slate-50 shadow-xs transition-colors"
          >
            <CalendarCheck className="w-4 h-4 text-emerald-600" />
            <span>Mark Attendance</span>
          </Link>
          <Link
            to="/sessions/new"
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-white border border-slate-300 text-slate-700 text-sm font-semibold rounded-lg hover:bg-slate-50 shadow-xs transition-colors"
          >
            <BookOpen className="w-4 h-4 text-indigo-600" />
            <span>Log Session</span>
          </Link>
        </div>
      </div>

      {error && <AlertBanner type="warning" message={error} />}

      {/* Super Admin Organization Benchmarks */}
      {isSuperAdmin && overview && (
        <div>
          <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-3">
            Organization-Wide Benchmarks
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between text-slate-500 mb-2">
                <span className="text-xs font-semibold uppercase">Active Centers</span>
                <Building2 className="w-5 h-5 text-indigo-500" />
              </div>
              <div className="text-2xl font-bold text-slate-900">{overview.total_centers}</div>
              <div className="text-xs text-slate-500 mt-1">Multi-center network</div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between text-slate-500 mb-2">
                <span className="text-xs font-semibold uppercase">Total Students</span>
                <Users className="w-5 h-5 text-sky-500" />
              </div>
              <div className="text-2xl font-bold text-slate-900">{overview.total_active_students}</div>
              <div className="text-xs text-slate-500 mt-1">Active enrollments</div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between text-slate-500 mb-2">
                <span className="text-xs font-semibold uppercase">Today's Attendance</span>
                <CalendarCheck className="w-5 h-5 text-emerald-500" />
              </div>
              <div className="text-2xl font-bold text-slate-900">
                {overview.system_wide_attendance_rate_today}%
              </div>
              <div className="text-xs text-slate-500 mt-1">Network-wide present/late</div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between text-slate-500 mb-2">
                <span className="text-xs font-semibold uppercase">Monthly Sessions</span>
                <BookOpen className="w-5 h-5 text-purple-500" />
              </div>
              <div className="text-2xl font-bold text-slate-900">{overview.monthly_sessions_count}</div>
              <div className="text-xs text-slate-500 mt-1">Conducted this month</div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between text-slate-500 mb-2">
                <span className="text-xs font-semibold uppercase">Pending Transfers</span>
                <ArrowRightLeft className="w-5 h-5 text-amber-500" />
              </div>
              <div className="text-2xl font-bold text-amber-700">{overview.pending_transfers_count}</div>
              <div className="text-xs text-slate-500 mt-1">Awaiting center approval</div>
            </div>
          </div>
        </div>
      )}

      {/* Center Specific Operational Metrics */}
      {metrics && (
        <div>
          <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-3">
            {activeCenter ? `${activeCenter.name} Operations` : 'Center Metrics'}
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between text-slate-500 mb-2">
                <span className="text-xs font-semibold uppercase">Enrolled Students</span>
                <Users className="w-5 h-5 text-indigo-500" />
              </div>
              <div className="text-2xl font-bold text-slate-900">
                {metrics.active_student_count || 0}
                {metrics.capacity && (
                  <span className="text-sm font-normal text-slate-500 ml-1">/ {metrics.capacity}</span>
                )}
              </div>
              {metrics.capacity_occupancy_percentage !== undefined && (
                <div className="mt-2 w-full bg-slate-100 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      metrics.capacity_occupancy_percentage > 90
                        ? 'bg-rose-500'
                        : metrics.capacity_occupancy_percentage > 70
                        ? 'bg-amber-500'
                        : 'bg-emerald-500'
                    }`}
                    style={{ width: `${Math.min(metrics.capacity_occupancy_percentage, 100)}%` }}
                  />
                </div>
              )}
            </div>

            {metrics.attendance_rate_today !== undefined && (
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                <div className="flex items-center justify-between text-slate-500 mb-2">
                  <span className="text-xs font-semibold uppercase">Today's Attendance</span>
                  <CalendarCheck className="w-5 h-5 text-emerald-500" />
                </div>
                <div className="text-2xl font-bold text-slate-900">
                  {metrics.attendance_rate_today}%
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  30-day average: {metrics.attendance_rate_30_days || 0}%
                </div>
              </div>
            )}

            {metrics.weekly_completed_sessions_count !== undefined && (
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                <div className="flex items-center justify-between text-slate-500 mb-2">
                  <span className="text-xs font-semibold uppercase">Weekly Sessions</span>
                  <BookOpen className="w-5 h-5 text-sky-500" />
                </div>
                <div className="text-2xl font-bold text-slate-900">
                  {metrics.weekly_completed_sessions_count}
                </div>
                <div className="text-xs text-slate-500 mt-1">Past 7 days activity</div>
              </div>
            )}

            {metrics.pending_incoming_transfers !== undefined && (
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                <div className="flex items-center justify-between text-slate-500 mb-2">
                  <span className="text-xs font-semibold uppercase">Pending Transfers</span>
                  <ArrowRightLeft className="w-5 h-5 text-amber-500" />
                </div>
                <div className="text-2xl font-bold text-amber-700">
                  {metrics.pending_incoming_transfers} incoming
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  {metrics.pending_outgoing_transfers || 0} outgoing
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Feature Navigation Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
        <Link
          to="/students"
          className="group block p-6 bg-white border border-slate-200 rounded-xl hover:border-indigo-400 hover:shadow-md transition-all"
        >
          <div className="w-10 h-10 rounded-lg bg-indigo-50 group-hover:bg-indigo-600 group-hover:text-white flex items-center justify-center text-indigo-600 transition-colors mb-4">
            <Users className="w-5 h-5" />
          </div>
          <h4 className="text-base font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
            Student Management
          </h4>
          <p className="text-sm text-slate-500 mt-1">
            Browse student roster, register new students, track guardian info, and view learning profiles.
          </p>
        </Link>

        <Link
          to="/attendance"
          className="group block p-6 bg-white border border-slate-200 rounded-xl hover:border-emerald-400 hover:shadow-md transition-all"
        >
          <div className="w-10 h-10 rounded-lg bg-emerald-50 group-hover:bg-emerald-600 group-hover:text-white flex items-center justify-center text-emerald-600 transition-colors mb-4">
            <CalendarCheck className="w-5 h-5" />
          </div>
          <h4 className="text-base font-bold text-slate-900 group-hover:text-emerald-600 transition-colors">
            Daily Attendance
          </h4>
          <p className="text-sm text-slate-500 mt-1">
            Mark center rosters with Present, Late, Absent, or Excused, with audit trail and 24h corrections.
          </p>
        </Link>

        <Link
          to="/competencies"
          className="group block p-6 bg-white border border-slate-200 rounded-xl hover:border-purple-400 hover:shadow-md transition-all"
        >
          <div className="w-10 h-10 rounded-lg bg-purple-50 group-hover:bg-purple-600 group-hover:text-white flex items-center justify-center text-purple-600 transition-colors mb-4">
            <Award className="w-5 h-5" />
          </div>
          <h4 className="text-base font-bold text-slate-900 group-hover:text-purple-600 transition-colors">
            Competency Catalog
          </h4>
          <p className="text-sm text-slate-500 mt-1">
            Standardized 4-tier rubrics across Cognitive, Social-Emotional, Physical, and Creative domains.
          </p>
        </Link>
      </div>
    </div>
  );
};

export default DashboardPage;

