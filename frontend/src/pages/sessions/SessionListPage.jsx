import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../api/client';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import AlertBanner from '../../components/common/AlertBanner';
import Badge from '../../components/common/Badge';
import Pagination from '../../components/common/Pagination';
import {
  BookOpen,
  PlusCircle,
  Calendar,
  Clock,
  User,
  Users,
  Eye,
  Award,
} from 'lucide-react';

export const SessionListPage = () => {
  const { activeCenter } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, size: 10, total_pages: 1, total_items: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Selected session for detail view modal
  const [selectedSession, setSelectedSession] = useState(null);

  const fetchSessions = async (page = 1) => {
    setLoading(true);
    setError('');
    try {
      const params = { page, size: 10 };
      if (activeCenter?.id) params.center_id = activeCenter.id;

      const { data } = await api.get('/sessions', { params });
      setSessions(data.items || []);
      setPagination(
        data.pagination || {
          page: 1,
          size: 10,
          total_pages: 1,
          total_items: data.items?.length || 0,
        }
      );
    } catch (err) {
      console.error('Error fetching sessions', err);
      setError(err.response?.data?.detail || 'Failed to load learning sessions.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions(1);
  }, [activeCenter]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Learning Sessions</h2>
          <p className="text-sm text-slate-500 mt-0.5">
            Conducted classroom activities & competency evaluations
          </p>
        </div>

        <Link
          to="/sessions/new"
          className="inline-flex items-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 shadow-xs transition-colors self-start sm:self-auto"
        >
          <PlusCircle className="w-4 h-4" />
          <span>Log Learning Session</span>
        </Link>
      </div>

      {error && <AlertBanner type="error" message={error} onClose={() => setError('')} />}

      {/* Session Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
        {loading ? (
          <LoadingSpinner text="Fetching session logs..." size="md" />
        ) : sessions.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <BookOpen className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-slate-800">No sessions recorded yet</h3>
            <p className="text-sm text-slate-400 mt-1">
              Start by logging your first completed classroom learning session.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left">
              <thead className="bg-slate-50 text-xs font-bold text-slate-500 uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3">Topic / Activity</th>
                  <th className="px-6 py-3">Date & Time</th>
                  <th className="px-6 py-3">Conducted By</th>
                  <th className="px-6 py-3 text-center">Participants</th>
                  <th className="px-6 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-sm">
                {sessions.map((sess) => (
                  <tr key={sess.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-semibold text-slate-900">{sess.topic_summary}</div>
                      <div className="text-xs text-indigo-600 font-medium">
                        {sess.activity_title || 'Custom Activity'}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-600">
                      <div>{sess.session_date}</div>
                      <div className="text-xs text-slate-400">
                        {new Date(sess.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} -{' '}
                        {new Date(sess.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-700">
                      <div className="flex items-center space-x-1.5">
                        <User className="w-3.5 h-3.5 text-slate-400" />
                        <span>{sess.teacher_name || 'Teacher'}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700">
                        <Users className="w-3 h-3 mr-1" />
                        {sess.student_roster?.length || 0} students
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => setSelectedSession(sess)}
                        className="inline-flex items-center space-x-1 px-2.5 py-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 rounded transition-colors"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>View Details</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <Pagination
          page={pagination.page}
          pageSize={pagination.size}
          total={pagination.total_items}
          totalPages={pagination.total_pages}
          onPageChange={(p) => fetchSessions(p)}
        />
      </div>

      {/* Detail Modal */}
      {selectedSession && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full p-6 space-y-4 max-h-[85vh] overflow-y-auto">
            <div className="flex items-start justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-lg font-bold text-slate-900">
                  {selectedSession.topic_summary}
                </h3>
                <p className="text-xs text-indigo-600 font-semibold mt-0.5">
                  {selectedSession.activity_title || 'Classroom Activity'} • {selectedSession.session_date}
                </p>
              </div>
              <button
                onClick={() => setSelectedSession(null)}
                className="text-slate-400 hover:text-slate-600 text-sm font-bold p-1"
              >
                ✕
              </button>
            </div>

            {selectedSession.general_notes && (
              <div className="bg-slate-50 p-3 rounded-lg text-xs text-slate-600 italic">
                <strong>Teacher Notes:</strong> {selectedSession.general_notes}
              </div>
            )}

            <div>
              <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                Participating Students & Skill Evaluations
              </h4>

              {(!selectedSession.student_roster || selectedSession.student_roster.length === 0) ? (
                <p className="text-xs text-slate-400 italic">No students recorded in this session roster.</p>
              ) : (
                <div className="space-y-3">
                  {selectedSession.student_roster.map((sr) => (
                    <div
                      key={sr.id}
                      className="p-3 border border-slate-200 rounded-lg bg-white space-y-2 text-xs"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-900 text-sm">
                          {sr.student_name || 'Student ID: ' + sr.student_id.slice(0, 8)}
                        </span>
                        <div className="flex items-center space-x-2">
                          {sr.score !== null && sr.score !== undefined && (
                            <span className="font-mono font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">
                              Score: {sr.score}%
                            </span>
                          )}
                          <Badge value={sr.participation_status} />
                        </div>
                      </div>

                      {sr.qualitative_feedback && (
                        <p className="text-slate-600 italic">Feedback: "{sr.qualitative_feedback}"</p>
                      )}

                      {sr.evaluations && sr.evaluations.length > 0 && (
                        <div className="pt-2 border-t border-slate-100 space-y-1">
                          <span className="text-[11px] font-semibold text-slate-400 uppercase">
                            Evaluated Competencies:
                          </span>
                          <div className="flex flex-wrap gap-2">
                            {sr.evaluations.map((ev) => (
                              <div
                                key={ev.id}
                                className="flex items-center space-x-1.5 bg-slate-50 border border-slate-200 px-2.5 py-1 rounded-md"
                              >
                                <span className="font-mono text-[11px] text-slate-700 font-semibold">
                                  {ev.competency_code || 'Skill'}:
                                </span>
                                <Badge value={ev.mastery_level} />
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex justify-end pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setSelectedSession(null)}
                className="px-4 py-2 bg-slate-800 text-white rounded-lg text-sm font-semibold hover:bg-slate-900"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SessionListPage;

