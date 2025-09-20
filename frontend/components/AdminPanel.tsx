'use client';

import { useState, useEffect } from 'react';

interface User {
  user_id: string;
  email: string;
  name: string;
  picture?: string;
  roles: string[];
  last_login?: string;
  user_metadata?: any;
  app_metadata?: any;
}

export default function ClearancesPanel() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [updating, setUpdating] = useState<string | null>(null);

  const fetchUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/admin/users');
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to fetch users');
      }
      const data = await response.json();
      setUsers(data.users || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch users');
    } finally {
      setLoading(false);
    }
  };

  const updateUserRole = async (userId: string, newRole: string) => {
    setUpdating(userId);
    try {
      const response = await fetch('/api/admin/users/roles', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userId,
          role: newRole,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to update role');
      }

      // Refresh users list
      await fetchUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update role');
    } finally {
      setUpdating(null);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const roleOptions = ['public-trust', 'confidential', 'secret', 'top-secret'];

  return (
    <div className="bg-gray-900 rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">User Management</h2>
        <button
          onClick={fetchUsers}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded transition-colors"
        >
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {error && (
        <div className="text-red-400 mb-4 p-3 bg-red-900/20 rounded">
          <strong>Error:</strong> {error}
          <div className="text-sm mt-2">
            <p>To fix this, you need to:</p>
            <ol className="list-decimal list-inside mt-1 space-y-1">
              <li>Go to Auth0 Dashboard → Applications → APIs</li>
              <li>Find "Auth0 Management API" → Machine to Machine Applications</li>
              <li>Authorize your application with these scopes: <code className="bg-gray-700 px-1 rounded">read:users</code>, <code className="bg-gray-700 px-1 rounded">update:users</code></li>
            </ol>
          </div>
        </div>
      )}

      {users.length === 0 && !loading ? (
        <div className="text-gray-400 text-center py-8">No users found</div>
      ) : (
        <div className="space-y-4 max-h-96 overflow-y-auto">
          {users.map((user) => (
            <div key={user.user_id} className="bg-gray-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  {user.picture && (
                    <img
                      src={user.picture}
                      alt={user.name}
                      className="w-10 h-10 rounded-full"
                    />
                  )}
                  <div>
                    <div className="text-white font-medium">
                      {user.name || 'Unknown'}
                    </div>
                    <div className="text-gray-400 text-sm">
                      {user.email}
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex flex-wrap gap-2">
                  {user.roles && user.roles.length > 0 ? (
                    user.roles.map((role, index) => (
                      <span
                        key={index}
                        className={`px-2 py-1 text-xs rounded ${
                          role === 'top-secret' ? 'bg-red-600' :
                          role === 'secret' ? 'bg-orange-600' :
                          role === 'confidential' ? 'bg-yellow-600' :
                          'bg-green-600'
                        } text-white`}
                      >
                        {role}
                      </span>
                    ))
                  ) : (
                    <span className="text-gray-400 text-xs">No roles</span>
                  )}
                </div>
                
                <select
                  value=""
                  onChange={(e) => {
                    if (e.target.value) {
                      updateUserRole(user.user_id, e.target.value);
                    }
                  }}
                  disabled={updating === user.user_id}
                  className="text-sm bg-gray-700 text-white rounded px-2 py-1 border-0 focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">Add Role</option>
                  {roleOptions.map((role) => (
                    <option key={role} value={role}>
                      {role}
                    </option>
                  ))}
                </select>
              </div>
              
              {updating === user.user_id && (
                <div className="text-xs text-gray-400 mt-2">Updating...</div>
              )}
              
              {/* Debug info */}
              <details className="mt-3">
                <summary className="text-xs text-gray-500 cursor-pointer">Debug Info</summary>
                <div className="text-xs text-gray-400 mt-2 space-y-1">
                  <div><strong>User Metadata:</strong> {JSON.stringify(user.user_metadata || {})}</div>
                  <div><strong>App Metadata:</strong> {JSON.stringify(user.app_metadata || {})}</div>
                </div>
              </details>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
