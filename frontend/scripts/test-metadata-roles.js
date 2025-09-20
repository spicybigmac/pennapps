// Test script to verify metadata-based roles
// This will help debug what's in the user metadata

const AUTH0_DOMAIN = process.env.AUTH0_DOMAIN;
const AUTH0_CLIENT_ID = process.env.AUTH0_CLIENT_ID;
const AUTH0_CLIENT_SECRET = process.env.AUTH0_CLIENT_SECRET;

async function testMetadataRoles() {
  try {
    // Get Management API token
    const tokenResponse = await fetch(`https://${AUTH0_DOMAIN}/oauth/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        grant_type: 'client_credentials',
        client_id: AUTH0_CLIENT_ID,
        client_secret: AUTH0_CLIENT_SECRET,
        audience: `https://${AUTH0_DOMAIN}/api/v2/`,
      }),
    });

    const tokens = await tokenResponse.json();

    if (!tokens.access_token) {
      console.error('Failed to get management token:', tokens);
      return;
    }

    console.log('✅ Got management token');

    // Get all users
    const usersResponse = await fetch(`https://${AUTH0_DOMAIN}/api/v2/users`, {
      headers: {
        'Authorization': `Bearer ${tokens.access_token}`,
      },
    });

    if (!usersResponse.ok) {
      console.error('Failed to fetch users:', await usersResponse.text());
      return;
    }

    const users = await usersResponse.json();
    console.log(`✅ Found ${users.length} users`);

    // Check each user's metadata
    users.forEach((user, index) => {
      console.log(`\n--- User ${index + 1}: ${user.email} ---`);
      console.log('User Metadata:', JSON.stringify(user.user_metadata || {}, null, 2));
      console.log('App Metadata:', JSON.stringify(user.app_metadata || {}, null, 2));
      
      // Extract roles
      const userMetadata = user.user_metadata || {};
      const appMetadata = user.app_metadata || {};
      
      const roles = userMetadata.roles || 
                   appMetadata.roles || 
                   userMetadata.role ? [userMetadata.role] : 
                   appMetadata.role ? [appMetadata.role] : 
                   [];
      
      console.log('Extracted Roles:', roles);
    });

  } catch (error) {
    console.error('Error:', error);
  }
}

testMetadataRoles();
