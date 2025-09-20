'use client';

import { useState, useEffect } from 'react';

interface User {
  sub: string;
  name: string;
  email: string;
  picture?: string;
  roles?: string[];
  permissions?: string[];
}

interface UseAuthReturn {
  user: User | null;
  error: Error | null;
  isLoading: boolean;
  hasRole: (role: string) => boolean;
  hasPermission: (permission: string) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
  hasAnyPermission: (permissions: string[]) => boolean;
}

export function useAuth(): UseAuthReturn {
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        const response = await fetch('/api/auth/me');
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        setUser(data.user);
      } catch (err) {
        console.error('Error fetching user:', err);
        setError(err instanceof Error ? err : new Error('Unknown error'));
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchUser();
  }, []);

  // Helper functions for role and permission checking
  const hasRole = (role: string): boolean => {
    return user?.roles?.includes(role) ?? false;
  };

  const hasPermission = (permission: string): boolean => {
    return user?.permissions?.includes(permission) ?? false;
  };

  const hasAnyRole = (roles: string[]): boolean => {
    return roles.some(role => hasRole(role));
  };

  const hasAnyPermission = (permissions: string[]): boolean => {
    return permissions.some(permission => hasPermission(permission));
  };

  return { 
    user, 
    error, 
    isLoading, 
    hasRole, 
    hasPermission, 
    hasAnyRole, 
    hasAnyPermission 
  };
}
