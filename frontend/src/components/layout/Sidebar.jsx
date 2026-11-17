import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  LayoutDashboard,
  Users,
  CalendarCheck,
  Award,
  BookOpen,
  ArrowRightLeft,
  Building2,
  UserCheck,
  FileBarChart,
  ShieldAlert,
} from 'lucide-react';

export const Sidebar = () => {
  const { user, isSuperAdmin, isCenterManager } = useAuth();

  const primaryNavItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Students', path: '/students', icon: Users },
    { name: 'Attendance', path: '/attendance', icon: CalendarCheck },
    { name: 'Competencies', path: '/competencies', icon: Award },
    { name: 'Learning Sessions', path: '/sessions', icon: BookOpen },
    { name: 'Student Transfers', path: '/transfers', icon: ArrowRightLeft },
  ];

  const adminNavItems = [];

  if (isSuperAdmin || isCenterManager) {
    adminNavItems.push({ name: 'Centers', path: '/admin/centers', icon: Building2 });
    adminNavItems.push({ name: 'Staff Management', path: '/admin/users', icon: UserCheck });
    adminNavItems.push({ name: 'Reports & Export', path: '/admin/reports', icon: FileBarChart });
  }

  if (isSuperAdmin) {
    adminNavItems.push({ name: 'Audit Logs', path: '/admin/audit-logs', icon: ShieldAlert });
  }

  const navLinkClass = ({ isActive }) =>
    `flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
      isActive
        ? 'bg-indigo-50 text-indigo-700 font-semibold shadow-xs'
        : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
    }`;

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col h-[calc(100vh-4rem)] sticky top-16 select-none">
      <div className="flex-1 py-4 px-3 space-y-6 overflow-y-auto">
        {/* Core Operations */}
        <div>
          <div className="px-3 mb-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Operations
          </div>
          <nav className="space-y-1">
            {primaryNavItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink key={item.path} to={item.path} className={navLinkClass}>
                  <Icon className="w-5 h-5 flex-shrink-0" />
                  <span>{item.name}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Administration */}
        {adminNavItems.length > 0 && (
          <div>
            <div className="px-3 mb-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Administration
            </div>
            <nav className="space-y-1">
              {adminNavItems.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink key={item.path} to={item.path} className={navLinkClass}>
                    <Icon className="w-5 h-5 flex-shrink-0" />
                    <span>{item.name}</span>
                  </NavLink>
                );
              })}
            </nav>
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="p-3 border-t border-slate-200 bg-slate-50 text-center">
        <div className="text-xs text-slate-500 font-medium">EduTrack MVP v1.0.0</div>
        <div className="text-[11px] text-slate-400">PostgreSQL 18 • FastAPI • React</div>
      </div>
    </aside>
  );
};

export default Sidebar;

