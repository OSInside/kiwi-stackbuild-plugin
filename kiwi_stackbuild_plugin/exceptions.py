# Copyright (c) 2020 SUSE Software Solutions Germany GmbH.  All rights reserved.
#
# This file is part of kiwi-stackbuild.
#
# kiwi-stackbuild is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# kiwi-stackbuild is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kiwi-stackbuild.  If not, see <http://www.gnu.org/licenses/>
#
from kiwi.exceptions import KiwiError


class KiwiStackBuildPluginStashNotFoundError(KiwiError):
    """
    Exception raised if the stash file does not exist
    """


class KiwiStackBuildPluginTargetDirExists(KiwiError):
    """
    Exception raised if the image target directory already exists
    """


class KiwiStackBuildPluginContainerNameInvalid(KiwiError):
    """
    Exception raised if the image name cannot be used as container name
    """
