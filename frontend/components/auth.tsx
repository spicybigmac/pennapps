'use client';

import { useState, useRef } from 'react';
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
          <HoverLogout name={user.name} />
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

function HoverLogout({ name }: { name: string }) {
  const [open, setOpen] = useState(false);
  const hideTimer = useRef<number | null>(null);

  const onEnter = () => {
    if (hideTimer.current) {
      window.clearTimeout(hideTimer.current);
      hideTimer.current = null;
    }
    setOpen(true);
  };

  const onLeave = () => {
    if (hideTimer.current) window.clearTimeout(hideTimer.current);
    hideTimer.current = window.setTimeout(() => setOpen(false), 200);
  };

  return (
    <div className="relative" onMouseEnter={onEnter} onMouseLeave={onLeave}>
      <span className="text-white text-sm cursor-default">Welcome, {name}</span>
      <div className={`absolute left-0 bottom-full mb-2 w-28 transition-opacity ${open ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}>
        <Link 
          href="/auth/logout" 
          className="block px-3 py-2 bg-black border border-white/20 text-white text-sm rounded hover:bg-white hover:text-black"
        >
          Logout
        </Link>
      </div>
    </div>
  );
}
