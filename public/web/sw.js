const CACHE='apexaudio-web-v1';
const ASSETS=['./','./index.html','./style.css','./app.js','./abp.js','./player-worklet.js','./capturer-worklet.js','./demo-source.js','./manifest.webmanifest','./icon.svg','./icon-192.png','./icon-512.png'];
self.addEventListener('install',event=>{event.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting()));});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('apexaudio-web-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',event=>{const url=new URL(event.request.url);if(event.request.method!=='GET'||url.origin!==self.location.origin||!ASSETS.some(p=>new URL(p,self.registration.scope).pathname===url.pathname))return;event.respondWith(fetch(event.request).catch(()=>caches.match(event.request,{ignoreSearch:true})));});
