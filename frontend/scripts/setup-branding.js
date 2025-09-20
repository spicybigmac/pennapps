// Script to set Auth0 Universal Login branding to black & white theme
// Run with: node scripts/setup-branding.js

const AUTH0_DOMAIN = process.env.AUTH0_DOMAIN;
const AUTH0_CLIENT_ID = process.env.AUTH0_CLIENT_ID;
const AUTH0_CLIENT_SECRET = process.env.AUTH0_CLIENT_SECRET;

if (!AUTH0_DOMAIN || !AUTH0_CLIENT_ID || !AUTH0_CLIENT_SECRET) {
  console.error('Missing AUTH0_DOMAIN/CLIENT_ID/CLIENT_SECRET env vars');
  process.exit(1);
}

async function setBranding() {
  // Get Management API token
  const tokenResponse = await fetch(`https://${AUTH0_DOMAIN}/oauth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
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
    process.exit(1);
  }

  const headers = {
    Authorization: `Bearer ${tokens.access_token}`,
    'Content-Type': 'application/json',
  };

  // Update universal login template to minimal BW style (use default template + CSS overrides)
  // Keep payload aligned with Branding API spec; unsupported keys are removed
  const colorsPayload = {
    colors: {
      primary: '#000000', // buttons/links use this
      page_background: '#000000',
    },
  };

  const brandingRes = await fetch(`https://${AUTH0_DOMAIN}/api/v2/branding`, {
    method: 'PATCH',
    headers,
    body: JSON.stringify(colorsPayload),
  });
  if (!brandingRes.ok) {
    const err = await brandingRes.text();
    console.error('Failed to update branding:', err);
  } else {
    console.log('✅ Updated branding colors');
  }

  const universalLoginTemplate = `
  <html>
    <head>
      <style>
        body { background:#000; color:#fff; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; }
        .auth0-lock, .auth0-lock-widget { filter:none; }
        .auth0-lock-header, .auth0-lock-header-bg { background:#000 !important; }
        .auth0-lock-header-logo { display:none; }
        .auth0-lock-name { color:#fff !important; }
        .auth0-lock-content { background:#000 !important; border:1px solid #1f2937; border-radius:12px; }
        .auth0-lock-input, .auth0-lock-input-wrap input { background:#000 !important; color:#fff !important; border-color:#1f2937 !important; }
        .auth0-lock-submit { background:#000 !important; color:#fff !important; border:1px solid #1f2937; }
        .auth0-lock-alternative { color:#9ca3af !important; }
        a { color:#e5e7eb !important; }
        button { background:#000 !important; color:#fff !important; border:1px solid #1f2937 !important; }
      </style>
    </head>
    <body>
      {{{__universal_login__}}}
    </body>
  </html>`;

  const templateRes = await fetch(`https://${AUTH0_DOMAIN}/api/v2/branding/templates/universal-login`, {
    method: 'PUT',
    headers,
    body: JSON.stringify({ template: universalLoginTemplate }),
  });
  if (!templateRes.ok) {
    const err = await templateRes.text();
    console.error('Failed to set universal login template:', err);
  } else {
    console.log('✅ Set Universal Login template to black & white');
  }
}

setBranding().catch((e) => {
  console.error(e);
  process.exit(1);
});
