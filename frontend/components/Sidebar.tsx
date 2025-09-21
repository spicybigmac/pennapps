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
    <div className="w-64 bg-black text-white h-screen p-6 flex flex-col border-r border-white/20">
      <div className="mb-10 select-none">
        <div className="flex items-center space-x-3">
          <img src="/OverSEAlogo.png" alt="OverSea" className="w-7 h-7 rounded" />
          <div className="text-2xl font-bold tracking-widest">OverSea</div>
        </div>
        <div className="h-px mt-3 bg-gradient-to-r from-white/60 to-white/0" />
      </div>
      <nav className="flex flex-col space-y-2 flex-1">
        {navItems.map((item) => (
          <Link
            key={item.label}
            href={item.href}
            className={`relative px-4 py-2 rounded-lg text-sm font-medium transition-colors overflow-hidden ${
              pathname === item.href
                ? 'bg-white/10 text-white border-l-2 border-white'
                : 'text-white/70 hover:text-white hover:bg-white/10'
            }`}
          >
            {item.icon && <span className="mr-2">{item.icon}</span>}
            {item.label}
            <span className="pointer-events-none absolute inset-0 opacity-0 hover:opacity-100 transition-opacity bg-[radial-gradient(ellipse_at_left,_rgba(255,255,255,0.08),_transparent_60%)]" />
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
