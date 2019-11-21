#!/usr/bin/env python3

## ## "Common Format" Automated Check
##
## ### Requirements
## 1. Released ontology **must** be in RDF/XML format
##
## ### Implementation
## Current implementation attempts to load the ontology using OWL API. If the ontology is loaded, it is assumed that it is in a good format, although it may not be RDF/XML. For large ontologies, the ontology is a valid format (either RDF/XML or Turtle) if it can be [loaded with Jena](http://robot.obolibrary.org/query#executing-on-disk) to run the ROBOT report over.

import dash_utils
from dash_utils import format_msg


def is_common_format(ontology):
    """Check FP 2 - Common Format.

    Args:
        ontology (OWLOntology): ontology object

    Return:
        PASS if OWLOntology is not None, ERROR otherwise.
    """
    if ontology is None:
        return {'status': 'ERROR', 'comment': 'Unable to load ontology'}
    else:
        return {'status': 'PASS'}


def big_is_common_format(good_format):
    """Check FP 2 - Common Format on large ontologies

    Args:
        good_format (bool): True if ontology could be parsed by Jena

    Return:
        PASS if good_format, ERROR otherwise.
    """
    if good_format is None:
        return {'status': 'INFO',
                'comment': 'Unable to load ontology (may be too large)'}
    elif good_format is False:
        return {'status': 'ERROR',
                'comment': 'Unable to parse ontology'}
    else:
        return {'status': 'PASS'}
