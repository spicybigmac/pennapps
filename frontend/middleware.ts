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
      loginUrl.searchParams.set('scope', 'openid profile email read:current_user');
      loginUrl.searchParams.set('state', 'random-state');
      loginUrl.searchParams.set('audience', `https://${auth0Domain}/api/v2/`);
      
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
      // Handle Auth0 callback - exchange code for tokens
      console.log('Auth callback received');
      
      const code = request.nextUrl.searchParams.get('code');
      const state = request.nextUrl.searchParams.get('state');
      
      if (!code) {
        return NextResponse.redirect(new URL('/?error=no_code', request.url));
      }
      
      try {
        // Exchange code for tokens
        const tokenResponse = await fetch(`https://${process.env.AUTH0_DOMAIN}/oauth/token`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            grant_type: 'authorization_code',
            client_id: process.env.AUTH0_CLIENT_ID,
            client_secret: process.env.AUTH0_CLIENT_SECRET,
            code: code,
            redirect_uri: `${process.env.AUTH0_BASE_URL}/auth/callback`,
          }),
        });
        
        const tokens = await tokenResponse.json();
        
        if (tokens.access_token) {
          // Get user info from Auth0
          const userResponse = await fetch(`https://${process.env.AUTH0_DOMAIN}/userinfo`, {
            headers: {
              'Authorization': `Bearer ${tokens.access_token}`,
            },
          });
          
          const userInfo = await userResponse.json();
          
          // Extract roles from user metadata
          let userRoles = [];
          try {
            // Get user details from Management API to access metadata
            const mgmtTokenResponse = await fetch(`https://${process.env.AUTH0_DOMAIN}/oauth/token`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                grant_type: 'client_credentials',
                client_id: process.env.AUTH0_CLIENT_ID,
                client_secret: process.env.AUTH0_CLIENT_SECRET,
                audience: `https://${process.env.AUTH0_DOMAIN}/api/v2/`,
              }),
            });
            
            const mgmtTokens = await mgmtTokenResponse.json();
            
            if (mgmtTokens.access_token) {
              // Get user details including metadata
              const userDetailsResponse = await fetch(`https://${process.env.AUTH0_DOMAIN}/api/v2/users/${userInfo.sub}`, {
                headers: {
                  'Authorization': `Bearer ${mgmtTokens.access_token}`,
                },
              });
              
              if (userDetailsResponse.ok) {
                const userDetails = await userDetailsResponse.json();
                const userMetadata = userDetails.user_metadata || {};
                const appMetadata = userDetails.app_metadata || {};
                
                // Extract roles from metadata
                userRoles = userMetadata.roles || 
                           appMetadata.roles || 
                           userMetadata.role ? [userMetadata.role] : 
                           appMetadata.role ? [appMetadata.role] : 
                           [];
                
                console.log('User roles from metadata:', userRoles);
              }
            }
          } catch (error) {
            console.error('Error fetching user metadata:', error);
          }
          
          // Store user info in session cookie
          const response = NextResponse.redirect(new URL('/', request.url));
          response.cookies.set('appSession', JSON.stringify({
            user: {
              ...userInfo,
              roles: userRoles
            },
            accessToken: tokens.access_token,
            idToken: tokens.id_token
          }), {
            httpOnly: true,
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'lax',
            maxAge: 60 * 60 * 24 * 7 // 7 days
          });
          
          return response;
        }
      } catch (error) {
        console.error('Auth callback error:', error);
        return NextResponse.redirect(new URL('/?error=auth_failed', request.url));
      }
      
      return NextResponse.redirect(new URL('/', request.url));
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
