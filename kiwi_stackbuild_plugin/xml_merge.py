# Copyright (c) 2021 SUSE Linux GmbH.  All rights reserved.
#
# This file is part of kiwi-stackbuild.
#
# kiwi is free software: you can redistribute it and/or modify
# it under the terms owf the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# kiwi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kiwi.  If not, see <http://www.gnu.org/licenses/>
#
from lxml import etree
import os
import glob
import logging

from kiwi.utils.sync import DataSync
from kiwi.defaults import Defaults
from kiwi.exceptions import (
    KiwiConfigFileNotFound
)

from kiwi_stackbuild_plugin.defaults import StackBuildDefaults
from kiwi_stackbuild_plugin.exceptions import (
    KiwiStackBuildPluginSchemaValidationFailed
)

log = logging.getLogger('kiwi')


class XMLMerge:
    """
    ***Implements the class to handle stackbuild schema and descriptions.
    Converts a given stackbuild description into a full KIWI description
    based on the stashed KIWI description***

    :param str description_dir: the folder path contianing the stackbuild
        description XML
    """
    def __init__(self, description_dir: str):
        self.description = self._find_description_file(description_dir)
        self.description_dir = description_dir
        self.description_tree = etree.parse(self.description)

    def is_stackbuild_description(self) -> bool:
        """
        Returns True if the root element includes the 'stackbuild="true"'
        attribute

        :returns: True if the stackbuild attribute is found, False otherwise

        :rtype: bool
        """
        root = self.description_tree.getroot()
        if 'stackbuild' in root.attrib and root.attrib['stackbuild'] == 'true':
            return True
        return False

    def validate_schema(self) -> None:
        """
        Runs the stackbuild schema validation, raises a
        'KiwiStackBuildPluginSchemaValidationFailed' exception
        if the validation fails
        """
        schema_file = StackBuildDefaults.get_schema_file()
        log.info('Loading stack build schema')
        schema_tree = etree.parse(schema_file)
        root = schema_tree.getroot()
        kiwi_schema = Defaults.get_schema_file()
        rngns = root.nsmap['rng']
        for child in root.iter():
            if child.tag == f'{{{rngns}}}include':
                log.debug(f'Setting stack build schema to include kiwi schema: {kiwi_schema}')
                child.set('href', kiwi_schema)
                break

        relaxng = etree.RelaxNG(schema_tree)
        validation_rng = relaxng.validate(self.description_tree)

        if not validation_rng:
            raise KiwiStackBuildPluginSchemaValidationFailed(f'Failed to validate schema: {relaxng.error_log}')

    def merge_description(self, derived_from_dir: str, target_dir: str) -> None:
        """
        Merges a stackbuild description with the KIWI description found
        in the given path. The original description is copied to the target
        directory and then the stackbuild description is applied on top.

        :param str derived_from_dir: path of the KIWI description to update
            with the stackbuild description
        :param str target_dir: path where the merged description is stored
        """
        sync = DataSync(os.path.join(derived_from_dir, ''), target_dir)
        sync.sync_data(options=Defaults.get_sync_options())

        derived_from = self._find_description_file(target_dir)
        work_tree = etree.parse(derived_from)

        self._image_merge(work_tree)
        self._description_replace(work_tree)
        self._preferences_merge(work_tree)
        self._profiles_merge(work_tree)
        self._users_merge(work_tree)
        self._drop_in_sections(work_tree)

        sync = DataSync(f'{self.description_dir}/', target_dir)
        sync.sync_data(options=Defaults.get_sync_options())

        work_tree.write(derived_from, pretty_print=True)

    def _description_replace(self, work_tree):
        """
        Replaces the description section of the original KIWI description
        with the one provided by the stackbuild description if any

        :param work_tree: parsed etree of the original KIWI description
            to modify
        """
        self._replace_unique_element_by_xpath(
            work_tree, '/image/description[@type="system"]'
        )

    def _drop_in_sections(self, work_tree):
        """
        Adds all sections in stackbuild description to the given etree
        except for 'description', 'preferences' and 'profiles' which require
        an specific merge logic

        :param work_tree: parsed etree of the original KIWI description
            to modify
        """
        root = self.description_tree.getroot()
        w_root = work_tree.getroot()
        exclude_list = ['description', 'preferences', 'profiles']
        for item in root:
            if item.tag not in exclude_list:
                w_root.append(item)

    def _replace_unique_element_by_xpath(self, work_tree, xpath):
        """
        Replaces an element found in the current stackbuild etree to the
        given etree. The element is refrenced and located with a given xpath

        :param work_tree: parsed etree of the original KIWI description
            to modify
        :param str xpath: the xpath to identify and locate the element to replace

        :return: true or false

        :rtype: bool
        """
        replacement = self.description_tree.xpath(xpath)
        if len(replacement):
            obsolete = work_tree.xpath(xpath)
            if len(obsolete):
                parent = obsolete[0].getparent()
                parent.replace(obsolete[0], replacement[0])
                return True
        return False

    def _profiles_merge(self, work_tree):
        """
        Appends or replaces the profiles included within the stackbuild description
        to the given working elementTree based on the original KIWI description

        :param work_tree: parsed etree of the original KIWI description
            to modify
        """
        profiles = self.description_tree.xpath('/image/profiles')
        if len(profiles):
            w_profiles = work_tree.xpath('/image/profiles')
            if len(w_profiles):
                for profile in profiles[0]:
                    name = profile.attrib['name']
                    if not self._replace_unique_element_by_xpath(
                        work_tree,
                        f'/image/profiles/profile[@name=\'{name}\']'
                    ):
                        w_profiles[0].append(profile)
            else:
                work_tree.getroot().append(profiles[0])

    def _preferences_merge(self, work_tree):
        """
        Combines the preferences available in the stackbuild description
        with the originial KIWI description. Stackbuild preferences are simply
        appended or combined to the original depending on attribures set
        of each preferences element. If a stackbuild preferences element includes
        the same set of attributes of another prefences element present in the
        original description they are combined. Otherwise the stackbuild
        element is simply appended to the original KIWI description.

        :param work_tree: parsed etree of the original KIWI description
            to modify
        """
        preferences = self.description_tree.xpath('/image/preferences')
        for preferences_set in preferences:
            pref = self._element_with_attributes_exists(
                work_tree, '/image/preferences', preferences_set.attrib
            )
            if pref is None:
                work_tree.getroot().append(preferences_set)
            else:
                self._merge_preferences_set(preferences_set, pref)

    def _element_with_attributes_exists(self, tree, e_path, attributes):
        """
        Check if it exists an elemental in the given tree matches the given
        path and attributes. Returns the first matching element or None if
        there is no match.

        :param tree: etree to evaluate
        :param str e_path: the path used to match elements
        :param attributes: the set of attributes to match

        :return: The first etree element matching with the given path
            and attributes. Returns None if no match
        """
        attr_list = [f'@{k}=\'{v}\'' for k, v in attributes.items()]
        constraints = '[not(@*)]'
        if attr_list:
            constraints = '[' + ' and '.join(attr_list) + ']'
        item = tree.xpath(e_path + constraints)
        if len(item):
            return item[0]
        return None

    def _merge_preferences_set(self, pref_setA, pref_setB):
        """
        Combines the two given preferences sets. A is applied over
        B. Any child element in A that is missing B is appended to B. Any
        child element in A that is already existing in B is replace in B
        with the contents of A. The rule has a couple of exceptions:

          * 'type' elements are only replaced if they also match the image type
          * 'showlicense' elements are only appended, they can't be replaced

        :param pref_setA: a preferences element tree object
        :param pref_setB: a preferences element tree object
        """
        for child in pref_setA:
            if child.tag == 'showlicense':
                pref_setB.append(child)
                continue
            if child.tag == 'type':
                b_type = self._element_with_attributes_exists(
                    pref_setB, './type', {'image': child.attrib['image']}
                )
                if b_type is None:
                    pref_setB.append(child)
                else:
                    pref_setB.replace(b_type, child)
                continue
            b_child = pref_setB.xpath(f'./{child.tag}')
            if len(b_child):
                pref_setB.replace(b_child[0], child)
            else:
                pref_setB.append(child)

    def _find_description_file(self, description_directory):
        """
        Finds a description XML file in given directory

        :param str description_directory: the directory path to evaluate

        :return: the found XML description file

        :rtype: str
        """
        config_file = description_directory + '/config.xml'
        log.debug(f'looking for XML description file {config_file}')
        if os.path.exists(config_file):
            return config_file

        log.debug(f'{config_file} not found...')
        glob_match = description_directory + '/*.kiwi'
        log.debug(f'looking for XML description file {glob_match}')
        for config_file in sorted(glob.iglob(glob_match)):
            return config_file

        raise KiwiConfigFileNotFound(
            'no XML description found in %s' % description_directory
        )

    def _image_merge(self, work_tree):
        """
        Replaces or adds the stackbuild image attributes to the
        original KIWI description image root element.

        :param work_tree: parsed etree of the original KIWI description
            to modify
        """
        img = self.description_tree.getroot()
        w_root = work_tree.getroot()
        if 'displayname' in img.attrib:
            w_root.attrib['displayname'] = img.attrib['displayname']
        if 'id' in img.attrib:
            w_root.attrib['id'] = img.attrib['id']
        if 'name' in img.attrib:
            w_root.attrib['name'] = img.attrib['name']

    def _users_merge(self, work_tree):
        """
        Appends or replaces users from the stackbuild description to the
        original KIWI description. The criteria to replace users is based on
        users name. If a user name defined in stackbuild description already
        exists in the KIWI description this gets replaced.

        :param work_tree: parsed etree of the original KIWI description
            to modify
        """
        users = self.description_tree.xpath('/image/users')
        for users_sec in users:
            usrs_match = self._element_with_attributes_exists(
                work_tree, '/image/users', users_sec.attrib
            )
            if usrs_match is None:
                work_tree.getroot().append(users_sec)
            else:
                for user in users_sec:
                    usr_match = self._element_with_attributes_exists(
                        usrs_match, './user', {'name': user.attrib['name']}
                    )
                    if usr_match is None:
                        usrs_match.append(user)
                    else:
                        usrs_match.replace(usr_match, user)
