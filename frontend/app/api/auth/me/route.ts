import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  // Check for session cookie
  const sessionCookie = request.cookies.get('appSession');
  
  if (sessionCookie) {
    try {
      const sessionData = JSON.parse(sessionCookie.value);
      const user = sessionData.user;
      
      if (user) {
        return NextResponse.json({ 
          user: {
            sub: user.sub,
            name: user.name,
            email: user.email,
            picture: user.picture,
            roles: user["https://myapp.example.com/roles"] || [],
            permissions: user.permissions || []
          }
        });
      }
    } catch (error) {
      console.error('Error parsing session cookie:', error);
    }
  }
  
  return NextResponse.json({ user: null });
}
