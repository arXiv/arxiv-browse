// Labs integration for displaying links to enabla

(function () {
    const container = document.getElementById("enabla-output")
    const containerAlreadyHasContent = container.innerHTML.trim().length > 0
    const brandIcon = `<svg width="33" height="17" style="flex-shrink: 0" viewBox="0 0 33 17" fill="none" xmlns="http://www.w3.org/2000/svg">
<path fill-rule="evenodd" clip-rule="evenodd" d="M0 0L6.93701 17H8.16399L15.1183 0H0Z" fill="url(#paint0_linear_138_599)"/>
<path d="M23.4686 1.81663H30.8739C31.2763 1.81663 31.6623 1.65675 31.9469 1.37217C32.2315 1.08759 32.3913 0.701617 32.3913 0.299158V0H19.1633V0.997195C19.1637 1.12039 19.1919 1.24191 19.2457 1.35272C19.2973 1.46423 19.3645 1.56787 19.4451 1.66055L25.1768 8.51951L19.5882 15.1747C19.4677 15.3047 19.3656 15.4506 19.2847 15.6083C19.2052 15.7686 19.1637 15.9452 19.1633 16.1242V16.9913H32.3913V16.7052C32.3913 16.3027 32.2315 15.9167 31.9469 15.6322C31.6623 15.3476 31.2763 15.1877 30.8739 15.1877H23.2085C22.9787 15.1877 22.7359 15.1877 22.4844 15.2137C22.233 15.2397 21.9598 15.2571 21.665 15.2961C21.8411 15.1827 22.0065 15.0535 22.1592 14.9102C22.3182 14.7541 22.5133 14.5417 22.7446 14.2729L26.5989 9.5037C26.7988 9.29891 26.9642 9.0632 27.0889 8.80566C27.1554 8.63866 27.1907 8.46082 27.1929 8.28105C27.1777 8.13113 27.1382 7.98469 27.0759 7.84749C26.9462 7.60538 26.7859 7.38097 26.5989 7.1798L23.1738 2.90487C22.9592 2.65323 22.7227 2.42109 22.4671 2.21117C22.195 1.99839 21.9049 1.80979 21.6 1.64754C21.8991 1.7039 22.1939 1.74726 22.4671 1.77327C22.7402 1.79929 23.1044 1.81663 23.4686 1.81663Z" fill="#130E20"/>
<defs>
<linearGradient id="paint0_linear_138_599" x1="5.87478" y1="-2.49299" x2="14.2295" y2="15.3178" gradientUnits="userSpaceOnUse">
<stop stop-color="#FFCE00"/>
<stop offset="0.38" stop-color="#FF3383"/>
<stop offset="0.67" stop-color="#851BFF"/>
<stop offset="1" stop-color="#851BFF"/>
</linearGradient>
</defs>
</svg>
`
    const commentsIcon = `<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
<path fill-rule="evenodd" clip-rule="evenodd" d="M10 9.5H10.6213L11.0607 9.93934L12.5706 11.4493C12.6031 11.4817 12.6471 11.5 12.6931 11.5C12.794 11.5 12.8736 11.4141 12.8658 11.3135L12.754 9.8597L12.6918 9.05124L13.3342 8.55639C14.0367 8.01515 14.5 7.21125 14.5 6C14.5 4.78641 14.0349 3.98143 13.3294 3.43993C12.5757 2.86151 11.4275 2.5 10 2.5C8.57248 2.5 7.42429 2.86151 6.67063 3.43993C5.96508 3.98143 5.5 4.78641 5.5 6C5.5 7.21359 5.96508 8.01856 6.67063 8.56007C7.42429 9.13849 8.57248 9.5 10 9.5ZM10.5199 11.5199L11.5099 12.5099C11.8237 12.8237 12.2493 13 12.6931 13C13.6678 13 14.4362 12.1702 14.3614 11.1984L14.2496 9.74466C15.3313 8.91133 16 7.66311 16 6C16 2.66667 13.3137 1 10 1C7.8732 1 6.00485 1.68655 4.93929 3.05966C2.13151 3.38398 1.52588e-05 5.03076 1.52588e-05 8C1.52588e-05 9.66311 0.668724 10.9113 1.75043 11.7447L1.6386 13.1984C1.56384 14.1702 2.33224 15 3.30693 15C3.7507 15 4.1763 14.8237 4.4901 14.5099L6.00002 13C7.80291 13 9.42008 12.5066 10.5199 11.5199ZM4.14306 4.73587C4.0494 5.1266 4 5.54797 4 6C4 8.9053 6.04069 10.5445 8.75885 10.9176C8.0421 11.2835 7.10469 11.5 6.00002 11.5H5.37869L4.93935 11.9393L3.42944 13.4493C3.39695 13.4817 3.35288 13.5 3.30693 13.5C3.206 13.5 3.12644 13.4141 3.13418 13.3135L3.24601 11.8597L3.3082 11.0512L2.66586 10.5564C1.96331 10.0152 1.50002 9.21125 1.50002 8C1.50002 6.78641 1.9651 5.98143 2.67064 5.43993C3.06096 5.14037 3.5571 4.89898 4.14306 4.73587Z" fill="black" fill-opacity="0.85"/>
</svg>
`

    // This script is invoked every time the Labs toggle is toggled, even when
    // it's toggled to disabled. So this check short-circuits the script if the
    // container already has content.
    if (containerAlreadyHasContent) {
        container.innerHTML = ""
        container.style.display = "none";
        return
    } else {
        container.style.display = "block";
    }

    // Get the arXiv paper ID from the URL, e.g. "2103.17249"
    // (this can be overridden for testing by passing an override_paper_id query parameter in the URL)
    const params = new URLSearchParams(document.location.search)
    const arxivPaperId = params.get("override_paper_id") || window.location.pathname.split('/').reverse()[0]
    if (!arxivPaperId) return

    const baseUrl = "https://enabla.com";
    const submitUrl = `${baseUrl}/submit`;
    const publicationsUrl = `${baseUrl}/publications`;
    const enablaApiBase = `${baseUrl}/api/v1`;
    const enablaLecturesApiUrl = `${enablaApiBase}/arxiv/lectures/list?arxivId=${arxivPaperId}`;

    // Fetch linked lectures
    (async () => {
        try {
            const response = await fetch(enablaLecturesApiUrl);
            if (!response.ok) {
                console.error(`Unable to fetch Enabla data from ${enablaLecturesApiUrl}`)
                render(null);
                return;
            }

            /*
             * {
             *   "lectureUrls": string[],
             *   "courseUrl": string | null,
             *   "searchUrl": string | null,
             *   "hasVideo": boolean,
             *   "hasText": boolean,
             *   "thumbnail": string | null,
             *   "activity": {
             *     "commentsCount": number,
             *     "reviewsCount": number
             *    }
             *  }
             */
            const lectures = await response.json();

            if (!lectures.lectureUrls || lectures.lectureUrls.length === 0) {
                render(null);
                return;
            }
            render(lectures);
        } catch (error) {
            console.error(`Unable to handle the Enabla data from ${enablaLecturesApiUrl}: `, error)
            render(null);
        }
    })()

    // Generate HTML, sanitize it to prevent XSS, and inject into the DOM
    function render(lectures) {
        container.innerHTML = window.DOMPurify.sanitize(`
           ${summary(lectures)} 
       `, {ADD_ATTR: ['target']})
    }

    function preprintUrl(lectures) {
        if (lectures.searchUrl){
            return lectures.searchUrl
        } else if (lectures.courseUrl) {
            return lectures.courseUrl
        } else if (lectures.lectureUrls.length === 1) {
            return lectures.lectureUrls[0]
        } else {
            return lectures.lectureUrls[0]
        }
    }

    function summary(lectures) {
        const header = `<h3 class="enabla-header">${brandIcon} Enabla: video recordings, HTML papers, and open discussions</h3>`
        let content = ""
        // == is on purpose to catch undefined case
        if (lectures == null) {
            content = `<p>No Enabla publication found for this preprint yet. 
           <a href="${submitUrl}" target="_blank">Upload its LaTeX sources or a related video</a> 
           yourself and start open discussions of this or 
           <a href="${publicationsUrl}" target="_blank">other works</a> 
           to benefit the arXiv community.
           </p>`
        } else {
          const preprintChunk = `<a href="${preprintUrl(lectures)}" target="_blank">this preprint on Enabla</a>`
          const commentsCount = lectures.activity.commentsCount || 0
          if (lectures.hasVideo && lectures.hasText) {
            if (commentsCount > 0) {
              content = `<p>
Explore the related video and${comments(commentsCount)}to ${preprintChunk}. Read the preprint in HTML and join the conversation.
${thumbnail(lectures.thumbnail)}
</p>`
            } else {
              content = `<p>
Watch the related video, read the HTML version, and discuss ${preprintChunk} to delve deeper and connect with peers.
${thumbnail(lectures.thumbnail)}
</p>`
            }
          } else if (lectures.hasText) {
            const video = `If you have a related video, feel free to <a href="${submitUrl}" target="_blank">upload it</a> and enhance the learning process.`
            if (commentsCount > 0) {
              content = `<p>There ${commentsCount > 1 ? "are" : "is"}${comments(commentsCount)}to ${preprintChunk}; join the discussion(s) or start new ones. ${video}</p>`
            } else {
              content = `<p>Ask your questions or discuss ${preprintChunk}. ${video}</p>`
            }
          } else if (lectures.hasVideo) {
            const commentsChunk = commentsCount > 0 ? `${comments(commentsCount)}to` : ` discuss`
            content = `<p>
Explore the related video and${commentsChunk} ${preprintChunk}. If you have the LaTeX sources, feel free to <a href="${submitUrl}" target="_blank">upload them</a> and enhance the learning process.
${thumbnail(lectures.thumbnail)}
</p>`
          }
        }
        return `<div class="enabla-content">
${header}
${content}
</div>`
    }

    function comments(count) {
        return `<span class="enabla-comments">${commentsIcon} ${count} open comment${count > 1 ? "s" : ""}</span>`
    }

    function thumbnail(src) {
        return `<img src="${src}" alt="" width="410" class="enabla-thumbnail">`
    }
})();
