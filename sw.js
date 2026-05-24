const CACHE='books-pwa-v5-series';
const BASE='/books/';
const SHELL=[BASE,BASE+'index.html',BASE+'manifest.webmanifest',BASE+'icons/icon-192.png',BASE+'icons/icon-512.png'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{ if(e.request.method!=='GET') return; const u=new URL(e.request.url);
 if(u.pathname.endsWith('/data/books.json')){e.respondWith(fetch(e.request).then(r=>{const cp=r.clone(); caches.open(CACHE).then(c=>c.put(e.request,cp)); return r;}).catch(()=>caches.match(e.request))); return;}
 if(u.pathname.toLowerCase().endsWith('.pdf')){e.respondWith(caches.match(e.request).then(cached=>cached||fetch(e.request).then(r=>{const cp=r.clone(); caches.open(CACHE).then(c=>c.put(e.request,cp)); return r;}))); return;}
 e.respondWith(caches.match(e.request).then(cached=>cached||fetch(e.request)));
});
