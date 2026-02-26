var selectionAnchorNode;
var bugReportState = {
    selectedHtml: "undefined",
    elementIdentifier: "undefined",
    setSelectedHtml: (selection) => {
        const range = selection.getRangeAt(0);
        const container = document.createElement('div');
        container.appendChild(range.cloneContents());
        this.selectedHtml = 'data:text/html;charset=utf-8,' + encodeURIComponent(container.innerHTML);
        let node = selection.anchorNode.parentNode;
        while (node && !node.id) {
            node = node.parentNode;
        }
        if (node && node.id) {
            this.elementIdentifier = node.id;
        }
    },
    getSelectedHtml: () => this.selectedHtml,
    getElementIdentifier: () => this.elementIdentifier,
    clear: () => {
        this.selectedHtml = "undefined";
        this.elementIdentifier = "undefined";
    }
};

// similar to the color parts of `initializeReadingPreferences`,
// but also updates the toggle button icons, as the DOM is already loaded when this is called.
function activateColorScheme() {
    let theme;
    let current_theme = localStorage.getItem("ar5iv_theme") || "automatic";
    let colorSchemeToggle = document.querySelector('.color-tog');
    let autoIcon = document.querySelectorAll('.automatic-tog');
    let lightIcon = document.querySelectorAll('.light-tog');
    let darkIcon = document.querySelectorAll('.dark-tog');

    if (current_theme === "automatic") {
        if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
            theme = "dark";
        } else {
            theme = "light";
        }
        colorSchemeToggle.setAttribute('aria-label', 'System preference')
        autoIcon.forEach(x => x.style.display = 'block');
        lightIcon.forEach(x => x.style.display = 'none');
        darkIcon.forEach(x => x.style.display = 'none');
    } else if (current_theme === "light") {
        colorSchemeToggle.setAttribute('aria-label', 'Light mode')
        autoIcon.forEach(x => x.style.display = 'none');
        lightIcon.forEach(x => x.style.display = 'block');
        darkIcon.forEach(x => x.style.display = 'none');
        theme = "light";
    } else {
        colorSchemeToggle.setAttribute('aria-label', 'Dark mode')
        autoIcon.forEach(x => x.style.display = 'none');
        lightIcon.forEach(x => x.style.display = 'none');
        darkIcon.forEach(x => x.style.display = 'block');
        theme = "dark";
    }

    if (theme == "dark") {
        document.documentElement.setAttribute("data-theme", "dark");
    } else {
        document.documentElement.setAttribute("data-theme", "light");
    }
}

function toggleColorScheme() {
    var current_theme = localStorage.getItem("ar5iv_theme");
    if (current_theme) {
        if (current_theme == "light") {
            localStorage.setItem("ar5iv_theme", "dark");
        } else if (current_theme == "dark") {
            localStorage.setItem("ar5iv_theme", "automatic");
        } else {
            localStorage.setItem("ar5iv_theme", "light");
        }
    } else {
        localStorage.setItem("ar5iv_theme", "light");
    }
    activateColorScheme();
}

// For toc, header and footer, we assume they are enabled by default (on large viewports).
// What is valuable is when users want to disable them, their preference can be sticky in that browser.
function toggleNavTOC() {
    const toc = document.querySelectorAll('.ltx_page_navbar>nav.ltx_TOC');
    if (toc.length > 0) {
        const style = window.getComputedStyle(toc[0]);
        let tocDisplay = (style.display === 'none') ? 'block' : 'none';
        document.documentElement.setAttribute("data-toc-display", tocDisplay);
        localStorage.setItem('arxiv_html_paper_toc_display', tocDisplay);
    }
}
function hideNavTOC() {
    const toc = document.querySelectorAll('.ltx_page_navbar>nav.ltx_TOC');
    if (toc.length > 0) {
        document.documentElement.setAttribute("data-toc-display", 'none');
        localStorage.setItem('arxiv_html_paper_toc_display', 'none');
    }
}

// in sync with our CSS @media breakpoints for ToC and header
const narrowViewport = window.matchMedia("(max-width: 1279px)").matches;
// Toggles header and footer
function toggleReadingMode() {
    const header = document.querySelectorAll('.arxiv-html-header');
    const collapseIcon = document.getElementById('disable-reading-mode-btn');
    if (header.length > 0 && collapseIcon) {
        const style = window.getComputedStyle(header[0]);
        let readingMode = (style.display === 'none') ? 'disabled' : 'enabled';
        if (narrowViewport && readingMode === 'enabled') {
            // In narrow viewports, the header logically owns the ToC UI,
            // thus a header hide should also hide the ToC.
            hideNavTOC();
        }
        document.documentElement.setAttribute("data-reading-mode", readingMode);
        localStorage.setItem('arxiv_html_paper_reading_mode', readingMode);
    }
}

function showModalForm() {
    const modal = document.getElementById('modal-form');
    if (modal) {
        modal.showModal();
    } else {
        console.error('Modal element with id "modal-form" not found.');
    }
}

function hideModalForm() {
    const modal = document.getElementById('modal-form');
    if (modal) {
        modal.close();
    } else {
        console.error('Modal element with id "modal-form" not found.');
    }
}

//submit to the backend, next step: finish
function submitBugReport(e) {
    e.preventDefault();
    const actionType = e.submitter.value || 'unknown';
    // Canonical URL
    ARXIV_ABS_PATH = 'https://arxiv.org/abs/';
    const arxivIdv = window.location.pathname.split('/')[2]; // pathname ex: '/html/2306.16433v1/2306.16433v1.html'
    const fullUrl = window.location.href;
    const canonicalURL = ARXIV_ABS_PATH + arxivIdv;
    // Report Time
    const currentTime = Date.now();

    // Browser Version
    const userAgent = navigator.userAgent;
    const browser = userAgent.match(/(firefox|edge|opr|chrome|safari)[\/]([\d.]+)/i)
    const browserName = browser[1];
    const browserVersion = browser[2];
    const browserInfo = browserName + '/' + browserVersion;

    // Relevant Selection
    let elementIdentifier = bugReportState.getElementIdentifier();
    const dataDescription = document.getElementById('description').value;
    const formTitle = document.getElementById('form_title').value;

    // add to the form data
    const issueData = {};
    issueData['uniqueId'] = window.crypto.randomUUID();
    issueData['canonicalURL'] = canonicalURL;
    issueData['conversionURL'] = window.location.origin + window.location.pathname;
    issueData['reportTime'] = currentTime;
    issueData['browserInfo'] = browserInfo;
    issueData['description'] = dataDescription;
    issueData['locationLow'] = elementIdentifier;
    //Deprecate the locationHigh field? A single point marker is sufficient for debugging purposes.
    issueData['locationHigh'] = elementIdentifier;
    issueData['selectedHtml'] = bugReportState.getSelectedHtml();
    issueData['initiationWay'] = 'header-button-to-' + actionType;

    // Send to Database for all reports.
    postToDB(issueData);

    //Send to GitHub issue tracker, if the action type is github
    if (actionType === 'github-report') {
        const githubUrl = buildGithubReportUrl(issueData, arxivIdv, formTitle, fullUrl);
        window.open(githubUrl, '_blank');
    }
    // Clean up and close the modal
    document.querySelector('#modal-form-content').reset();
    bugReportState.clear();
    hideModalForm();
}

function postToDB(issueData) {
    const DB_BACKEND_URL = 'https://services.arxiv.org/latexml/feedback';
    const queryString = new URLSearchParams(issueData).toString();
    fetch(DB_BACKEND_URL, {
        method: "POST",
        mode: "no-cors",
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: queryString, // body data type must match "Content-Type" header
    });
}

function buildGithubReportUrl(issueData, arxivIdv, formTitle, fullUrl){
    var url = `https://github.com/arXiv/html_feedback/issues/new?assignees=&labels=&projects=&title=${formTitle}&template=Feedback_about_HTML_formatted_papers.yml`;
    let compoundDescription = issueData.description;
    if (issueData.locationLow && issueData.locationLow !== "undefined") {
        compoundDescription += `\n\n---\nHTML id location: ${issueData.locationLow}\n`;
    }
    // Note: Defer adding the selection until we have a good way to view <math> tags in GitHub.
    //
    // if (issueData.selectedHtml && issueData.selectedHtml !== "undefined") {
    //     compoundDescription += `\n\n---\nSelected HTML content:\n<details><summary>Click to expand</summary>
    //     ${decodeURIComponent(issueData.selectedHtml.replace('data:text/html;charset=utf-8,', ''))}</details>\n`;
    // }
    url += `&description=${encodeURIComponent(compoundDescription)}`;
    url += `&uniqueId=${issueData.uniqueId}`;
    url += `&arxivId=${arxivIdv}`;
    url += `&browserInfo=${issueData.browserInfo}`;
    // send the full url to the github issue
    url += `&fullUrl=${fullUrl}`;
    // device type
    url += `&deviceType=${getDeviceType()}`;
    return url;
}

// test device type
function getDeviceType() {
    const userAgent = navigator.userAgent;

    if (/iPad|iPadOS/i.test(userAgent)) {
        return 'iPad';
    }
    if (/iP(hone|od)/i.test(userAgent)) {
        return 'iOS';
    }
    if (/Android/i.test(userAgent)) {
        return 'Android';
    }
    if (/BlackBerry|IEMobile|Windows Phone/i.test(userAgent)) {
        return 'Other Smartphone';
    }

    if (/Mobile|iP(hone|od)|Android|BlackBerry|IEMobile/i.test(userAgent)) {
        return 'Smartphone';
    }
    if (/tablet|tab/i.test(userAgent) && !/Mobile/i.test(userAgent)) {
        return 'Tablet';
    }
    return 'Desktop';
}

document.addEventListener("DOMContentLoaded", () => {
    const is_submission = window.location.pathname.split('/')[2] === 'submission';
    document.getElementById('modal-form-content').onsubmit = submitBugReport;
    document.getElementById('modal-form').addEventListener("close", (event) => {
        bugReportState.clear();
    });

    const content = document.querySelector('.ltx_page_content');
    // Save selections on mouse up, to forward during bug reports.
    content.addEventListener('mouseup', function() {   
        const selection = window.getSelection();
        if (!window.getSelection().isCollapsed) {
            selectionAnchorNode = selection.anchorNode;
            bugReportState.setSelectedHtml(selection);
        }
    });
});