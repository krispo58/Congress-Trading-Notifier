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
  // TODO: Send subscription to application server

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
  navigator.serviceWorker.ready.then(function(swReg){
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
  })
}

function registerServiceWorker(serviceWorkerUrl, applicationServerPublicKey, apiEndpoint){
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

async function start(){
    const trades_div = document.getElementById("recent_trades")
    const response = await fetch("/backend/recenttrades")
    const trades = await response.json()
    console.log(trades)
    for(let i = 0; i < trades.length; i++){
        trades_div.innerHTML += "<div class=\"trade\"><span class=\"senatorName\">" + trades[i]["Senator"] + "</span> bought " + trades[i]["Range"] + " worth of " + trades[i]["Ticker"] + "</div>"
    }
}

async function getNotificationPermission(){
    let permission = await Notification.requestPermission()
    console.log(permission)
    if(permission == "granted"){
      registerServiceWorker("service_worker.js", PUBLIC_VAPID_KEY, "/backend/pushsubscriptions")
    }
    else{
      alert("You need to accept notifications so we can send you notifications. Please try again")
      getNotificationPermission()
    }
}

async function sendEmail(){
  const email = document.getElementById("emailField").value
  const response = await fetch("/backend/subscribeemail", {
    method: "POST",
    body: JSON.stringify({"email": email}),
    headers: {
      "Content-Type": "application/json"
    }
  })
  const data = await response.json()
  if (data["success"] = true){
    console.log("success")
    document.getElementsByClassName("input-container")[0].innerHTML += "<div style=\"color: green;\">Success! You can now close the page.</div>"
  }
}

// Add event listener to submit button
document.getElementById("emailSubmit").addEventListener("click", function(){
  sendEmail()
  getNotificationPermission()
})

start()