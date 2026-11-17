import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../api/client';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import AlertBanner from '../../components/common/AlertBanner';
import {
  ArrowLeft,
  Save,
  BookOpen,
  Users,
  Award,
  Clock,
  Plus,
  Trash2,
} from 'lucide-react';

export const SessionCreatePage = () => {
  const { activeCenter } = useAuth();
  const navigate = useNavigate();

  const [activities, setActivities] = useState([]);
  const [competencies, setCompetencies] = useState([]);
  const [centerStudents, setCenterStudents] = useState([]);

  const todayStr = new Date().toISOString().split('T')[0];

  const [formData, setFormData] = useState({
    activity_template_id: '',
    session_date: todayStr,
    start_time: `${todayStr}T09:00:00`,
    end_time: `${todayStr}T10:00:00`,
    topic_summary: '',
    general_notes: '',
  });

  // Participating students state: map of studentId -> { participation_status, score, qualitative_feedback, evaluations: [{ competency_id, mastery_level, teacher_notes }] }
  const [selectedStudents, setSelectedStudents] = useState({});

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const initData = async () => {
      setLoading(true);
      setError('');
      try {
        const [actRes, compRes, stuRes] = await Promise.all([
          api.get('/activities?size=50'),
          api.get('/competencies?size=100'),
          api.get('/students?status=ACTIVE&size=100'),
        ]);

        const acts = actRes.data.items || [];
        setActivities(acts);
        if (acts.length > 0) {
          setFormData((prev) => ({
            ...prev,
            activity_template_id: acts[0].id,
            topic_summary: acts[0].title || 'Session Activity',
          }));
        }

        const comps = compRes.data.items || [];
        setCompetencies(comps);

        const studs = stuRes.data.items || [];
        setCenterStudents(studs);

        // Pre-select first 3 students or all if fewer
        const initialSelected = {};
        studs.slice(0, 3).forEach((s) => {
          initialSelected[s.id] = {
            student_id: s.id,
            student_name: `${s.first_name} ${s.last_name}`,
            participation_status: 'COMPLETED',
            score: '85',
            qualitative_feedback: 'Active participant throughout the lesson.',
            evaluations: comps.length > 0 ? [{ competency_id: comps[0].id, mastery_level: 'PROFICIENT', teacher_notes: 'Demonstrated solid grasp.' }] : [],
          };
        });
        setSelectedStudents(initialSelected);
      } catch (err) {
        console.error('Initialization error', err);
        setError('Failed to load required session forms data.');
      } finally {
        setLoading(false);
      }
    };

    if (activeCenter) initData();
  }, [activeCenter]);

  const handleActivityChange = (e) => {
    const actId = e.target.value;
    const act = activities.find((a) => a.id === actId);
    setFormData((prev) => ({
      ...prev,
      activity_template_id: actId,
      topic_summary: act ? act.title : prev.topic_summary,
    }));
  };

  const handleToggleStudent = (student) => {
    setSelectedStudents((prev) => {
      const copy = { ...prev };
      if (copy[student.id]) {
        delete copy[student.id];
      } else {
        copy[student.id] = {
          student_id: student.id,
          student_name: `${student.first_name} ${student.last_name}`,
          participation_status: 'COMPLETED',
          score: '',
          qualitative_feedback: '',
          evaluations: competencies.length > 0 ? [{ competency_id: competencies[0].id, mastery_level: 'DEVELOPING', teacher_notes: '' }] : [],
        };
      }
      return copy;
    });
  };

  const updateStudentField = (studentId, field, value) => {
    setSelectedStudents((prev) => ({
      ...prev,
      [studentId]: {
        ...prev[studentId],
        [field]: value,
      },
    }));
  };

  const addEvaluationToStudent = (studentId) => {
    if (competencies.length === 0) return;
    setSelectedStudents((prev) => {
      const current = prev[studentId];
      return {
        ...prev,
        [studentId]: {
          ...current,
          evaluations: [
            ...(current.evaluations || []),
            { competency_id: competencies[0].id, mastery_level: 'DEVELOPING', teacher_notes: '' },
          ],
        },
      };
    });
  };

  const removeEvaluationFromStudent = (studentId, index) => {
    setSelectedStudents((prev) => {
      const current = prev[studentId];
      const evals = [...current.evaluations];
      evals.splice(index, 1);
      return {
        ...prev,
        [studentId]: {
          ...current,
          evaluations: evals,
        },
      };
    });
  };

  const updateEvaluationField = (studentId, evalIndex, field, value) => {
    setSelectedStudents((prev) => {
      const current = prev[studentId];
      const evals = [...current.evaluations];
      evals[evalIndex] = { ...evals[evalIndex], [field]: value };
      return {
        ...prev,
        [studentId]: {
          ...current,
          evaluations: evals,
        },
      };
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!activeCenter?.id) return;
    if (!formData.activity_template_id) {
      setError('Please select an activity template.');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      const rosterList = Object.values(selectedStudents).map((s) => ({
        student_id: s.student_id,
        participation_status: s.participation_status,
        score: s.score && s.score.trim() ? parseFloat(s.score) : null,
        qualitative_feedback: s.qualitative_feedback?.trim() || null,
        evaluations: (s.evaluations || []).map((ev) => ({
          competency_id: ev.competency_id,
          mastery_level: ev.mastery_level,
          teacher_notes: ev.teacher_notes?.trim() || null,
        })),
      }));

      const payload = {
        center_id: activeCenter.id,
        activity_template_id: formData.activity_template_id,
        session_date: formData.session_date,
        start_time: formData.start_time,
        end_time: formData.end_time,
        topic_summary: formData.topic_summary,
        general_notes: formData.general_notes.trim() || null,
        students: rosterList,
      };

      await api.post('/sessions', payload);
      navigate('/sessions');
    } catch (err) {
      console.error('Session creation error', err);
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
          ? detail.map((d) => d.msg).join(', ')
          : 'Failed to record learning session.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <LoadingSpinner fullPage text="Preparing learning session form..." />;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-3">
        <Link
          to="/sessions"
          className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Log Learning Session</h2>
          <p className="text-sm text-slate-500">
            Center: <strong className="text-slate-800">{activeCenter?.name}</strong>
          </p>
        </div>
      </div>

      {error && <AlertBanner type="error" message={error} onClose={() => setError('')} />}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Session Metadata Card */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
          <h3 className="text-base font-bold text-slate-900 pb-2 border-b border-slate-100">
            Session Details
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                Activity Template *
              </label>
              <select
                required
                value={formData.activity_template_id}
                onChange={handleActivityChange}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-indigo-500"
              >
                {activities.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.title} ({a.subject_area})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                Topic Summary *
              </label>
              <input
                type="text"
                required
                value={formData.topic_summary}
                onChange={(e) => setFormData({ ...formData, topic_summary: e.target.value })}
                placeholder="Lesson focus or theme..."
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                Session Date *
              </label>
              <input
                type="date"
                required
                value={formData.session_date}
                onChange={(e) => setFormData({ ...formData, session_date: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                  Start Time *
                </label>
                <input
                  type="datetime-local"
                  required
                  value={formData.start_time}
                  onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                  End Time *
                </label>
                <input
                  type="datetime-local"
                  required
                  value={formData.end_time}
                  onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            <div className="sm:col-span-2">
              <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                General Observations / Teacher Notes
              </label>
              <textarea
                rows="2"
                value={formData.general_notes}
                onChange={(e) => setFormData({ ...formData, general_notes: e.target.value })}
                placeholder="Classroom group dynamics, engagement levels, materials used..."
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>
        </div>

        {/* Student Participation & Evaluation Roster */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <div>
              <h3 className="text-base font-bold text-slate-900">Student Evaluations Roster</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Select participants, grade outcomes, and record competency mastery levels
              </p>
            </div>
            <span className="text-xs font-bold text-indigo-700 bg-indigo-50 px-3 py-1 rounded-full">
              {Object.keys(selectedStudents).length} Selected
            </span>
          </div>

          {/* Quick toggle chips */}
          <div className="flex flex-wrap gap-2 pt-1 pb-3">
            {centerStudents.map((s) => {
              const isSelected = !!selectedStudents[s.id];
              return (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => handleToggleStudent(s)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center space-x-1.5 ${
                    isSelected
                      ? 'bg-indigo-600 text-white shadow-xs'
                      : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  }`}
                >
                  <span>{s.first_name} {s.last_name}</span>
                </button>
              );
            })}
          </div>

          {/* Participant cards */}
          <div className="space-y-4">
            {Object.values(selectedStudents).map((stud) => (
              <div
                key={stud.student_id}
                className="p-4 border border-slate-200 rounded-xl bg-slate-50/50 space-y-3"
              >
                <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                  <h4 className="font-bold text-sm text-slate-900">{stud.student_name}</h4>
                  <button
                    type="button"
                    onClick={() => handleToggleStudent({ id: stud.student_id })}
                    className="text-xs font-semibold text-rose-600 hover:underline"
                  >
                    Remove
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-500 uppercase mb-1">
                      Participation
                    </label>
                    <select
                      value={stud.participation_status}
                      onChange={(e) => updateStudentField(stud.student_id, 'participation_status', e.target.value)}
                      className="w-full px-2.5 py-1.5 text-xs border border-slate-300 rounded bg-white"
                    >
                      <option value="COMPLETED">COMPLETED</option>
                      <option value="PARTIAL">PARTIAL</option>
                      <option value="ABSENT">ABSENT</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-[11px] font-semibold text-slate-500 uppercase mb-1">
                      Score (0 - 100)
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={stud.score}
                      onChange={(e) => updateStudentField(stud.student_id, 'score', e.target.value)}
                      placeholder="e.g. 88"
                      className="w-full px-2.5 py-1.5 text-xs border border-slate-300 rounded"
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] font-semibold text-slate-500 uppercase mb-1">
                      Feedback
                    </label>
                    <input
                      type="text"
                      value={stud.qualitative_feedback}
                      onChange={(e) => updateStudentField(stud.student_id, 'qualitative_feedback', e.target.value)}
                      placeholder="Teacher qualitative remark..."
                      className="w-full px-2.5 py-1.5 text-xs border border-slate-300 rounded"
                    />
                  </div>
                </div>

                {/* Granular Competencies */}
                <div className="pt-2 border-t border-slate-200/80 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-600 uppercase">
                      Skill Observations ({stud.evaluations?.length || 0})
                    </span>
                    <button
                      type="button"
                      onClick={() => addEvaluationToStudent(stud.student_id)}
                      className="inline-flex items-center space-x-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>Add Skill Observation</span>
                    </button>
                  </div>

                  {stud.evaluations?.map((ev, evIdx) => (
                    <div key={evIdx} className="flex flex-wrap sm:flex-nowrap items-center gap-2 bg-white p-2.5 border border-slate-200 rounded-lg">
                      <select
                        value={ev.competency_id}
                        onChange={(e) => updateEvaluationField(stud.student_id, evIdx, 'competency_id', e.target.value)}
                        className="flex-1 text-xs px-2 py-1 border border-slate-200 rounded bg-white"
                      >
                        {competencies.map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.code} - {c.name}
                          </option>
                        ))}
                      </select>

                      <select
                        value={ev.mastery_level}
                        onChange={(e) => updateEvaluationField(stud.student_id, evIdx, 'mastery_level', e.target.value)}
                        className="text-xs px-2 py-1 border border-slate-200 rounded bg-white font-semibold"
                      >
                        <option value="EMERGING">EMERGING</option>
                        <option value="DEVELOPING">DEVELOPING</option>
                        <option value="PROFICIENT">PROFICIENT</option>
                        <option value="MASTERY">MASTERY</option>
                      </select>

                      <input
                        type="text"
                        placeholder="Evaluation note..."
                        value={ev.teacher_notes}
                        onChange={(e) => updateEvaluationField(stud.student_id, evIdx, 'teacher_notes', e.target.value)}
                        className="flex-1 text-xs px-2 py-1 border border-slate-200 rounded"
                      />

                      <button
                        type="button"
                        onClick={() => removeEvaluationFromStudent(stud.student_id, evIdx)}
                        className="p-1 text-slate-400 hover:text-rose-600"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Buttons */}
        <div className="flex items-center justify-end space-x-3 pt-3">
          <Link
            to="/sessions"
            className="px-4 py-2 border border-slate-300 rounded-lg text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={submitting}
            className="inline-flex items-center space-x-2 px-6 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50 transition-colors shadow-xs"
          >
            <Save className="w-4 h-4" />
            <span>{submitting ? 'Recording Session...' : 'Log Conducted Session'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};

export default SessionCreatePage;

