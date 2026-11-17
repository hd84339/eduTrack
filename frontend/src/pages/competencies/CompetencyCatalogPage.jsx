import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../api/client';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import AlertBanner from '../../components/common/AlertBanner';
import Badge from '../../components/common/Badge';
import {
  Award,
  Search,
  PlusCircle,
  BookOpen,
  Filter,
  CheckCircle2,
  Sparkles,
} from 'lucide-react';

export const CompetencyCatalogPage = () => {
  const { isSuperAdmin } = useAuth();
  const [competencies, setCompetencies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedDomain, setSelectedDomain] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Add Competency Modal State
  const [showAddModal, setShowAddModal] = useState(false);
  const [newComp, setNewComp] = useState({
    code: '',
    name: '',
    domain: 'Cognitive',
    description: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [modalError, setModalError] = useState('');

  const fetchCompetencies = async () => {
    setLoading(true);
    setError('');
    try {
      const params = { size: 100 };
      if (search.trim()) params.search = search.trim();
      if (selectedDomain) params.domain = selectedDomain;

      const { data } = await api.get('/competencies', { params });
      setCompetencies(data.items || []);
    } catch (err) {
      console.error('Error fetching competencies', err);
      setError(err.response?.data?.detail || 'Failed to load competency catalog.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCompetencies();
  }, [selectedDomain]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchCompetencies();
  };

  const handleAddSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setModalError('');

    try {
      await api.post('/competencies', newComp);
      setSuccess(`Competency "${newComp.code}" created successfully.`);
      setShowAddModal(false);
      setNewComp({ code: '', name: '', domain: 'Cognitive', description: '' });
      fetchCompetencies();
    } catch (err) {
      console.error('Error adding competency', err);
      const detail = err.response?.data?.detail;
      setModalError(typeof detail === 'string' ? detail : 'Failed to create competency.');
    } finally {
      setSubmitting(false);
    }
  };

  const uniqueDomains = Array.from(new Set(competencies.map((c) => c.domain))).filter(Boolean);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Curriculum Competency Catalog</h2>
          <p className="text-sm text-slate-500 mt-0.5">
            Standardized developmental rubrics tracked across all learning centers
          </p>
        </div>

        {isSuperAdmin && (
          <button
            onClick={() => setShowAddModal(true)}
            className="inline-flex items-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 shadow-xs transition-colors self-start sm:self-auto"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Add Competency</span>
          </button>
        )}
      </div>

      {success && <AlertBanner type="success" message={success} onClose={() => setSuccess('')} />}
      {error && <AlertBanner type="error" message={error} onClose={() => setError('')} />}

      {/* 4-Tier Rubric Reference Banner */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
        <div className="flex items-center space-x-2 text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
          <Sparkles className="w-4 h-4 text-indigo-500" />
          <span>Standardized 4-Tier Rubric Framework</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
          <div className="p-3 rounded-lg border border-amber-200 bg-amber-50/50">
            <Badge value="EMERGING" className="mb-1.5" />
            <p className="text-slate-600 font-medium">Initial awareness; requires direct teacher guidance.</p>
          </div>
          <div className="p-3 rounded-lg border border-sky-200 bg-sky-50/50">
            <Badge value="DEVELOPING" className="mb-1.5" />
            <p className="text-slate-600 font-medium">Demonstrates skill with partial support and coaching.</p>
          </div>
          <div className="p-3 rounded-lg border border-emerald-200 bg-emerald-50/50">
            <Badge value="PROFICIENT" className="mb-1.5" />
            <p className="text-slate-600 font-medium">Consistent, independent mastery of learning objective.</p>
          </div>
          <div className="p-3 rounded-lg border border-purple-200 bg-purple-50/50">
            <Badge value="MASTERY" className="mb-1.5" />
            <p className="text-slate-600 font-medium">Generalizes skill to novel contexts and guides peers.</p>
          </div>
        </div>
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
              placeholder="Search competencies by code, name, or description..."
              className="w-full pl-9 pr-4 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
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
          <span className="text-xs font-semibold text-slate-500 uppercase">Domain:</span>
          <select
            value={selectedDomain}
            onChange={(e) => setSelectedDomain(e.target.value)}
            className="text-sm border border-slate-300 rounded-lg px-3 py-2 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Domains</option>
            {uniqueDomains.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Competencies Grid */}
      {loading ? (
        <LoadingSpinner text="Fetching competency catalog..." size="md" />
      ) : competencies.length === 0 ? (
        <div className="bg-white p-12 text-center rounded-xl border border-slate-200">
          <Award className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-800">No competencies found</h3>
          <p className="text-sm text-slate-500 mt-1">
            Try adjusting your search query or domain filter.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {competencies.map((comp) => (
            <div
              key={comp.id}
              className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex flex-col justify-between hover:border-indigo-300 transition-colors"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-xs font-bold text-indigo-600 bg-indigo-50 px-2.5 py-0.5 rounded">
                    {comp.code}
                  </span>
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    {comp.domain}
                  </span>
                </div>
                <h4 className="text-base font-bold text-slate-900 mb-2">{comp.name}</h4>
                <p className="text-xs text-slate-600 line-clamp-3">
                  {comp.description || 'Standardized curriculum rubric item.'}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
                <span>Standardized Rubric</span>
                <Award className="w-4 h-4 text-indigo-400" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Competency Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
              <PlusCircle className="w-5 h-5 text-indigo-600" />
              <span>Add Catalog Competency</span>
            </h3>

            {modalError && <AlertBanner type="error" message={modalError} />}

            <form onSubmit={handleAddSubmit} className="space-y-4 pt-1">
              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                  Competency Code *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. MATH-FRAC-01"
                  value={newComp.code}
                  onChange={(e) => setNewComp({ ...newComp, code: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                  Display Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Fraction Multiplication"
                  value={newComp.name}
                  onChange={(e) => setNewComp({ ...newComp, name: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                  Domain *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Cognitive, Social-Emotional, STEM"
                  value={newComp.domain}
                  onChange={(e) => setNewComp({ ...newComp, domain: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                  Rubric & Description
                </label>
                <textarea
                  rows="3"
                  placeholder="Guidance on observing and assessing this competency across tiers..."
                  value={newComp.description}
                  onChange={(e) => setNewComp({ ...newComp, description: e.target.value })}
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
                  {submitting ? 'Creating...' : 'Save Competency'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default CompetencyCatalogPage;

