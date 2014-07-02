#!/usr/bin/python
# Copyright (c) 2014, Red Hat, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the
#    distribution.
# 3. Neither the name of the Red Hat nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Authors:  Michal Srb <msrb@redhat.com>

import sys

from artifact import AbstractArtifact, ArtifactFormatException
from exclusion import Exclusion
from pomreader import POMReader
from lxml.etree import Element, SubElement, tostring


class Dependency(AbstractArtifact):

    def __init__(self, groupId, artifactId, extension="", classifier="",
                 version="", scope="", optional=None, exclusions=set()):
        self.groupId = groupId.strip()
        self.artifactId = artifactId.strip()
        self.extension = extension.strip() or "jar"
        self.classifier = classifier.strip()
        self.version = version.strip()
        self.scope = scope.strip()
        self.optional = optional
        self.exclusions = exclusions

    def get_xml_element(self, root="dependency"):
        """
        Return XML Element node representation of the Artifact
        """
        root = AbstractArtifact.get_xml_element(self, root)

        if self.scope:
            item = SubElement(root, "scope")
            item.text = self.scope

        if self.optional is not None:
            item = SubElement(root, "optional")
            item.text = str(self.optional).lower()

        if self.exclusions:
            exc_root = Element("exclusions")
            for e in self.exclusions:
                exc_root.insert(len(exc_root), e.get_xml_element())
            root.insert(len(root), exc_root)

        return root

    @classmethod
    def from_xml_element(cls, xmlnode):
        """
        Create Dependency from xml.etree.ElementTree.Element as contained
        within pom.xml.
        """

        parts = {'groupId': '',
                 'artifactId': '',
                 'type': '',
                 'classifier': '',
                 'version': '',
                 'scope': '',
                 'optional': None}

        parts = POMReader.find_parts(xmlnode, parts)

        if not parts['groupId'] or not parts['artifactId']:
            raise ArtifactFormatException(
                "Empty groupId or artifactId encountered. "
                "This is a bug, please report it!")

        if parts['optional'] is not None:
            if parts['optional'] == "false":
                parts['optional'] = False
            elif parts['optional'] == "true":
                parts['optional'] = True

        # exclusions
        excnodes = xmlnode.findall("{*}exclusions/{*}exclusion")

        exclusions = set()
        for e in [Exclusion.from_xml_element(x) for x in excnodes]:
            exclusions.add(e)

        return cls(parts['groupId'], parts['artifactId'], parts['type'],
                   parts['classifier'], parts['version'], parts['scope'],
                   parts['optional'], exclusions)

    @classmethod
    def from_mvn_str(cls, mvnstr):
        """
        Create Dependency from Maven-style definition

        The string should be in the format of:
           groupId:artifactId[:extension[:classifier]][:version]

        Where last part is always considered to be version unless empty
        """
        p = cls.get_parts_from_mvn_str(mvnstr)
        return cls(p['groupId'], p['artifactId'], p['extension'],
                   p['classifier'], p['version'])