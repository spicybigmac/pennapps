'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import React from 'react';
import AuthNav from './auth';
import { useAuth } from '../hooks/useAuth';

interface NavItem {
  href: string;
  label: string;
  icon?: string;
}

const Sidebar = () => {
  const pathname = usePathname();
  const { user, hasRole } = useAuth();

  const navItems: NavItem[] = [
    { href: '/', label: 'Dashboard' },
    { href: '/analyze', label: 'Gemini' },
    { href: '/reports', label: 'Reports' },
    { href: '/profile', label: 'Profile' },
  ];

  // Add clearances only for logged-in users with top-secret clearance
  if (user && hasRole('top-secret')) {
    navItems.push({ href: '/clearances', label: 'Clearances' });
  }

  return (
    <div className="w-64 bg-black text-white h-screen p-6 flex flex-col border-r border-gray-800">
      <div className="mb-10">
        <h1 className="text-2xl font-bold">Expansi</h1>
      </div>
      <nav className="flex flex-col space-y-4 flex-1">
        {navItems.map((item) => (
          <Link
            key={item.label}
            href={item.href}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              pathname === item.href
                ? 'bg-gray-800 text-white'
                : 'text-gray-400 hover:bg-gray-900 hover:text-white'
            }`}
          >
            {item.icon && <span className="mr-2">{item.icon}</span>}
            {item.label}
          </Link>
        ))}
      </nav>
      <div className="mt-auto">
        <AuthNav />
      </div>
    </div>
  );
};

export default Sidebar;
