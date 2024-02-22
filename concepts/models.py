from django.db import models
from django.utils.translation import gettext as _

class Author(models.Model):
    """
    Represents the author of one or more documents in a corpus.
    """

    #: The author's first name.
    first_name = models.CharField(_("first name"), max_length=100, blank=False,
            null=False)

    #: The author's last name. 
    last_name = models.CharField(_("last name"), max_length=1000, blank=True)

class Collection(models.Model):
    """
    Represents a collection of documents in the corpus. Collections can be
    thought of as high-level contexts in which terms may appear; it is more
    likely that the usage of a term will vary form context to context rather
    than from document to document.
    """

    #: The human-readable name of the collection.
    name = models.CharField(_("name"), max_length=500, blank=False, null=False,
            unique=True)

    #: A free-form description of the collection.
    description = models.TextField(_("description"), blank=True)

    #: The priority of this collection; higher-priority collections are
    #: displayed first.
    priority = models.IntegerField(_('priority'), null=False, default=0)

    def __str__(self):

        return self.name

class Document(models.Model):
    """
    Represents a single document in the corpus. Documents are not further
    subdivided into sections or subsections.
    """

    #: The title of the document.
    title = models.CharField(_("title"), max_length=500, blank=False,
            null=False)

    #: The authors of the document.
    authors = models.ManyToManyField('Author', verbose_name=_("authors"),
            blank=True)

    #: A URL to the original document.
    url = models.URLField(_("URL"), blank=True)

    #: The document's publication date.
    pub_date = models.DateField(_("publication date"), blank=True, null=True)

    #: The colleciton this document appears in.
    collection = models.ForeignKey('Collection', verbose_name=_("collection"),
            blank=False, null=False, on_delete=models.CASCADE)

    def __str__(self):

        return self.title

class Sentence(models.Model):
    """
    Represents a normalized sentence within a document.
    """

    #: The document containing this sentence.
    document = models.ForeignKey('Document', verbose_name=_("document"),
            on_delete=models.CASCADE)

    #: The text of the sentence.
    text = models.TextField(_("text"), blank=False)

    #: The list of lemmas in the sentence.
    lemmas = models.TextField(_("lemmas"), blank=False)

class Token(models.Model):
    """
    Represents a single token in a document.
    """

    #: The sentence that this token appears in.
    sentence = models.ForeignKey('Sentence', verbose_name=_("sentence"),
            on_delete=models.CASCADE, related_name='tokens')

    #: The token's index in the sentence.
    index = models.IntegerField(_("index"))

    #: The token's form.
    form = models.CharField(_("form"), max_length=500)

    #: The token's lemma.
    lemma = models.CharField(_("lemma"), max_length=500)

    #: The token's course-grained POS tag.
    upos = models.CharField(_("UPOS"), max_length=10)

    #: The token's fine-grained POS tag.
    xpos = models.CharField(_("XPOS"), max_length=10)

    #: The token's features.
    features = models.CharField(_("features"), max_length=500, blank=True)

    #: The index of the token's head.
    head = models.IntegerField(_("head"), null=True)

    #: The token's relation to its head.
    deprel = models.CharField(_("deprel"), max_length=500, blank=True)

    #: Miscellaneous features of the word.
    misc = models.CharField(_("misc"), max_length=500, blank=True)

class Term(models.Model):
    """
    Represents a well-formed term. 
    """

    #: The normalized form of the term.
    term = models.CharField(_("term"), max_length=500, blank=False, null=False)

class Definition(models.Model):
    """
    A definition of a term from a particular source.
    """

    #: The term being defined.
    term = models.ForeignKey('Term', verbose_name=_("term"), null=False,
            on_delete=models.CASCADE)

    #: The name of this term, according to the source.
    source_name = models.CharField(_("source name"), max_length=500, blank=False, null=False)

    #: The definition of the term.
    definition = models.TextField(_("definition"), blank=False, null=False)

    #: The source of the definition.
    source = models.ForeignKey('Source', verbose_name=_("source"), null=True,
            on_delete=models.SET_NULL)

    #: The URL to the definition of this term in the given source.
    source_url = models.URLField(_("URL"), blank=True)

    #: The date and time the definition was accessed from the source.
    accessed = models.DateTimeField(_("accessed"), blank=True, null=True,
            auto_now=True)

class Source(models.Model):
    """
    An external source of information about terms and their definitions.
    """

    #: The name of the data source.
    name = models.TextField(_("name"), max_length=500, blank=False)

    #: The home page of this data source.
    home_page = models.URLField(_("home page"), blank=True)

class SourceLink(models.Model):
    """
    Represents a source's information about a particular term.
    """

    #: The term being linked.
    term = models.ForeignKey('Term', verbose_name=_("term"),
            on_delete=models.CASCADE)

    #: The source linking this term.
    source = models.ForeignKey('Source', verbose_name=_("source"),
            on_delete=models.CASCADE)

    #: A link to the source's information about the given term.
    link = models.URLField(_("link"), blank=False)

class Query(models.Model):
    """
    Represents the set of queries that have been made. 
    """

    query = models.TextField(_("query"), blank=False, null=False)

    count = models.IntegerField(_("count"), blank=False, null=False, default=0)
