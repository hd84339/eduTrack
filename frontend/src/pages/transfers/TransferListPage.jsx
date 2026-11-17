import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../api/client';
import Badge from '../../components/common/Badge';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import AlertBanner from '../../components/common/AlertBanner';
import Pagination from '../../components/common/Pagination';
import {
  ArrowRightLeft,
  CheckCircle,
  XCircle,
  Clock,
  Filter,
  AlertTriangle,
} from 'lucide-react';

export const TransferListPage = () => {
  const { user, isSuperAdmin, isCenterManager } = useAuth();
  const [transfers, setTransfers] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, size: 10, total_pages: 1, total_items: 0 });
  const [statusFilter, setStatusFilter] = useState('');
  const [directionFilter, setDirectionFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Review Modal State
  const [selectedTransfer, setSelectedTransfer] = useState(null);
  const [reviewAction, setReviewAction] = useState('APPROVE');
  const [reviewNotes, setReviewNotes] = useState('');
  const [capacityOverride, setCapacityOverride] = useState(false);
  const [capacityOverrideReason, setCapacityOverrideReason] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewError, setReviewError] = useState('');

  const fetchTransfers = async (page = 1) => {
    setLoading(true);
    setError('');
    try {
      const params = { page, size: 10 };
      if (statusFilter) params.status = statusFilter;
      if (directionFilter) params.direction = directionFilter;

      const { data } = await api.get('/transfers', { params });
      setTransfers(data.items || []);
      setPagination(
        data.pagination || {
          page: 1,
          size: 10,
          total_pages: 1,
          total_items: data.items?.length || 0,
        }
      );
    } catch (err) {
      console.error('Error fetching transfers', err);
      setError(err.response?.data?.detail || 'Failed to load transfer requests.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransfers(1);
  }, [statusFilter, directionFilter]);

  const handleOpenReview = (transfer, action) => {
    setSelectedTransfer(transfer);
    setReviewAction(action);
    setReviewNotes('');
    setCapacityOverride(false);
    setCapacityOverrideReason('');
    setReviewError('');
  };

  const handleSubmitReview = async (e) => {
    e.preventDefault();
    if (capacityOverride && !capacityOverrideReason.trim()) {
      setReviewError('Capacity override justification is required when override is enabled.');
      return;
    }

    setSubmittingReview(true);
    setReviewError('');

    try {
      const payload = {
        action: reviewAction,
        review_notes: reviewNotes.trim() || null,
        capacity_override: capacityOverride,
        capacity_override_reason: capacityOverride ? capacityOverrideReason.trim() : null,
      };

      await api.post(`/transfers/${selectedTransfer.id}/review`, payload);
      setSuccess(`Transfer request has been successfully ${reviewAction.toLowerCase()}d.`);
      setSelectedTransfer(null);
      fetchTransfers(pagination.page);
    } catch (err) {
      console.error('Error reviewing transfer', err);
      const detail = err.response?.data?.detail;
      setReviewError(typeof detail === 'string' ? detail : 'Failed to process transfer review.');
    } finally {
      setSubmittingReview(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Student Transfer Requests</h2>
          <p className="text-sm text-slate-500 mt-0.5">
            Inter-center transfers and enrollment transitions
          </p>
        </div>
      </div>

      {success && <AlertBanner type="success" message={success} onClose={() => setSuccess('')} />}
      {error && <AlertBanner type="error" message={error} onClose={() => setError('')} />}

      {/* Filter Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-wrap gap-4 items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <span className="text-xs font-semibold text-slate-500 uppercase">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-sm border border-slate-300 rounded-lg px-3 py-1.5 bg-white text-slate-700 focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">All Statuses</option>
              <option value="PENDING">Pending</option>
              <option value="APPROVED">Approved</option>
              <option value="REJECTED">Rejected</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </div>

          {!isSuperAdmin && (
            <div className="flex items-center space-x-2">
              <span className="text-xs font-semibold text-slate-500 uppercase">Direction:</span>
              <select
                value={directionFilter}
                onChange={(e) => setDirectionFilter(e.target.value)}
                className="text-sm border border-slate-300 rounded-lg px-3 py-1.5 bg-white text-slate-700 focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">All Directions</option>
                <option value="incoming">Incoming to Center</option>
                <option value="outgoing">Outgoing from Center</option>
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Transfer List Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
        {loading ? (
          <LoadingSpinner text="Loading transfer requests..." size="md" />
        ) : transfers.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <ArrowRightLeft className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-slate-800">No transfer requests</h3>
            <p className="text-sm text-slate-400 mt-1">
              No inter-center student transfer requests found for your selected filters.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left">
              <thead className="bg-slate-50 text-xs font-bold text-slate-500 uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3">Student</th>
                  <th className="px-6 py-3">Route (From → To)</th>
                  <th className="px-6 py-3">Effective Date</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3">Reason</th>
                  <th className="px-6 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-sm">
                {transfers.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-6 py-4 font-semibold text-slate-900">
                      {t.student_name || 'Student ID: ' + t.student_id.slice(0, 8)}
                    </td>
                    <td className="px-6 py-4 text-slate-700">
                      <div className="flex items-center space-x-1.5 font-medium">
                        <span className="text-slate-600">{t.from_center_name || 'Origin'}</span>
                        <ArrowRightLeft className="w-3.5 h-3.5 text-slate-400" />
                        <span className="text-indigo-600">{t.to_center_name || 'Destination'}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-600 font-mono text-xs">
                      {t.effective_date}
                    </td>
                    <td className="px-6 py-4">
                      <Badge value={t.status} />
                    </td>
                    <td className="px-6 py-4 text-slate-600 max-w-xs truncate text-xs" title={t.request_reason}>
                      {t.request_reason}
                    </td>
                    <td className="px-6 py-4 text-right space-x-2">
                      {t.status === 'PENDING' && (isSuperAdmin || isCenterManager) && (
                        <>
                          <button
                            onClick={() => handleOpenReview(t, 'APPROVE')}
                            className="inline-flex items-center space-x-1 px-2.5 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded text-xs font-semibold hover:bg-emerald-100 transition-colors"
                          >
                            <CheckCircle className="w-3.5 h-3.5" />
                            <span>Approve</span>
                          </button>
                          <button
                            onClick={() => handleOpenReview(t, 'REJECT')}
                            className="inline-flex items-center space-x-1 px-2.5 py-1 bg-rose-50 text-rose-700 border border-rose-200 rounded text-xs font-semibold hover:bg-rose-100 transition-colors"
                          >
                            <XCircle className="w-3.5 h-3.5" />
                            <span>Reject</span>
                          </button>
                        </>
                      )}
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
          onPageChange={(p) => fetchTransfers(p)}
        />
      </div>

      {/* Review Modal */}
      {selectedTransfer && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
              {reviewAction === 'APPROVE' ? (
                <CheckCircle className="w-5 h-5 text-emerald-600" />
              ) : (
                <XCircle className="w-5 h-5 text-rose-600" />
              )}
              <span>{reviewAction === 'APPROVE' ? 'Approve Transfer' : 'Reject Transfer'}</span>
            </h3>

            <p className="text-sm text-slate-600">
              Transfer student <strong>{selectedTransfer.student_name}</strong> to{' '}
              <strong>{selectedTransfer.to_center_name}</strong>.
            </p>

            {reviewError && <AlertBanner type="error" message={reviewError} />}

            <form onSubmit={handleSubmitReview} className="space-y-4 pt-1">
              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                  Review Notes
                </label>
                <textarea
                  rows="3"
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="Optional review observations or feedback..."
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              {/* Capacity Override for Super Admin */}
              {isSuperAdmin && reviewAction === 'APPROVE' && (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg space-y-2">
                  <label className="flex items-center space-x-2 text-xs font-semibold text-amber-900 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={capacityOverride}
                      onChange={(e) => setCapacityOverride(e.target.checked)}
                      className="rounded text-indigo-600 focus:ring-indigo-500"
                    />
                    <span>Super Admin Capacity Override</span>
                  </label>
                  {capacityOverride && (
                    <input
                      type="text"
                      required
                      value={capacityOverrideReason}
                      onChange={(e) => setCapacityOverrideReason(e.target.value)}
                      placeholder="Mandatory override reason (e.g. Director exemption)..."
                      className="w-full px-2.5 py-1.5 border border-amber-300 rounded text-xs bg-white focus:outline-none focus:ring-1 focus:ring-amber-500"
                    />
                  )}
                </div>
              )}

              <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setSelectedTransfer(null)}
                  className="px-4 py-2 border border-slate-300 rounded-lg text-sm font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingReview}
                  className={`px-5 py-2 text-white rounded-lg text-sm font-semibold transition-colors disabled:opacity-50 ${
                    reviewAction === 'APPROVE'
                      ? 'bg-emerald-600 hover:bg-emerald-700'
                      : 'bg-rose-600 hover:bg-rose-700'
                  }`}
                >
                  {submittingReview ? 'Processing...' : `Confirm ${reviewAction}`}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default TransferListPage;

