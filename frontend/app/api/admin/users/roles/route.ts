import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { userId, role } = await request.json();

    if (!userId || !role) {
      return NextResponse.json({ error: 'Missing userId or role' }, { status: 400 });
    }

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

    // First, get the current user to see their existing metadata
    const userResponse = await fetch(`https://${process.env.AUTH0_DOMAIN}/api/v2/users/${userId}`, {
      headers: {
        'Authorization': `Bearer ${mgmtTokens.access_token}`,
      },
    });

    if (!userResponse.ok) {
      const errorText = await userResponse.text();
      console.error('Failed to fetch user:', errorText);
      return NextResponse.json({ error: 'Failed to fetch user' }, { status: 500 });
    }

    const user = await userResponse.json();
    const currentRoles = user.app_metadata?.roles || user.user_metadata?.roles || [];
    
    // Add the new role if it doesn't already exist
    const updatedRoles = [...new Set([...currentRoles, role])];

    // Update user metadata with the new roles
    const updateResponse = await fetch(`https://${process.env.AUTH0_DOMAIN}/api/v2/users/${userId}`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${mgmtTokens.access_token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        app_metadata: {
          ...user.app_metadata,
          roles: updatedRoles,
        },
      }),
    });

    if (!updateResponse.ok) {
      const errorData = await updateResponse.json();
      console.error('Failed to update user metadata:', errorData);
      return NextResponse.json({ 
        error: `Failed to update user metadata: ${errorData.message || 'Unknown error'}` 
      }, { status: 500 });
    }

    console.log(`Successfully added role "${role}" to user "${userId}"`);
    
    return NextResponse.json({ 
      success: true, 
      message: 'Role updated successfully in Auth0',
      roles: updatedRoles 
    });
  } catch (error) {
    console.error('Error updating user role:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
