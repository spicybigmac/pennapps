'use client';

import { useAuth } from '../hooks/useAuth';
import Link from 'next/link';

export default function AuthNav() {
  const { user, error, isLoading } = useAuth();

  if (isLoading) return <div className="text-gray-400">Loading...</div>;
  if (error) return <div className="text-red-400">Error: {error.message}</div>;

  return (
    <div className="flex items-center space-x-4">
      {user ? (
        <>
          <span className="text-gray-300 text-sm">Welcome, {user.name}</span>
          <Link 
            href="/auth/logout" 
            className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-sm rounded transition-colors"
          >
            Logout
          </Link>
        </>
      ) : (
        <Link 
          href="/auth/login" 
          className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors"
        >
          Login
        </Link>
      )}
    </div>
  );
}
