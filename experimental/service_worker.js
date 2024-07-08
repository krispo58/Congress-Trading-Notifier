self.addEventListener('push', function(event) {
    const data = event.data.json();
    self.registration.showNotification('New Trades Alert', {
        body: `New trades detected. Check the recent trades section for details.`,
        icon: '/DollarFinanceLogo.png'
    });
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    event.waitUntil(
        clients.openWindow('/')
    );
});