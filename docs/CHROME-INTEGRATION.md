# Spinout header/footer chrome — integration guide

The "spinout" site chrome (black header bar with search overlay, the
acknowledgement + funders footer, and the announcement banner) is packaged so it
can be **carried over** into any arXiv app — either inherited via `arxiv-base` or
vendored file-by-file into apps that can't easily bump `arxiv-base`.

`arxiv-browse` is the **source of truth**. The design reference (tokens, policies)
lives in the `arXiv/design-system` repo.

## The bundle

**Templates** (`browse/templates/`)
- `header.html` — `<header class="arxiv-header">` + the search overlay.
- `footer.html` — `<footer class="arxiv-footer">` (acknowledgement nav + funders).
- `announcement_banner.html` — reusable `announcement_banner(text, link_text, link, name, end)` macro.

**Static assets** (`browse/static/`)
- `css/arxiv-header-footer.css` — all chrome styles; **framework-agnostic, no deps**.
- `js/arxiv-header.js` — search overlay, phone hamburger, member-institution ack,
  and persistent banner dismissal; **vanilla JS, no jQuery**.
- `fonts/IBMPlexSans-{Regular,Medium,SemiBold}.woff2` + `IBMPlexSans-LICENSE.txt`.
- `images/arxiv-logo-primary-light.svg`
- `images/funders/{simons-foundation,schmidt-sciences}.png`
- `images/icons/smileybones-small.svg`

The CSS/JS/assets are the **universal, copy-anywhere** core. The templates carry
framework bindings (see Contract) and so are reused directly across the Jinja/Flask
family (browse, arxiv-base and its consumers) or hand-ported for other engines.

## Integrate in a Jinja/Flask app

In the app's `base.html`:

1. **Head**, before the stylesheets, set the JS flag (progressive enhancement):
   ```html
   <script>document.documentElement.classList.add('js');</script>
   ```
2. **Head**, link the stylesheet:
   ```html
   <link rel="stylesheet" media="screen" href="{{ url_for('static', filename='css/arxiv-header-footer.css') }}?v=YYYYMMDD">
   ```
3. **Body**, include the chrome (block-wrapped so downstream apps can override):
   ```jinja
   {% block header %}{% include "header.html" %}{% endblock header %}
   ...
   {% block footer %}{% include "footer.html" %}{% endblock footer %}
   ```
4. **Before `</body>`**, load the script:
   ```html
   <script src="{{ url_for('static', filename='js/arxiv-header.js') }}?v=YYYYMMDD"></script>
   ```
5. **Announcement banner** (optional, caller controls the date window):
   ```jinja
   {% import 'announcement_banner.html' as ab %}
   {{ ab.announcement_banner("arXiv is now an independent nonprofit!", "Learn more",
                             "https://info.arxiv.org/about", "spinout-nonprofit") }}
   ```

## Contract (host bindings the templates expect)

- **Routes** via `url_for`: `home`, `search_box`, `create`, `account`, `logout`,
  `login` (header); `about`, `help`, `contact`, `subscribe`, `copyright`,
  `privacy_policy`, `a11y` (footer). Map these to the app's endpoints (or replace
  with literal URLs when porting to a non-Flask engine).
- **Static**: the asset paths above resolve via `url_for('static', filename=...)`.
  Adjust to the app's static mount.
- **Auth**: the header shows My Account/Logout when `request.auth.user` is defined,
  else Log in. Adapt to the app's auth object.
- **Member-institution acknowledgement**: `arxiv-header.js` fetches
  `/institutional_banner` (IP-keyed JSON `{"label": "<Institution>"}`) and fills
  `#arxiv-ack-member`. Without that endpoint the name is simply omitted — the rest
  of the footer is unaffected.
- **Announcement banner**: the caller gates rendering (e.g. a date window);
  dismissal is remembered in a `localStorage` flag keyed by `name`, so a closed
  banner stays closed and a new announcement (new `name`) shows again. No cookie,
  no external JS/CSS.

## Non-Jinja apps (e.g. arxiv-submit, Perl/Catalyst)

Copy the **static bundle** as-is into the app's public assets, then **hand-port the
markup** from `header.html` / `footer.html` / `announcement_banner.html`: substitute
`url_for(...)` with the app's URLs and the auth conditional with its session check.
Keep the class names and DOM structure identical so the shared CSS/JS apply unchanged.

## Design tokens

`arxiv-header-footer.css` uses `--arxiv-*` custom properties that map 1:1 to the
`arXiv/design-system` canonical tokens (`design-system.css`). Three values are not
yet canonical and are flagged in the CSS for the design system to name: Open Blue
`#a5d6fe`, Warm Wash `#f9f7f7`, brown-divider `#2d2a26`.
