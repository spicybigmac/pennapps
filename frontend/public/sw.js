// Minimal no-op service worker to prevent 404s on /sw.js
self.addEventListener('install', () => {
	self.skipWaiting();
});

self.addEventListener('activate', (event) => {
	event.waitUntil(self.clients.claim());
});

// Pass-through fetch handler (no caching by default)
self.addEventListener('fetch', () => {
	// Intentionally empty
});


