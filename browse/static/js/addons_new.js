let create_favicon = () => {
  let favicon32 = document.createElement('link');
  favicon32.rel = 'icon';
  favicon32.type = 'image/png';
  favicon32.href = 'https://static.arxiv.org/static/browse/0.3.4/images/icons/favicon-32x32.png';
  favicon32.sizes = '32x32';

  let favicon16 = document.createElement('link');
  favicon16.rel = 'icon';
  favicon16.type = 'image/png';
  favicon16.href = 'https://static.arxiv.org/static/browse/0.3.4/images/icons/favicon-16x16.png';
  favicon16.sizes = '16x16';

  document.head.appendChild(favicon16);
  document.head.appendChild(favicon32);
}

let create_header = () => {
    let desktop_header = document.createElement('header');
    let ABS_URL_BASE = 'https://arxiv.org/abs';
    let id = window.location.pathname.split('/')[2];

    var LogoBanner = `
    <div class="html-header-logo">
      <a href="https://arxiv.org/">
          <img alt="logo" class="logo" role="presentation" width="100" src="https://services.dev.arxiv.org/html/static/arxiv-logo-one-color-white.svg">
          <span class="sr-only">Back to arXiv</span>
      </a>
    </div>
    <div class="html-header-message" role="banner">
        <p>${id === 'submission' ? 'This is <strong>experimental HTML</strong> to improve accessibility. By design, HTML will not look exactly like the PDF. Please report any errors that don\'t represent the intent or meaning of your paper. <span class="sr-only">Use Alt+Y to toggle on accessible reporting links and Alt+Shift+Y to toggle off.</span> View LaTeX Markup <a href="https://info.arxiv.org/help/submit_latex_best_practices.html" target="_blank">Best Practices</a> for Successful HTML Papers.' :
        'This is <strong>experimental HTML</strong> to improve accessibility. We invite you to report rendering errors. <span class="sr-only">Use Alt+Y to toggle on accessible reporting links and Alt+Shift+Y to toggle off.</span> Learn more <a href="https://info.arxiv.org/about/accessible_HTML.html" target="_blank">about this project</a> and <a href="https://info.arxiv.org/help/submit_latex_best_practices.html" target="_blank">help improve conversions</a>.'}
        </p>
    </div>`;

    const locationId = encodeURI(window.location.href.match(/https:\/\/.+\/html\/(.+)/)[1]);
    var Links = `
    <nav class="html-header-nav">
      <a class="ar5iv-footer-button hover-effect" href="https://info.arxiv.org/about/accessible_HTML.html" target="_blank">Why HTML?</a>
      <a class="ar5iv-footer-button hover-effect" target="_blank" href="#myForm" onclick="event.preventDefault(); var modal = document.getElementById('myForm'); modal.style.display = 'block'; bugReportState.setInitiateWay('Header');">Report Issue</a>
      ${id === 'submission' ? '' : `<a class="ar5iv-footer-button hover-effect" href="https://arxiv.org/abs/${locationId}">Back to Abstract</a>`}
      ${id === 'submission' ? '' : `<a class="ar5iv-footer-button hover-effect" href="https://arxiv.org/pdf/${locationId}" target="_blank">Download PDF</a>`}
      <a class="ar5iv-toggle-color-scheme" href="javascript:toggleColorScheme()"
        title="Toggle dark/light mode">
        <label id="automatic-tog" class="toggle-icon" title="Switch to light mode" for="__palette_3">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="m14.3 16-.7-2h-3.2l-.7 2H7.8L11 7h2l3.2 9h-1.9M20 8.69V4h-4.69L12 .69 8.69 4H4v4.69L.69 12 4 15.31V20h4.69L12 23.31 15.31 20H20v-4.69L23.31 12 20 8.69m-9.15 3.96h2.3L12 9l-1.15 3.65Z"></path></svg>
        </label>
        <label id="light-tog" class="toggle-icon" title="Switch to dark mode" for="__palette_1" hidden>
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 8a4 4 0 0 0-4 4 4 4 0 0 0 4 4 4 4 0 0 0 4-4 4 4 0 0 0-4-4m0 10a6 6 0 0 1-6-6 6 6 0 0 1 6-6 6 6 0 0 1 6 6 6 6 0 0 1-6 6m8-9.31V4h-4.69L12 .69 8.69 4H4v4.69L.69 12 4 15.31V20h4.69L12 23.31 15.31 20H20v-4.69L23.31 12 20 8.69Z"></path></svg>
        </label>
        <label id="dark-tog" class="toggle-icon" title="Switch to system preference" for="__palette_2" hidden>
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 18c-.89 0-1.74-.2-2.5-.55C11.56 16.5 13 14.42 13 12c0-2.42-1.44-4.5-3.5-5.45C10.26 6.2 11.11 6 12 6a6 6 0 0 1 6 6 6 6 0 0 1-6 6m8-9.31V4h-4.69L12 .69 8.69 4H4v4.69L.69 12 4 15.31V20h4.69L12 23.31 15.31 20H20v-4.69L23.31 12 20 8.69Z"></path></svg>
        </label>
      </a>
    </nav>`;

    desktop_header.innerHTML = LogoBanner + Links;
    desktop_header.classList.add('desktop_header');
    document.body.insertBefore(desktop_header, document.body.firstChild);
};

let generate_upper_content_from_metadata = async () => {
  // fetch metadata
  let path = window.location.origin+window.location.pathname;
  if (path.endsWith('/view')) {
    path = path.slice(0, -5);
  }
  let response = await fetch (path+'/__metadata.json');

  if (!response.ok) {
    throw new Error('Failed to retrieve metadata for license, watermark, and missing packages');
  }

  const metadata = await response.json();

  // Create target section
  let target_section = document.createElement('div');
  target_section.setAttribute('id', 'target-section');
  target_section.setAttribute('class', 'section');

  // Add license
  let license = document.createElement('a');
  license.setAttribute('id', 'license-tr');
  license.setAttribute('href', 'https://info.arxiv.org/help/license/index.html#licenses-available');
  license.innerText = metadata.license;
  target_section.appendChild(license);

  // Add watermark
  if ('submission_timestamp' in metadata && 'primary_category' in metadata) {
    let watermark = document.createElement('div');
    watermark.setAttribute('id', 'watermark-tr');
    watermark.innerText = 'arXiv:' + metadata.id + ' [' + metadata.primary_category + '] ' + metadata.submission_timestamp;
    target_section.appendChild(watermark);
  }

  // Add missing packages
  let page_content = document.querySelector('.ltx_page_content');
  page_content.prepend(target_section);

  if (metadata.missing_packages) {
    let missing_package_lis = metadata.missing_packages.map(x => `<li>failed: ${x}</li>`).join('');
    target_section.insertAdjacentHTML('beforebegin', 
    `<div class="package-alerts ltx_document" role="status" aria-label="Conversion errors have been found">
      <button aria-label="Dismiss alert" onclick="closePopup()">
          <span aria-hidden="true"><svg role="presentation" width="20" height="20" viewBox="0 0 44 44" aria-hidden="true" focusable="false">
          <path d="M0.549989 4.44999L4.44999 0.549988L43.45 39.55L39.55 43.45L0.549989 4.44999Z" />
          <path d="M39.55 0.549988L43.45 4.44999L4.44999 43.45L0.549988 39.55L39.55 0.549988Z" />
          </svg></span>
      </button>
      <p>HTML conversions <a href="https://info.dev.arxiv.org/about/accessibility_html_error_messages.html" target="_blank">sometimes display errors</a> due to content that did not convert correctly from the source. This paper uses the following packages that are not yet supported by the HTML conversion tool. Feedback on these issues are not necessary; they are known and are being worked on.</p>
          <ul arial-label="Unsupported packages used in this paper">
              ${missing_package_lis}
          </ul>
      <p>Authors: achieve the best HTML results from your LaTeX submissions by following these <a href="https://info.arxiv.org/help/submit_latex_best_practices.html" target="_blank">best practices</a>.</p>
    </div>`
    );
  }
}

function closePopup() {
  document.querySelector('.package-alerts').style.display = 'none';
}

let add_abs_refs_to_toc = () => {
  let toc = document.querySelector('.ltx_toclist');

  let abs = document.querySelector('.ltx_abstract');
  if (abs) {
    abs.setAttribute('id', 'abstract');
    let abs_li = document.createElement('li');
    abs_li.setAttribute('class', 'ltx_tocentry ltx_tocentry_section');
    abs_li.innerHTML = `
    <a class="ltx_ref" href="${encodeURI(document.location.href.match(/(^[^#]*)/)[0] + "#abstract")}" title="Abstract">
      <span class="ltx_text ltx_ref_title">
        <span class="ltx_tag ltx_tag_ref"></span>
        Abstract
      </span>
    </a>`;
    toc.prepend(abs_li);
  }

  let references = document.querySelector('.ltx_bibliography');
  if (references) {
    let li = document.createElement('li');
    li.setAttribute('class', 'ltx_tocentry ltx_tocentry_section');
    li.innerHTML = `
    <a class="ltx_ref" href="${encodeURI(document.location.href.match(/(^[^#]*)/)[0] + "#bib")}" title="References">
      <span class="ltx_text ltx_ref_title">
        <span class="ltx_tag ltx_tag_ref"></span>
        References
      </span>
    </a>`;
    toc.appendChild(li);
  }
}

let create_mobile_header = () => {
    let mob_header = document.createElement('header');
    let ABS_URL_BASE = 'https://arxiv.org/abs';
    let id = window.location.pathname.split('/')[2];

    var mobile_header= `
    <div class="html-header-logo">
      <a href="https://arxiv.org/">
        <img alt="logo" class="logomark" role="presentation" width="100" src="https://services.dev.arxiv.org/html/static/arxiv-logomark-small-white.svg">
        <span class="sr-only">Back to arXiv</span>
      </a>
    </div>

    <!--TOC, dark mode, links-->
    <div class='html-header-nav'>
      <!--back to abstract-->
      ${id === 'submission' ? '' : `
        <a class="nav-link ar5iv-footer-button hover-effect" aria-label="Back to abstract page" href="https://arxiv.org/abs/${encodeURI(window.location.href.match(/https:\/\/.+\/html\/(.+)/)[1])}">
        <svg xmlns="http://www.w3.org/2000/svg" height="1.25em" viewBox="0 0 512 512" fill="#ffffff" aria-hidden="true">
            <path d="M502.6 278.6c12.5-12.5 12.5-32.8 0-45.3l-128-128c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3L402.7 224 192 224c-17.7 0-32 14.3-32 32s14.3 32 32 32l210.7 0-73.4 73.4c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0l128-128zM160 96c17.7 0 32-14.3 32-32s-14.3-32-32-32L96 32C43 32 0 75 0 128L0 384c0 53 43 96 96 96l64 0c17.7 0 32-14.3 32-32s-14.3-32-32-32l-64 0c-17.7 0-32-14.3-32-32l0-256c0-17.7 14.3-32 32-32l64 0z"/>
        </svg>
        </a>`}
      <!--dark mode-->
      <a class="ar5iv-toggle-color-scheme" href="javascript:toggleColorScheme()"
        title="Toggle dark/light mode">
        <label id="automatic-tog" class="toggle-icon" title="Switch to light mode" for="__palette_3">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="m14.3 16-.7-2h-3.2l-.7 2H7.8L11 7h2l3.2 9h-1.9M20 8.69V4h-4.69L12 .69 8.69 4H4v4.69L.69 12 4 15.31V20h4.69L12 23.31 15.31 20H20v-4.69L23.31 12 20 8.69m-9.15 3.96h2.3L12 9l-1.15 3.65Z"></path></svg>
        </label>
        <label id="light-tog" class="toggle-icon" title="Switch to dark mode" for="__palette_1" hidden>
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 8a4 4 0 0 0-4 4 4 4 0 0 0 4 4 4 4 0 0 0 4-4 4 4 0 0 0-4-4m0 10a6 6 0 0 1-6-6 6 6 0 0 1 6-6 6 6 0 0 1 6 6 6 6 0 0 1-6 6m8-9.31V4h-4.69L12 .69 8.69 4H4v4.69L.69 12 4 15.31V20h4.69L12 23.31 15.31 20H20v-4.69L23.31 12 20 8.69Z"></path></svg>
        </label>
        <label id="dark-tog" class="toggle-icon" title="Switch to system preference" for="__palette_2" hidden>
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 18c-.89 0-1.74-.2-2.5-.55C11.56 16.5 13 14.42 13 12c0-2.42-1.44-4.5-3.5-5.45C10.26 6.2 11.11 6 12 6a6 6 0 0 1 6 6 6 6 0 0 1-6 6m8-9.31V4h-4.69L12 .69 8.69 4H4v4.69L.69 12 4 15.31V20h4.69L12 23.31 15.31 20H20v-4.69L23.31 12 20 8.69Z"></path></svg>
        </label>
      </a>
      <!--nav-->
      <button class="navbar-toggler ar5iv-footer-button" type="button" data-bs-theme="dark" data-bs-toggle="collapse" aria-expanded="false"
        data-bs-target=".ltx_page_main >.ltx_TOC.mobile" aria-controls="navbarSupportedContent" aria-expanded="false"
        aria-label="Toggle navigation" style="border:none; margin-right: 0em;">
        <svg xmlns="http://www.w3.org/2000/svg" height="1.25em" viewBox="0 0 448 512" aria-hidden="true" role="img" fill="#ffffff"><path d="M0 96C0 78.3 14.3 64 32 64H416c17.7 0 32 14.3 32 32s-14.3 32-32 32H32C14.3 128 0 113.7 0 96zM0 256c0-17.7 14.3-32 32-32H416c17.7 0 32 14.3 32 32s-14.3 32-32 32H32c-17.7 0-32-14.3-32-32zM448 416c0 17.7-14.3 32-32 32H32c-17.7 0-32-14.3-32-32s14.3-32 32-32H416c17.7 0 32 14.3 32 32z"/></svg>
      </button>
    </div>
    `;
    mob_header.innerHTML=mobile_header
    // mob_header.classList.add('navbar');
    // mob_header.classList.add('bg-body-tertiary');
    mob_header.classList.add('mob_header');
    document.body.insertBefore(mob_header, document.body.firstChild);
}

let delete_footer = () => document.querySelector('footer').remove();


let create_footer = () => {
    let footer = document.createElement('footer');
    let ltx_page_footer = document.createElement('div');
    ltx_page_footer.setAttribute('class', 'ltx_page_footer');
    footer.setAttribute('id', 'footer');
    footer.setAttribute('class', 'ltx_document');

    var TimeLogo = `
        <div class="ltx_page_logo">
            Generated by
            <a href="https://math.nist.gov/~BMiller/LaTeXML/" class="ltx_LaTeXML_logo">
                <span style="letter-spacing: -0.2em; margin-right: 0.1em;">
                    L
                    <span style="font-size: 70%; position: relative; bottom: 2.2pt;">A</span>
                    T
                    <span style="position: relative; bottom: -0.4ex;">E</span>
                </span>
                <span class="ltx_font_smallcaps">xml</span>
                <img alt="[LOGO]" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAsAAAAOCAYAAAD5YeaVAAAAAXNSR0IArs4c6QAAAAZiS0dEAP8A/wD/oL2nkwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB9wKExQZLWTEaOUAAAAddEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIFRoZSBHSU1Q72QlbgAAAdpJREFUKM9tkL+L2nAARz9fPZNCKFapUn8kyI0e4iRHSR1Kb8ng0lJw6FYHFwv2LwhOpcWxTjeUunYqOmqd6hEoRDhtDWdA8ApRYsSUCDHNt5ul13vz4w0vWCgUnnEc975arX6ORqN3VqtVZbfbTQC4uEHANM3jSqXymFI6yWazP2KxWAXAL9zCUa1Wy2tXVxheKA9YNoR8Pt+aTqe4FVVVvz05O6MBhqUIBGk8Hn8HAOVy+T+XLJfLS4ZhTiRJgqIoVBRFIoric47jPnmeB1mW/9rr9ZpSSn3Lsmir1fJZlqWlUonKsvwWwD8ymc/nXwVBeLjf7xEKhdBut9Hr9WgmkyGEkJwsy5eHG5vN5g0AKIoCAEgkEkin0wQAfN9/cXPdheu6P33fBwB4ngcAcByHJpPJl+fn54mD3Gg0NrquXxeLRQAAwzAYj8cwTZPwPH9/sVg8PXweDAauqqr2cDjEer1GJBLBZDJBs9mE4zjwfZ85lAGg2+06hmGgXq+j3+/DsixYlgVN03a9Xu8jgCNCyIegIAgx13Vfd7vdu+FweG8YRkjXdWy329+dTgeSJD3ieZ7RNO0VAXAPwDEAO5VKndi2fWrb9jWl9Esul6PZbDY9Go1OZ7PZ9z/lyuD3OozU2wAAAABJRU5ErkJggg==">
            </a>
        </div>`;

    footer.innerHTML = `
        <div class="keyboard-glossary">
            <h2>Instructions for reporting errors</h2>
            <p>We are continuing to improve HTML versions of papers, and your feedback helps enhance accessibility and mobile support. To report errors in the HTML that will help us improve conversion and rendering, choose any of the methods listed below:</p>
            <ul>
                <li>Click the "Report Issue" button.</li>
                <li>Open a report feedback form via keyboard, use "<strong>Ctrl + ?</strong>".</li>
                <li>Make a text selection and click the "Report Issue for Selection" button near your cursor.</li>
                <li class="sr-only">You can use Alt+Y to toggle on and Alt+Shift+Y to toggle off accessible reporting links at each section.</li>
            </ul>
            <p>Our team has already identified <a class="ltx_ref" href=https://github.com/arXiv/html_feedback/issues target="_blank">the following issues</a>. We appreciate your time reviewing and reporting rendering errors we may not have found yet. Your efforts will help us improve the HTML versions for all readers, because disability should not be a barrier to accessing research. Thank you for your continued support in championing open access for all.</p>
            <p>Have a free development cycle? Help support accessibility at arXiv! Our collaborators at LaTeXML maintain a <a class="ltx_ref" href=https://github.com/brucemiller/LaTeXML/wiki/Porting-LaTeX-packages-for-LaTeXML target="_blank">list of packages that need conversion</a>, and welcome <a class="ltx_ref" href=https://github.com/brucemiller/LaTeXML/issues target="_blank">developer contributions</a>.</p>
        </div>
    `;

    ltx_page_footer.innerHTML = TimeLogo;
    ltx_page_footer.setAttribute('class', 'ltx_page_footer');

    document.body.appendChild(ltx_page_footer);
    document.body.appendChild(footer);
};

let unwrap_nav = () => {
    let nav = document.querySelector('.ltx_page_navbar');
    document.querySelector('#main').prepend(...nav.childNodes);
    nav.remove();

    let toc = document.querySelector('.ltx_TOC');
    let toc_header = document.createElement('h2');
    toc_header.innerText = 'Table of Contents';
    toc_header.id = 'toc_header';
    toc_header.setAttribute('class', 'sr-only');
    toc.prepend(toc_header);
    toc.setAttribute('aria-labelledby', 'toc_header');

    const olElement = document.querySelector('.ltx_toclist');
    const listIconHTML = `
      <div id="listIcon" type="button" class='hide'>
          <svg width='17px' height='17px' viewBox="0 0 512 512" style="pointer-events: none;">
          <path d="M40 48C26.7 48 16 58.7 16 72v48c0 13.3 10.7 24 24 24H88c13.3 0 24-10.7 24-24V72c0-13.3-10.7-24-24-24H40zM192 64c-17.7 0-32 14.3-32 32s14.3 32 32 32H480c17.7 0 32-14.3 32-32s-14.3-32-32-32H192zm0 160c-17.7 0-32 14.3-32 32s14.3 32 32 32H480c17.7 0 32-14.3 32-32s-14.3-32-32-32H192zm0 160c-17.7 0-32 14.3-32 32s14.3 32 32 32H480c17.7 0 32-14.3 32-32s-14.3-32-32-32H192zM16 232v48c0 13.3 10.7 24 24 24H88c13.3 0 24-10.7 24-24V232c0-13.3-10.7-24-24-24H40c-13.3 0-24 10.7-24 24zM40 368c-13.3 0-24 10.7-24 24v48c0 13.3 10.7 24 24 24H88c13.3 0 24-10.7 24-24V392c0-13.3-10.7-24-24-24H40z"/>
          </svg>
      </div>`;

      const arrowIconHTML = `
      <div id="arrowIcon" type="button">
          <svg width='17px' height='17px' viewBox="0 0 448 512" style="pointer-events: none;">
          <path d="M9.4 233.4c-12.5 12.5-12.5 32.8 0 45.3l160 160c12.5 12.5 32.8 12.5 45.3 0s12.5-32.8 0-45.3L109.2 288 416 288c17.7 0 32-14.3 32-32s-14.3-32-32-32l-306.7 0L214.6 118.6c12.5-12.5 12.5-32.8 0-45.3s-32.8-12.5-45.3 0l-160 160z"/>
          </svg>
      </div>`;
    olElement.insertAdjacentHTML('beforebegin', listIconHTML + arrowIconHTML);

    if(window.innerWidth <=719){
      toc.classList.add('mobile');
      toc.classList.add('collapse');
    }
    else{
      toc.classList.add('active');
    }
}

function ref_ArXivFont(){
  var link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = "https://use.typekit.net/rwr5zpx.css";
  document.head.appendChild(link);
}

window.addEventListener('load', function() {
  if (window.location.pathname.split('/')[2] === 'submission') {
    const baseTag = this.document.querySelector('base');
    if (baseTag) {
      baseTag.remove();
    }
  }
});

document.addEventListener("DOMContentLoaded", () => {
    document.querySelector('.ltx_page_main').id = 'main';

    ref_ArXivFont();
    create_favicon();
    add_abs_refs_to_toc();
    unwrap_nav();
    create_header();
    create_mobile_header();
    generate_upper_content_from_metadata();

    delete_footer();
    create_footer();

    window.addEventListener('resize', function() {
      if (window.innerWidth <=719) {
        const toc= document.querySelector('.ltx_page_main>.ltx_TOC');
        toc.classList.add('mobile');
        toc.classList.add('collapse');
        toc.classList.remove('active');
      }
      else{
        //TOC is shown
        const toc_m = document.querySelector('.ltx_page_main>.ltx_TOC.mobile');
        if (toc_m !== null) {
          toc_m.classList.remove('mobile');
          toc_m.classList.remove('collapse');
          toc_m.classList.remove('show');
          toc_m.classList.add('active');

          //arrow Icon is shown
          const arrowIcon = document.getElementById('arrowIcon');
          arrowIcon.classList.remove('hide');
          //list Icon is hidden
          const listIcon = document.getElementById('listIcon');
          listIcon.classList.add('hide');
          //TOC list is shown
          const toc_list= document.querySelector('.ltx_toclist');
          toc_list.classList.remove('hide');
        }
      }
    });

    const referenceItems = document.querySelectorAll(".ltx_bibitem");

    referenceItems.forEach(item => {
      const referenceId = item.getAttribute("id");
      const backToReferenceBtn = document.createElement("button");
      backToReferenceBtn.innerHTML = "&#x2191;";
      backToReferenceBtn.classList.add("back-to-reference-btn");
      backToReferenceBtn.setAttribute("aria-label", "Back to the article");

      let scrollPosition = 0;
      let clickedCite = false;

      backToReferenceBtn.addEventListener("click", function() {
        if (clickedCite) {
          window.scrollTo(0, scrollPosition);
        } else {
          let citeElement = document.querySelector(`cite a[href="${window.location.origin}${window.location.pathname}#${referenceId}"]`);
          if (citeElement === null) {
            citeElement = document.querySelector(`cite a[href="#${referenceId}"]`)
          }
          if (citeElement) {
            citeElement.scrollIntoView({ behavior: "smooth" });
          }
        }
      });

      let citeElements = document.querySelectorAll(`cite a[href="${window.location.origin}${window.location.pathname}#${referenceId}"]`);
      if (citeElements.length === 0) {
        citeElements = document.querySelectorAll(`cite a[href="#${referenceId}"]`);
      }
      citeElements.forEach(citeElement => {
        citeElement.addEventListener("click", function() {
          scrollPosition = window.scrollY;
          clickedCite = true;
        });
      });

      const refNumElement = item.querySelector(".ltx_tag_bibitem");
      if (refNumElement) {
        refNumElement.appendChild(backToReferenceBtn);
    }
    });
  });
