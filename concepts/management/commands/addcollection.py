import argparse

from concepts.models import *
from conllu import parse_incr
from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm

class Command(BaseCommand):
    help = "Load a collection into the database."

    def add_arguments(self, parser):

        parser.add_argument('--name', type=str, default='Default')
        parser.add_argument('filename', type=argparse.FileType('r'))

    def handle(self, *args, **kwargs):

        collection = Collection.objects.get_or_create(
                name=kwargs['name'][:500],
        )[0]
        current_document = None
        for sentence in tqdm(parse_incr(kwargs['filename'])):
            if 'doc_id' in sentence.metadata:
                document = Document(
                    title=sentence.metadata.get('doc_title', "Untitled")[:400],
                    url=sentence.metadata['doc_url'],
                    collection=collection,
                )
                document.save()
                current_document = document

            if current_document is None:
                print("No document available.")
                continue

            sentence_model = Sentence(
                document=current_document,
                text=sentence.metadata['text'],
            )
            sentence_model.save()

            lemmas = []

            for token in sentence:
                if token['feats']:
                    features = '|'.join('%s=%s' % (key, value) for (key, value) in
                            token['feats'].items())
                else:
                    features = ""
                if token['misc']:
                    misc = '|'.join('%s=%s' % (key, value) for (key, value) in
                            token['misc'].items())
                else:
                    misc = ""
                token_model = Token(
                    sentence=sentence_model,
                    index=int(token['id']),
                    form=token.get('form', '')[:400],
                    lemma=token.get('lemma', '')[:400],
                    upos=token.get('upos', '')[:8],
                    xpos=token.get('xpos', '')[:8],
                    features=features[:400],
                    head=int(token['head']) if token['head'] else None,
                    deprel=token.get('deprel', '')[:400],
                    misc=misc[:400],
                )
                if token_model.lemma:
                    lemmas.append(token_model.lemma)
                token_model.save()

            sentence_model.lemmas = ' '.join(lemmas)
            sentence_model.save()
