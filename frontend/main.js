'use strict';

const PUBLIC_VAPID_KEY = "BBy0JDW0WUs9SLC33fI2X7bny1AiP6swaBv6R-US2kYHyrrOs3PXSDfr9rqkPk39UVWJKJSjPXJcV6Ejw80KxAU";

function urlB64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/\-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray; 
}

function updateSubscriptionOnServer(subscription, apiEndpoint) {
  return fetch(apiEndpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      subscription_json: JSON.stringify(subscription)
    })
  });
}

function subscribeUser(swRegistration, applicationServerPublicKey, apiEndpoint) {
  const applicationServerKey = urlB64ToUint8Array(applicationServerPublicKey);
  navigator.serviceWorker.ready.then(function(swReg) {
    swRegistration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: applicationServerKey
    })
    .then(function(subscription) {
      console.log('User is subscribed.');
      return updateSubscriptionOnServer(subscription, apiEndpoint);
    })
    .then(function(response) {
      if (!response.ok) {
        throw new Error('Bad status code from server.');
      }
      return response.json();
    });
  });
}

function registerServiceWorker(serviceWorkerUrl, applicationServerPublicKey, apiEndpoint) {
  let swRegistration = null;
  if ('serviceWorker' in navigator && 'PushManager' in window) {
    console.log('Service Worker and Push is supported');

    navigator.serviceWorker.register(serviceWorkerUrl)
    .then(function(swReg) {
      console.log('Service Worker is registered', swReg);
      subscribeUser(swReg, applicationServerPublicKey, apiEndpoint);

      swRegistration = swReg;
    });
  } else {
    console.warn('Push messaging is not supported');
  } 
  return swRegistration;
}

async function start() {
    const trades_div = document.getElementById("recent_trades");
    const response = await fetch("/backend/recenttrades");
    const trades = await response.json();
    console.log(trades);
    for (let i = 0; i < trades.length && i < 5; i++) {
        const trade = trades[i];
        const tradeElement = document.createElement("div");
        tradeElement.className = "trade";
        tradeElement.innerHTML = `
            <div class="senatorName">${trade.Representative}</div>
            <div class="tradeDetail">${trade.Transaction} of Ticker ${trade.Ticker} worth ${trade.Range}</div>
            <div class="tradeDate">Transaction Date: ${trade.TransactionDate} Report Date: ${trade.ReportDate}</div>
        `;
        trades_div.appendChild(tradeElement);
    }
}

async function getNotificationPermission() {
    let permission = await Notification.requestPermission();
    console.log(permission);
    if (permission == "granted") {
        registerServiceWorker("service_worker.js", PUBLIC_VAPID_KEY, "/backend/pushsubscriptions");
    } else {
        alert("You need to accept notifications so we can send you notifications.");
        getNotificationPermission();
    }
}

async function sendEmail() {
    const email = document.getElementById("emailField").value;
    if (email.length < 5) {
        alert("Please enter your email");
        return;
    }
    const response = await fetch("/backend/subscribeemail", {
        method: "POST",
        body: JSON.stringify({"email": email}),
        headers: {
            "Content-Type": "application/json"
        }
    });
    const data = await response.json();
    if (data.success) {
        console.log("success");
        const successMessage = document.getElementById("successMessage");
        successMessage.innerHTML = "Success! You can now close the page.";
    }
}

// Add event listener to submit button
document.getElementById("emailSubmit").addEventListener("click", function() {
    sendEmail();
    getNotificationPermission();
});

start();
