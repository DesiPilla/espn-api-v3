import React, { createContext, useContext, useReducer, useEffect } from 'react';
import playoffPoolAPI from '../../utils/PlayoffPool/api';

const PlayoffPoolAuthContext = createContext();

const authReducer = (state, action) => {
  switch (action.type) {
    case 'LOGIN_SUCCESS':
      return {
        ...state,
        isAuthenticated: true,
        user: action.payload.user,
        loading: false,
        error: null,
      };
    case 'LOGOUT':
      return {
        ...state,
        isAuthenticated: false,
        user: null,
        loading: false,
        error: null,
      };
    case 'SET_LOADING':
      return {
        ...state,
        loading: action.payload,
      };
    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        loading: false,
      };
    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
      };
    default:
      return state;
  }
};

const initialState = {
  isAuthenticated: false,
  user: null,
  loading: true,
  error: null,
};

export const PlayoffPoolAuthProvider = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  useEffect(() => {
    const initializeAuth = async () => {
      // Initialize CSRF token first
      await playoffPoolAPI.initializeCSRF();
      
      // Check if user is already logged in
      const user = playoffPoolAPI.getCurrentUser();
      const isAuthenticated = playoffPoolAPI.isAuthenticated();

      if (isAuthenticated && user) {
        dispatch({
          type: 'LOGIN_SUCCESS',
          payload: { user },
        });
      } else {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    };

    initializeAuth();
  }, []);

  const login = async (username, password) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'CLEAR_ERROR' });
      
      const data = await playoffPoolAPI.login(username, password);
      dispatch({
        type: 'LOGIN_SUCCESS',
        payload: data,
      });
      
      return { success: true, data };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.non_field_errors?.[0] || 
                          'Login failed';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      return { success: false, error: errorMessage };
    }
  };

  const register = async (userData) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'CLEAR_ERROR' });
      
      const data = await playoffPoolAPI.register(userData);
      dispatch({
        type: 'LOGIN_SUCCESS',
        payload: data,
      });
      
      return { success: true, data };
    } catch (error) {
      const errorMessage = error.response?.data?.username?.[0] || 
                          error.response?.data?.email?.[0] || 
                          error.response?.data?.password?.[0] || 
                          'Registration failed';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      return { success: false, error: errorMessage };
    }
  };

  const logout = () => {
    playoffPoolAPI.logout();
    dispatch({ type: 'LOGOUT' });
  };

  const value = {
    ...state,
    login,
    register,
    logout,
    clearError: () => dispatch({ type: 'CLEAR_ERROR' }),
  };

  return (
    <PlayoffPoolAuthContext.Provider value={value}>
      {children}
    </PlayoffPoolAuthContext.Provider>
  );
};

export const usePlayoffPoolAuth = () => {
  const context = useContext(PlayoffPoolAuthContext);
  if (!context) {
    throw new Error('usePlayoffPoolAuth must be used within a PlayoffPoolAuthProvider');
  }
  return context;
};