import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../api/client';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import AlertBanner from '../../components/common/AlertBanner';
import Badge from '../../components/common/Badge';
import {
  UserCheck,
  PlusCircle,
  Mail,
  Phone,
  Building2,
  Shield,
  Key,
} from 'lucide-react';

export const UserManagementPage = () => {
  const { user, isSuperAdmin, isCenterManager, activeCenter } = useAuth();
  const [users, setUsers] = useState([]);
  const [centers, setCenters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Add User Modal State
  const [showAddModal, setShowAddModal] = useState(false);
  const [newUser, setNewUser] = useState({
    email: '',
    password: '',
    full_name: '',
    phone_number: '',
    role: isSuperAdmin ? 'TEACHER' : 'TEACHER',
    center_ids: [],
  });
  const [submitting, setSubmitting] = useState(false);
  const [modalError, setModalError] = useState('');

  const fetchUsersAndCenters = async () => {
    setLoading(true);
    setError('');
    try {
      const [uRes, cRes] = await Promise.all([
        api.get('/users?size=100'),
        api.get('/centers?size=100'),
      ]);
      setUsers(uRes.data.items || []);
      setCenters(cRes.data.items || []);
    } catch (err) {
      console.error('Error fetching users', err);
      setError(err.response?.data?.detail || 'Failed to load staff roster.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsersAndCenters();
  }, []);

  const handleToggleCenterSelect = (centerId) => {
    setNewUser((prev) => {
      const exists = prev.center_ids.includes(centerId);
      return {
        ...prev,
        center_ids: exists
          ? prev.center_ids.filter((id) => id !== centerId)
          : [...prev.center_ids, centerId],
      };
    });
  };

  const handleAddSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setModalError('');

    try {
      const payload = {
        email: newUser.email.trim(),
        password: newUser.password,
        full_name: newUser.full_name.trim(),
        phone_number: newUser.phone_number.trim() || null,
        role: newUser.role,
        center_ids: newUser.center_ids.length > 0 ? newUser.center_ids : (activeCenter ? [activeCenter.id] : []),
      };

      await api.post('/users', payload);
      setSuccess(`Staff account for ${newUser.full_name} created successfully.`);
      setShowAddModal(false);
      setNewUser({
        email: '',
        password: '',
        full_name: '',
        phone_number: '',
        role: 'TEACHER',
        center_ids: [],
      });
      fetchUsersAndCenters();
    } catch (err) {
      console.error('User creation error', err);
      const detail = err.response?.data?.detail;
      setModalError(typeof detail === 'string' ? detail : 'Failed to provision staff account.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Staff & Role Administration</h2>
          <p className="text-sm text-slate-500 mt-0.5">
            Role assignments (Super Admin, Center Manager, Teacher) and multi-center links
          </p>
        </div>

        <button
          onClick={() => {
            setNewUser({
              email: '',
              password: '',
              full_name: '',
              phone_number: '',
              role: isSuperAdmin ? 'CENTER_MANAGER' : 'TEACHER',
              center_ids: activeCenter ? [activeCenter.id] : [],
            });
            setShowAddModal(true);
          }}
          className="inline-flex items-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 shadow-xs transition-colors self-start sm:self-auto"
        >
          <PlusCircle className="w-4 h-4" />
          <span>Provision Staff Member</span>
        </button>
      </div>

      {success && <AlertBanner type="success" message={success} onClose={() => setSuccess('')} />}
      {error && <AlertBanner type="error" message={error} onClose={() => setError('')} />}

      {/* Users Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
        {loading ? (
          <LoadingSpinner text="Fetching staff accounts..." size="md" />
        ) : users.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <UserCheck className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-slate-800">No staff members found</h3>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left">
              <thead className="bg-slate-50 text-xs font-bold text-slate-500 uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3">Staff Name</th>
                  <th className="px-6 py-3">Email & Phone</th>
                  <th className="px-6 py-3">Role</th>
                  <th className="px-6 py-3">Assigned Centers</th>
                  <th className="px-6 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-sm">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-6 py-4 font-semibold text-slate-900">
                      {u.full_name}
                    </td>
                    <td className="px-6 py-4 text-slate-600">
                      <div>{u.email}</div>
                      {u.phone_number && (
                        <div className="text-xs text-slate-400 font-mono">{u.phone_number}</div>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <Badge value={u.role} />
                    </td>
                    <td className="px-6 py-4">
                      {u.role === 'SUPER_ADMIN' ? (
                        <span className="text-xs font-semibold text-purple-700 bg-purple-50 px-2 py-0.5 rounded">
                          All Centers (Global Access)
                        </span>
                      ) : !u.assigned_centers || u.assigned_centers.length === 0 ? (
                        <span className="text-xs text-slate-400 italic">No center assigned</span>
                      ) : (
                        <div className="flex flex-wrap gap-1.5">
                          {u.assigned_centers.map((c) => (
                            <span
                              key={c.id}
                              className="text-xs font-medium text-slate-700 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded"
                            >
                              {c.name} ({c.code})
                            </span>
                          ))}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <Badge value={u.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Provision User Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
              <PlusCircle className="w-5 h-5 text-indigo-600" />
              <span>Provision Staff Member</span>
            </h3>

            {modalError && <AlertBanner type="error" message={modalError} />}

            <form onSubmit={handleAddSubmit} className="space-y-4 pt-1">
              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                  Full Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Sarah Connor"
                  value={newUser.full_name}
                  onChange={(e) => setNewUser({ ...newUser, full_name: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                  Email Address *
                </label>
                <input
                  type="email"
                  required
                  placeholder="e.g. sarah@edutrack.org"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                  Initial Password (Min 8 chars) *
                </label>
                <input
                  type="password"
                  required
                  minLength={8}
                  placeholder="••••••••••••"
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                    System Role *
                  </label>
                  <select
                    value={newUser.role}
                    onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  >
                    <option value="TEACHER">TEACHER</option>
                    {isSuperAdmin && <option value="CENTER_MANAGER">CENTER_MANAGER</option>}
                    {isSuperAdmin && <option value="SUPER_ADMIN">SUPER_ADMIN</option>}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                    Phone (Optional)
                  </label>
                  <input
                    type="tel"
                    placeholder="+1 555-019-1234"
                    value={newUser.phone_number}
                    onChange={(e) => setNewUser({ ...newUser, phone_number: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              {/* Center Assignments */}
              {newUser.role !== 'SUPER_ADMIN' && (
                <div>
                  <label className="block text-xs font-semibold text-slate-600 uppercase mb-2">
                    Assign to Centers (Multi-Center Supported)
                  </label>
                  <div className="space-y-1.5 max-h-36 overflow-y-auto p-2 border border-slate-200 rounded-lg bg-slate-50">
                    {centers.map((c) => (
                      <label
                        key={c.id}
                        className="flex items-center space-x-2 text-xs text-slate-700 cursor-pointer p-1 rounded hover:bg-slate-100"
                      >
                        <input
                          type="checkbox"
                          checked={newUser.center_ids.includes(c.id)}
                          onChange={() => handleToggleCenterSelect(c.id)}
                          className="rounded text-indigo-600 focus:ring-indigo-500"
                        />
                        <span className="font-medium">{c.name}</span>
                        <span className="text-slate-400 font-mono text-[11px]">({c.code})</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}

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
                  {submitting ? 'Provisioning...' : 'Provision Account'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagementPage;

