console.log("Service worker loaded.");

self.addEventListener("push", function(event){
  const trade = event.data.json();
  console.log(trade)
  self.registration.showNotification(trade.Representative + " Just bought " + trade.Range + " worth of " + trade.Ticker)
});