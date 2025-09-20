import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    // Get Management API token
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

    if (!mgmtTokens.access_token) {
      console.error('Failed to get management token:', mgmtTokens);
      return NextResponse.json({ error: 'Failed to get management token' }, { status: 500 });
    }

    // Fetch all users from Auth0
    const usersResponse = await fetch(`https://${process.env.AUTH0_DOMAIN}/api/v2/users`, {
      headers: {
        'Authorization': `Bearer ${mgmtTokens.access_token}`,
      },
    });

    if (!usersResponse.ok) {
      const errorText = await usersResponse.text();
      console.error('Failed to fetch users:', errorText);
      return NextResponse.json({ error: 'Failed to fetch users from Auth0' }, { status: 500 });
    }

    const users = await usersResponse.json();

    // Extract roles from user metadata for each user
    const usersWithRoles = users.map((user: any) => {
      const userMetadata = user.user_metadata || {};
      const appMetadata = user.app_metadata || {};
      
      // Extract roles from metadata - prioritize app_metadata.roles
      let roles = [];
      if (appMetadata.roles && Array.isArray(appMetadata.roles)) {
        roles = appMetadata.roles;
      } else if (userMetadata.roles && Array.isArray(userMetadata.roles)) {
        roles = userMetadata.roles;
      } else if (appMetadata.role) {
        roles = [appMetadata.role];
      } else if (userMetadata.role) {
        roles = [userMetadata.role];
      }

      // Filter out null/undefined values
      const cleanRoles = roles.filter((role: any) => role && role !== null && role !== undefined);

      return {
        user_id: user.user_id,
        email: user.email,
        name: user.name,
        picture: user.picture,
        roles: cleanRoles,
        last_login: user.last_login,
        user_metadata: userMetadata,
        app_metadata: appMetadata,
      };
    });

    return NextResponse.json({ 
      users: usersWithRoles,
      message: 'Real user data from Auth0'
    });
  } catch (error) {
    console.error('Error fetching users:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
