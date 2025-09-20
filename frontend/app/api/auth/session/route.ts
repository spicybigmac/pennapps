import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  // Check for session cookie
  const sessionCookie = request.cookies.get('appSession');
  
  if (sessionCookie) {
    // Return mock user data for demo purposes
    return NextResponse.json({ 
      user: {
        sub: 'demo-user-123',
        name: 'Demo User',
        email: 'demo@example.com',
        picture: 'https://via.placeholder.com/150'
      }
    });
  }
  
  return NextResponse.json({ user: null });
}
