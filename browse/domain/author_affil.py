"""Parse Authors lines to extract author and affiliation data"""
import pprint
import re
from itertools import dropwhile, takewhile
from typing import List

PREFIX_MATCH = 'van|der|de|la|von|del|della|da|mac|ter|dem|di'

# TODO update comments for Python

"""
Takes data from an Author: line in the current arXiv abstract
file and returns a structured set of data:
 
 author_list_ptr = [
  [ author1_keyname, author1_firstnames, author1_suffix, affil1, affil2 ] ,
  [ author2_keyname, author2_firstnames, author1_suffix, affil1 ] ,
  [ author3_keyname, author3_firstnames, author1_suffix ] 
         ]

All fields are passed through the Tex2UTF filter so UTF-8 will
be returned if accents are present. 

Abstracted from Dienst software for OAI1 and other uses. This
routine might at some stage be incorporated into Metadata.pm
but should just go away when a better metadata structure is
adopted that deals with names and affiliations properly.

Must remember that there is at least one person one the archive 
who has only one name, this should clearly be considered the key name.

Code originally written by Christina Scovel, Simeon Warner Dec99/Jan00 
 2000-10-16 - separated. 
 2000-12-07 - added support for suffix
 2003-02-14 - get surname prefixes from arXiv::Filters::Index [Simeon]
 2007-10-01 - created test script, some tidying [Simeon]
 2018-05-21 - Translated from Perl to Python [Brian C.]
"""


def parse_author_affil(authors: str) -> List[List[str]]:
    """
    Takes an unparsed author line as input string and returns a pointer
    to an array of author and affiliation data.

    The array for each author will have at least three elements for
    keyname, firstname(s) and suffix. The keyname will always have content
    but the other stings might be empty stings if there is no firstname
    or suffix. Any additional elements after the first three are affiliations,
    there may be zero or more.

    Handling of prefix "XX collaboration" etc. is duplicated here and in
    L<arXiv::HTML::AuthorLink> -- it shouldn't be. Likely should just be here.

    This routine is just a wrapper around the two parts that first split
    the authors line into parts, and then back propagate the affiliations.
    The first part is to be used along for display where we do not want
    to back propagate affiliation information.

    :param authors: TeX string of authors from abs file or similar
    :return:
    Returns a structured set of data:
    author_list_ptr = [
        [ author1_keyname, author1_firstnames, author1_suffix, affil1, affil2 ] ,
        [ author2_keyname, author2_firstnames, author1_suffix, affil1 ] ,
        [ author3_keyname, author3_firstnames, author1_suffix ]
    ]
    """

    return parse_author_affil_back_propagate(**parse_author_affil_split(authors))


def parse_author_affil_split(author_line: str):
    """
    Take author line, tidy spacing and punctuation, and then split up into
    individual author an affiliation data. Has special cases to avoid splitting
    an initial collaboration name and records in $back_propagate_affiliation_to
    the fact that affiliations should not be back propagated to collaboration
    names.

    Does not handle multiple collaboration names.
    """

    author_list = []  # build result in here

    parts1 = split_authors(author_line)
    if not parts1 or len(parts1) == 0:
        return {'author_list': [], 'back_prop': 0}

    # Tidy: remove extra spaces and double commas
    parts1 = map(lambda n: n.lstrip().rstrip(), parts1)

    parts = []
    last = ''
    for p in parts1:
        if p == ',' and last == ',':
            next
        else:
            parts.append(p)
            last = p

    print('before filter')
    pprint.pprint(parts)

    parts = dropwhile(lambda x: x == ',', parts)  # get rid of commas at front
    parts = takewhile(lambda x: x != ',', parts)  # get rid of commas at back


    # Extract all names (all parts not starting with comma or paren)
    names = list(filter(lambda x: re.match('^[^](,]', x), parts))
    print('after filter')
    pprint.pprint(names)

    # General tidying first
    author_line = re.sub('\s\s+', ' ', author_line)  # also gets rid of CR

    #TODO the Below didn't seem to be used. go back to perl and check if it was really doing something
    # Now find the author names

    # Get rid of all parenthesis, just names will be left
    # name_line = author_line
    # # parens->comma, 2 levels
    # name_line = re.sub(r'\([^\(\)]*\)', ',', name_line)
    # name_line = re.sub(r'\([^\(\)]*\)', ',', name_line)
    # name_line = re.sub(r'\s+(and|&)', ',', name_line)  # and->comma
    # name_line = re.sub(r',\s*,', ',', name_line)  # multi->single commas
    # name_line = re.sub(r',\s*,', ',', name_line)
    # name_line = re.sub(r',\s*$', '', name_line)  # no comma at end
    # # Now have comma separated list of names, loop over them
    #
    # print('name_line')
    # pprint.pprint(name_line)

    # TODO end of unsed section ^^^^^

    #   # Special handling of collaboration etc. at start
    back_propagate_affilitions_to = 0

    # TODO BDC is this redundent to split_lines()?
    while len(names) > 0:
        m = re.match(r'^([a-z0-9]+\s+(collaboration|group|team))',
                     names[0], flags=re.IGNORECASE)
        if not m:
            break

        # Add to author list
        author_list.append([m.group(1), '', ''])
        back_propagate_affilitions_to += 1
        # Remove from names
        names.pop(0)
        # Also swallow and following comma or colon
        if len(names) > 0 and (names[0] == ',' or names[0] == ':'):
            names.pop(0)

    # TODO affiliations

    # Now see if we have a separate set of enumerated affiliations
    # This is indicated by finding '(\s*('

    #   my %enumaffils=();
    #   my $num;
    #   my $affils=undef;
    #   if ($author_line =~ /\(\s*\((.*)$/) {
    #     $affils=$1;
    #     $affils=~s/\s*\)\s*$//;
    #     # Now expect to have '1) affil1 (2) affil2 (3) affil3'
    #     foreach my $affil (split(/\(/,$affils)) {
    #       # Now expect `1) affil1 ', discard if no match
    #       if ($affil=~/^(\d+)\)\s*(\S.*\S)\s*$/) {
    #         $num=$1; $affil=$2;
    #         $affil =~ s/[\.,\s]*$//;
    #         $enumaffils{$num}=$affil;
    #       }
    #     }
    #   }

    print( 'names right before loop')
    pprint.pprint(names)

    # Now go through names in turn and try to get affiliations
    # to go with them
    for name in names:

        print('working on name ' + name)

        # Forget about `et al'
        if re.match(r'^\s*et\.\s+al\.?\s*', name, flags=re.IGNORECASE):
            next

        # Split name into keyname and firstnames/initials.
        #
        # Deal with different patterns in turn: prefixes, suffixes, plain
        # and single name.
        name = name.lstrip().rstrip()

        # add space after dot (except in TeX)
        name = re.sub(r'(?<!\\)\.(\S)', '. \g<1>', name)

        # Simple kludge to deal with two prefixes
        patterns = [('double-prefix',    r'^(.*)\s+('+PREFIX_MATCH+r')\s('+PREFIX_MATCH+r')\s(\S+)$'),
                    ('name-prefix-name', r'^(.*)\s+('+PREFIX_MATCH+')\s(\S+)$'),
                    ('name-name-prefix', r'^(.*)\s+(\S+)\s(I|II|III|IV|V|Sr|Jr|Sr\.|Jr\.)$'),
                    ('name-name',        r'^(.*)\s+(\S+)$'), ]

        pattern_matches = ((mtype, re.match(m, name, flags=re.IGNORECASE))
                           for (mtype, m) in patterns)

        (mtype, match) = next(((mtype, m)
                               for (mtype, m) in pattern_matches if m is not None), ('default', None))

        if mtype == 'double-prefix':
            s = '{} {} {}'.format(match.group(2), match.group(3), match.group(4))
            author_entry = [s, match.group(1), '']
        elif mtype == 'name-prefix-name':
            s = '{} {}'.format(match.group(2), match.group(3))
            author_entry = [s, match.group(1), '']
        elif mtype == 'name-name-prefix':
            author_entry = [match.group(2), match.group(1), match.group(3)]
        elif mtype == 'name-name':
            author_entry = [match.group(2), match.group(1), '']
        else:
            author_entry = [name, '', '']

        #     if ($n=~/^(.*)\s+($PREFIX_MATCH)\s($PREFIX_MATCH)\s(\S+)$/i) {
        #       $author_entry_ptr=["$2 $3 $4",$1,''];
        #     } elsif ($n=~/^(.*)\s+($PREFIX_MATCH)\s(\S+)$/i) {
        #       $author_entry_ptr=["$2 $3",$1,''];
        #     } elsif ($n=~/^(.*)\s+(\S+)\s(I|II|III|IV|V|Sr|Jr|Sr\.|Jr\.)$/i) {
        #       $author_entry_ptr=[$2,$1,$3];
        #     } elsif ($n=~/^(.*)\s+(\S+)$/) {
        #       $author_entry_ptr=[$2,$1,''];
        #     } else {
        #       $author_entry_ptr=[$n,'',''];
        #     }
        #     #
        #     # Find match for affiliation
        #     if ($author_line=~/\Q$name\E\s*\(([^\(\)]+)/ ) {
        #       $affils=$1;
        #       $affils=~s/^\s+//; $affils=~s/\s+$//;  #strip leading and trailing spaces
        #       # Now see if we have enumerated references
        #       # (just commas, digits, &, and)
        #       my $affils2=$affils; $affils2=~s/(&|and)/,/g;
        #       if ($affils2=~/^[\d,\s]+$/) {
        #         $affils2=~s/\s//g;   #zap spaces
        #         foreach my $affil (split(/,/,$affils2)) {
        #           if (defined $enumaffils{$affil}) {
        # 	          push(@$author_entry_ptr,$enumaffils{$affil});
        #           }
        #         }
        #       } else {
        #         push(@$author_entry_ptr,$affils);
        #       }
        #     }
        author_list.append(author_entry)

    return {'author_list': author_list, 'back_prop': back_propagate_affilitions_to}


def parse_author_affil_back_propagate(author_list: List[List[str]], back_prop: int) -> List[List[str]]:
    # TODO implement this
    return author_list


# Take the author list structure generated by parse_author_affil_split(..)
# and propagate affiliation information backwards to preceeding author
# entries where none was give. Stop before entry $back_prop to avoid
# adding affiliation information to collaboration names.

#   given, eg:
#     a.b.first, c.d.second (affil)
#   implies
#     a.b.first (affil), c.d.second (affil)
#   and in more complex cases:
#     a.b.first, c.d.second (1), e.f.third, g.h.forth (2,3)
#   implies
#     a.b.first (1), c.d.second (1), e.f.third (2,3), g.h.forth (2,3)

# =cut

# sub parse_author_affil_back_propagate {
#   my ($author_list_ptr,$back_propagate_affilitions_to)=@_;

#   my $last_affil_ptr=undef;
#   for (my $j=$#{$author_list_ptr};$j>=$back_propagate_affilitions_to;$j--) {
#     my $author_entry_ptr=$author_list_ptr->[$j];
#     if ($#{$author_entry_ptr}>2) {
#       # This author has affiliation, store ptr
#       $last_affil_ptr=$author_entry_ptr;
#     } elsif (defined $last_affil_ptr) {
#       # This author doesn't but a later one did => copy
#       for (my $k=3;$k<=$#{$last_affil_ptr};$k++) {
#         push(@$author_entry_ptr,$last_affil_ptr->[$k]);
#       }
#     }
#   }

#   return($author_list_ptr);
# }


# =head3 parse_author_affil_utf($author_line)

# Passes $author_line to parse_author_affil() and does TeX to UTF
# conversion on all elements of the resulting array. Output
# structure is the same but should be in UTF and not TeX.

# =cut

# sub parse_author_affil_utf {
#   my ($author_line)=@_;
#   my $author_list_ptr=parse_author_affil($author_line);

#   # Go through all fields and do in place TeX to UTF conversion
#   #
#   foreach my $author_entry_ptr (@$author_list_ptr) {
#     for (my $j=0;$j<=$#{$author_entry_ptr};$j++) {
#       $author_entry_ptr->[$j]=tex2UTF($author_entry_ptr->[$j]);
#     }
#   }
#   return($author_list_ptr);
# }


def split_authors(authors):
    """ Take and author line as a string and return a reference to a list of the
    different name and affiliation blocks. While this does normalize spacing
    and 'and', it is a key feature that the set of strings returned can be
    concatenated to reproduce the original authors line. This code thus
    provides a very graceful degredation for badly formatted authors lines,
    the text at least shows up."""

    # split authors field into blocks with boundaries of ( and )
    aus = re.split('(\(|\))', authors)

    blocks = []
    if len(aus) == 1:
        blocks.append(authors)
    else:
        c = ''
        depth = 0
        for bit in aus:
            if bit == '(':  # track open parentheses
                depth += 1
                if depth == 1:
                    blocks.append(c)
                    c = '('
                else:
                    c = c + bit
            elif bit == ')':  # track close parentheses
                depth -= 1
                c = c + bit
                if depth != 0:
                    next
                blocks.append(c)
                c = ''
            else:
                c = c + bit
        if c:
            blocks.append(c)

    list = []

    for block in blocks:
        block = re.sub('\s+', ' ', block)
        if re.match('^\(', block):  # it is a comment
            list.append(block)
        else:  # it is a name
            block = re.sub(',?\s+(and|\&)\s', ',', block)
            names = re.split('(,|:)\s*', block)
            for name in names:
                if not name:
                    next
                name = name.rstrip().lstrip()
                if name:
                    list.append(name)

    # Recombine suffixes that were separated with a comma
    parts = []
    for p in list:
        if re.match('^(Jr\.?|Sr\.?\[IV]{2,})&', p) \
                and len(parts) >= 2 \
                and parts[-1] == ',' \
                and not re.match('\)$', parts[-2]):
            separator = parts.pop()
            last = parts.pop()
            p = p.format("{}{} {}", last, separator, p)
        parts.append(p)

    return parts
