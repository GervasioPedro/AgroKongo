// static/js/sw.js
const CACHE_NAME = 'agrokongo-v27';
const urlsToCache = [
  '/',
  '/static/css/main.css',
  '/static/js/app.js',
  '/static/icons/icon-192.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache).catch(console.warn))
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});