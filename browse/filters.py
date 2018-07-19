"""Browse jinja filters."""
import re
from jinja2 import evalcontextfilter, Markup, escape
from flask import url_for


# sub write_abs_text {
#   my $self = shift;
#
#   my $br='';
#   foreach my $line ( split("\n",$self->this_version()->field('Abstract')) ) {
#    $line=escape_special_characters($line);
#     $line=filter_urls($line);
#     next unless ($line=~/\S/); #ignore blank lines
#     # if lines start with \s, they need a <br /> (except first line)
#     $line =~ s/^\s+/$br/;
#     $br = '<br />'; #assign here to avoid first line
#     print "$line\n";
#   }
# }

# sub filter_urls {
#   my $string = shift;
#   $string =~ s#((ftp|http)://[^]*})\s",>&;]+)#<a href="$1">this $2 URL</a>#ig;
#   $string =~ s#(^|[^/A-Za-z-])((arXiv:|(?<!viXra:))($ID_REGEX))#$1<a href="/abs/$5">$2</a>#g;
#   return $string;
# }

def escape_special_chracters(text: str) -> str:
    result = text
    result = re.sub(r'&(?!amp;)', '&amp;', result)
    result = re.sub(r'<', '&lt;', result)
    result = re.sub(r'>', '&gt;', result)
    return result


@evalcontextfilter
def filter_urls(eval_ctx, text: str) -> str:
    result = re.sub(r'((ftp|https?)://[^\[\]*{}()\s",>&;]+)\s',
                    r'<a href="\g<1>">this \g<2> URL</a>\g<3>',
                    text,
                    re.IGNORECASE)
    # result = re.sub(r'(^|[^/A-Za-z-])((arXiv:|(?<!viXra:))($ID_REGEX))')
    if eval_ctx.autoescape:
        result = Markup(result)
    return result


@evalcontextfilter
def abstract_breaks(eval_ctx, text: str) -> str:
    """Line breaks for abstract field."""
    result = ''
    for (idx, line) in enumerate(text.split('\n')):
        if not re.search(r'\S', line):
            # ignore blank lines
            next
        line = escape_special_chracters(line)
        line = filter_urls(eval_ctx, line)
        # print(f'url line {line}')
        # line = escape(line)
        # print(f'escaped line: {line}')
        if idx > 0:
            line = re.sub(r'^\s+', '<br/>', line)
        result = f'{result}{line}\n'
    if eval_ctx.autoescape:
        print('yes')
        result = Markup(result)
        # Markup
    return result if result else text
