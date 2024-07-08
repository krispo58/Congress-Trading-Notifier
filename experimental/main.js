document.addEventListener('DOMContentLoaded', function() {
    fetchRecentTrades();

    const emailForm = document.getElementById('emailForm');
    emailForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const emailInput = document.getElementById('emailInput').value;
        if (emailInput) {
            subscribeUserForNotifications(emailInput);
        }
    });
});

function fetchRecentTrades() {
    fetch('/api/recenttrades')
        .then(response => response.json())
        .then(data => {
            const tradesContainer = document.getElementById('tradesContainer');
            tradesContainer.innerHTML = ''; // Clear any existing content

            data.forEach(trade => {
                const tradeElement = document.createElement('div');
                tradeElement.className = 'trade';
                tradeElement.innerHTML = `
                    <p><strong>Senator:</strong> ${trade.Senator}</p>
                    <p><strong>Ticker:</strong> ${trade.Ticker}</p>
                    <p><strong>Transaction:</strong> ${trade.Transaction}</p>
                    <p><strong>Range:</strong> ${trade.Range}</p>
                    <p><strong>Amount:</strong> ${trade.Amount}</p>
                    <p><strong>Date:</strong> ${trade.Date}</p>
                    <p><strong>Last Modified:</strong> ${trade.last_modified}</p>
                `;
                tradesContainer.appendChild(tradeElement);
            });
        })
        .catch(error => console.error('Error fetching recent trades:', error));
}

function subscribeUserForNotifications(email) {
    if ('serviceWorker' in navigator && 'PushManager' in window) {
        navigator.serviceWorker.register('/service-worker.js')
        .then(function(swReg) {
            console.log('Service Worker is registered', swReg);

            // Request permission for notifications
            return swReg.pushManager.getSubscription()
            .then(function(subscription) {
                if (subscription === null) {
                    return swReg.pushManager.subscribe({
                        userVisibleOnly: true,
                        applicationServerKey: urlBase64ToUint8Array('BBy0JDW0WUs9SLC33fI2X7bny1AiP6swaBv6R-US2kYHyrrOs3PXSDfr9rqkPk39UVWJKJSjPXJcV6Ejw80KxAU')
                    });
                } else {
                    // We have a subscription
                    return subscription;
                }
            });
        })
        .then(function(subscription) {
            console.log('User is subscribed:', subscription);

            // Send subscription to your server to save it
            return fetch('/api/pushsubscriptions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(subscription),
            });
        })
        .then(function() {
            console.log('Subscription sent to server.');

            // Save the email to the server
            return fetch('/api/postemail', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email: email }),
            });
        })
        .then(function(response) {
            if (!response.ok) {
                throw new Error('Failed to save email');
            }
            console.log('Email saved.');
        })
        .catch(function(error) {
            console.error('Service Worker Error', error);
        });
    } else {
        console.warn('Push messaging is not supported');
    }
}

// Utility function to convert VAPID key
function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}
