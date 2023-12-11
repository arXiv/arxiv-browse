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

    var Links = `
    <nav class="html-header-nav">
      <a class="ar5iv-footer-button hover-effect" href="https://info.arxiv.org/about/accessible_HTML.html" target="_blank">Why HTML?</a>
      <a class="ar5iv-footer-button hover-effect" target="_blank" href="#myForm" onclick="event.preventDefault(); var modal = document.getElementById('myForm'); modal.style.display = 'block'; bugReportState.setInitiateWay('Header');">Report Issue</a>
      ${id === 'submission' ? '' : `<a class="ar5iv-footer-button hover-effect" href="https://arxiv.org/abs/${window.location.href.match(/https:\/\/.+\/html\/(.+)/)[1]}">Back to Abstract</a>`}
      <a class="ar5iv-toggle-color-scheme" href="javascript:toggleColorScheme()" title="Toggle dark/light mode">
          <span class="color-scheme-icon"></span>
      </a>
    </nav>`;

    desktop_header.innerHTML = LogoBanner + Links;
    desktop_header.classList.add('desktop_header');
    document.body.insertBefore(desktop_header, document.body.firstChild);
};

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
        <a class="nav-link ar5iv-footer-button hover-effect" aria-label="Back to abstract page" href="https://arxiv.org/abs/${window.location.href.match(/https:\/\/.+\/html\/(.+)/)[1]}">
        <svg xmlns="http://www.w3.org/2000/svg" height="1.25em" viewBox="0 0 512 512" fill="#ffffff" aria-hidden="true">
            <path d="M502.6 278.6c12.5-12.5 12.5-32.8 0-45.3l-128-128c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3L402.7 224 192 224c-17.7 0-32 14.3-32 32s14.3 32 32 32l210.7 0-73.4 73.4c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0l128-128zM160 96c17.7 0 32-14.3 32-32s-14.3-32-32-32L96 32C43 32 0 75 0 128L0 384c0 53 43 96 96 96l64 0c17.7 0 32-14.3 32-32s-14.3-32-32-32l-64 0c-17.7 0-32-14.3-32-32l0-256c0-17.7 14.3-32 32-32l64 0z"/>
        </svg>
        </a>`}
      <!--dark mode-->
      <a class="ar5iv-toggle-color-scheme" href="javascript:toggleColorScheme()"
        title="Toggle dark/light mode">
        <span class="color-scheme-icon"></span>
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

    //killed the footer nav with the following 4 variables, keeping them in case we want to bring them back
    var night = `
        <a class="ar5iv-toggle-color-scheme" href="javascript:toggleColorScheme()" title="Toggle ar5iv color scheme">
            <span class="color-scheme-icon"></span>
        </a>`;

    var copyLink = `
        <a class="ar5iv-footer-button" href="https://arxiv.org/help/license" target="_blank">Copyright</a>`;

    var policyLink = `
        <a class="ar5iv-footer-button" href="https://arxiv.org/help/policies/privacy_policy" target="_blank">Privacy Policy</a>`;

    var HTMLLink = `
        <a class="ar5iv-footer-button" href="https://info.arxiv.org/about/accessible_HTML.html" target="_blank">Why HTML?</a>`;

    var TimeLogo = `
        <div class="ltx_page_logo">
            Generated on Wed Dec 14 18:01:44 2022 by
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
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const href = this.getAttribute('href');
        const targetElement = document.getElementById(href.substring(1));
        const position = targetElement.getBoundingClientRect();
        if (targetElement) {
          window.scrollTo({left: position.left, 
                           top: position.top + window.scrollY - 60, 
                           behavior: 'smooth'});
        } else {
          console.warn('No element found for selector:', href);
        }
      });
    });
    document.querySelector('.ltx_page_main').id = 'main';

    ref_ArXivFont();
    create_favicon();
    unwrap_nav();
    create_header();
    create_mobile_header();

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
        const toc_m= document.querySelector('.ltx_page_main>.ltx_TOC.mobile');
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
          const citeElement = document.querySelector(`cite a[href="#${referenceId}"]`);
          if (citeElement) {
            citeElement.scrollIntoView({ behavior: "smooth" });
          }
        }
      });

      const citeElements = document.querySelectorAll(`cite a[href="#${referenceId}"]`);
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
