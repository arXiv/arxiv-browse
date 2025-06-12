(function () {
  const container = document.getElementById("summarizepaper-output");
  const toggle = document.getElementById("summarizepaper-toggle");

  // Preload logo for faster rendering
  const logoLink = document.createElement('link');
  logoLink.rel = 'preload';
  logoLink.as = 'image';
  logoLink.href = 'https://summarizepaper.com/static/summarizer/images/logo.dd1579dd7c43.png';
  document.head.appendChild(logoLink);

  // Removed prefetch link to prevent CORB issues

  // If no container or toggle, exit early
  if (!container || !toggle) {
    console.error('SummarizePaper: Missing container or toggle');
    return;
  }

  // Simple cache to prevent unnecessary regeneration
  const contentCache = {
    arxivId: null,
    html: null
  };

  // Function to clear content
  function clearContent() {
    container.innerHTML = "";
    container.style.display = "none";
    container.setAttribute('aria-hidden', 'true');
  }

  // Function to show content
  function showContent() {
    // Get the arXiv paper ID from the URL
    const currentUrl = window.location.href;
    const arxivId = currentUrl.split('/').pop();
    const summarizepaperUrl = `https://summarizepaper.com/arxiv-id/${arxivId}/`;
    const summarizepaperLogo = 'https://summarizepaper.com/static/summarizer/images/logo.dd1579dd7c43.png';

    // Use cached content if available for the same arxiv ID
    if (contentCache.arxivId === arxivId && contentCache.html) {
      container.innerHTML = contentCache.html;
      container.style.display = "block";
      container.setAttribute('aria-hidden', 'false');
      return;
    }

    const html = `
      <div class="labs-display" role="region" aria-labelledby="summarizepaper-title">
        <div style="
          background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
          border-radius: 16px;
          box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
          padding: 24px;
          margin: 15px 0;
          border: 1px solid rgba(0, 0, 0, 0.05);
        ">
          <div style="display: flex; align-items: center; margin-bottom: 20px;">
            <div style="
              background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
              border-radius: 12px;
              padding: 12px;
              margin-right: 15px;
              display: flex;
              align-items: center;
              justify-content: center;
            ">
              <img 
                src="${summarizepaperLogo}" 
                alt="SummarizePaper Logo: AI-powered paper summarization tool" 
                style="
                  max-width: 40px;
                  max-height: 40px;
                  object-fit: contain;
                "
                onerror="this.style.display='none'"
              >
            </div>
            <h3 
              id="summarizepaper-title" 
              style="
                color: #1e293b;
                font-size: 1.5rem;
                font-weight: 600;
                margin: 0;
              "
            >
              SummarizePaper.com
            </h3>
          </div>
          
          <p style="
            color: #475569;
            font-size: 1.1rem;
            margin-bottom: 16px;
            line-height: 1.5;
          ">
            Get instant access to AI-powered insights:
          </p>
          
          <div style="display: grid; gap: 12px; margin-bottom: 20px;">
            ${[
              'Comprehensive global summary of the paper',
              'Key points and main findings',
              'Layman\'s explanation for everyone',
              'Blog post-style summary with clear explanations'
            ].map((feature, index) => `
              <div style="
                display: flex;
                align-items: center;
                padding: 12px;
                background: rgba(37, 99, 235, 0.05);
                border-radius: 12px;
                transition: transform 0.2s;
              " onmouseover="this.style.transform='translateX(5px)'" onmouseout="this.style.transform='translateX(0)'">
                <span style="
                  background: #2563eb;
                  border-radius: 8px;
                  color: white;
                  width: 24px;
                  height: 24px;
                  display: flex;
                  align-items: center;
                  justify-content: center;
                  margin-right: 12px;
                  font-weight: 600;
                ">${index + 1}</span>
                <span style="color: #1e293b;">${feature}</span>
              </div>
            `).join('')}
          </div>
          
          <div style="
            background: linear-gradient(135deg, rgba(37, 99, 235, 0.1) 0%, rgba(37, 99, 235, 0.05) 100%);
            border-radius: 12px;
            padding: 16px;
            display: flex;
            align-items: center;
            margin-top: 20px;
          ">
            <div style="
              background: #2563eb;
              border-radius: 50%;
              width: 32px;
              height: 32px;
              display: flex;
              align-items: center;
              justify-content: center;
              margin-right: 14px;
            ">
              <span style="color: white; font-size: 1.2rem;">💬</span>
            </div>
            <div>
              <p style="
                color: #1e293b;
                font-weight: 600;
                margin: 0 0 4px 0;
              ">Interactive AI Chat</p>
              <p style="
                color: #475569;
                margin: 0;
                font-size: 0.95rem;
              ">Ask questions and get instant answers about the paper</p>
            </div>
          </div>
        </div>
        
        <a 
          href="${summarizepaperUrl}" 
          target="_blank" 
          class="button is-link" 
          style="
            display: inline-block;
            padding: 12px 24px;
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            color: white;
            text-decoration: none;
            border-radius: 12px;
            font-weight: 500;
            margin-top: 16px;
            border: none;
            box-shadow: 0 4px 6px rgba(37, 99, 235, 0.1);
            transition: transform 0.2s, box-shadow 0.2s;
          "
          onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 12px rgba(37, 99, 235, 0.2)';"
          onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 6px rgba(37, 99, 235, 0.1)';"
        >
          Read summaries and chat about this paper
        </a>
      </div>
    `;

    // Cache the generated content
    contentCache.arxivId = arxivId;
    contentCache.html = window.DOMPurify.sanitize(html);

    container.innerHTML = contentCache.html;
    container.style.display = "block";
    container.setAttribute('aria-hidden', 'false');

    // Optional: Track usage (you could replace this with a more sophisticated tracking method)
    try {
      localStorage.setItem('summarizepaper_usage', 
        JSON.stringify({
          lastUsed: new Date().toISOString(),
          arxivId: arxivId
        })
      );
    } catch (error) {
      console.warn('Could not track SummarizePaper usage', error);
    }
  }

  // Check initial state and handle accordingly
  function handleToggleState() {
    const isToggleOn = toggle.classList.contains('enabled');

    if (isToggleOn) {
      showContent();
    } else {
      clearContent();
    }
  }

  // Initial state check
  handleToggleState();

  // Add event listener for toggle changes
  toggle.addEventListener('change', handleToggleState);
})();
