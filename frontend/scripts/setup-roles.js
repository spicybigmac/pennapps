// Script to create roles in Auth0
// Run this with: node scripts/setup-roles.js

const AUTH0_DOMAIN = process.env.AUTH0_DOMAIN;
const AUTH0_CLIENT_ID = process.env.AUTH0_CLIENT_ID;
const AUTH0_CLIENT_SECRET = process.env.AUTH0_CLIENT_SECRET;

const roles = [
  { name: 'public-trust', description: 'Public trust level access' },
  { name: 'confidential', description: 'Confidential level access' },
  { name: 'secret', description: 'Secret level access' },
  { name: 'top-secret', description: 'Top secret level access' }
];

async function createRoles() {
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

    console.log('Got management token, creating roles...');

    // Create each role
    for (const role of roles) {
      try {
        const response = await fetch(`https://${AUTH0_DOMAIN}/api/v2/roles`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${tokens.access_token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(role),
        });

        if (response.ok) {
          console.log(`✅ Created role: ${role.name}`);
        } else {
          const error = await response.json();
          if (error.code === 'role_exists') {
            console.log(`⚠️  Role already exists: ${role.name}`);
          } else {
            console.error(`❌ Failed to create role ${role.name}:`, error);
          }
        }
      } catch (error) {
        console.error(`❌ Error creating role ${role.name}:`, error);
      }
    }

    console.log('Role creation complete!');
  } catch (error) {
    console.error('Error:', error);
  }
}

createRoles();
