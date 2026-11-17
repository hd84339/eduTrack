import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api from '../../api/client';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import AlertBanner from '../../components/common/AlertBanner';
import { ArrowLeft, Save, RefreshCw, AlertTriangle } from 'lucide-react';

export const StudentEditPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const [student, setStudent] = useState(null);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    date_of_birth: '',
    gender: '',
    guardian_name: '',
    guardian_phone: '',
    guardian_email: '',
    guardian_relationship: '',
    emergency_contact: '',
    notes: '',
    status: 'ACTIVE',
    version: 1,
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [occConflict, setOccConflict] = useState(false);

  const fetchStudent = async () => {
    setLoading(true);
    setError('');
    setOccConflict(false);
    try {
      const { data } = await api.get(`/students/${id}`);
      setStudent(data);
      setFormData({
        first_name: data.first_name || '',
        last_name: data.last_name || '',
        date_of_birth: data.date_of_birth || '',
        gender: data.gender || 'female',
        guardian_name: data.guardian_name || '',
        guardian_phone: data.guardian_phone || '',
        guardian_email: data.guardian_email || '',
        guardian_relationship: data.guardian_relationship || 'Parent',
        emergency_contact: data.emergency_contact || '',
        notes: data.notes || '',
        status: data.status || 'ACTIVE',
        version: data.version,
      });
    } catch (err) {
      console.error('Error fetching student', err);
      setError(err.response?.data?.detail || 'Failed to load student profile.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) fetchStudent();
  }, [id]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setOccConflict(false);

    try {
      const payload = {
        ...formData,
        guardian_email: formData.guardian_email.trim() ? formData.guardian_email.trim() : null,
      };

      await api.put(`/students/${id}`, payload);
      navigate(`/students/${id}`);
    } catch (err) {
      console.error('Update error', err);
      if (err.response?.status === 409) {
        setOccConflict(true);
        setError(
          'Optimistic Concurrency Collision: This record was modified by another staff member while you were editing. Please reload the latest data.'
        );
      } else {
        const detail = err.response?.data?.detail;
        setError(
          typeof detail === 'string'
            ? detail
            : Array.isArray(detail)
            ? detail.map((d) => d.msg).join(', ')
            : 'Failed to update student profile.'
        );
      }
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <LoadingSpinner fullPage text="Loading student record..." />;
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Link
            to={`/students/${id}`}
            className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h2 className="text-2xl font-bold text-slate-900">Edit Student Record</h2>
            <p className="text-sm text-slate-500 font-mono">
              ID: {student?.student_id_number} • Locking Version: {formData.version}
            </p>
          </div>
        </div>

        {occConflict && (
          <button
            onClick={fetchStudent}
            type="button"
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-amber-600 text-white rounded-lg text-sm font-semibold hover:bg-amber-700 transition-colors shadow-xs"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Reload Latest</span>
          </button>
        )}
      </div>

      {error && (
        <AlertBanner
          type={occConflict ? 'warning' : 'error'}
          message={error}
          onClose={() => setError('')}
        />
      )}

      <form onSubmit={handleSubmit} className="bg-white border border-slate-200 rounded-xl shadow-xs p-6 space-y-6">
        {/* Core fields */}
        <div>
          <h3 className="text-base font-bold text-slate-900 pb-2 border-b border-slate-100 mb-4">
            Demographic Information
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                First Name *
              </label>
              <input
                type="text"
                required
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                Last Name *
              </label>
              <input
                type="text"
                required
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                Date of Birth *
              </label>
              <input
                type="date"
                required
                name="date_of_birth"
                value={formData.date_of_birth}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                Gender *
              </label>
              <select
                name="gender"
                value={formData.gender}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              >
                <option value="female">Female</option>
                <option value="male">Male</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                Enrollment Status
              </label>
              <select
                name="status"
                value={formData.status}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              >
                <option value="ACTIVE">ACTIVE</option>
                <option value="INACTIVE">INACTIVE</option>
                <option value="ARCHIVED">ARCHIVED</option>
              </select>
            </div>
          </div>
        </div>

        {/* Guardian and Emergency */}
        <div>
          <h3 className="text-base font-bold text-slate-900 pb-2 border-b border-slate-100 mb-4">
            Guardian & Emergency Contacts
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                Guardian Full Name *
              </label>
              <input
                type="text"
                required
                name="guardian_name"
                value={formData.guardian_name}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                Guardian Relationship *
              </label>
              <input
                type="text"
                required
                name="guardian_relationship"
                value={formData.guardian_relationship}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                Guardian Phone *
              </label>
              <input
                type="tel"
                required
                name="guardian_phone"
                value={formData.guardian_phone}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                Guardian Email (Optional)
              </label>
              <input
                type="email"
                name="guardian_email"
                value={formData.guardian_email}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                Emergency Contact Details
              </label>
              <input
                type="text"
                name="emergency_contact"
                value={formData.emergency_contact}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                Administrative / Medical Notes
              </label>
              <textarea
                name="notes"
                rows="2"
                value={formData.notes}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-100">
          <Link
            to={`/students/${id}`}
            className="px-4 py-2 border border-slate-300 rounded-lg text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={saving}
            className="inline-flex items-center space-x-2 px-5 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50 transition-colors shadow-xs"
          >
            <Save className="w-4 h-4" />
            <span>{saving ? 'Saving...' : 'Save Changes'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};

export default StudentEditPage;

