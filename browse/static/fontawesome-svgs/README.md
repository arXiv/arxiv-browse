#How to use this implementation of Font Awesome

This is a very minimal self-hosted svg implementation of font-awesome.
We are loading svg icon sprites as images.
Only the few icons currently in use on arxiv.org are being hosted.

## Add new icons to implementation
To add a new icon download the svg file you need from here:
https://github.com/FortAwesome/Font-Awesome/tree/master/svgs/brands
You can also download the entire package and get the individual svg files you need:
https://fontawesome.com/download

## Set icon color
To set the color open the svg file and add a "fill" attribute to to the path:
<path fill="#FFFFFF" d="etc etc etc">

## Add icons to your page
Add icons using img. Ex:
<img src="{{ url_for('static', filename='fontawesome-svgs/svgs/solid/envelope.svg') }}" alt="contact icon">

## Making icons accessible
Write clear and legible alt text for screen readers. If the icon is purely decorative add role="presentation" so screen readers know to skip it.
