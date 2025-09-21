'use client';

import { useAuth } from '../../hooks/useAuth';
import Link from 'next/link';
import ClearancesPanel from '../../components/ClearancesPanel';

export default function Clearances() {
  const { user, error, isLoading, hasRole } = useAuth();

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="text-white">Error: {error.message}</div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="p-8">
        <div className="max-w-md mx-auto bg-black border border-white rounded-lg p-6">
          <h1 className="text-2xl font-bold text-white mb-4">Access Denied</h1>
          <p className="text-white mb-4">You need to be logged in to view clearances.</p>
          <Link 
            href="/auth/login" 
            className="inline-block px-4 py-2 bg-white hover:bg-gray-300 text-black rounded transition-colors"
          >
            Login
          </Link>
        </div>
      </div>
    );
  }

  if (!hasRole('top-secret')) {
    return (
      <div className="p-8">
        <div className="max-w-md mx-auto bg-black border border-white rounded-lg p-6">
          <h1 className="text-2xl font-bold text-white mb-4">Access Denied</h1>
          <p className="text-white mb-4">You need top-secret clearance to view this page.</p>
          <div className="flex space-x-4">
            <Link 
              href="/profile" 
              className="inline-block px-4 py-2 bg-white hover:bg-gray-300 text-black rounded transition-colors"
            >
              View Profile
            </Link>
            <Link 
              href="/" 
              className="inline-block px-4 py-2 bg-white hover:bg-gray-300 text-black rounded transition-colors"
            >
              Go Home
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Security Clearances</h1>
          <p className="text-white">Manage user access levels and security clearances</p>
        </div>
        
        <ClearancesPanel />
      </div>
    </div>
  );
}
