const CACHE_NAME = 'samr-pwa-v1';
const urlsToCache = [
  '/',
  '/static/css/bootstrap.min.css',
  '/static/css/styles.css',
  '/static/js/bootstrap.bundle.min.js',
  '/static/js/chatbot.js'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Return cache hit or fetch from network
        return response || fetch(event.request).catch(() => {
          // Si falla la red (Offline), podríamos devolver un fallback de Edge AI aquí
          return new Response(JSON.stringify({ status: 'error', reply: 'Estás sin conexión. El Edge AI básico indica que si tienes dolor de pecho, busques ayuda inmediata.' }), {
            headers: { 'Content-Type': 'application/json' }
          });
        });
      })
  );
});
