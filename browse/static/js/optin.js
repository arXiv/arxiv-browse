// Support Opt-In banner and associated buttons
function checkOptInParticipation() {
  const banner = document.querySelector('.slider-wrapper.bps-banner.forum:not(.blue)');
  const cookies = document.cookie;
  // User opted in
  const optedIn = cookies.includes('opt-in-tracking');
  // User opted out (this is different than dismissed banner)
  const optedOut = cookies.includes('opt-out-tracking');
  // We want to know whether the user made an opt-in choice or simply
  // dismissed the banner. Remember, selection cookies may expire at
  // different times. This allows us to make informed decisions for each case.
  const userDismissedBanner = cookies.includes('seenBanner_opt-in');
  // We have control over our own opt-in dismissed cookie. This may
  // be set differently depending on whether the user opted in, opted out,
  // or simply dismissed the banner (x).
  const optInDismissed = cookies.includes('opt-in-dismissed');

  // Hide the banner after user makes a choice
  if ((optedIn || optedOut || optInDismissed) && banner) {
    console.log("Hiding banner due to user choice (checkOptIn)");
    banner.style.display = 'none';
    banner.style.setProperty('display', 'none', 'important');
  }

  const message = document.getElementById('opt-in-message');
  const optInBtn = document.getElementById('opt-in-registration');
  const enrolledMsg = document.getElementById('opt-in-enrolled');

  if (userDismissedBanner) {
    // Refresh and expire after users is idle for a period of time.
    document.cookie = 'opt-in-dismissed=true; Path=/; Max-Age=2592000';
  }

  // This was used to provide status information - this may end up informing
  // the opt-in status button.
  if (optedIn) {
    if (message) {
      message.innerHTML = "Thank you for agreeing to participate in research by allowing researchers to collect anonymized usage data. Your preferences have been saved."
        + "<p>USER OPTED IN: THIS STATE WILL APPEAR AS SEPARATE BUTTON TBD</p>";
    }
    updateStatusButton('optedIn');
  } else if (optedOut) {
    if (message) {
      message.innerHTML = "Thank you for your response. Your preference not to participate has been saved. Click 'I agree' below if you later decide to participate."
        + "<p>USER OPTED OUT: THIS STATE WILL APPEAR AS SEPARATE BUTTON TBD</p>";
    }
    updateStatusButton('optedOut');
  } else if (optInDismissed && !optedIn && !optedOut) {
    if (message) {
      message.innerHTML = "You've previously dismissed this banner. You can still opt in by clicking 'I Agree' below."
        + "<p>USER DISMISSED BANNER: THIS STATE WILL APPEAR AS SEPARATE BUTTON TBD!</p>";
    }
    updateStatusButton('dismissed');
  }

  // Control state of banner
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

    const banner = document.querySelector('.slider-wrapper.bps-banner.forum:not(.blue');
    if (banner) {
        console.log("Hiding banner due to user choice (Opt In event)");
        banner.style.display = 'none'
        // Disable banner on refresh after user has made selection
        document.cookie = 'seenBanner_opt-in=; Path=/; Max-Age=2592000';
    }

    checkOptInParticipation();
  });

  document.getElementById('opt-out').addEventListener('click', function (event) {
    event.preventDefault();
    document.cookie = 'opt-in-tracking=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    document.cookie = 'opt-out-tracking=true; Path=/; Max-Age=2592000';
    document.cookie = 'opt-in-dismissed=true; Path=/; Max-Age=2592000';

    const banner = document.querySelector('.slider-wrapper.bps-banner.forum:not(.blue)');
    if (banner) {
        console.log("Hiding banner due to user choice (Opt Out event)");
        banner.style.display = 'none';
        // Disable banner on refresh after user has made selection
        document.cookie = 'seenBanner_opt-in=; Path=/; Max-Age=2592000';
    }

    checkOptInParticipation();
  });
});

// Update residual 'status' indicator after initial choice has ben
// made and banner is hidden. The status button does not appear when
// banner is displayed.
function updateStatusButton(state) {
  const container = document.getElementById('opt-in-status-button-container');
  const button = document.getElementById('opt-in-status-button');

  container.style.display = 'block';

  if (state === 'optedIn') {
    button.textContent = 'Opt Out';
    button.title = 'You are currently opted in. Click to opt out.';
    button.onclick = function () {
      document.cookie = 'opt-in-tracking=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
      document.cookie = 'opt-out-tracking=true; Path=/; Max-Age=2592000';
      console.log("Hiding banner due to user choice (Opt Out button)");
      checkOptInParticipation();
    };
  } else if (state === 'optedOut') {
    button.textContent = 'Opt In';
    button.title = 'You are currently opted out. Click to opt in.';
    button.onclick = function () {
      const uuid = crypto.randomUUID();
      document.cookie = `opt-in-tracking=${uuid}; Path=/; Max-Age=31536000`;
      document.cookie = 'opt-out-tracking=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
      console.log("Hiding banner due to user choice (Opt In button)");
      checkOptInParticipation();
    };
  } else if (state === 'dismissed') {
    button.textContent = 'Opt In';
    button.title = 'You previously dismissed the banner. Click to opt in.';
    button.onclick = function () {
      const uuid = crypto.randomUUID();
      document.cookie = `opt-in-tracking=${uuid}; Path=/; Max-Age=31536000`;
      document.cookie = 'opt-out-tracking=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
      checkOptInParticipation();
    };
  }
}
