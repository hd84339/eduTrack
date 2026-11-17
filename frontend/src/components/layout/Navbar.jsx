import React from 'react';
import { useAuth } from '../../context/AuthContext';
import Badge from '../common/Badge';
import { LogOut, Building2, User, ChevronDown } from 'lucide-react';

export const Navbar = () => {
  const { user, activeCenter, assignedCenters, switchCenter, logout, isSuperAdmin } = useAuth();

  const handleCenterChange = (e) => {
    const selectedId = e.target.value;
    const center = assignedCenters.find((c) => c.id === selectedId);
    if (center) {
      switchCenter(center);
    }
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between sticky top-0 z-30 shadow-sm">
      {/* Brand & Active Center */}
      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-2">
          <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-lg shadow-sm">
            E
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-900 leading-none">EduTrack</h1>
            <p className="text-xs text-slate-500 mt-0.5">Multi-Center Learning Platform</p>
          </div>
        </div>

        {/* Center Switcher */}
        <div className="hidden sm:flex items-center space-x-2 bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5">
          <Building2 className="w-4 h-4 text-indigo-600" />
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Center:</span>
          {assignedCenters.length > 1 || isSuperAdmin ? (
            <div className="relative">
              <select
                value={activeCenter?.id || ''}
                onChange={handleCenterChange}
                className="bg-transparent text-sm font-semibold text-slate-800 pr-6 pl-1 py-0.5 border-none focus:outline-none cursor-pointer appearance-none"
              >
                {assignedCenters.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.code})
                  </option>
                ))}
              </select>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-0 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          ) : (
            <span className="text-sm font-semibold text-slate-800">
              {activeCenter ? `${activeCenter.name} (${activeCenter.code})` : 'No Center Assigned'}
            </span>
          )}
        </div>
      </div>

      {/* User info and Logout */}
      <div className="flex items-center space-x-4">
        {user && (
          <div className="flex items-center space-x-3">
            <div className="text-right hidden md:block">
              <div className="text-sm font-semibold text-slate-800">{user.full_name}</div>
              <div className="text-xs text-slate-500">{user.email}</div>
            </div>
            <Badge value={user.role} />
          </div>
        )}

        <button
          onClick={logout}
          title="Sign out of EduTrack"
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-sm font-medium text-slate-600 hover:text-rose-600 hover:bg-rose-50 border border-slate-200 rounded-lg transition-colors"
        >
          <LogOut className="w-4 h-4" />
          <span className="hidden sm:inline">Sign Out</span>
        </button>
      </div>
    </header>
  );
};

export default Navbar;

