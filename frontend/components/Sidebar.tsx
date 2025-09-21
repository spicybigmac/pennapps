'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import React, { useState } from 'react';
import AuthNav from './auth';
import { useAuth } from '../hooks/useAuth';
import { 
  FiHome, 
  FiBarChart, 
  FiFileText, 
  FiUser, 
  FiShield
} from 'react-icons/fi';

interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const Sidebar = () => {
  const pathname = usePathname();
  const { user, hasRole } = useAuth();
  const [isHovered, setIsHovered] = useState(false);

  const navItems: NavItem[] = [
    { href: '/dashboard', label: 'Dashboard', icon: FiHome },
    { href: '/analyze', label: 'Intelligence Console', icon: FiBarChart },
    { href: '/reports', label: 'Reports', icon: FiFileText },
    { href: '/profile', label: 'Profile', icon: FiUser },
  ];

  // Add clearances only for logged-in users with top-secret clearance
  if (user && hasRole('top-secret')) {
    navItems.push({ href: '/clearances', label: 'Clearances', icon: FiShield });
  }

  return (
    <div 
      className={`${isHovered ? 'w-64' : 'w-26'} bg-black text-white h-screen flex flex-col border-r border-white/20 transition-all duration-300 ease-in-out`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Header with logo */}
      <div className="px-6 py-4 select-none">
        <div className="flex items-center min-w-0 h-8">
          <img src="/OverSEAlogo.png" alt="OverSea" className="w-5 h-5 rounded flex-shrink-0" style={{marginLeft:"18px"}} />
          {isHovered && (
            <div className="ml-3 text-2xl font-bold tracking-widest truncate overflow-hidden whitespace-nowrap">
              OverSea
            </div>
          )}
        </div>
        <div className="h-px mt-3 bg-gradient-to-r from-white/60 to-white/0" />
      </div>

      {/* Navigation */}
      <nav className="flex flex-col space-y-2 flex-1 px-6">
        {navItems.map((item) => {
          const IconComponent = item.icon;
          return (
            <Link
              key={item.label}
              href={item.href}
              className={`relative px-4 py-2 rounded-lg text-sm font-medium transition-colors overflow-hidden group h-10 flex items-center ${
                pathname === item.href
                  ? 'bg-white/10 text-white border-l-2 border-white'
                  : 'text-white/70 hover:text-white hover:bg-white/10'
              }`}
              title={!isHovered ? item.label : undefined}
            >
              <div className="flex items-center min-w-0 h-6">
                <IconComponent className="w-5 h-5 flex-shrink-0" />
                {isHovered && (
                  <span className="ml-3 truncate overflow-hidden whitespace-nowrap">
                    {item.label}
                  </span>
                )}
              </div>
              <span className="pointer-events-none absolute inset-0 opacity-0 hover:opacity-100 transition-opacity bg-[radial-gradient(ellipse_at_left,_rgba(255,255,255,0.08),_transparent_60%)]" />
            </Link>
          );
        })}
      </nav>

      {/* Auth section */}
      <div className="mt-auto px-6 py-4">
        <div className="h-10 flex items-center" style={{marginLeft:"10px"}}>
          <AuthNav isCollapsed={!isHovered} />
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
