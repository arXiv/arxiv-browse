(function() {
  const container = document.getElementById("emergentmind-output");
  if (!container) {
    console.error("Emergent Mind: container not found");
    return;
  }

  const containerAlreadyHasContent = container.innerHTML.trim().length > 0;

  // This script is invoked every time the Labs toggle is toggled, even when
  // it's toggled to disabled. So this check short-circuits the script if the
  // container already has content.
  if (containerAlreadyHasContent) {
    container.innerHTML = "";
    hideContainer();
    return;
  }

  showContainer();

  // Get the arXiv paper ID from the URL, e.g. "2103.17249"
  const params = new URLSearchParams(document.location.search);
  const arxivPaperId = params.get("override_paper_id") || window.location.pathname.split('/').reverse()[0];
  if (!arxivPaperId) {
    console.warn("Emergent Mind: No arXiv paper ID found");
    hideContainer();
    return;
  }

  const emergentMindApi = `https://www.emergentmind.com/api/v1/papers/info/${arxivPaperId}`;

  (async () => {
      try {
        let response = await fetch(emergentMindApi);
        if (!response.ok) {
          console.error(`Unable to fetch data from ${emergentMindApi}`);
          hideContainer();
          return;
        }

        let result = await response.json();
        render(result);
      } catch (error) {
        console.error("Emergent Mind fetch error:", error);
        hideContainer();
      }
  })();

  function hideContainer() {
    if (container) {
      container.setAttribute("style", "display:none");
      container.setAttribute("aria-hidden", "true");
    }
  }

  function showContainer() {
    if (container) {
      container.setAttribute("style", "display:block");
      container.setAttribute("aria-hidden", "false");
      // Add aria-live attribute if not already present
      if (!container.hasAttribute("aria-live")) {
        container.setAttribute("aria-live", "polite");
        container.setAttribute("aria-label", "Emergent Mind social media metrics");
      }
    }
  }

  // Injects the HTML into the container
  function render(result) {
    if (!container || !window.DOMPurify) {
      console.error("Emergent Mind: Missing container or DOMPurify");
      return;
    }

    container.innerHTML = window.DOMPurify.sanitize(`
      <h2 class="">
        <svg aria-hidden="true" style="display: inline-block; vertical-align: middle; margin-right: 3px;" width="30" height="30" fill="none" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 35 35">
          <title>Emergent Mind logo</title>
          <g clip-path="url(#a)"><circle cx="17.5" cy="17.5" r="17.5" fill="#FADD07"/><path d="M32.976 35H17.683c-1.02 0-1.385-1.347-.506-1.863l10.56-6.19a1 1 0 0 1 1.3.256l4.734 6.19A1 1 0 0 1 32.976 35Z" fill="#FADD07"/><path d="m10.616 9.567.516.516M17.714 7v.73M27.38 16.665h-.73M8.78 16.665h-.731M24.813 9.567l-.516.516M21.774 14.601c.42.725.64 1.549.633 2.386-.003.87-.25 1.72-.71 2.457-.154.246-.298.462-.43.66-.478.716-.805 1.206-.897 2.082h-5.31c-.09-.905-.423-1.396-.94-2.163-.105-.155-.217-.321-.337-.504a4.694 4.694 0 1 1 7.991-4.918ZM19.336 25.429h-3.243" stroke="#231E21" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/></g><defs><clipPath id="a"><path fill="#fff" d="M0 0h35v35H0z"/></clipPath></defs>
        </svg>
        <span style="vertical-align: middle;">Emergent Mind</span>
      </h2>
      ${generateHtml(result)}`, { ADD_ATTR: ['target', 'rel', 'aria-label'] });
  }

  // Generates the HTML that will be injected into the container
  function generateHtml(result) {
    let content = '';

    // Twitter/X
    if (result.has_any_socials) {
      content += `
        <h4>Social Media Discussions</h4>
        <div class="social-metrics" role="list" aria-label="Social media engagement metrics">
      `;
      if (result.twitter_likes_count > 0) {
        content += `
          <div role="listitem" aria-label="Twitter likes: ${result.twitter_likes_count}" style="text-decoration: none; margin-right: 9px; display: inline-flex; align-items: center;">
            <svg aria-hidden="true" width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
              <title>Twitter/X icon</title>
              <path d="M3.33301 3.33331L13.1105 16.6666H16.6663L6.88884 3.33331H3.33301Z" stroke="currentColor" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M3.33301 16.6666L8.97301 11.0266M11.023 8.97665L16.6663 3.33331" stroke="currentColor" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span aria-hidden="true" style="margin-left: 4px">
              ${result.twitter_likes_count}
            </span>
          </div>
        `;
      }

      // Reddit
      if (result.reddit_points_count > 0) {
        content += `
          <div role="listitem" aria-label="Reddit points: ${result.reddit_points_count}" style="text-decoration: none; margin-right: 9px; display: inline-flex; align-items: center;">
            <svg aria-hidden="true" width="23" height="23" viewBox="0 0 23 23" fill="none" xmlns="http://www.w3.org/2000/svg">
              <title>Reddit icon</title>
              <path d="M11.5007 7.66669C14.0383 7.66669 16.3192 8.45827 17.8975 9.71752C18.4375 9.52825 19.0273 9.53847 19.5604 9.74632C20.0935 9.95418 20.5346 10.3459 20.8039 10.8508C21.0732 11.3556 21.153 11.9401 21.0287 12.4986C20.9045 13.0572 20.5845 13.5528 20.1266 13.8959C20.1266 17.3363 16.2645 20.125 11.5016 20.125C6.82973 20.125 3.02515 17.4417 2.87661 14.0933L1.91828 13.8959C1.46037 13.5528 1.14036 13.0572 1.01614 12.4986C0.891913 11.9401 0.97167 11.3556 1.24099 10.8508C1.5103 10.3459 1.95139 9.95418 2.48446 9.74632C3.01754 9.53847 3.6074 9.52825 4.14736 9.71752C5.72478 8.45923 8.00561 7.66669 10.5433 7.66669H11.5007Z" stroke="currentColor" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M11.5 7.66667L12.4583 2.875L18.2083 3.83333" stroke="currentColor" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M17.25 3.83333C17.25 4.0875 17.351 4.33125 17.5307 4.51098C17.7104 4.6907 17.9542 4.79167 18.2083 4.79167C18.4625 4.79167 18.7063 4.6907 18.886 4.51098C19.0657 4.33125 19.1667 4.0875 19.1667 3.83333C19.1667 3.57917 19.0657 3.33541 18.886 3.15569C18.7063 2.97597 18.4625 2.875 18.2083 2.875C17.9542 2.875 17.7104 2.97597 17.5307 3.15569C17.351 3.33541 17.25 3.57917 17.25 3.83333Z" stroke="currentColor" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M8.62565 12.9375C8.89029 12.9375 9.10482 12.723 9.10482 12.4584C9.10482 12.1937 8.89029 11.9792 8.62565 11.9792C8.36101 11.9792 8.14648 12.1937 8.14648 12.4584C8.14648 12.723 8.36101 12.9375 8.62565 12.9375Z" fill="#8F8F80" stroke="currentColor" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M14.3757 12.9375C14.6403 12.9375 14.8548 12.723 14.8548 12.4584C14.8548 12.1937 14.6403 11.9792 14.3757 11.9792C14.111 11.9792 13.8965 12.1937 13.8965 12.4584C13.8965 12.723 14.111 12.9375 14.3757 12.9375Z" fill="#8F8F80" stroke="currentColor" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M9.58398 16.2917C10.2232 16.6108 10.8614 16.7709 11.5007 16.7709C12.1399 16.7709 12.7781 16.6108 13.4173 16.2917" stroke="currentColor" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span aria-hidden="true" style="margin-left: 4px;">
              ${result.reddit_points_count}
            </span>
          </div>
        `;
      }

      // Hacker News
      if (result.hacker_news_points_count > 0) {
        content += `
          <div role="listitem" aria-label="Hacker News points: ${result.hacker_news_points_count}" style="text-decoration: none; margin-right: 9px; display: inline-flex; align-items: center;">
            <svg aria-hidden="true" width="23" height="23" viewBox="0 0 23 23" fill="none" xmlns="http://www.w3.org/2000/svg">
              <title>Hacker News icon</title>
              <path d="M3.83398 5.75004C3.83398 5.24171 4.03592 4.7542 4.39536 4.39475C4.75481 4.03531 5.24232 3.83337 5.75065 3.83337L17.2507 3.83337C17.759 3.83337 18.2465 4.03531 18.6059 4.39475C18.9654 4.7542 19.1673 5.24171 19.1673 5.75004V17.25C19.1673 17.7584 18.9654 18.2459 18.6059 18.6053C18.2465 18.9648 17.759 19.1667 17.2507 19.1667H5.75065C5.24232 19.1667 4.75481 18.9648 4.39536 18.6053C4.03592 18.2459 3.83398 17.7584 3.83398 17.25L3.83398 5.75004Z" stroke="currentColor" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M7.66602 6.70831L11.4993 12.4583L15.3327 6.70831" stroke="currentColor" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M11.5 16.2916V12.4583" stroke="currentColor" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>

            <span aria-hidden="true" style="margin-left: 4px;">
              ${result.hacker_news_points_count}
            </span>
          </div>
        `;
      }

      // GitHub
      if (result.github_stars_count > 0) {
        content += `
          <div role="listitem" aria-label="GitHub stars: ${result.github_stars_count}" style="text-decoration: none; margin-right: 11px; display: inline-flex; align-items: center;">
            <svg aria-hidden="true" width="22" height="22" viewBox="0 0 22 22" fill="none" xmlns="http://www.w3.org/2000/svg">
              <title>GitHub icon</title>
              <path d="M8.25 17.4167C4.30833 18.7 4.30833 15.125 2.75 14.6667M13.75 19.25V16.0417C13.75 15.125 13.8417 14.7583 13.2917 14.2083C15.8583 13.9333 18.3333 12.925 18.3333 8.70835C18.3322 7.6129 17.9048 6.56088 17.1417 5.77502C17.4996 4.82349 17.4666 3.76901 17.05 2.84168C17.05 2.84168 16.0417 2.56668 13.8417 4.03335C11.9783 3.54805 10.0217 3.54805 8.15833 4.03335C5.95833 2.56668 4.95 2.84168 4.95 2.84168C4.53336 3.76901 4.50041 4.82349 4.85833 5.77502C4.09517 6.56088 3.66778 7.6129 3.66667 8.70835C3.66667 12.925 6.14167 13.9333 8.70833 14.2083C8.15833 14.7583 8.15833 15.3083 8.25 16.0417V19.25" stroke="currentColor" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span aria-hidden="true" style="margin-left: 4px;">
              ${result.github_stars_count}
            </span>
          </div>
        `;
      }

      // YouTube
      if (result.youtube_paper_mentions_count > 0) {
        content += `
          <div role="listitem" aria-label="YouTube mentions: ${result.youtube_paper_mentions_count}" style="text-decoration: none; margin-right: 9px; display: inline-flex; align-items: center;">
            <svg aria-hidden="true" width="24" height="23" viewBox="0 0 24 23" fill="none" xmlns="http://www.w3.org/2000/svg">
              <title>YouTube icon</title>
              <path d="M1.99707 7.66671C1.99707 6.65004 2.41777 5.67502 3.16661 4.95613C3.91545 4.23724 4.9311 3.83337 5.99013 3.83337H17.9693C19.0283 3.83337 20.044 4.23724 20.7928 4.95613C21.5417 5.67502 21.9623 6.65004 21.9623 7.66671V15.3334C21.9623 16.35 21.5417 17.3251 20.7928 18.0439C20.044 18.7628 19.0283 19.1667 17.9693 19.1667H5.99013C4.9311 19.1667 3.91545 18.7628 3.16661 18.0439C2.41777 17.3251 1.99707 16.35 1.99707 15.3334V7.66671Z" stroke="currentColor" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M9.98242 8.625L14.9737 11.5L9.98242 14.375V8.625Z" stroke="currentColor" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>

            <span aria-hidden="true" style="margin-left: 4px;">
              ${result.youtube_paper_mentions_count}
            </span>
          </div>
        `;
      }

      content += `
        </div>
        <p><a href="https://www.emergentmind.com/papers/${arxivPaperId}" target="_blank" aria-label="View social media discussions about this paper (opens in new tab)">View social media discussions about this paper</a> or <a href="https://www.emergentmind.com/papers" target="_blank" aria-label="Explore trending papers (opens in new tab)">explore trending papers</a>.</p>
      `;
    } else {
      content += `<p>No social media activity found for this paper yet.</p>`;
      content += `<p><a href="https://www.emergentmind.com/papers" target="_blank" aria-label="Explore trending papers (opens in new tab)">Explore trending papers</a>.</p>`;
    }

    return content;
  }
})();
