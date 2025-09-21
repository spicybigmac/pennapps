'use client';

import { useAuth } from '../../hooks/useAuth';
import Link from 'next/link';

export default function Profile() {
  const { user, error, isLoading } = useAuth();

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
          <h1 className="text-2xl font-bold text-white mb-4">Not Logged In</h1>
          <p className="text-white mb-4">You need to be logged in to view your profile.</p>
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

  return (
    <div className="p-8" style={{marginLeft:"104px"}}>
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold text-white mb-8">Profile</h1>
        
        <div className="bg-black border border-white rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4">User Information</h2>
          <div className="space-y-3">
            <div>
              <label className="text-white text-sm">Name</label>
              <p className="text-white">{user.name || 'Not provided'}</p>
            </div>
            <div>
              <label className="text-white text-sm">Email</label>
              <p className="text-white">{user.email || 'Not provided'}</p>
            </div>
            <div>
              <label className="text-white text-sm">User ID</label>
              <p className="text-white font-mono text-sm">{user.sub || 'Not provided'}</p>
            </div>
            {user.roles && user.roles.length > 0 && (
              <div>
                <label className="text-white text-sm">Roles</label>
                <div className="flex flex-wrap gap-2 mt-1">
                  {user.roles.map((role, index) => (
                    <span 
                      key={index}
                      className="px-2 py-1 border border-white text-white text-xs rounded bg-black"
                    >
                      {role}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {user.picture && (
              <div>
                <label className="text-white text-sm">Profile Picture</label>
                <div className="mt-2">
                  <img 
                    src={user.picture} 
                    alt="Profile" 
                    className="w-16 h-16 rounded-full"
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="bg-black border border-white rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Account Actions</h2>
          <div className="space-y-3">
            <Link 
              href="/auth/logout" 
              className="inline-block px-4 py-2 bg-white hover:bg-gray-300 text-black rounded transition-colors"
            >
              Logout
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
