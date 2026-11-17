import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../api/client';
import AlertBanner from '../../components/common/AlertBanner';
import { UserPlus, ArrowLeft, Save } from 'lucide-react';

export const StudentCreatePage = () => {
  const { activeCenter } = useAuth();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    student_id_number: `STU-${new Date().getFullYear()}-${Math.floor(1000 + Math.random() * 9000)}`,
    first_name: '',
    last_name: '',
    date_of_birth: '2016-01-15',
    gender: 'female',
    guardian_name: '',
    guardian_phone: '',
    guardian_email: '',
    guardian_relationship: 'Parent',
    emergency_contact: '',
    notes: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!activeCenter?.id) {
      setError('Active center is required to enroll a student.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const payload = {
        ...formData,
        center_id: activeCenter.id,
        guardian_email: formData.guardian_email.trim() ? formData.guardian_email.trim() : null,
      };

      const { data } = await api.post('/students', payload);
      navigate(`/students/${data.id}`);
    } catch (err) {
      console.error('Error creating student', err);
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
          ? detail.map((d) => d.msg).join(', ')
          : 'Failed to create student.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Link
            to="/students"
            className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h2 className="text-2xl font-bold text-slate-900">Enroll New Student</h2>
            <p className="text-sm text-slate-500">
              Center: <strong className="text-slate-800">{activeCenter?.name}</strong>
            </p>
          </div>
        </div>
      </div>

      {error && <AlertBanner type="error" message={error} onClose={() => setError('')} />}

      <form onSubmit={handleSubmit} className="bg-white border border-slate-200 rounded-xl shadow-xs p-6 space-y-6">
        {/* Student Profile Info */}
        <div>
          <h3 className="text-base font-bold text-slate-900 pb-2 border-b border-slate-100 mb-4">
            Student Identity
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                Student ID Number *
              </label>
              <input
                type="text"
                required
                name="student_id_number"
                value={formData.student_id_number}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-indigo-500 focus:outline-none"
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
                First Name *
              </label>
              <input
                type="text"
                required
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                placeholder="Jane"
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
                placeholder="Doe"
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
          </div>
        </div>

        {/* Guardian and Emergency Contact Info */}
        <div>
          <h3 className="text-base font-bold text-slate-900 pb-2 border-b border-slate-100 mb-4">
            Guardian & Contact Details
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
                placeholder="Eleanor Doe"
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
                placeholder="Mother, Father, Guardian"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                Guardian Phone Number *
              </label>
              <input
                type="tel"
                required
                name="guardian_phone"
                value={formData.guardian_phone}
                onChange={handleChange}
                placeholder="+1 555-019-2831"
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
                placeholder="eleanor@example.com"
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
                placeholder="Grandparent: Robert Doe (555-019-9999)"
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
                placeholder="Dietary requirements, allergies, or educational accommodations..."
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>
          </div>
        </div>

        {/* Buttons */}
        <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-100">
          <Link
            to="/students"
            className="px-4 py-2 border border-slate-300 rounded-lg text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center space-x-2 px-5 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50 transition-colors shadow-xs"
          >
            <Save className="w-4 h-4" />
            <span>{loading ? 'Registering...' : 'Complete Enrollment'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};

export default StudentCreatePage;

