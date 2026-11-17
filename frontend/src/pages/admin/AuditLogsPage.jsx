import React, { useState, useEffect } from 'react';
import api from '../../api/client';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import AlertBanner from '../../components/common/AlertBanner';
import Pagination from '../../components/common/Pagination';
import {
  ShieldAlert,
  Search,
  Filter,
  Eye,
  Calendar,
  Lock,
} from 'lucide-react';

export const AuditLogsPage = () => {
  const [logs, setLogs] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, size: 20, total_pages: 1, total_items: 0 });
  const [actionFilter, setActionFilter] = useState('');
  const [resourceFilter, setResourceFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Selected log snapshot modal
  const [selectedLog, setSelectedLog] = useState(null);

  const fetchLogs = async (page = 1) => {
    setLoading(true);
    setError('');
    try {
      const params = { page, size: 20 };
      if (actionFilter) params.action = actionFilter;
      if (resourceFilter) params.resource_type = resourceFilter;

      const { data } = await api.get('/audit-logs', { params });
      setLogs(data.items || []);
      setPagination(
        data.pagination || {
          page: 1,
          size: 20,
          total_pages: 1,
          total_items: data.items?.length || 0,
        }
      );
    } catch (err) {
      console.error('Audit fetch error', err);
      setError(err.response?.data?.detail || 'Failed to load audit trail.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs(1);
  }, [actionFilter, resourceFilter]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-2xl font-bold text-slate-900">System Audit Trail</h2>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300">
              <Lock className="w-3 h-3 mr-1" />
              Immutable
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-0.5">
            Cryptographically tracked audit events across all entity lifecycles
          </p>
        </div>
      </div>

      {error && <AlertBanner type="error" message={error} onClose={() => setError('')} />}

      {/* Filters */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-wrap gap-4 items-center">
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-semibold text-slate-500 uppercase">Resource:</span>
          <select
            value={resourceFilter}
            onChange={(e) => setResourceFilter(e.target.value)}
            className="text-sm border border-slate-300 rounded-lg px-3 py-1.5 bg-white text-slate-700 focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Resources</option>
            <option value="STUDENT">STUDENT</option>
            <option value="ATTENDANCE">ATTENDANCE</option>
            <option value="TRANSFER">TRANSFER</option>
            <option value="SESSION">SESSION</option>
            <option value="CENTER">CENTER</option>
            <option value="USER">USER</option>
          </select>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs font-semibold text-slate-500 uppercase">Action:</span>
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="text-sm border border-slate-300 rounded-lg px-3 py-1.5 bg-white text-slate-700 focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Actions</option>
            <option value="CREATE">CREATE</option>
            <option value="UPDATE">UPDATE</option>
            <option value="DELETE">DELETE</option>
            <option value="CORRECT">CORRECT</option>
            <option value="TRANSFER_APPROVE">TRANSFER_APPROVE</option>
            <option value="TRANSFER_REJECT">TRANSFER_REJECT</option>
          </select>
        </div>
      </div>

      {/* Audit Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
        {loading ? (
          <LoadingSpinner text="Querying audit records..." size="md" />
        ) : logs.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <ShieldAlert className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-slate-800">No audit logs found</h3>
            <p className="text-sm text-slate-400 mt-1">No system events match your query.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left">
              <thead className="bg-slate-50 text-xs font-bold text-slate-500 uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3">Timestamp</th>
                  <th className="px-6 py-3">Actor</th>
                  <th className="px-6 py-3">Action</th>
                  <th className="px-6 py-3">Target Entity</th>
                  <th className="px-6 py-3">Client IP</th>
                  <th className="px-6 py-3 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-xs">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/70 font-mono">
                    <td className="px-6 py-3.5 text-slate-500">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-3.5 font-sans font-semibold text-slate-800">
                      {log.user_name || (log.user_id ? log.user_id.slice(0, 8) : 'SYSTEM')}
                    </td>
                    <td className="px-6 py-3.5">
                      <span className="inline-flex px-2 py-0.5 rounded text-[11px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-100">
                        {log.action}
                      </span>
                    </td>
                    <td className="px-6 py-3.5 text-slate-600 font-sans">
                      <span className="font-semibold text-slate-800">{log.resource_type}</span>{' '}
                      <span className="text-[11px] text-slate-400 font-mono">
                        ({log.resource_id.slice(0, 8)})
                      </span>
                    </td>
                    <td className="px-6 py-3.5 text-slate-400">
                      {log.client_ip || '127.0.0.1'}
                    </td>
                    <td className="px-6 py-3.5 text-right font-sans">
                      <button
                        onClick={() => setSelectedLog(log)}
                        className="inline-flex items-center space-x-1 px-2 py-1 text-slate-600 hover:text-indigo-600 hover:bg-indigo-50 rounded transition-colors"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Inspect</span>
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
          onPageChange={(p) => fetchLogs(p)}
        />
      </div>

      {/* Snapshot Modal */}
      {selectedLog && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-xl w-full p-6 space-y-4 max-h-[85vh] overflow-y-auto">
            <div className="flex items-start justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900">
                  Audit Snapshot: {selectedLog.action} on {selectedLog.resource_type}
                </h3>
                <p className="text-xs font-mono text-slate-400">
                  ID: {selectedLog.id} • {new Date(selectedLog.created_at).toLocaleString()}
                </p>
              </div>
              <button
                onClick={() => setSelectedLog(null)}
                className="text-slate-400 hover:text-slate-600 text-sm font-bold p-1"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="font-bold text-slate-600 uppercase">Prior State (old_values):</span>
                <pre className="mt-1 p-3 bg-slate-50 border border-slate-200 rounded-lg overflow-x-auto text-[11px] font-mono text-slate-700">
                  {selectedLog.old_values ? JSON.stringify(selectedLog.old_values, null, 2) : 'null (New entity creation)'}
                </pre>
              </div>

              <div>
                <span className="font-bold text-slate-600 uppercase">Updated State (new_values):</span>
                <pre className="mt-1 p-3 bg-slate-50 border border-slate-200 rounded-lg overflow-x-auto text-[11px] font-mono text-slate-700">
                  {selectedLog.new_values ? JSON.stringify(selectedLog.new_values, null, 2) : 'null'}
                </pre>
              </div>
            </div>

            <div className="flex justify-end pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setSelectedLog(null)}
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

export default AuditLogsPage;

