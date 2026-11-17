import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../api/client';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('user_info');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('access_token'));
  const [assignedCenters, setAssignedCenters] = useState(() => {
    const saved = localStorage.getItem('assigned_centers');
    return saved ? JSON.parse(saved) : [];
  });
  const [activeCenter, setActiveCenter] = useState(() => {
    const saved = localStorage.getItem('active_center');
    return saved ? JSON.parse(saved) : null;
  });
  const [loading, setLoading] = useState(true);

  // Sync / refresh profile on boot
  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('access_token');
      if (!storedToken) {
        setLoading(false);
        return;
      }

      try {
        const { data: userData } = await api.get('/auth/me');
        setUser(userData);
        localStorage.setItem('user_info', JSON.stringify(userData));

        let centers = userData.assigned_centers || [];
        if (userData.role === 'SUPER_ADMIN') {
          // Super admin has access to all centers in system
          try {
            const { data: centerList } = await api.get('/centers?page_size=100');
            centers = centerList.items || centerList;
          } catch (e) {
            console.error('Failed to load all centers for super admin', e);
          }
        }
        setAssignedCenters(centers);
        localStorage.setItem('assigned_centers', JSON.stringify(centers));

        // Preserve or assign active center
        const savedCenterId = localStorage.getItem('active_center_id');
        const match = centers.find((c) => c.id === savedCenterId);
        if (match) {
          setActiveCenter(match);
          localStorage.setItem('active_center', JSON.stringify(match));
        } else if (centers.length > 0) {
          setActiveCenter(centers[0]);
          localStorage.setItem('active_center_id', centers[0].id);
          localStorage.setItem('active_center', JSON.stringify(centers[0]));
        }
      } catch (err) {
        console.error('Failed to verify existing session', err);
        logout();
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    const { access_token, refresh_token, user: userData } = response.data;

    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    localStorage.setItem('user_info', JSON.stringify(userData));

    setToken(access_token);
    setUser(userData);

    // Resolve centers
    let centers = userData.assigned_centers || [];
    if (userData.role === 'SUPER_ADMIN') {
      try {
        const { data: centerList } = await api.get('/centers?page_size=100', {
          headers: { Authorization: `Bearer ${access_token}` },
        });
        centers = centerList.items || centerList;
      } catch (e) {
        console.error('Failed to fetch centers for super admin', e);
      }
    }

    setAssignedCenters(centers);
    localStorage.setItem('assigned_centers', JSON.stringify(centers));

    if (centers.length > 0) {
      const defaultCenter = centers[0];
      setActiveCenter(defaultCenter);
      localStorage.setItem('active_center_id', defaultCenter.id);
      localStorage.setItem('active_center', JSON.stringify(defaultCenter));
    } else {
      setActiveCenter(null);
      localStorage.removeItem('active_center_id');
      localStorage.removeItem('active_center');
    }

    return userData;
  };

  const switchCenter = (center) => {
    setActiveCenter(center);
    if (center && center.id) {
      localStorage.setItem('active_center_id', center.id);
      localStorage.setItem('active_center', JSON.stringify(center));
    } else {
      localStorage.removeItem('active_center_id');
      localStorage.removeItem('active_center');
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_info');
    localStorage.removeItem('active_center_id');
    localStorage.removeItem('active_center');
    localStorage.removeItem('assigned_centers');

    setUser(null);
    setToken(null);
    setActiveCenter(null);
    setAssignedCenters([]);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        activeCenter,
        assignedCenters,
        loading,
        login,
        logout,
        switchCenter,
        isAuthenticated: !!token && !!user,
        isSuperAdmin: user?.role === 'SUPER_ADMIN',
        isCenterManager: user?.role === 'CENTER_MANAGER',
        isTeacher: user?.role === 'TEACHER',
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

