import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../api/client';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import AlertBanner from '../../components/common/AlertBanner';
import Badge from '../../components/common/Badge';
import {
  Building2,
  PlusCircle,
  Users,
  MapPin,
  Phone,
  Mail,
  Clock,
  CheckCircle,
} from 'lucide-react';

export const CenterManagementPage = () => {
  const { isSuperAdmin } = useAuth();
  const [centers, setCenters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Add Center Modal State
  const [showAddModal, setShowAddModal] = useState(false);
  const [newCenter, setNewCenter] = useState({
    code: '',
    name: '',
    address: '',
    timezone: 'UTC',
    contact_phone: '',
    contact_email: '',
    capacity: 100,
  });
  const [submitting, setSubmitting] = useState(false);
  const [modalError, setModalError] = useState('');

  const fetchCenters = async () => {
    setLoading(true);
    setError('');
    try {
      const { data } = await api.get('/centers?size=100');
      setCenters(data.items || []);
    } catch (err) {
      console.error('Error fetching centers', err);
      setError(err.response?.data?.detail || 'Failed to load centers directory.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCenters();
  }, []);

  const handleAddSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setModalError('');

    try {
      const payload = {
        ...newCenter,
        capacity: parseInt(newCenter.capacity, 10),
        contact_phone: newCenter.contact_phone.trim() || null,
        contact_email: newCenter.contact_email.trim() || null,
      };

      await api.post('/centers', payload);
      setSuccess(`Center "${newCenter.name}" registered successfully.`);
      setShowAddModal(false);
      setNewCenter({
        code: '',
        name: '',
        address: '',
        timezone: 'UTC',
        contact_phone: '',
        contact_email: '',
        capacity: 100,
      });
      fetchCenters();
    } catch (err) {
      console.error('Center creation error', err);
      const detail = err.response?.data?.detail;
      setModalError(typeof detail === 'string' ? detail : 'Failed to create center.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Learning Center Directory</h2>
          <p className="text-sm text-slate-500 mt-0.5">
            Campus locations, capacity limits, and operating profiles
          </p>
        </div>

        {isSuperAdmin && (
          <button
            onClick={() => setShowAddModal(true)}
            className="inline-flex items-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 shadow-xs transition-colors self-start sm:self-auto"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Add Learning Center</span>
          </button>
        )}
      </div>

      {success && <AlertBanner type="success" message={success} onClose={() => setSuccess('')} />}
      {error && <AlertBanner type="error" message={error} onClose={() => setError('')} />}

      {/* Centers Grid */}
      {loading ? (
        <LoadingSpinner text="Fetching centers..." size="md" />
      ) : centers.length === 0 ? (
        <div className="bg-white p-12 text-center rounded-xl border border-slate-200">
          <Building2 className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-800">No centers found</h3>
          <p className="text-sm text-slate-500 mt-1">
            Provision the first center location using the button above.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {centers.map((center) => (
            <div
              key={center.id}
              className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs flex flex-col justify-between hover:border-indigo-300 transition-colors"
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded">
                    {center.code}
                  </span>
                  <Badge
                    value={center.is_active ? 'ACTIVE' : 'INACTIVE'}
                    label={center.is_active ? 'Operational' : 'Inactive'}
                  />
                </div>

                <div>
                  <h3 className="text-lg font-bold text-slate-900">{center.name}</h3>
                  <div className="flex items-start space-x-1.5 text-xs text-slate-500 mt-1">
                    <MapPin className="w-3.5 h-3.5 text-slate-400 mt-0.5 flex-shrink-0" />
                    <span>{center.address}</span>
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-100 space-y-2 text-xs text-slate-600">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Max Capacity:</span>
                    <span className="font-semibold text-slate-800">{center.capacity} students</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Timezone:</span>
                    <span className="font-medium text-slate-700">{center.timezone}</span>
                  </div>
                  {center.contact_phone && (
                    <div className="flex items-center space-x-2 text-slate-600">
                      <Phone className="w-3.5 h-3.5 text-slate-400" />
                      <span>{center.contact_phone}</span>
                    </div>
                  )}
                  {center.contact_email && (
                    <div className="flex items-center space-x-2 text-slate-600">
                      <Mail className="w-3.5 h-3.5 text-slate-400" />
                      <span>{center.contact_email}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
                <span>Created {new Date(center.created_at).toLocaleDateString()}</span>
                <Building2 className="w-4 h-4 text-slate-400" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Center Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
              <Building2 className="w-5 h-5 text-indigo-600" />
              <span>Add Learning Center</span>
            </h3>

            {modalError && <AlertBanner type="error" message={modalError} />}

            <form onSubmit={handleAddSubmit} className="space-y-4 pt-1">
              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                  Center Code *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. CEN-WEST-01"
                  value={newCenter.code}
                  onChange={(e) => setNewCenter({ ...newCenter, code: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                  Center Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. West Coast Innovation Hub"
                  value={newCenter.name}
                  onChange={(e) => setNewCenter({ ...newCenter, name: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                  Address *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 742 Evergreen Terrace, Springfield"
                  value={newCenter.address}
                  onChange={(e) => setNewCenter({ ...newCenter, address: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                    Student Capacity *
                  </label>
                  <input
                    type="number"
                    required
                    min="1"
                    value={newCenter.capacity}
                    onChange={(e) => setNewCenter({ ...newCenter, capacity: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                    Timezone
                  </label>
                  <input
                    type="text"
                    value={newCenter.timezone}
                    onChange={(e) => setNewCenter({ ...newCenter, timezone: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                  Phone (Optional)
                </label>
                <input
                  type="tel"
                  placeholder="+1 555-010-0000"
                  value={newCenter.contact_phone}
                  onChange={(e) => setNewCenter({ ...newCenter, contact_phone: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                  Email (Optional)
                </label>
                <input
                  type="email"
                  placeholder="center@edutrack.org"
                  value={newCenter.contact_email}
                  onChange={(e) => setNewCenter({ ...newCenter, contact_email: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 border border-slate-300 rounded-lg text-sm font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-5 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50"
                >
                  {submitting ? 'Creating...' : 'Register Center'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default CenterManagementPage;

