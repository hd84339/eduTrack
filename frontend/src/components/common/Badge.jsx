import React from 'react';

const BADGE_VARIANTS = {
  // Roles
  SUPER_ADMIN: 'bg-purple-100 text-purple-800 border-purple-200',
  CENTER_MANAGER: 'bg-indigo-100 text-indigo-800 border-indigo-200',
  TEACHER: 'bg-emerald-100 text-emerald-800 border-emerald-200',

  // Statuses
  ACTIVE: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  INACTIVE: 'bg-slate-100 text-slate-700 border-slate-200',
  LOCKED: 'bg-rose-100 text-rose-800 border-rose-200',
  TRANSFERRED: 'bg-amber-100 text-amber-800 border-amber-200',
  ARCHIVED: 'bg-gray-100 text-gray-700 border-gray-200',
  PENDING: 'bg-amber-100 text-amber-800 border-amber-200',
  APPROVED: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  REJECTED: 'bg-rose-100 text-rose-800 border-rose-200',
  CANCELLED: 'bg-slate-100 text-slate-700 border-slate-200',

  // Mastery Levels (4-Tier Rubric)
  EMERGING: 'bg-amber-100 text-amber-800 border-amber-300',
  DEVELOPING: 'bg-sky-100 text-sky-800 border-sky-300',
  PROFICIENT: 'bg-emerald-100 text-emerald-800 border-emerald-300',
  MASTERY: 'bg-purple-100 text-purple-800 border-purple-300',

  // Attendance Statuses
  PRESENT: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  LATE: 'bg-amber-100 text-amber-800 border-amber-200',
  ABSENT: 'bg-rose-100 text-rose-800 border-rose-200',
  EXCUSED: 'bg-slate-100 text-slate-700 border-slate-200',
};

export const Badge = ({ value, label, variant, className = '' }) => {
  const key = variant || value;
  const style = BADGE_VARIANTS[key] || 'bg-slate-100 text-slate-800 border-slate-200';
  const displayLabel = label || (typeof value === 'string' ? value.replace(/_/g, ' ') : value);

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${style} ${className}`}
    >
      {displayLabel}
    </span>
  );
};

export default Badge;

