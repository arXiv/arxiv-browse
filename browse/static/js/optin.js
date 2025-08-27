// Support Opt-In banner and associated buttons
function checkOptInParticipation() {
  const cookies = document.cookie;
  const optedIn = cookies.includes('opt-in-tracking');
  const optedOut = cookies.includes('opt-out-tracking');
  const userDismissedBanner = cookies.includes('seenBanner_opt-in');
  const optInDismissed = cookies.includes('opt-in-dismissed');

  const message = document.getElementById('opt-in-message');
  const optInBtn = document.getElementById('opt-in-registration');
  const enrolledMsg = document.getElementById('opt-in-enrolled');

  if (userDismissedBanner) {
    document.cookie = 'opt-in-dismissed=true; Path=/; Max-Age=2592000';
    document.cookie = 'seenBanner_opt-in=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
  }

  if (optedIn) {
    if (message) {
      message.innerHTML = "Thank you for agreeing to participate in research by allowing researchers to collect anonymized usage data. Your preferences have been saved."
        + "<p>DEBUG: USER OPTED IN: THIS STATE WILL APPEAR AS SEPARATE BUTTON TBD</p>";
    }
  } else if (optedOut) {
    if (message) {
      message.innerHTML = "Thank you for your response. Your preference not to participate has been saved. Click 'I agree' below if you later decide to participate."
        + "<p>DEBUG: USER OPTED OUT: THIS STATE WILL APPEAR AS SEPARATE BUTTON TBD</p>";
    }
  } else if (optInDismissed && !optedIn && !optedOut) {
    if (message) {
      message.innerHTML = "You've previously dismissed this banner. You can still opt in by clicking 'I Agree' below."
        + "<p>DEBUG: USER DISMISSED BANNER: THIS STATE WILL APPEAR AS SEPARATE BUTTON TBD!</p>";
    }
  }

  if (optedIn) {
    optInBtn.style.display = 'none';
    enrolledMsg.style.display = 'inline';
  } else {
    optInBtn.style.display = 'inline';
    enrolledMsg.style.display = 'none';
  }
}

document.addEventListener('DOMContentLoaded', function () {
  checkOptInParticipation();

  document.getElementById('opt-in-registration').addEventListener('click', function (event) {
    event.preventDefault();
    const uuid = crypto.randomUUID();
    document.cookie = `opt-in-tracking=${uuid}; Path=/; Max-Age=31536000`;
    document.cookie = 'opt-out-tracking=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    document.cookie = 'opt-in-dismissed=true; Path=/; Max-Age=2592000';
    checkOptInParticipation();
  });

  document.getElementById('opt-out').addEventListener('click', function (event) {
    event.preventDefault();
    document.cookie = 'opt-in-tracking=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    document.cookie = 'opt-out-tracking=true; Path=/; Max-Age=2592000';
    document.cookie = 'opt-in-dismissed=true; Path=/; Max-Age=2592000';
    checkOptInParticipation();
  });
});

