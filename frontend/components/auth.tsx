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
          <div className="relative group">
            <span className="text-white text-sm cursor-default">Welcome, {user.name}</span>
            <div className="absolute left-0 bottom-full mb-2 w-28 opacity-0 pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto transition-opacity">
              <Link 
                href="/auth/logout" 
                className="block px-3 py-2 bg-black border border-gray-800 text-white text-sm rounded hover:bg-gray-900 outline outline-gray-700"
              >
                Logout
              </Link>
            </div>
          </div>
        </>
      ) : (
        <Link 
          href="/auth/login" 
          className="px-3 py-1 bg-white hover:bg-gray-300 text-black text-sm rounded transition-colors"
        >
          Login
        </Link>
      )}
    </div>
  );
}
