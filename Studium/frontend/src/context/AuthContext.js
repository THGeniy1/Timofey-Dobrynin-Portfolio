import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { createContext, useState, useEffect, useRef, useCallback, useMemo } from 'react';
import device from 'current-device';

axios.defaults.withCredentials = true;

const AuthContext = createContext();

const getIsMobileOrTablet = () =>
  device.mobile() || device.tablet() || window.innerWidth < 1200;

export default AuthContext;

export function AuthProvider({ children }) {
  const navigate = useNavigate();
  const [accessToken, setAccessToken] = useState(null);
  const [user, setUser] = useState({});
  const [error, setError] = useState(null);
  const [cachedFiles, setCachedFiles] = useState(null);
  const [isMobileOrTablet, setIsMobileOrTablet] = useState(getIsMobileOrTablet());
  const [authData, setAuthData] = useState({});
  const [onLogoutCallbacks, setOnLogoutCallbacks] = useState([]);
  
  const refreshTimer = useRef(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    const authType = params.get('auth_type') || 'login';
    if (token) setAuthData({ token, authType });
  }, []);

  useEffect(() => {
    const onResize = () => setIsMobileOrTablet(getIsMobileOrTablet());
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const clearRefreshTimer = () => {
    if (refreshTimer.current) {
      clearInterval(refreshTimer.current);
      refreshTimer.current = null;
    }
  };

  const startRefreshTimer = () => {
    clearRefreshTimer();
    refreshTimer.current = setInterval(() => {
      updateToken();
    }, 4 * 60 * 1000); // 4 минуты
  };

  const login = async e => {
    e.preventDefault();

    try {
      const { data } = await axios.post('/api/auth/login/', {
        email: e.target.email.value,
        password: e.target.password.value,
      });      
      setUser(data.user_data);
      setAccessToken(data.access)
      startRefreshTimer();
    } catch (error) {      
      setError(error.response.data.message || 'Произошла ошибка при входе');
    }
  };

  const logout = async () => {
    try {
      clearRefreshTimer();
      await axios.post('/api/auth/logout/');
    } finally {
      onLogoutCallbacks.forEach(callback => callback());
      setUser({});
      setAccessToken(null)
      navigate('/');
    }
  };

  const updateUserData = async updatedData => {
    try {
      const { data } = await axios.put('/api/up/me/upd/', updatedData, {headers: { 'Authorization': `Bearer ${accessToken}`}});
      setUser(data.user_data);
    } catch (error) {
      setError(error.response.data.message  || 'Произошла ошибка при обновлении данных');
    }
  };

  const refreshUserData = async () => {
    try {
      const { data } = await axios.get('/api/auth/me/', {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    });
      setUser(data);
    } catch (error) {
      setError(error.response.data.message  || 'Произошла ошибка при обновлении данных');
    }
  };

  const updateToken = async () => {
    try {
      const { data } = await axios.post('/api/auth/token/refresh/');
      setAccessToken(data.access); // обновляем состояние
      if (!refreshTimer.current) startRefreshTimer();
      return data.access; // возвращаем новый токен
    } catch {
      if (accessToken && user.id) await logout();
      return null;
    }
  };
  
  const initializeAuth = async () => {
    const token = await updateToken();
    if (token) {
      try{
        const { data } = await axios.get('/api/auth/me/', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        setUser(data);
      } catch (error) {
        setError(error.response.data.message  || 'Произошла ошибка при обновлении данных');
      }
    }
  };

  useEffect(() => {
    initializeAuth();
    return clearRefreshTimer;
  }, []);


  const registerLogoutCallback = useCallback((callback) => {
    setOnLogoutCallbacks(prev => [...prev, callback]);
    return () => setOnLogoutCallbacks(prev => prev.filter(cb => cb !== callback));
  }, []);

  const loadFilesFromCache = async () => {
    try {
      const { data } = await axios.get('/api/jsons/main/');
      setCachedFiles(data);
    } catch (error) {
      setError(error.response.data.message  || 'Ошибка при загрузке файлов');
    }
  };

  useEffect(() => {
    loadFilesFromCache();
  }, []);

  useEffect(() => {
    if (user?.client?.is_banned) {
      setError('Ваш аккаунт заблокирован. Свяжитесь с поддержкой для разблокировки.');
    }
  }, [user]);

  useEffect(() => {
    const interceptorId = axios.interceptors.response.use(
      response => response,
      error => {
        const r = error.response;
        if (r?.status === 423) {
          setError('Ваш аккаунт заблокирован. Свяжитесь с поддержкой.');
        }
        return Promise.reject(error);
      }
    );
  
    return () => axios.interceptors.response.eject(interceptorId);
  }, []);
  
  const contextValue = useMemo(() => ({
    user,
    error,
    accessToken,
    cachedFiles,
    isMobileOrTablet,
    login,
    logout,
    updateUserData,
    refreshUserData,
    registerLogoutCallback,
    authData,
    setError,
  }), [
    user,
    error,
    accessToken,
    cachedFiles,
    isMobileOrTablet,
    login,
    logout,
    updateUserData,
    refreshUserData,
    registerLogoutCallback,
    authData,
  ]);

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}