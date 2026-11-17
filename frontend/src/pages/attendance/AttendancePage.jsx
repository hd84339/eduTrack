import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../api/client';
import Badge from '../../components/common/Badge';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import AlertBanner from '../../components/common/AlertBanner';
import {
  CalendarCheck,
  Calendar,
  CheckCircle,
  Clock,
  Save,
  Edit,
  UserCheck,
  AlertCircle,
} from 'lucide-react';

export const AttendancePage = () => {
  const { activeCenter } = useAuth();
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [records, setRecords] = useState([]);
  const [unrecordedStudents, setUnrecordedStudents] = useState([]);
  const [bulkEntries, setBulkEntries] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Correction Modal State
  const [correctingRecord, setCorrectingRecord] = useState(null);
  const [correctedStatus, setCorrectedStatus] = useState('PRESENT');
  const [correctionReason, setCorrectionReason] = useState('');
  const [correctionRemarks, setCorrectionRemarks] = useState('');
  const [submittingCorrection, setSubmittingCorrection] = useState(false);
  const [correctionError, setCorrectionError] = useState('');

  const loadAttendanceData = async () => {
    if (!activeCenter?.id) return;
    setLoading(true);
    setError('');
    try {
      // 1. Fetch recorded attendance for the day
      const { data: recordedList } = await api.get('/attendance', {
        params: { date: selectedDate },
      });
      setRecords(recordedList || []);

      // 2. Fetch all active students in the center to identify unrecorded students
      const { data: studentsData } = await api.get('/students', {
        params: { status: 'ACTIVE', size: 100 },
      });
      const allActiveStudents = studentsData.items || [];

      const recordedStudentIds = new Set((recordedList || []).map((r) => r.student_id));
      const unrecorded = allActiveStudents.filter((s) => !recordedStudentIds.has(s.id));
      setUnrecordedStudents(unrecorded);

      // Pre-populate bulk form for unrecorded students (default: PRESENT)
      const initialBulk = {};
      unrecorded.forEach((s) => {
        initialBulk[s.id] = { status: 'PRESENT', remarks: '' };
      });
      setBulkEntries(initialBulk);
    } catch (err) {
      console.error('Attendance fetch error', err);
      setError(err.response?.data?.detail || 'Failed to fetch attendance data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAttendanceData();
  }, [activeCenter, selectedDate]);

  const handleBulkStatusChange = (studentId, status) => {
    setBulkEntries((prev) => ({
      ...prev,
      [studentId]: { ...prev[studentId], status },
    }));
  };

  const handleBulkRemarksChange = (studentId, remarks) => {
    setBulkEntries((prev) => ({
      ...prev,
      [studentId]: { ...prev[studentId], remarks },
    }));
  };

  const handleMarkAll = (status) => {
    setBulkEntries((prev) => {
      const updated = { ...prev };
      Object.keys(updated).forEach((id) => {
        updated[id] = { ...updated[id], status };
      });
      return updated;
    });
  };

  const handleSubmitBulk = async (e) => {
    e.preventDefault();
    if (!activeCenter?.id) return;

    const items = Object.entries(bulkEntries).map(([studentId, entry]) => ({
      student_id: studentId,
      status: entry.status,
      remarks: entry.remarks.trim() ? entry.remarks.trim() : null,
    }));

    if (items.length === 0) return;

    setSaving(true);
    setError('');
    setSuccess('');

    try {
      await api.post('/attendance/bulk', {
        center_id: activeCenter.id,
        attendance_date: selectedDate,
        records: items,
      });
      setSuccess(`Successfully recorded attendance for ${items.length} students.`);
      loadAttendanceData();
    } catch (err) {
      console.error('Bulk attendance error', err);
      setError(err.response?.data?.detail || 'Failed to submit bulk attendance.');
    } finally {
      setSaving(false);
    }
  };

  const handleOpenCorrection = (record) => {
    setCorrectingRecord(record);
    setCorrectedStatus(record.status);
    setCorrectionReason('');
    setCorrectionRemarks(record.remarks || '');
    setCorrectionError('');
  };

  const handleSubmitCorrection = async (e) => {
    e.preventDefault();
    if (!correctionReason.trim()) {
      setCorrectionError('Audit justification reason is required for attendance correction.');
      return;
    }

    setSubmittingCorrection(true);
    setCorrectionError('');

    try {
      await api.put(`/attendance/${correctingRecord.id}`, {
        status: correctedStatus,
        reason: correctionReason.trim(),
        remarks: correctionRemarks.trim() || null,
        version: correctingRecord.version,
      });
      setSuccess('Attendance record corrected successfully.');
      setCorrectingRecord(null);
      loadAttendanceData();
    } catch (err) {
      console.error('Correction error', err);
      setCorrectionError(err.response?.data?.detail || 'Failed to correct attendance record.');
    } finally {
      setSubmittingCorrection(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Daily Attendance</h2>
          <p className="text-sm text-slate-500 mt-0.5">
            Classroom roll call & 24-hour audit-tracked corrections
          </p>
        </div>

        {/* Date Selector */}
        <div className="flex items-center space-x-2 bg-white border border-slate-200 rounded-lg px-3 py-1.5 shadow-xs">
          <Calendar className="w-4 h-4 text-indigo-600" />
          <span className="text-xs font-semibold text-slate-500 uppercase">Date:</span>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="text-sm font-semibold text-slate-800 bg-transparent border-none focus:outline-none cursor-pointer"
          />
        </div>
      </div>

      {success && <AlertBanner type="success" message={success} onClose={() => setSuccess('')} />}
      {error && <AlertBanner type="error" message={error} onClose={() => setError('')} />}

      {/* Roster Container */}
      <div className="space-y-6">
        {/* Unrecorded Section: Bulk Form */}
        {unrecordedStudents.length > 0 && (
          <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
            <div className="p-4 sm:p-6 border-b border-slate-200 bg-slate-50 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <h3 className="text-base font-bold text-slate-900">
                  Unrecorded Students ({unrecordedStudents.length})
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Record attendance for {selectedDate}
                </p>
              </div>

              {/* Quick Actions */}
              <div className="flex items-center space-x-2">
                <span className="text-xs font-semibold text-slate-500 uppercase mr-1">Mark all:</span>
                <button
                  type="button"
                  onClick={() => handleMarkAll('PRESENT')}
                  className="px-2.5 py-1 bg-emerald-100 text-emerald-800 rounded text-xs font-bold hover:bg-emerald-200 transition-colors"
                >
                  Present
                </button>
                <button
                  type="button"
                  onClick={() => handleMarkAll('ABSENT')}
                  className="px-2.5 py-1 bg-rose-100 text-rose-800 rounded text-xs font-bold hover:bg-rose-200 transition-colors"
                >
                  Absent
                </button>
              </div>
            </div>

            <form onSubmit={handleSubmitBulk}>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 text-left">
                  <thead className="bg-slate-50 text-xs font-bold text-slate-500 uppercase tracking-wider">
                    <tr>
                      <th className="px-6 py-3">Student Name</th>
                      <th className="px-6 py-3">Status</th>
                      <th className="px-6 py-3">Remarks</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 text-sm">
                    {unrecordedStudents.map((s) => (
                      <tr key={s.id} className="hover:bg-slate-50/70 transition-colors">
                        <td className="px-6 py-3.5">
                          <div className="font-semibold text-slate-900">
                            {s.first_name} {s.last_name}
                          </div>
                          <div className="text-xs font-mono text-slate-400">{s.student_id_number}</div>
                        </td>
                        <td className="px-6 py-3.5">
                          <div className="inline-flex rounded-lg border border-slate-200 p-0.5 bg-slate-50 space-x-1">
                            {['PRESENT', 'LATE', 'ABSENT', 'EXCUSED'].map((st) => (
                              <button
                                key={st}
                                type="button"
                                onClick={() => handleBulkStatusChange(s.id, st)}
                                className={`px-2.5 py-1 rounded text-xs font-bold transition-colors ${
                                  bulkEntries[s.id]?.status === st
                                    ? st === 'PRESENT'
                                      ? 'bg-emerald-600 text-white shadow-xs'
                                      : st === 'LATE'
                                      ? 'bg-amber-500 text-white shadow-xs'
                                      : st === 'ABSENT'
                                      ? 'bg-rose-600 text-white shadow-xs'
                                      : 'bg-slate-700 text-white shadow-xs'
                                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
                                }`}
                              >
                                {st}
                              </button>
                            ))}
                          </div>
                        </td>
                        <td className="px-6 py-3.5">
                          <input
                            type="text"
                            placeholder="Optional note..."
                            value={bulkEntries[s.id]?.remarks || ''}
                            onChange={(e) => handleBulkRemarksChange(s.id, e.target.value)}
                            className="w-full max-w-sm px-2.5 py-1 text-xs border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500"
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="p-4 bg-slate-50 border-t border-slate-200 flex justify-end">
                <button
                  type="submit"
                  disabled={saving}
                  className="inline-flex items-center space-x-2 px-5 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50 transition-colors shadow-xs"
                >
                  <Save className="w-4 h-4" />
                  <span>{saving ? 'Submitting...' : 'Save Attendance Roll Call'}</span>
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Recorded Attendance Section */}
        <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
          <div className="p-4 sm:p-6 border-b border-slate-200 flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-slate-900">
                Logged Attendance Records ({records.length})
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Saved records for {selectedDate}
              </p>
            </div>
            <UserCheck className="w-5 h-5 text-emerald-600" />
          </div>

          {loading ? (
            <LoadingSpinner text="Fetching daily records..." size="md" />
          ) : records.length === 0 ? (
            <div className="p-10 text-center text-slate-500">
              <CalendarCheck className="w-10 h-10 text-slate-300 mx-auto mb-2" />
              <p className="text-sm font-medium">No attendance recorded yet for this date.</p>
              <p className="text-xs text-slate-400 mt-1">
                Use the form above to record classroom roll call.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-left">
                <thead className="bg-slate-50 text-xs font-bold text-slate-500 uppercase tracking-wider">
                  <tr>
                    <th className="px-6 py-3">Student</th>
                    <th className="px-6 py-3">Status</th>
                    <th className="px-6 py-3">Remarks</th>
                    <th className="px-6 py-3">Recorded At</th>
                    <th className="px-6 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 text-sm">
                  {records.map((r) => (
                    <tr key={r.id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="px-6 py-4">
                        <div className="font-semibold text-slate-900">
                          {r.student_name || 'Student'}
                        </div>
                        <div className="text-xs font-mono text-slate-400">
                          {r.student_id_number || r.student_id.slice(0, 8)}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <Badge value={r.status} />
                      </td>
                      <td className="px-6 py-4 text-xs text-slate-600 italic">
                        {r.remarks || '—'}
                      </td>
                      <td className="px-6 py-4 text-xs text-slate-500">
                        {new Date(r.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => handleOpenCorrection(r)}
                          className="inline-flex items-center space-x-1 px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-xs font-semibold transition-colors"
                        >
                          <Edit className="w-3.5 h-3.5" />
                          <span>Correct</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* 24-Hour Correction Modal */}
      {correctingRecord && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
              <Edit className="w-5 h-5 text-indigo-600" />
              <span>Correct Attendance Record</span>
            </h3>
            <p className="text-sm text-slate-600">
              Student: <strong>{correctingRecord.student_name}</strong> • Date: <strong>{selectedDate}</strong>
            </p>

            {correctionError && <AlertBanner type="error" message={correctionError} />}

            <form onSubmit={handleSubmitCorrection} className="space-y-4 pt-1">
              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                  Corrected Attendance Status *
                </label>
                <select
                  value={correctedStatus}
                  onChange={(e) => setCorrectedStatus(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                >
                  <option value="PRESENT">PRESENT</option>
                  <option value="LATE">LATE</option>
                  <option value="ABSENT">ABSENT</option>
                  <option value="EXCUSED">EXCUSED</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                  Audit Justification Reason *
                </label>
                <textarea
                  required
                  rows="2"
                  value={correctionReason}
                  onChange={(e) => setCorrectionReason(e.target.value)}
                  placeholder="e.g. Student arrived at 9:15 with excused parent note..."
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                  Updated Remarks (Optional)
                </label>
                <input
                  type="text"
                  value={correctionRemarks}
                  onChange={(e) => setCorrectionRemarks(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setCorrectingRecord(null)}
                  className="px-4 py-2 border border-slate-300 rounded-lg text-sm font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingCorrection}
                  className="px-5 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50"
                >
                  {submittingCorrection ? 'Saving...' : 'Save Correction'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AttendancePage;

