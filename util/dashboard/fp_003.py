#!/usr/bin/env python3

## ## "URIs" Automated Check
##
## ### Requirements
## 1. All entities in the ontology namespace **must** use an underscore to separate the namespace and local ID.
## 2. The local ID *should* not be semantically significant, and *should* be numeric.
##
## ### Implementation
## All entity IRIs are retrieved from the ontology, excluding annotation properties. Annotation properties may use hashtags and words due to legacy OBO conversions for subset properties. All other IRIs are checked if they are in the ontology's namespace. If the IRI begins with the ontology namespace, the next character must be an underscore. If not, this is an error. The IRI is also compared to a regex pattern to check if the local ID after the underscore is numeric. If not, this is a warning.

import dash_utils
import os
import re

from dash_utils import format_msg

iri_pattern = r'http:\/\/purl\.obolibrary\.org\/obo\/%s_[0-9]{1,9}'
owl_deprecated = 'http://www.w3.org/2002/07/owl#deprecated'

error_msg = '{0} invalid IRIs'
warn_msg = '{0} warnings on IRIs'


def has_valid_uris(robot_gateway, namespace, ontology):
    """Check FP 3 - URIs.

    This check ensures that all ontology entities follow NS_LOCALID.
    Annotation properties are not checked, as many are in legacy OBO format
    and use #LOCALID. Obsolete entities are also ignored. LOCALID should
    not be semantically meaningful, therefore numeric IDs should be used.
    If the IRI start with the namespace, but does not use `_`, it will be
    added to errors. If IRI starts with NS, uses _, but does not match the
    IRI pattern with numbers, it will be added to warnings.

    Args:
        robot_gateway (Gatway):
        namespace (str): ontology ID
        ontology (OWLOntology): ontology object

    Return:
        INFO if ontology is None. ERROR if any errors, WARN if any warns, PASS
        otherwise.
    """
    if not ontology:
        return {'status': 'INFO', 'comment': 'Unable to load ontology'}

    entities = robot_gateway.OntologyHelper.getEntities(ontology)
    error = []
    warn = []

    for e in entities:
        if e.isOWLAnnotationProperty():
            # allow legacy annotation properties
            continue

        # check if the entity is obsolete
        obsolete = False
        for ann in ontology.getAnnotationAssertionAxioms(e.getIRI()):
            if ann.getProperty().getIRI().toString() == owl_deprecated:
                # check if the entity is obsolete
                obsolete = dash_utils.is_obsolete(ann)
        # if so, just ignore it
        if obsolete:
            continue

        iri = e.getIRI().toString().lower()
        check = check_uri(namespace, iri)
        if check == 'ERROR':
            error.append(iri)
        elif check == 'WARN':
            warn.append(iri)

    return save_invalid_uris(namespace, error, warn)


def big_has_valid_uris(namespace, file):
    """Check FP 3 - URIs on a big ontology.

    This check ensures that all ontology entities follow NS_LOCALID.
    Annotation properties are not checked, as many are in legacy OBO format
    and use #LOCALID. Obsolete entities are also ignored. LOCALID should
    not be semantically meaningful, therefore numeric IDs should be used.
    If the IRI start with the namespace, but does not use `_`, it will be
    added to errors. If IRI starts with NS, uses _, but does not match the
    IRI pattern with numbers, it will be added to warnings.

    Args:
        namespace (str): ontology ID
        file (str): path to ontology file

    Return:
        INFO if ontology IRIs cannot be parsed. ERROR if any errors, WARN if
        any warns, PASS otherwise.
    """
    error = []
    warn = []

    prefixes = True
    header = True
    valid = False

    # prefixes
    owl = None
    rdf = None

    with open(file, 'r') as f:
        # TODO: rework to exclude deprecated classes
        for line in f:
            if 'Ontology' and 'about' in line:
                if not owl and not rdf:
                    # did not find OWL and RDF - end now
                    return {'status': 'INFO',
                            'comment': 'Unable to parse ontology'}

                # end prefixes
                prefixes = False
                # valid ontology to parse (found Ontology declaration)
                valid = True

                if line.strip().endswith('/>'):
                    # no ontology annotations - end header now
                    header = False

            elif prefixes and 'http://www.w3.org/2002/07/owl#' in line:
                # set the OWL prefix
                owl = dash_utils.get_prefix(line)

            elif prefixes and 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'\
                    in line:
                # set the RDF prefix
                rdf = dash_utils.get_prefix(line)

            elif header and '</{0}:Ontology>'.format(owl) in line:
                # end of Ontology annotations = end of header
                header = False

            elif not header and '{0}:about'.format(rdf) in line \
                    and '{0}:AnnotationProperty'.format(owl) not in line:
                # non-AP entity found - check the IRI
                iri = dash_utils.get_resource_value(line).lower()
                check = check_uri(namespace, iri)
                if check == 'ERROR':
                    error.append(iri)
                elif check == 'WARN':
                    warn.append(iri)

    if not valid:
        # not valid ontology
        return {'status': 'INFO',
                'comment': 'Unable to parse ontology'}

    return save_invalid_uris(namespace, error, warn)


def check_uri(namespace, iri):
    """Check if a given IRI is valid.

    Args:
        namespace (str): ontology ID
        iri (str): IRI to check

    Return:
        ERROR, WARN, or True if passing.
    """
    pattern = iri_pattern % namespace
    if iri == 'http://purl.obolibrary.org/obo/{0}.owl'.format(namespace):
        # ignore ontology IRI as it may be used in the ontology
        return True
    if iri.startswith(namespace):
        # all NS IRIs must follow NS_
        if not iri.startwith(namespace + '_'):
            return 'ERROR'
        # it is recommended to follow NS_NUMID
        elif not re.match(pattern, iri, re.IGNORECASE):
            return 'WARN'
    return True


def save_invalid_uris(ns, error, warn):
    """Save invalid (error or warning) IRIs to a report file
    (reports/dashboard/*/fp3.tsv).

    Args:
        ns (str): ontology ID
        error (list): list of ERROR IRIs
        warn (list): list of WARN IRIs

    Return:
        ERROR or WARN with detailed message, or PASS if no errors or warnings.
    """
    if len(error) > 0 or len(warn) > 0:
        file = 'build/dashboard/{0}/fp3.tsv'.format(ns)
        with open(file, 'w+') as f:
            for e in error:
                f.write('ERROR\t{0}\n'.format(e))
            for w in warn:
                f.write('WARN\t{0}\n'.format(w))

    if len(error) > 0 and len(warn) > 0:
        return {'status': 'ERROR',
                'comment': ' '.join([error_msg.format(len(error)),
                                     warn_msg.format(len(warn))])}
    elif len(error) > 0:
        return {'status': 'ERROR',
                'comment': error_msg.format(len(error))}
    elif len(warn) > 0:
        return {'status': 'ERROR',
                'comment': warn_msg.format(len(warn))}
    return {'status': 'PASS'}
