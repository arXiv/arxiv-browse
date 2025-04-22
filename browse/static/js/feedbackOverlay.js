var selectionAnchorNode;
var bugReportState = {
    initiateWay: null,
    setInitiateWay: (value) => this.initiateWay = value,
    getInitiateWay: () => this.initiateWay,
    selectedHtml: null,
    elementIdentifier: null,
    setSelectedHtmlSRB: (value) => {
        this.selectedHtml = "data:text/html;charset=utf-8," + encodeURIComponent(value.innerHTML);
        this.elementIdentifier = value.id;
    },
    setSelectedHtmlSmallButton: (value) => {
        const range = value.getRangeAt(0);
        const container = document.createElement('div');
        container.appendChild(range.cloneContents());
        this.selectedHtml = 'data:text/html;charset=utf-8,' + encodeURIComponent(container.innerHTML);
    },
    getSelectedHtml: () => this.selectedHtml,
    getElementIdentifier: () => this.elementIdentifier,
    clear: () => {
        this.selectedHtml = "undefined";
        this.elementIdentifier = "undefined";
        this.initiateWay = "undefined";
    }
};

function detectColorScheme() {
    let theme = "light";
    let current_theme = localStorage.getItem("ar5iv_theme");
    let colorSchemeToggle = document.querySelector('.ar5iv-toggle-color-scheme');
    let autoIcon = document.querySelectorAll('#automatic-tog');
    let lightIcon = document.querySelectorAll('#light-tog');
    let darkIcon = document.querySelectorAll('#dark-tog');

    if (current_theme === "automatic") {
        if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
            theme = "dark";
        } else {
            theme = "light";
        }
        colorSchemeToggle.setAttribute('aria-label', 'System preference')
        autoIcon.forEach(x => x.hidden = false);
        lightIcon.forEach(x => x.hidden = true);
        darkIcon.forEach(x => x.hidden = true);
    } else if (current_theme === "light") {
        colorSchemeToggle.setAttribute('aria-label', 'Light mode')
        lightIcon.forEach(x => x.hidden = false);
        autoIcon.forEach(x => x.hidden = true);
        darkIcon.forEach(x => x.hidden = true);
        theme = "light";
    } else {
        colorSchemeToggle.setAttribute('aria-label', 'Dark mode')
        darkIcon.forEach(x => x.hidden = false);
        autoIcon.forEach(x => x.hidden = true);
        lightIcon.forEach(x => x.hidden = true);
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
        localStorage.setItem("ar5iv_theme", "automatic");
    }
    detectColorScheme();
}

function addBugReportForm() {
    const is_submission = window.location.pathname.split('/')[2] === 'submission';
    const theme = document.documentElement.getAttribute("data-theme");
    
    // Create the button element(the right bottom button)
    const button = document.createElement("button");
    button.setAttribute("type", "button");
    button.setAttribute("class", "btn btn-primary hover-rp-button");
    button.setAttribute("id", "openForm");
    button.appendChild(document.createTextNode("Report Issue"));

    // Create the modal container element
    const modal = document.createElement("div");
    modal.setAttribute("class", "modal");
    modal.setAttribute("id", "myForm");
    modal.setAttribute("role", "dialog");
    modal.setAttribute("aria-labelledby", "modal-title");

    // Create the modal dialog element
    const modalDialog = document.createElement("div");
    modalDialog.setAttribute("class", "modal-dialog");

    // Create the form element
    const form = document.createElement("form");
    form.setAttribute("class", "modal-content");
    form.setAttribute("id", "myFormContent");
    form.setAttribute("enctype", "multipart/form-data");

    // Create the modal header
    const modalHeader = document.createElement("div");
    modalHeader.setAttribute("class", "modal-header");
    modalHeader.setAttribute("id", "modal-header");

    // Create the modal title
    const modalTitle = document.createElement("h5");
    modalTitle.setAttribute("class", "modal-title");
    modalTitle.appendChild(document.createTextNode("Report Github Issue"));

    // Create the close button for the modal
    const closeButton = document.createElement("button");
    closeButton.setAttribute("type", "button");
    closeButton.setAttribute("class", "btn-close");
    closeButton.setAttribute("data-bs-dismiss", "modal");
    closeButton.setAttribute("aria-label", "Close");

    // Append the title and close button to the modal header
    modalHeader.appendChild(modalTitle);
    modalHeader.appendChild(closeButton);

    console.log("Test theme:" + theme);
    if (theme === 'dark') {
        console.log("Dark Enter!")
        modalHeader.setAttribute('data-bs-theme', "dark");
    }

    // Create the modal body
    const modalBody = document.createElement("div");
    modalBody.setAttribute("class", "modal-body");

    // Update: Add warning label. Need add format in style.css.
    const warningLabel = document.createElement("div");
    warningLabel.id = "warningLabel";
    warningLabel.setAttribute('class', 'form-text');
    warningLabel.textContent = "Warning: Issue reports will be publicly available on Github, including highlighted text. You may want to omit screenshots if you are reporting on a paper still in submission.";

    // Create the description input field
    const selectedTextDescriptionLabel = document.createElement("label");
    selectedTextDescriptionLabel.setAttribute("for", "description");
    //descriptionLabel.setAttribute("class", "form-label");
    selectedTextDescriptionLabel.setAttribute("id", "selectedTextModalDescription");
    selectedTextDescriptionLabel.appendChild(document.createTextNode("Content selection saved. Describe the issue below:"));


    // Title.
    const titleLabel = document.createElement("label");
    titleLabel.setAttribute("for", "form_title");
    titleLabel.setAttribute("id", "modalTitle");
    titleLabel.appendChild(document.createTextNode("Title:"));

    const titleInput = document.createElement("input");
    titleInput.setAttribute("class", "form-control");
    titleInput.setAttribute("id", "form_title");
    titleInput.setAttribute("name", "form_title");
    titleInput.setAttribute("required", "required");
    titleInput.setAttribute("placeholder", "Enter title");

    // Description.
    const NomralDescriptionLabel = document.createElement("label");
    NomralDescriptionLabel.setAttribute("for", "description");
    //descriptionLabel.setAttribute("class", "form-label");
    NomralDescriptionLabel.setAttribute("id", "nomralModalDescription");
    NomralDescriptionLabel.appendChild(document.createTextNode("Description:"));


    const descriptionTextarea = document.createElement("textarea");
    descriptionTextarea.setAttribute("class", "form-control");
    descriptionTextarea.setAttribute("id", "description");
    descriptionTextarea.setAttribute("name", "description");
    descriptionTextarea.setAttribute("required", "required");
    descriptionTextarea.setAttribute("style", "height: 80px;");
    // Update: Change to 500 for next two lines.
    descriptionTextarea.setAttribute("maxlength", "500"); // Set the maximum length to 200 characters
    descriptionTextarea.setAttribute("placeholder", "500 characters maximum");

    // Create the modal footer
    const modalFooter = document.createElement("div");
    modalFooter.setAttribute("class", "modal-footer d-flex justify-content-end");

    // Create the submit button
    const submitButton = document.createElement("button");
    submitButton.setAttribute("type", "submit");
    submitButton.setAttribute("class", "btn btn-primary");
    submitButton.setAttribute("id", "modal-submit"); // This id will use in submitBugReport function !!!
    // submitButton.setAttribute("style", "background-color: #b31b1b;", "border-color: #690604;");
    submitButton.appendChild(document.createTextNode("Submit in Github"));

    // Update: ScreenReader Submit Buttons. Needed for Submit without Github Function.
    const srSubmit = document.createElement("button");
    srSubmit.setAttribute("type", "submit");
    srSubmit.setAttribute("class", "sr-only button");
    srSubmit.setAttribute("id", "modal-submit-sr");
    srSubmit.appendChild(document.createTextNode("Submit without Github"));

    // Create a container div for the buttons
    const buttonsContainer = document.createElement("div");
    buttonsContainer.setAttribute("class", "d-flex justify-content-between");

    // Append the elements to their respective parents
    // Update: Add warning label (next line)
    if (is_submission) {
        modalBody.appendChild(warningLabel);
    }
    modalBody.appendChild(titleLabel);
    modalBody.appendChild(titleInput);
    modalBody.appendChild(selectedTextDescriptionLabel);
    modalBody.appendChild(NomralDescriptionLabel);
    modalBody.appendChild(descriptionTextarea);

    // Update: Add buttonsContainer (next line)
    modalFooter.appendChild(srSubmit);
    modalFooter.appendChild(submitButton);

    form.appendChild(modalHeader);
    form.appendChild(modalBody);
    form.appendChild(modalFooter);

    modalDialog.appendChild(form);

    modal.appendChild(modalDialog);

    document.body.appendChild(button);
    document.body.appendChild(modal);

    button.onclick = (e) => {
        currentAnchorNode = null;
        showModal(modal, 'button');
        bugReportState.setInitiateWay("Fixedbutton");
    }
    closeButton.onclick = (e) => {
        hideModal(modal);
        selectedTextDescriptionLabel.style.display = 'none';
        NomralDescriptionLabel.style.display = 'block';
    }
    selectedTextDescriptionLabel.style.display = 'none';
    return modal;
}

// Create SRButton that can open the report modal
function addSRButton(modal) {

    // Make SR button will only show in the main content area. Careful for id.
    const contentDiv = document.querySelector('.ltx_page_content');
    if (!contentDiv) {
        console.error("Element with class 'ltx_page_content' not found.");
        return [];
    }

    const contents = contentDiv.querySelectorAll('p, svg, figure, .ltx_title, .ltx_authors');
    const buttons = [];

    // Get all the paragraphs in the document
    // Add a hidden button after each paragraph
    // Add a hidden button after each paragraph
    contents.forEach((content, i) => {
        if (content.classList.contains("header-message") || content.classList.contains("logomark")) return;

        const button = document.createElement("button");
        button.setAttribute("class", "sr-only button");
        button.style.display = "none";
        button.textContent = "Report issue for preceding element";

        button.onfocus = () => previousFocusElement = document.activeElement;

        button.onclick = (e) => {
            /*
                Comment: Need add a variable named initiateWay, so we can know how users initiate the report.

                For addSRbutton, initiateWay = "srButton"
                For smallReportButton, initiateWay = "smallButton"
                For ShortCut, initiateWay = "ShortCut"
                For click the button(right bi button) created in the modal, initiateWay = "FixedButton".

                So you may need to create a global variable. I have checked showModal it cannot send any parameter to modal.
            */
            showModal(modal);
            bugReportState.setSelectedHtmlSRB(content);
            bugReportState.setInitiateWay("SRButton");
            e.preventDefault();
        };

        // Insert the button after the paragraph
        content.parentNode.insertBefore(button, content.nextSibling);

        buttons.push(button);
    });

    return buttons;
}

function showModal(modal) {
    const theme = document.documentElement.getAttribute("data-theme");
    const modalHeader = document.getElementById("modal-header");
    if (theme === 'dark') {  
        modalHeader.setAttribute('data-bs-theme', "dark");
    }else{
        modalHeader.setAttribute('data-bs-theme', "light");
    }
        
    modal.style.display = 'block';
    modal.setAttribute('tabindex', '-1'); // Ensure the modal is focusable
    modal.focus();
}

function hideModal(modal) {
    modal.style.display = 'none';
}

function showButtons(buttons) {
    // buttons.forEach((button) => {
    //     console.log(button);
    //     console.log(button.style.display);
    //     button.style.display === 'none' ?
    //         button.style.display = 'inline' :
    //         button.style.display = 'none';
    // })
    buttons.forEach((button) => button.style.display = 'inline');
}

function hideButtons(buttons) {
    buttons.forEach((button) => button.style.display = 'none');
}

// Code for handling key press to open/close modal
const handleKeyDown = (e, modal, buttons) => {
    const ctrlOrMeta = e.metaKey || e.ctrlKey;

    // if(e.key === '¥'){
    //     showButtons(buttons);
    // } else if (e.key === 'Á'){
    //     hideButtons(buttons)
    // }
    if (e.altKey && e.code === 'KeyY' && !ctrlOrMeta) {
        e.shiftKey ? hideButtons(buttons) : showButtons(buttons);
    } else if (ctrlOrMeta && (e.key === '/' || e.key === '?')) {
        showModal(modal)
        bugReportState.setInitiateWay("ShortCut");
    } else if (ctrlOrMeta && (e.key === '}' || e.key === ']')) {
        hideModal(modal);
    }
}

//The highlight initiation way
function handleMouseUp(e, smallButton) {
    if (e.target.id === "small-report-button")
        return;
    if (!window.getSelection().isCollapsed) {
        selection = window.getSelection();
        currentAnchorNode = selection.anchorNode;
        bugReportState.setSelectedHtmlSmallButton(selection);
        // var range = selection.getRangeAt(0);
        // var container = document.createElement('div');
        // container.appendChild(range.cloneContents());
        // // Use the selected text to generate the dataURI
        // selectedHtml = 'data:text/html;charset=utf-8,' + encodeURIComponent(container.innerHTML);
        //Comment: Need to get the selected text and pass it to the backend
        //reference: var selectedhtml in app.js
        showSmallButton(smallButton);
    } else hideSmallButton(smallButton);
}

function createSmallButton(modal) {
    const smallReportButton = document.createElement('button');
    smallReportButton.id = 'small-report-button';
    smallReportButton.type = 'button';
    smallReportButton.className = 'btn btn-secondary btn-sm';
    smallReportButton.style.backgroundColor = '#b31b1b';
    smallReportButton.textContent = 'Report Issue for Selection';
    smallReportButton.style.position = 'fixed';

    document.body.appendChild(smallReportButton);

    smallReportButton.onclick = (e) => {
        document.getElementById('selectedTextModalDescription').style.display = 'block';
        document.getElementById('nomralModalDescription').style.display = 'none';
        showModal(modal); // do something with window.getSelection()
        bugReportState.setInitiateWay("selectedText-smallButton");
    }

    smallReportButton.addEventListener("focusout", function (e) {
        hideSmallButton(this);
    });

    return smallReportButton;
}

// Display the smallButton for bug report, click and scroll included
function showSmallButton(smallReportButton) {
    selection = window.getSelection();

    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();

    smallReportButton.style.left = `${rect.left + rect.width / 2}px`;

    // Check if there is enough space above the selected text
    smallReportButton.style.top = `${rect.top}px`;
    smallReportButton.style.transform = 'translate(-50%, -100%)';

    smallReportButton.style.display = 'inline';
}

function hideSmallButton(smallReportButton) {
    smallReportButton.style.display = 'none';
}

//submit to the backend, next step: finish
function submitBugReport(e) {
    e.preventDefault();
    //document.getElementById('notification').style = 'display: block';
    const issueData = {};

    // Canonical URL
    ARXIV_ABS_PATH = 'https://arxiv.org/abs/';
    const arxivIdv = window.location.pathname.split('/')[2]; // pathname ex: '/html/2306.16433v1/2306.16433v1.html'
    const fullUrl = window.location.href;
    const canonicalURL = ARXIV_ABS_PATH + arxivIdv;

    // const user_info = "account:yc2455 contact:@cornll.edu "

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
    let topLayer = 'Unknown';
    console.log(currentAnchorNode);
    if (currentAnchorNode !== null) {
        const parentNode = currentAnchorNode.parentNode;
        const id = parentNode.id;
        const classList = parentNode.classList;
        //if there is no id, than use class to identify
        elementIdentifier = id || classList[0] || 'Unknown';
        console.log(elementIdentifier);

        //get the topLayer of id
        if (elementIdentifier.match(/^S\d/)) {
            topLayer = id ? id.split('.')[1] : classList[0];
        } else {
            topLayer = id ? id.split('.')[0] : classList[0];
        }
    }

    const dataDescription = document.getElementById('description').value;
    const formTitle = document.getElementById('form_title').value;

    const uniqueId = window.crypto.randomUUID();

    // add to the form data
    // issueData['template'] = 'bug_report.md'); // TODO: Change this to a template with fields matching the ones below
    issueData['uniqueId'] = uniqueId;
    issueData['canonicalURL'] = canonicalURL;
    issueData['conversionURL'] = window.location.origin + window.location.pathname;
    issueData['reportTime'] = currentTime;
    issueData['browserInfo'] = browserInfo;
    issueData['description'] = dataDescription;
    issueData['locationLow'] = elementIdentifier;
    issueData['locationHigh'] = topLayer;
    issueData['selectedHtml'] = bugReportState.getSelectedHtml();
    issueData['initiationWay'] = bugReportState.getInitiateWay();

    form = new FormData();
    form.append('template', 'bug_report.md');
    form.append('title', `Improve article : ${arxivIdv}`)
    form.append('body', makeGithubBody(issueData));

    // Send to Database.
    postToDB(issueData);

    // Send to Github Issue. !!!NEED: make sure submitter id is same as the html submit button id.
    if (e.submitter.id === 'modal-submit') {
        const GITHUB_BASE_URL = 'https://github.com/arXiv/html_feedback/issues/new?'
        const queryString = new URLSearchParams(form).toString()
        const link = GITHUB_BASE_URL + queryString;
        // window.open(link, '_blank');
        // disable, test later.

        //Testing
        const url = testForGitHubIssue(issueData, arxivIdv, formTitle, fullUrl);
        window.open(url, '_blank');
    } 

    document.querySelector('#myFormContent').reset();
    bugReportState.clear();
    hideModal(document.getElementById('myForm'));
}

function handleClickOutsideModal(e, modal) {
    if (e.target == modal)
        modal.style.display = 'none';
}

function handleClickTOCToggle(e) {
    const listIcon= document.getElementById('listIcon');
    const arrowIcon= document.getElementById('arrowIcon');
    const toc = document.querySelector('.ltx_toclist');
    const toc_main = document.querySelector('.ltx_page_main>.ltx_TOC');
    // const content=document.querySelector('.ltx_page_content');
    if (e.target == listIcon) {
        //show toc and arrowIcon
        toc.classList.remove('hide');
        // toc.classList.add('show');
        arrowIcon.classList.remove('hide');
        // arrowIcon.classList.add('show');
        listIcon.classList.add('hide');
        toc_main.classList.add('active')
        // listIcon.classList.remove('show');
        // toc_main.style.backgroundColor = 'var(--background-color)';
        //change 
        /*toc_main.style.flex='1';
        content.style.flex='5';*/
        // toc_main.style.flex = '1 0 20%';  // This means it will start with 20% of the parent width but won't grow or shrink.
        // content.style.flex = '1 1 80%';  // This will make it take the remaining 80% but allows it to adjust as needed.
    }
    if (e.target == arrowIcon) {
        //hide toc and arrowIcon
        toc.classList.add('hide');
        // toc.classList.remove('show');
        arrowIcon.classList.add('hide');
        // arrowIcon.classList.remove('show');
        listIcon.classList.remove('hide');
        toc_main.classList.remove('active');
        // listIcon.classList.add('show');
        // toc_main.style.backgroundColor = 'transparent';
        // toc_main.style.flex='0 0 3rem';
        // content.style.flex='1 1 100%';
    }
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

function makeGithubBody(issueData) {
    let body = "## Describe the issue\n\n";
    body += `**Description**: ${issueData.description}\n\n`;
    body += "Feel free to attach a screenshot (or document) link below: \n\n\n\n";
    // Auto Fill Data
    body += "## Auto Fill Data - !!! Please do not edit below this line !!!\n";
    body += "----------------------------------------------------------------------------------------\n\n";
    body += `Id: ${issueData.uniqueId}\n`
    return body;
}

function testForGitHubIssue(issueData, arxivIdv, formTitle, fullUrl){
    var url = `https://github.com/arXiv/html_feedback/issues/new?assignees=&labels=&projects=&title= ${formTitle}&template=Feedback_about_HTML_formatted_papers.yml`;
    url += `&description=${issueData.description}`;
    url += `&uniqueId=${issueData.uniqueId}`;
    url += `&arxivId=${arxivIdv}`;
    url += `&browserInfo=${issueData.browserInfo}`;
    // send the full url to the github issue
    url += `&fullUrl=${fullUrl}`;
    // device type
    url += `&deviceType=${getDeviceType()}`;
    // https://browse.arxiv.org/latexml/2308.06262v1/2308.06262v1.html

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




function handleClickMobileTOC(e){
    const tocItems = document.querySelectorAll('.ltx_ref');
    const toc = document.querySelector('.ltx_page_main >.ltx_TOC.mobile')
    // //const toggle=document.getElementById('navbar-mobile-toggler')
    // const toggle=document.querySelector('.navbar-toggler-icon');

    // if(e.target==toggle){
    //     if(toc.classList.contains('show')){
    //         //toc.setAttribute('display','none');
    //         //toc.style.setProperty('display','none','important');
    //         toc.classList.add('hide');
    //         toc.classList.remove('show');
    //     }
    //     else{
    //         //toc.setAttribute('display','block');
    //         //toc.style.setProperty('display','block','important');
    //         toc.classList.remove('hide');
    //         toc.classList.add('show');
    //     }
    // }
    tocItems.forEach(item => {
        item.addEventListener('click', () => {
            toc.classList.remove('show');
        });
    });
}

// This is a hack to wait for the toggle, which will now only exist after a fetch
function waitForToggleExist() {
    const selector = '.ar5iv-toggle-color-scheme';
    return new Promise(resolve => {
        if (document.querySelector(selector)) {
            return resolve(document.querySelector(selector));
        }

        const observer = new MutationObserver(mutations => {
            if (document.querySelector(selector)) {
                observer.disconnect();
                resolve(document.querySelector(selector));
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    });
}

document.addEventListener("DOMContentLoaded", () => {

    const modal = addBugReportForm();
    const reportButtons = addSRButton(modal);
    const smallReportButton = createSmallButton(modal);

    document.onkeydown = (e) => handleKeyDown(e, modal, reportButtons);
    document.onclick = (e) => {
        handleClickOutsideModal(e, modal);
        if(window.innerWidth <= 719){
            handleClickMobileTOC(e);
        }
        else{
            handleClickTOCToggle(e);
        }
    }

    document.onmouseup = (e) => handleMouseUp(e, smallReportButton);
    document.ontouchend = (e) => handleMouseUp(e, smallReportButton);

    let lastScrollPosition = window.scrollY || document.documentElement.scrollTop || document.body.scrollTop;
    window.addEventListener('scroll', () => {
        const currentScrollPosition = window.scrollY || document.documentElement.scrollTop || document.body.scrollTop;
        if (currentScrollPosition > lastScrollPosition || currentScrollPosition < lastScrollPosition) {
            smallReportButton.style.display = "none";
        } else {
            smallReportButton.style.display = "block";
        }
        lastScrollPosition = currentScrollPosition;
    });

    document.getElementById('myFormContent').onsubmit = submitBugReport;

    localStorage.setItem('ar5iv_theme', 'automatic');

    waitForToggleExist().then((_) => {
        detectColorScheme();
    })
});