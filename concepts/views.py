from bs4 import BeautifulSoup
from django.conf import settings
from django.db.models import Case, Count, F, IntegerField, Q, Sum, Value, When
from django.views.generic import TemplateView
from itertools import groupby
from urllib.parse import quote_plus
from .models import *
from .forms import SearchForm

import requests
import spacy
import time

#nlp = spacy.load('en_core_web_trf')

ENDPOINT = "https://query.wikidata.org/sparql"
HEADERS = {
    'User-Agent': 'parmesan/0.2',
}

# MINUS instance of Wikimedia category
# MINUS subclass of concrete object
# MINUS subclass of physical object
# MINUS subclass of geographic region
# MINUS subclass of artistic concept
# MINUS subclass of geographic location
# MINUS subclass of human behavior
# MINUS subclass of point of time
# MINUS subclass of time interval
# MINUS subclass of currency
sparql_query = """
SELECT distinct ?item ?itemLabel ?itemDescription WHERE {
    {?item rdfs:label "%s"@en.} UNION
    {?item skos:altLabel "%s"@en.}
    MINUS { ?item wdt:P31 wd:Q4167836 }
    MINUS { ?item wdt:P279 wd:Q4167836 }
    MINUS { ?item wdt:P279 wd:Q4406616 }
    MINUS { ?item wdt:P279 wd:Q223557 }
    MINUS { ?item wdt:P279 wd:Q82794 }
    MINUS { ?item wdt:P279 wd:Q63539947 }
    MINUS { ?item wdt:P279 wd:Q2221906 }
    MINUS { ?item wdt:P279 wd:Q3769299 }
    MINUS { ?item wdt:P279 wd:Q186408 }
    MINUS { ?item wdt:P279 wd:Q186081 }
    MINUS { ?item wdt:P279 wd:Q8142 }
    SERVICE wikibase:label {
        bd:serviceParam wikibase:language "en" .
    }
}
"""

#class Link:
#
#    def __init__(self, name, source, url, description):
#
#        self.name = name
#        self.source = source
#        self.url = url
#        self.description = description

def extract_definition(response):

    soup = BeautifulSoup(response.text, 'lxml')
    revision = soup.find(id="revision")
    paragraph = revision.find("p").get_text()

    return paragraph

def get_nlab(query):

    nlab_source = Source.objects.get_or_create(
        name="nLab",
    )[0]

    links = Definition.objects.filter(
        term__term=query,
        source=nlab_source,
    )

    if links.count() > 0:
        print("Using cached nLab")
        return links

    try:
        url = "http://ncatlab.org/nlab/show/%s" % quote_plus(query)
        response = requests.get(url)
        if response.status_code == 200:
            term = Term(term=query)
            term.save()
            definition = Definition(
                term=term,
                source_name=query,
                definition=extract_definition(response),
                source=nlab_source,
                source_url=url,
            )
            definition.save()
            return [definition]
        else:
            return []
    except Exception as err:
        print("An error occurred.")
        print(err)
        return []

def get_wikidata(query):

    wikidata_source = Source.objects.get_or_create(
        name="Wikidata",
    )[0]

    links = Definition.objects.filter(
        term__term=query,
        source=wikidata_source,
    )

    if links.count() > 0:
        print("Using cache")
        return links

    try:
        while True:
            print("Querying Wikidata")
            result = requests.post(
                ENDPOINT,
                data={'query': sparql_query % (query, query), 'format': 'json'},
                headers=HEADERS,
            )
            if result.status_code == 429:
                print("Too many requests. Retrying.")
                time.sleep(result.headers['retry-after'])
                continue
            break

        json = result.json()
        links = []
        for item in json['results']['bindings']:
            link = item['item']['value']
            description = item.get('itemDescription', {"value": ""})['value']
            label = item['itemLabel']['value']
            term = Term(term=label)
            term.save()
            definition = Definition(
                term=term,
                source_name=label,
                definition=description,
                source=wikidata_source,
                source_url=link,
            )
            #definition.save()
            links.append(definition)
        return links
    except Exception as err:
        print("An exception occurred.")
        print(err)
        return []

class IndexView(TemplateView):

    template_name = 'concepts/index.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context['form'] = SearchForm()

        return context

class QueryResults:

    def __init__(self, documents, query):

        self.documents = documents
        self.query = query

    def get_documents(self):

        regex = settings.SEARCH_REGEX

        for document in self.documents:

            sentences = Sentence.objects.filter(
                document=document,
                lemmas__iregex=regex % self.query,
            )[:10]

            yield QueryResult(
                document,
                sentences,
                self.query,
            )

class QueryResult:

    def __init__(self, document, sentences, query):

        self.document = document
        self.sentences = sentences
        self.query = query

class SearchView(TemplateView):

    template_name = 'concepts/results.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        
        regex = settings.SEARCH_REGEX

        form = SearchForm(self.request.GET)
        if form.is_valid():
            collections = form.cleaned_data['collections']
            query = form.cleaned_data['query']
            query_record = Query.objects.get_or_create(
                query=query,
            )[0]
            query_record.count += 1
            query_record.save()
            #parsed_query = nlp(query)
            #lemmatized_query = ' '.join([token.lemma_ for token in
            #    query])
            results = []
            total_count = 0
            for collection in collections:
                documents = Document.objects.filter(
                    sentence__lemmas__iregex=regex % query,
                    collection=collection,
                ).distinct().annotate(
                    num_sentences=Count("sentence", filter=Q(sentence__lemmas__iregex=regex % query)),
                ).annotate(
                    title_match=Case(
                        When(title__iregex=regex % query, then=Value(10)),
                        default=Value(0),
                        output_field=IntegerField(),
                    ),
                ).annotate(
                    total_score=F('num_sentences') + F('title_match'),
                ).order_by('-total_score')
                count = documents.count()
                total_count += count
                results.append((collection, QueryResults(documents[:10],
                    query), count))

            context['links'] = list(get_wikidata(query)[:5]) + list(get_nlab(query)[:5])
            context['results'] = results
            context['form'] = form
            context['query'] = query
            context['total_count'] = total_count

            return context
        else:
            context['results'] = []
            context['form'] = form
            context['query'] = "No query given"
            context['total_count'] = 0

            return context

class AboutView(TemplateView):

    template_name = 'concepts/about.html'
