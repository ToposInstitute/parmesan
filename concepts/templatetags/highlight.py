import re

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

regex = re.compile(r'(\\n)|(\\s)|(\\r)')

@register.simple_tag
def highlight(sentence, query):

    tokens = sentence.tokens.order_by('index')
    query_components = query.split()
    token_span = ""
    to_mark = 0
    for start_index in range(len(tokens)):
        token = tokens[start_index]
        token_form = regex.sub(' ', token.form)
        if to_mark > 0:
            token_span += token_form
            to_mark -= 1
            if to_mark == 0:
                token_span += "</mark>"
            if 'SpaceAfter=No' not in token.misc:
                token_span += " "
            continue
        
        matches = True
        for i in range(len(query_components)):
            component = query_components[i]
            if tokens[start_index + i].lemma != component:
                matches = False
                to_mark = 0
                break

        if matches:
            to_mark = len(query_components) - 1
            token_span += "<mark>"
        token_span += token_form
        if matches and to_mark == 0:
            token_span += "</mark>"
        if 'SpaceAfter=No' not in token.misc:
            token_span += " "

    return mark_safe(token_span.strip())
