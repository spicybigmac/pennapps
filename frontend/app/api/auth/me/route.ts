import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  // Check for session cookie
  const sessionCookie = request.cookies.get('appSession');
  
  if (sessionCookie) {
    // Return mock user data with roles for demo purposes
    // In a real implementation, you'd decode the JWT token and extract roles
    return NextResponse.json({ 
      user: {
        sub: 'demo-user-123',
        name: 'Demo User',
        email: 'demo@example.com',
        picture: 'https://via.placeholder.com/150',
        roles: ['admin', 'user'], // Mock roles - replace with actual role extraction
        permissions: ['read:users', 'write:users', 'delete:users'] // Mock permissions
      }
    });
  }
  
  return NextResponse.json({ user: null });
}
