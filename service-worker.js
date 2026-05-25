// xrdoverlay service worker
//
// IMPORTANT: bump CACHE on ANY change to index.html, manifest.json,
// manifest.webmanifest, plotly.min.js, icons/*, or standards/*.csv.
// add_standard.py auto-bumps this constant when standards change.

const CACHE = 'xrdoverlay-v1.2.0';
const CORE = [
  './',
  './index.html',
  './manifest.json',
  './manifest.webmanifest',
  './plotly.min.js',
  './vendor/jszip.min.js',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './samples/demo.xy',
];

self.addEventListener('install', e => {
  e.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    // Core assets first (best-effort: tolerate missing files on the very first install)
    await Promise.all(CORE.map(u =>
      cache.add(u).catch(err => console.warn('[SW] cache.add failed', u, err))
    ));
    // Then standards, discovered from manifest.json
    try {
      const m = await fetch('./manifest.json', { cache: 'no-store' }).then(r => r.json());
      const stdUrls = (m.standards || []).map(s => './' + s.file);
      await Promise.all(stdUrls.map(u =>
        cache.add(u).catch(err => console.warn('[SW] cache.add std failed', u, err))
      ));
    } catch (err) {
      console.warn('[SW] manifest.json not yet available at install', err);
    }
    self.skipWaiting();
  })());
});

self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    // Only sweep our own old versions; never touch caches belonging to
    // other apps on the same origin (github.io is a shared origin).
    await Promise.all(
      keys.filter(k => k.startsWith('xrdoverlay-') && k !== CACHE)
          .map(k => caches.delete(k))
    );
    self.clients.claim();
  })());
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const url = new URL(e.request.url);
  // Same-origin only
  if (url.origin !== location.origin) return;
  e.respondWith((async () => {
    const cache = await caches.open(CACHE);
    const cached = await cache.match(e.request);
    if (cached) {
      // Cache-first, revalidate in background
      fetch(e.request).then(resp => {
        if (resp.ok) cache.put(e.request, resp.clone());
      }).catch(() => {});
      return cached;
    }
    try {
      const resp = await fetch(e.request);
      if (resp.ok) cache.put(e.request, resp.clone());
      return resp;
    } catch {
      return new Response('Offline and not cached', { status: 503, statusText: 'Offline' });
    }
  })());
});

// Message handler: lets the page request a hard cache clear (reset-cache button).
// Only delete caches owned by xrdoverlay so we don't trash other apps that may
// share the same github.io origin.
self.addEventListener('message', e => {
  if (e.data && e.data.type === 'CLEAR_CACHE') {
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => k.startsWith('xrdoverlay-')).map(k => caches.delete(k))
      ))
      .then(() => self.registration.unregister())
      .then(() => e.source && e.source.postMessage({ type: 'CACHE_CLEARED' }));
  }
});
