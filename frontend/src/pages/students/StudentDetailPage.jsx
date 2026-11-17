import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../api/client';
import Badge from '../../components/common/Badge';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import AlertBanner from '../../components/common/AlertBanner';
import {
  ArrowLeft,
  Edit,
  ArrowRightLeft,
  User,
  Phone,
  Mail,
  Calendar,
  Building2,
  Award,
  BookOpen,
  Clock,
  ShieldCheck,
  HeartPulse,
} from 'lucide-react';

export const StudentDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { activeCenter, assignedCenters, isSuperAdmin, isCenterManager } = useAuth();

  const [student, setStudent] = useState(null);
  const [progress, setProgress] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Transfer Modal State
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [targetCenterId, setTargetCenterId] = useState('');
  const [effectiveDate, setEffectiveDate] = useState(
    new Date(Date.now() + 86400000).toISOString().split('T')[0]
  );
  const [transferReason, setTransferReason] = useState('');
  const [transferSubmitting, setTransferSubmitting] = useState(false);
  const [transferSuccess, setTransferSuccess] = useState('');

  useEffect(() => {
    const fetchStudentData = async () => {
      setLoading(true);
      setError('');
      try {
        const { data: studentData } = await api.get(`/students/${id}`);
        setStudent(studentData);

        // Fetch competency progress
        try {
          const { data: progData } = await api.get(`/progress/students/${id}`);
          setProgress(progData.competencies || []);
        } catch (e) {
          console.error('Error fetching student progress', e);
        }
      } catch (err) {
        console.error('Error loading student', err);
        setError(err.response?.data?.detail || 'Failed to load student details.');
      } finally {
        setLoading(false);
      }
    };

    if (id) fetchStudentData();
  }, [id, activeCenter]);

  const handleInitiateTransfer = async (e) => {
    e.preventDefault();
    if (!targetCenterId || !transferReason.trim()) {
      alert('Please select a destination center and state the transfer reason.');
      return;
    }

    setTransferSubmitting(true);
    try {
      await api.post('/transfers', {
        student_id: student.id,
        to_center_id: targetCenterId,
        effective_date: effectiveDate,
        request_reason: transferReason.trim(),
      });
      setShowTransferModal(false);
      setTransferSuccess('Transfer request submitted successfully. Awaiting approval by destination center.');
      // Refresh student data
      const { data } = await api.get(`/students/${id}`);
      setStudent(data);
    } catch (err) {
      console.error('Transfer error', err);
      alert(err.response?.data?.detail || 'Failed to submit transfer request.');
    } finally {
      setTransferSubmitting(false);
    }
  };

  if (loading) {
    return <LoadingSpinner fullPage text="Loading student learning profile..." />;
  }

  if (error || !student) {
    return (
      <div className="space-y-4">
        <Link to="/students" className="inline-flex items-center text-sm font-semibold text-indigo-600 hover:underline">
          <ArrowLeft className="w-4 h-4 mr-1" />
          Back to Student Directory
        </Link>
        <AlertBanner type="error" message={error || 'Student record could not be loaded.'} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center space-x-3">
          <Link
            to="/students"
            className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-2xl font-bold text-slate-900">
                {student.first_name} {student.last_name}
              </h2>
              <Badge value={student.status} />
            </div>
            <p className="text-sm text-slate-500 font-mono mt-0.5">
              ID: {student.student_id_number} • Version: {student.version}
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-3">
          {(isSuperAdmin || isCenterManager) && (
            <>
              {student.status === 'ACTIVE' && (
                <button
                  onClick={() => setShowTransferModal(true)}
                  className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-amber-50 text-amber-800 border border-amber-300 rounded-lg text-sm font-semibold hover:bg-amber-100 transition-colors"
                >
                  <ArrowRightLeft className="w-4 h-4" />
                  <span>Request Transfer</span>
                </button>
              )}
              <Link
                to={`/students/${student.id}/edit`}
                className="inline-flex items-center space-x-1.5 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 shadow-xs transition-colors"
              >
                <Edit className="w-4 h-4" />
                <span>Edit Profile</span>
              </Link>
            </>
          )}
        </div>
      </div>

      {transferSuccess && (
        <AlertBanner type="success" message={transferSuccess} onClose={() => setTransferSuccess('')} />
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Demographics and Contacts */}
        <div className="space-y-6 lg:col-span-1">
          {/* Bio Card */}
          <div className="bg-white border border-slate-200 rounded-xl shadow-xs p-6 space-y-4">
            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider pb-2 border-b border-slate-100">
              Student Information
            </h3>
            <div className="space-y-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Center:</span>
                <span className="font-semibold text-slate-900">
                  {student.center_name || activeCenter?.name}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Date of Birth:</span>
                <span className="font-semibold text-slate-900">{student.date_of_birth}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Gender:</span>
                <span className="font-semibold text-slate-900 capitalize">{student.gender}</span>
              </div>
              {student.active_enrollment && (
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Enrolled Since:</span>
                  <span className="font-semibold text-indigo-700">
                    {student.active_enrollment.start_date}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Guardian & Emergency Card */}
          <div className="bg-white border border-slate-200 rounded-xl shadow-xs p-6 space-y-4">
            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider pb-2 border-b border-slate-100">
              Guardian & Emergency
            </h3>
            <div className="space-y-3 text-sm">
              <div>
                <span className="text-xs text-slate-400 uppercase font-semibold">Primary Guardian</span>
                <div className="font-semibold text-slate-900 mt-0.5">
                  {student.guardian_name}{' '}
                  <span className="text-xs font-normal text-slate-500">
                    ({student.guardian_relationship})
                  </span>
                </div>
              </div>

              <div className="flex items-center space-x-2 text-slate-700">
                <Phone className="w-4 h-4 text-slate-400" />
                <span className="font-mono text-sm">{student.guardian_phone}</span>
              </div>

              {student.guardian_email && (
                <div className="flex items-center space-x-2 text-slate-700">
                  <Mail className="w-4 h-4 text-slate-400" />
                  <span className="text-sm">{student.guardian_email}</span>
                </div>
              )}

              {student.emergency_contact && (
                <div className="pt-2 border-t border-slate-100">
                  <span className="text-xs text-slate-400 uppercase font-semibold">Emergency Contact</span>
                  <div className="text-sm text-slate-700 mt-0.5">{student.emergency_contact}</div>
                </div>
              )}

              {student.notes && (
                <div className="pt-2 border-t border-slate-100">
                  <span className="text-xs text-slate-400 uppercase font-semibold">Special Notes</span>
                  <div className="text-sm text-slate-600 bg-slate-50 p-2.5 rounded-lg mt-1 italic">
                    {student.notes}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Longitudinal Competency Mastery */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
            <div className="p-6 border-b border-slate-200 flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-slate-900">
                  Longitudinal Competency Progression
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Standardized 4-tier rubric evaluation tracked across learning sessions
                </p>
              </div>
              <Award className="w-6 h-6 text-indigo-500" />
            </div>

            {progress.length === 0 ? (
              <div className="p-8 text-center text-slate-500">
                <Award className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                <p className="text-sm font-medium">No skill evaluations recorded yet</p>
                <p className="text-xs text-slate-400 mt-1">
                  Evaluations are registered during conducted learning sessions.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 text-left">
                  <thead className="bg-slate-50 text-xs font-bold text-slate-500 uppercase tracking-wider">
                    <tr>
                      <th className="px-6 py-3">Competency</th>
                      <th className="px-6 py-3">Domain</th>
                      <th className="px-6 py-3">Mastery Level</th>
                      <th className="px-6 py-3 text-center">Sessions Evaluated</th>
                      <th className="px-6 py-3 text-right">Last Evaluated</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 text-sm">
                    {progress.map((item) => (
                      <tr key={item.id} className="hover:bg-slate-50/70 transition-colors">
                        <td className="px-6 py-4">
                          <div className="font-semibold text-slate-900">{item.name || item.code}</div>
                          <div className="text-xs font-mono text-slate-400">{item.code}</div>
                        </td>
                        <td className="px-6 py-4 text-slate-600 font-medium">
                          {item.domain}
                        </td>
                        <td className="px-6 py-4">
                          <Badge value={item.current_level} />
                        </td>
                        <td className="px-6 py-4 text-center font-semibold text-slate-700">
                          {item.total_sessions_count}
                        </td>
                        <td className="px-6 py-4 text-right text-xs text-slate-500">
                          {item.last_evaluated_at ? new Date(item.last_evaluated_at).toLocaleDateString() : 'N/A'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Transfer Request Modal */}
      {showTransferModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6 space-y-4">
            <h3 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
              <ArrowRightLeft className="w-5 h-5 text-indigo-600" />
              <span>Initiate Center Transfer</span>
            </h3>
            <p className="text-sm text-slate-600">
              Request to transfer <strong>{student.first_name} {student.last_name}</strong> from{' '}
              <strong>{activeCenter?.name}</strong> to another learning center.
            </p>

            <form onSubmit={handleInitiateTransfer} className="space-y-4 pt-2">
              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                  Destination Center *
                </label>
                <select
                  required
                  value={targetCenterId}
                  onChange={(e) => setTargetCenterId(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                >
                  <option value="">-- Select Destination Center --</option>
                  {assignedCenters
                    .filter((c) => c.id !== activeCenter?.id)
                    .map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name} ({c.code})
                      </option>
                    ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                  Effective Transfer Date *
                </label>
                <input
                  type="date"
                  required
                  value={effectiveDate}
                  onChange={(e) => setEffectiveDate(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                  Reason for Transfer *
                </label>
                <textarea
                  required
                  rows="3"
                  value={transferReason}
                  onChange={(e) => setTransferReason(e.target.value)}
                  placeholder="e.g. Family relocation closer to destination center..."
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowTransferModal(false)}
                  className="px-4 py-2 border border-slate-300 rounded-lg text-sm font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={transferSubmitting}
                  className="px-5 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50"
                >
                  {transferSubmitting ? 'Submitting...' : 'Submit Request'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default StudentDetailPage;

