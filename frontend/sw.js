// Service Worker for TNPSC Current Affairs AI Platform
// Progressive Web App functionality with offline support

const CACHE_NAME = 'tnpsc-quiz-v1.0.0';
const CACHE_URLS = [
  '/',
  '/index.html',
  '/styles.css',
  '/app.js',
  '/manifest.json'
];

// Install event - cache resources
self.addEventListener('install', event => {
  console.log('Service Worker: Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Service Worker: Caching files');
        return cache.addAll(CACHE_URLS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean old caches
self.addEventListener('activate', event => {
  console.log('Service Worker: Activating...');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('Service Worker: Removing old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event - serve cached content when offline
self.addEventListener('fetch', event => {
  // Only cache GET requests
  if (event.request.method !== 'GET') return;

  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Return cached version if found
        if (response) {
          return response;
        }

        // Fetch from network if not cached
        return fetch(event.request)
          .then(response => {
            // Check if valid response
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }

            // Cache successful responses for static assets
            const responseToCache = response.clone();
            if (event.request.url.includes('/css/') ||
                event.request.url.includes('/js/') ||
                event.request.url.includes('/img/')) {
              caches.open(CACHE_NAME)
                .then(cache => cache.put(event.request, responseToCache));
            }

            return response;
          })
          .catch(error => {
            console.log('Service Worker: Fetch failed, returning offline page');
            // Return offline fallback for navigation requests
            if (event.request.mode === 'navigate') {
              return caches.match('/index.html');
            }
            return new Response('Offline content not available', {
              status: 503,
              statusText: 'Service Unavailable'
            });
          });
      })
  );
});

// Background sync for offline quiz submissions
self.addEventListener('sync', event => {
  console.log('Service Worker: Background sync triggered');
  if (event.tag === 'quiz-sync') {
    event.waitUntil(syncQuizData());
  }
});

// Push notifications (for future updates)
self.addEventListener('push', event => {
  console.log('Service Worker: Push received');
  const data = event.data.json();

  const options = {
    body: data.body,
    icon: '/icon-192.png',
    badge: '/icon-192.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: data.id
    },
    actions: [
      {
        action: 'view',
        title: 'View Details'
      },
      {
        action: 'dismiss',
        title: 'Dismiss'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', event => {
  console.log('Service Worker: Notification clicked');
  event.notification.close();

  if (event.action === 'view') {
    event.waitUntil(
      clients.openWindow('/news')
    );
  }
});

// Message handler for client communication
self.addEventListener('message', event => {
  console.log('Service Worker: Message received', event.data);

  if (event.data.action === 'skipWaiting') {
    self.skipWaiting();
  }

  if (event.data.action === 'cacheQuiz') {
    cacheQuizData(event.data.quiz);
  }
});

// Helper functions
function syncQuizData() {
  // Sync offline quiz results when connectivity returns
  return new Promise((resolve, reject) => {
    // Implementation depends on how quiz data is stored locally
    // Could use IndexedDB or Cache API
    console.log('Service Worker: Syncing quiz data');
    resolve();
  });
}

function cacheQuizData(quiz) {
  // Cache quiz data for offline use
  const cacheKey = `quiz_${quiz.id}`;
  const data = new Response(JSON.stringify(quiz));

  caches.open(CACHE_NAME)
    .then(cache => cache.put(cacheKey, data))
    .then(() => console.log('Service Worker: Quiz cached'))
    .catch(error => console.error('Service Worker: Cache error', error));
}

// Periodic background updates (if needed)
self.addEventListener('periodicsync', event => {
  if (event.tag === 'content-refresh') {
    event.waitUntil(refreshContentCache());
  }
});

function refreshContentCache() {
  // Refresh cached news content periodically
  return fetch('/api/news?limit=10')
    .then(response => response.json())
    .then(news => {
      cacheQuizData({
        id: 'latest_news',
        data: news,
        timestamp: Date.now()
      });
    })
    .catch(error => console.log('Background refresh failed:', error));
}

// Performance monitoring
self.addEventListener('message', event => {
  if (event.data.action === 'logPerformance') {
    // Log performance metrics (could send to analytics)
    console.log('Performance:', event.data.metric, event.data.value);
  }
});