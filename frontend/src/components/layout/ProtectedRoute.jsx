import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import LoadingSpinner from '../common/LoadingSpinner';

export const ProtectedRoute = ({ allowedRoles }) => {
  const { isAuthenticated, loading, user } = useAuth();

  if (loading) {
    return <LoadingSpinner fullPage text="Authenticating session..." />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user?.role)) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-rose-200 p-8 text-center max-w-lg mx-auto my-12">
        <h2 className="text-xl font-bold text-rose-700 mb-2">Access Restricted</h2>
        <p className="text-sm text-slate-600 mb-6">
          Your assigned role (<strong>{user?.role}</strong>) does not have authorization to view this area.
        </p>
        <a
          href="/dashboard"
          className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700"
        >
          Return to Dashboard
        </a>
      </div>
    );
  }

  return <Outlet />;
};

export default ProtectedRoute;

