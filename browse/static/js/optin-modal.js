// Support for Opt-In modal
document.addEventListener('DOMContentLoaded', function () {
  function getCookie(name) {
    const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? match[2] : null;
  }

  function showModal() {
    // User opted in
    const optedIn = getCookie('opt-in-tracking');
    const modal = document.getElementById('optin-modal');
    const title = document.getElementById('optin-title');
    const paragraphs = modal.querySelectorAll('p');
    const agreeBtn = document.getElementById('optin-agree');
    const optoutBtn = document.getElementById('optin-optout');

    if (optedIn) {
      title.textContent = "You're Already Enrolled";
      paragraphs[0].textContent = "You’ve already opted in to contribute your reading data to research. If you’d like to opt out, click below.";
      paragraphs[1].style.display = "none"; // hide privacy policy link
      agreeBtn.style.display = "none";
      optoutBtn.style.display = "inline-block";
    } else {
      title.textContent = "Help Improve arXiv";
      paragraphs[0].textContent = "arXiv is working with academic researchers to investigate ways to improve the service for our users. This requires a rich dataset to better inform the research. Users who wish to contribute to the future of arXiv may opt in to allow arXiv to use their reading data for research purposes. By clicking ‘I agree’ below, you consent to your reading data being collected, retained, and processed by arXiv and shared with researchers conducting research in the public interest. Reading data will never be shared publicly or otherwise incorporated into public systems in a personally identifiable format. Research use cases include developing privacy-preserving recommendation systems for arXiv.";
      paragraphs[1].style.display = "block";
      agreeBtn.style.display = "inline-block";
      optoutBtn.style.display = "none";
    }

    modal.classList.remove('hidden');
  }

  document.getElementById('optin-trigger').addEventListener('click', showModal);

  document.getElementById('optin-close').addEventListener('click', function() {
    document.cookie = 'opt-out-tracking=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    document.getElementById('optin-modal').classList.add('hidden');
  });

  document.getElementById('optin-agree').addEventListener('click', function() {
    const uuid = crypto.randomUUID();
    document.cookie = `opt-in-tracking=${uuid}; Path=/; Max-Age=31536000`;
    document.getElementById('optin-modal').classList.add('hidden');
  });

  document.getElementById('optin-optout').addEventListener('click', function() {
    document.cookie = 'opt-in-tracking=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    document.getElementById('optin-modal').classList.add('hidden');
  });
});


