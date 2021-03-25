# Copyright (c) 2021 SUSE Linux GmbH.  All rights reserved.
#
# This file is part of kiwi.
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
import copy
import os
import glob

# project
from kiwi.utils.sync import DataSync
from kiwi.defaults import Defaults
from kiwi.exceptions import (
    KiwiConfigFileNotFound
)

class XMLMerge:

    def __init__(self, description_dir: str, derived_from_dir: str):
        self.description = self._find_description_file(description_dir)
        self.derived_from = self._find_description_file(derived_from_dir)
        self.description_dir = description_dir
        self.derived_from_dir = derived_from_dir
        self.description_tree = etree.parse(self.description)
        self.derived_from_tree = etree.parse(self.derived_from)

    def merge_description(self):
        work_tree = copy.deepcopy(self.derived_from_tree)

        self._image_merge(work_tree)
        self._description_replace(work_tree)
        self._preferences_merge(work_tree)
        self._profiles_merge(work_tree)
        self._users_merge(work_tree)
        self._drop_in_sections(work_tree)
        
        sync = DataSync(f'{self.description_dir}/', self.derived_from_dir)
        sync.sync_data(options=Defaults.get_sync_options())

        work_tree.write(self.derived_from, pretty_print=True)

    def _description_replace(self, work_tree):
        self._replace_unique_element_by_xpath(
            work_tree,'/image/description[@type="system"]'
        )

    def _drop_in_sections(self, work_tree):
        root = self.description_tree.getroot()
        w_root = work_tree.getroot()
        exclude_list = ['description', 'preferences', 'profiles']
        for item in root:
            if item.tag not in exclude_list:
                w_root.append(item)

    def _replace_unique_element_by_xpath(self, work_tree, xpath):
        replacement = self.description_tree.xpath(xpath)
        if len(replacement):
            obsolete = work_tree.xpath(xpath)
            if len(obsolete):
                parent = obsolete[0].getparent()
                parent.replace(obsolete[0], replacement[0])
                return True
        return False

    def _profiles_merge(self, work_tree):
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
        attr_list = [f'@{k}=\'{v}\'' for k, v in attributes.items()]
        constraints = '[not(@*)]'
        if attr_list:
            constraints = '[' + ' and '.join(attr_list) + ']'
        item = tree.xpath(e_path + constraints)
        if len(item):
            return item[0]
        return None

    def _merge_preferences_set(self, pref_setA, pref_setB):
        for child in pref_setA:
            if child.tag == 'showlicense':
                pret_setB.append(child)
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
        config_file = description_directory + '/config.xml'
        if not os.path.exists(config_file):
            # alternative config file lookup location
            config_file = description_directory + '/image/config.xml'
        if not os.path.exists(config_file):
            # glob config file search, first match wins
            glob_match = description_directory + '/*.kiwi'
            for kiwi_file in sorted(glob.iglob(glob_match)):
                config_file = kiwi_file
                break

        if not os.path.exists(config_file):
            raise KiwiConfigFileNotFound(
                'no XML description found in %s' % description_directory
            )
        return config_file

    def _image_merge(self, work_tree):
        # TODO
        pass

    def _users_merge(self, work_tree):
        # TODO
        pass
