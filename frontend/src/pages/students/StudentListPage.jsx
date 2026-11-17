import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../api/client';
import Badge from '../../components/common/Badge';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import AlertBanner from '../../components/common/AlertBanner';
import Pagination from '../../components/common/Pagination';
import {
  Users,
  Search,
  PlusCircle,
  Eye,
  Edit,
  ArrowRightLeft,
  Filter,
} from 'lucide-react';

export const StudentListPage = () => {
  const { activeCenter, isSuperAdmin, isCenterManager } = useAuth();
  const [students, setStudents] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, size: 10, total_pages: 1, total_items: 0 });
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchStudents = async (page = 1) => {
    if (!activeCenter?.id) return;
    setLoading(true);
    setError('');
    try {
      const params = {
        page,
        size: 10,
      };
      if (search.trim()) params.search = search.trim();
      if (statusFilter) params.status = statusFilter;

      const { data } = await api.get('/students', { params });
      setStudents(data.items || []);
      setPagination(
        data.pagination || {
          page: 1,
          size: 10,
          total_pages: 1,
          total_items: data.items?.length || 0,
        }
      );
    } catch (err) {
      console.error('Error fetching students', err);
      setError(err.response?.data?.detail || 'Failed to load students roster.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStudents(1);
  }, [activeCenter, statusFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchStudents(1);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Student Directory</h2>
          <p className="text-sm text-slate-500 mt-0.5">
            {activeCenter
              ? `Roster for ${activeCenter.name} (${activeCenter.code})`
              : 'Select an active center to view enrolled students'}
          </p>
        </div>

        {(isSuperAdmin || isCenterManager) && (
          <Link
            to="/students/new"
            className="inline-flex items-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 shadow-xs transition-colors self-start sm:self-auto"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Enroll New Student</span>
          </Link>
        )}
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
        <form onSubmit={handleSearchSubmit} className="flex-1 flex items-center space-x-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by student name or ID..."
              className="w-full pl-9 pr-4 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-slate-800 text-white text-sm font-medium rounded-lg hover:bg-slate-900 transition-colors"
          >
            Search
          </button>
        </form>

        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-semibold text-slate-500 uppercase">Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-sm border border-slate-300 rounded-lg px-3 py-2 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="INACTIVE">Inactive</option>
            <option value="TRANSFERRED">Transferred</option>
            <option value="ARCHIVED">Archived</option>
          </select>
        </div>
      </div>

      {error && <AlertBanner type="error" message={error} onClose={() => setError('')} />}

      {/* Student Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
        {loading ? (
          <LoadingSpinner text="Fetching students..." size="md" />
        ) : students.length === 0 ? (
          <div className="p-12 text-center">
            <Users className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-slate-800">No students found</h3>
            <p className="text-sm text-slate-500 mt-1 max-w-sm mx-auto">
              No student profiles match your search criteria or are enrolled in this center.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left">
              <thead className="bg-slate-50 text-xs font-bold text-slate-500 uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3">Student ID</th>
                  <th className="px-6 py-3">Name</th>
                  <th className="px-6 py-3">DOB / Gender</th>
                  <th className="px-6 py-3">Guardian</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-sm">
                {students.map((student) => (
                  <tr key={student.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-6 py-4 font-mono font-semibold text-indigo-600">
                      {student.student_id_number}
                    </td>
                    <td className="px-6 py-4 font-semibold text-slate-900">
                      {student.first_name} {student.last_name}
                    </td>
                    <td className="px-6 py-4 text-slate-600">
                      <div>{student.date_of_birth}</div>
                      <div className="text-xs text-slate-400 capitalize">{student.gender}</div>
                    </td>
                    <td className="px-6 py-4 text-slate-600">
                      <div>{student.guardian_name}</div>
                      <div className="text-xs text-slate-400 font-mono">{student.guardian_phone}</div>
                    </td>
                    <td className="px-6 py-4">
                      <Badge value={student.status} />
                    </td>
                    <td className="px-6 py-4 text-right space-x-2">
                      <Link
                        to={`/students/${student.id}`}
                        title="View Profile & Progress"
                        className="inline-flex items-center p-1.5 text-slate-600 hover:text-indigo-600 hover:bg-indigo-50 rounded-md transition-colors"
                      >
                        <Eye className="w-4 h-4" />
                      </Link>
                      {(isSuperAdmin || isCenterManager) && (
                        <Link
                          to={`/students/${student.id}/edit`}
                          title="Edit Student Record"
                          className="inline-flex items-center p-1.5 text-slate-600 hover:text-amber-600 hover:bg-amber-50 rounded-md transition-colors"
                        >
                          <Edit className="w-4 h-4" />
                        </Link>
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
          onPageChange={(p) => fetchStudents(p)}
        />
      </div>
    </div>
  );
};

export default StudentListPage;

