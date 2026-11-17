import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Layout from './components/layout/Layout';
import ProtectedRoute from './components/layout/ProtectedRoute';

// Pages
import LoginPage from './pages/auth/LoginPage';
import DashboardPage from './pages/dashboard/DashboardPage';
import StudentListPage from './pages/students/StudentListPage';
import StudentCreatePage from './pages/students/StudentCreatePage';
import StudentDetailPage from './pages/students/StudentDetailPage';
import StudentEditPage from './pages/students/StudentEditPage';
import TransferListPage from './pages/transfers/TransferListPage';
import AttendancePage from './pages/attendance/AttendancePage';
import CompetencyCatalogPage from './pages/competencies/CompetencyCatalogPage';
import SessionListPage from './pages/sessions/SessionListPage';
import SessionCreatePage from './pages/sessions/SessionCreatePage';
import CenterManagementPage from './pages/admin/CenterManagementPage';
import UserManagementPage from './pages/admin/UserManagementPage';
import ReportsPage from './pages/admin/ReportsPage';
import AuditLogsPage from './pages/admin/AuditLogsPage';

export const App = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public Authentication */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected Application Layout */}
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardPage />} />

              {/* Students */}
              <Route path="/students" element={<StudentListPage />} />
              <Route
                path="/students/new"
                element={<StudentCreatePage />}
              />
              <Route path="/students/:id" element={<StudentDetailPage />} />
              <Route
                path="/students/:id/edit"
                element={<StudentEditPage />}
              />

              {/* Attendance */}
              <Route path="/attendance" element={<AttendancePage />} />

              {/* Competencies */}
              <Route path="/competencies" element={<CompetencyCatalogPage />} />

              {/* Learning Sessions */}
              <Route path="/sessions" element={<SessionListPage />} />
              <Route path="/sessions/new" element={<SessionCreatePage />} />

              {/* Transfers */}
              <Route path="/transfers" element={<TransferListPage />} />

              {/* Administration: Center Managers & Super Admin */}
              <Route
                element={
                  <ProtectedRoute allowedRoles={['SUPER_ADMIN', 'CENTER_MANAGER']} />
                }
              >
                <Route path="/admin/centers" element={<CenterManagementPage />} />
                <Route path="/admin/users" element={<UserManagementPage />} />
                <Route path="/admin/reports" element={<ReportsPage />} />
              </Route>

              {/* Administration: Super Admin only */}
              <Route
                element={<ProtectedRoute allowedRoles={['SUPER_ADMIN']} />}
              >
                <Route path="/admin/audit-logs" element={<AuditLogsPage />} />
              </Route>
            </Route>
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;

