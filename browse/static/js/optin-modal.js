// Support for Opt-In modal
document.addEventListener('DOMContentLoaded', function () {
  const trigger = document.getElementById('optin-trigger');
  const modal = document.getElementById('optin-modal');
  const agreeBtn = document.getElementById('optin-agree');
  const optOutBtn = document.getElementById('optin-optout');
  const closeBtn = document.getElementById('optin-close');

  const modalContent = {
    optedIn: {
      title: "You're Already Enrolled",
      message: "You’ve already opted in...",
      showAgree: false,
      showOptOut: true,
      showPrivacy: false
    },
    notOptedIn: {
      title: "Help Improve arXiv",
      message: "arXiv is working with academic researchers...",
      showAgree: true,
      showOptOut: false,
      showPrivacy: true
    }
  };

  function getCookie(name) {
    const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? match[2] : null;
  }

  function showModal() {
    // User opted in
    const optedIn = getCookie('opt-in-tracking');
    const title = document.getElementById('optin-title');
    const paragraphs = modal.querySelectorAll('p');

    // Moved state to const above
    const state = optedIn ? modalContent.optedIn : modalContent.notOptedIn;
    title.textContent = state.title;
    paragraphs[0].textContent = state.message;
    paragraphs[1].style.display = state.showPrivacy ? "block" : "none";
    agreeBtn.style.display = state.showAgree ? "inline-block" : "none";
    optOutBtn.style.display = state.showOptOut ? "inline-block" : "none";

    modal.classList.remove('hidden');
  }


  if (trigger) {
    trigger.addEventListener('click', showModal);
  }
  if (closeBtn) {
      closeBtn.addEventListener('click', function() {
        document.cookie = 'opt-out-tracking=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
        if (modal) modal.classList.add('hidden');
      });
  }
  if (agreeBtn) {
      agreeBtn.addEventListener('click', function() {
        const uuid = crypto.randomUUID();
        document.cookie = `opt-in-tracking=${uuid}; Path=/; Max-Age=31536000`;
        if (modal) modal.classList.add('hidden');
      });
  }
  if (optOutBtn) {
      optOutBtn.addEventListener('click', function() {
        document.cookie = 'opt-in-tracking=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
        alert("You have opted out.");
        if (modal) modal.classList.add('hidden');
      });
  }
});


