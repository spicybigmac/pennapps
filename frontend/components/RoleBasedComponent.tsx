'use client';

import { useAuth } from '../hooks/useAuth';

interface RoleBasedComponentProps {
  children: React.ReactNode;
  requiredRole?: string;
  requiredRoles?: string[];
  requiredPermission?: string;
  requiredPermissions?: string[];
  fallback?: React.ReactNode;
}

export default function RoleBasedComponent({
  children,
  requiredRole,
  requiredRoles,
  requiredPermission,
  requiredPermissions,
  fallback = null
}: RoleBasedComponentProps) {
  const { user, hasRole, hasPermission, hasAnyRole, hasAnyPermission } = useAuth();

  // Check if user has required role
  if (requiredRole && !hasRole(requiredRole)) {
    return <>{fallback}</>;
  }

  // Check if user has any of the required roles
  if (requiredRoles && !hasAnyRole(requiredRoles)) {
    return <>{fallback}</>;
  }

  // Check if user has required permission
  if (requiredPermission && !hasPermission(requiredPermission)) {
    return <>{fallback}</>;
  }

  // Check if user has any of the required permissions
  if (requiredPermissions && !hasAnyPermission(requiredPermissions)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}

// Example usage components
export function AdminOnlyButton() {
  return (
    <RoleBasedComponent requiredRole="admin" fallback={<div className="text-gray-500">Admin access required</div>}>
      <button className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">
        Admin Action
      </button>
    </RoleBasedComponent>
  );
}

export function UserManagementSection() {
  return (
    <RoleBasedComponent 
      requiredPermissions={['read:users', 'write:users']} 
      fallback={<div className="text-gray-500">User management access required</div>}
    >
      <div className="p-4 bg-gray-800 rounded">
        <h3 className="text-white font-bold">User Management</h3>
        <p className="text-gray-300">You can manage users here</p>
      </div>
    </RoleBasedComponent>
  );
}
