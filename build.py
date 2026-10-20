# Builds the standalone site (site/) from app/katya.html
import os, re, hashlib
from PIL import Image, ImageDraw, ImageFont
OUT = '.'
src = open('src/katya.html').read()

def icon(size, path, pad=0.0):
    S = 1024
    im = Image.new('RGB', (S, S), '#F4EDE9')
    d = ImageDraw.Draw(im)
    m = int(S * (0.2 + pad))
    d.rounded_rectangle([m, m - 20, S - m, S - m + 20], radius=60, fill='#B0707B')          # notebook cover
    d.rectangle([m + 70, m - 20, m + 96, S - m + 20], fill='#9A5E69')                       # spine line
    d.polygon([(S - m - 150, m - 20), (S - m - 90, m - 20), (S - m - 90, m + 120), (S - m - 120, m + 95), (S - m - 150, m + 120)], fill='#F2E1E2')  # bookmark
    f = ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf', int(380 * (1 - pad * 1.5)))
    d.text((S / 2 + 40, S / 2 + 20), 'К', font=f, fill='#FFFBF9', anchor='mm')
    im.resize((size, size), Image.LANCZOS).save(path)
icon(180, './apple-touch-icon.png')
icon(192, './icon-192.png')
icon(512, './icon-512.png')
icon(512, './icon-maskable-512.png', pad=0.08)

open('./manifest.webmanifest', 'w').write('''{
  "name": "Катин блокнот",
  "short_name": "Блокнот",
  "lang": "ru",
  "start_url": "./",
  "scope": "./",
  "display": "standalone",
  "background_color": "#F4EDE9",
  "theme_color": "#F4EDE9",
  "icons": [
    {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
    {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
    {"src": "icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}
  ]
}
''')

ver = hashlib.md5(src.encode()).hexdigest()[:8]
open('./sw.js', 'w').write('''// Offline support: the app shell is cached, pages are refreshed from the network when online
const CACHE = 'katya-%s';
const SHELL = ['./', './manifest.webmanifest', './apple-touch-icon.png', './icon-192.png', './icon-512.png'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL))); self.skipWaiting(); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))); self.clients.claim(); });
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  if (req.mode === 'navigate') {
    e.respondWith(fetch(req).then(r => { const c = r.clone(); caches.open(CACHE).then(x => x.put('./', c)); return r; }).catch(() => caches.match('./')));
    return;
  }
  e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(r => {
    if (r.ok || r.type === 'opaque') { const c = r.clone(); caches.open(CACHE).then(x => x.put(req, c)); }
    return r;
  })));
});
''' % ver)

head = '''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#F4EDE9" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#1D1718" media="(prefers-color-scheme: dark)">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Блокнот">
<meta name="format-detection" content="telephone=no">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="icon" href="icon-192.png">
<style>:root{padding-top:env(safe-area-inset-top,0px)}body{margin:0;font:14px system-ui,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style>
'''
# move <title>, meta and font links into <head>; drop the artifact-only meta
lines = src.split('\n')
headbits = [l for l in lines[:8] if l.startswith('<title') or l.startswith('<link')]
rest = '\n'.join(l for i, l in enumerate(lines) if not (i < 8 and (l.startswith('<title') or l.startswith('<link') or l.startswith('<meta name="claude'))))
sw = '''<script>if('serviceWorker' in navigator)addEventListener('load',()=>navigator.serviceWorker.register('sw.js').catch(()=>{}));</script>'''
open('./index.html', 'w').write(head + '\n'.join(headbits) + '\n</head>\n<body>\n' + rest + '\n' + sw + '\n</body>\n</html>\n')
print('built', ver)
