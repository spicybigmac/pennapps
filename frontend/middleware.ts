import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

export async function middleware(request: NextRequest) {
  console.log('Middleware called for:', request.nextUrl.pathname);
  
  // Handle auth routes manually for now
  if (request.nextUrl.pathname.startsWith('/auth/')) {
    console.log('Handling auth route:', request.nextUrl.pathname);
    
    if (request.nextUrl.pathname === '/auth/login') {
      // Redirect to Auth0 login
      const auth0Domain = process.env.AUTH0_DOMAIN;
      const clientId = process.env.AUTH0_CLIENT_ID;
      const baseUrl = process.env.AUTH0_BASE_URL;
      
      if (!auth0Domain || !clientId || !baseUrl) {
        return new NextResponse('Auth0 configuration missing', { status: 500 });
      }
      
      const loginUrl = new URL(`https://${auth0Domain}/authorize`);
      loginUrl.searchParams.set('client_id', clientId);
      loginUrl.searchParams.set('response_type', 'code');
      loginUrl.searchParams.set('redirect_uri', `${baseUrl}/auth/callback`);
      loginUrl.searchParams.set('scope', 'openid profile email');
      loginUrl.searchParams.set('state', 'random-state');
      
      return NextResponse.redirect(loginUrl);
    }
    
    if (request.nextUrl.pathname === '/auth/logout') {
      // Clear session cookies and redirect to Auth0 logout
      const auth0Domain = process.env.AUTH0_DOMAIN;
      const baseUrl = process.env.AUTH0_BASE_URL;
      const clientId = process.env.AUTH0_CLIENT_ID;
      
      if (!auth0Domain || !baseUrl || !clientId) {
        return new NextResponse('Auth0 configuration missing', { status: 500 });
      }
      
      const logoutUrl = new URL(`https://${auth0Domain}/v2/logout`);
      logoutUrl.searchParams.set('returnTo', baseUrl);
      logoutUrl.searchParams.set('client_id', clientId);
      
      const response = NextResponse.redirect(logoutUrl);
      // Clear session cookies
      response.cookies.delete('appSession');
      response.cookies.delete('auth0.is.authenticated');
      
      return response;
    }
    
    if (request.nextUrl.pathname === '/auth/callback') {
      // Handle Auth0 callback - for now, just redirect to home
      // In a real implementation, you'd exchange the code for tokens
      console.log('Auth callback received');
      const response = NextResponse.redirect(new URL('/', request.url));
      
      // For demo purposes, set a simple session cookie
      response.cookies.set('appSession', 'demo-user', {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        maxAge: 60 * 60 * 24 * 7 // 7 days
      });
      
      return response;
    }
    
    if (request.nextUrl.pathname === '/auth/profile') {
      // Redirect /auth/profile to /profile
      console.log('Redirecting /auth/profile to /profile');
      return NextResponse.redirect(new URL('/profile', request.url));
    }
  }
  
  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico, sitemap.xml, robots.txt (metadata files)
     */
    "/((?!_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt).*)"
  ]
};
