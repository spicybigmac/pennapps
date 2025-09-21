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
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

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
    setSuccessMessage(null); // Clear any previous success message
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

      // Clear any existing errors and show success message
      setError(null);
      setSuccessMessage(`Successfully added "${newRole}" role!`);
      
      // Small delay to ensure Auth0 has processed the update
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Refresh users list to show the new role
      await fetchUsers();
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000);
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
    <div className="bg-black border border-white rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">User Management</h2>
        <button
          onClick={fetchUsers}
          disabled={loading}
          className="px-4 py-2 bg-white hover:bg-gray-300 disabled:opacity-60 text-black rounded transition-colors"
        >
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {error && (
        <div className="text-white mb-4 p-3 border border-white rounded">
          <strong>Error:</strong> {error}
        </div>
      )}

      {successMessage && (
        <div className="text-black mb-4 p-3 bg-white rounded">
          <strong>Success:</strong> {successMessage}
        </div>
      )}

      {users.length === 0 && !loading ? (
        <div className="text-white text-center py-8">No users found</div>
      ) : (
        <div className="space-y-4">
          {users.map((user) => (
            <div key={user.user_id} className="bg-black border border-white/20 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  {user.picture && (
                    <img
                      src={user.picture}
                      alt={user.name}
                      className="w-12 h-12 rounded-full object-cover"
                    />
                  )}
                  <div className="flex-1">
                    <div className="text-white font-medium">
                      {user.name || 'Unknown'}
                    </div>
                    <div className="text-white text-sm">
                      {user.email}
                    </div>
                    {user.user_metadata?.department && (
                      <div className="text-white text-xs">
                        {user.user_metadata.department}
                      </div>
                    )}
                    {user.last_login && (
                      <div className="text_white text-xs">
                        Last login: {new Date(user.last_login).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex flex-wrap gap-2">
                  {user.roles && user.roles.length > 0 ? (
                    user.roles.map((role, index) => (
                      <span
                        key={index}
                        className={`px-2 py-1 text-xs rounded border border-white text-white`}
                      >
                        {role}
                      </span>
                    ))
                  ) : (
                    <span className="text-white text-xs">No roles</span>
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
                  className="text-sm bg-black border border_white text-white rounded px-2 py-1 focus:outline-none"
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
                <div className="text-xs text-white mt-2">Updating...</div>
              )}
              
              {/* Debug info */}
              <details className="mt-3">
                <summary className="text-xs text-white cursor-pointer">Debug Info</summary>
                <div className="text-xs text-white mt-2 space-y-1">
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
