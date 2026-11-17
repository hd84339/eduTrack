import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../api/client';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import AlertBanner from '../../components/common/AlertBanner';
import Badge from '../../components/common/Badge';
import {
  FileBarChart,
  Download,
  Calendar,
  Building2,
  Table,
  User,
  Award,
} from 'lucide-react';

export const ReportsPage = () => {
  const { activeCenter, assignedCenters } = useAuth();

  const todayStr = new Date().toISOString().split('T')[0];
  const thirtyDaysAgoStr = new Date(Date.now() - 30 * 86400000).toISOString().split('T')[0];

  const [selectedCenterId, setSelectedCenterId] = useState(activeCenter?.id || '');
  const [startDate, setStartDate] = useState(thirtyDaysAgoStr);
  const [endDate, setEndDate] = useState(todayStr);

  const [loading, setLoading] = useState(false);
  const [reportRows, setReportRows] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (activeCenter?.id) {
      setSelectedCenterId(activeCenter.id);
    }
  }, [activeCenter]);

  const handleFetchReport = async () => {
    if (!selectedCenterId) {
      setError('Please select a center.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const { data } = await api.get('/reports/attendance', {
        params: {
          center_id: selectedCenterId,
          start_date: startDate,
          end_date: endDate,
          format: 'json',
        },
      });
      setReportRows(data.rows || []);
    } catch (err) {
      console.error('Report fetch error', err);
      setError(err.response?.data?.detail || 'Failed to generate attendance report.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadCsv = async () => {
    if (!selectedCenterId) return;

    try {
      const response = await api.get('/reports/attendance', {
        params: {
          center_id: selectedCenterId,
          start_date: startDate,
          end_date: endDate,
          format: 'csv',
        },
        responseType: 'blob',
      });

      const blob = new Blob([response.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `attendance_${selectedCenterId}_${startDate}_${endDate}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('CSV download error', err);
      setError('Failed to export CSV report.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Reports & Export Center</h2>
        <p className="text-sm text-slate-500 mt-0.5">
          Compliance logs, attendance exports, and multi-center analytical datasets
        </p>
      </div>

      {error && <AlertBanner type="error" message={error} onClose={() => setError('')} />}

      {/* Filter Control Card */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
        <h3 className="text-base font-bold text-slate-900 pb-2 border-b border-slate-100 flex items-center space-x-2">
          <FileBarChart className="w-5 h-5 text-indigo-600" />
          <span>Attendance Report Generator</span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
              Select Center
            </label>
            <select
              value={selectedCenterId}
              onChange={(e) => setSelectedCenterId(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-indigo-500"
            >
              {assignedCenters.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.code})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
              Start Date
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
              End Date
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>

        <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-100">
          <button
            type="button"
            onClick={handleDownloadCsv}
            className="inline-flex items-center space-x-2 px-4 py-2 border border-slate-300 bg-white text-slate-700 rounded-lg text-sm font-semibold hover:bg-slate-50 transition-colors shadow-xs"
          >
            <Download className="w-4 h-4 text-emerald-600" />
            <span>Download CSV</span>
          </button>
          <button
            type="button"
            onClick={handleFetchReport}
            disabled={loading}
            className="inline-flex items-center space-x-2 px-5 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50 transition-colors shadow-xs"
          >
            <Table className="w-4 h-4" />
            <span>{loading ? 'Generating...' : 'Preview Report'}</span>
          </button>
        </div>
      </div>

      {/* Preview Table */}
      {reportRows && (
        <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
          <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
            <div>
              <h4 className="text-sm font-bold text-slate-800">
                Attendance Dataset Preview ({reportRows.length} rows)
              </h4>
              <p className="text-xs text-slate-500">
                Date Range: {startDate} to {endDate}
              </p>
            </div>
          </div>

          {reportRows.length === 0 ? (
            <div className="p-8 text-center text-slate-500">
              <Calendar className="w-10 h-10 text-slate-300 mx-auto mb-2" />
              <p className="text-sm font-medium">No records match this date window.</p>
            </div>
          ) : (
            <div className="overflow-x-auto max-h-96">
              <table className="min-w-full divide-y divide-slate-200 text-left">
                <thead className="bg-slate-50 text-xs font-bold text-slate-500 uppercase tracking-wider sticky top-0">
                  <tr>
                    <th className="px-6 py-3">Date</th>
                    <th className="px-6 py-3">Student Name</th>
                    <th className="px-6 py-3">Status</th>
                    <th className="px-6 py-3">Remarks</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 text-xs">
                  {reportRows.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/70">
                      <td className="px-6 py-3 font-mono text-slate-600">{row.attendance_date}</td>
                      <td className="px-6 py-3 font-semibold text-slate-900">{row.student_name}</td>
                      <td className="px-6 py-3">
                        <Badge value={row.status} />
                      </td>
                      <td className="px-6 py-3 text-slate-600 italic">{row.remarks || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ReportsPage;

