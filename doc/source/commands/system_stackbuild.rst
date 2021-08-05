kiwi-ng system stackbuild
=========================

SYNOPSIS
--------

.. code:: bash

   kiwi-ng system stackbuild -h | --help
   kiwi-ng system stackbuild --stash=<name>... --description=<directory> --target-dir=<directory>
       [--from-registry=<URI>]
       [-- <kiwi_build_command_args>...]
   kiwi-ng system stackbuild --stash=<name>... --target-dir=<directory>
       [--from-registry=<URI>]
       [-- <kiwi_create_command_args>...]
   kiwi-ng system stackbuild help

DESCRIPTION
-----------

This [KIWI](https://osinside.github.io/kiwi/) plugin allows to store
and reuse KIWI built root-trees as OCI containers. The idea is using OCI images
as portable format to store and distribute a root-tree, so they can be pushed
and pulled from OCI registries.

This plugin allows the user to operate in two modes

1. Rebuild an image from a stash

   In this mode `stackbuild` takes a stash, makes it available to the
   local registry and builds the image using the stash rootfs and
   in stash stored image description.

   .. code:: bash

      $ kiwi-ng system stackbuild --stash NAME \
          --target-dir /target/rebuild


2. Build an image based on a stash

   In this mode `stackbuild` takes a stash, makes it available to the
   local registry and uses the stash rootfs as the base for an image
   build of another image description.

   .. code:: bash

      $ kiwi-ng system stackbuild --stash NAME \
          --description=/some/image-description --target-dir /target/rebuild

   .. note::

      The stackbuild plugin does not perform any consistency check
      if the used stash rootfs is compatible with the provided image
      description. With that in mind there is nothing which would
      prevent you from using a Leap stash and try to build a Fedora
      image on top of it. That an attempt like this will not produce
      anything useful should be clear to the user and is in the
      users responsibility to prevent combining apples with pears

OPTIONS
-------

--stash=<name>

  Name of the stash. See `system stash --list` for available stashes.
  Multiple stashes will be stacked together in the given order

--from-registry=<URI>

  Pull given stash container name from the provided
  registry URI

--description=<directory>

  Path to the XML description. This is a directory containing at least
  one _config.xml_ or _*.kiwi_ XML file.

--target-dir=<directory>

  Path to store the build results.

-- <kiwi_build_command_args>...

  List of command parameters as supported by the kiwi-ng
  build command. The information given here is passed
  along to the `kiwi-ng system build` command.

-- <kiwi_create_command_args>...

  List of command parameters as supported by the kiwi-ng
  build command. The information given here is passed
  along to the `kiwi-ng system create` command.

EXAMPLE
-------

.. code:: bash

   $ kiwi-ng system stackbuild --stash NAME --target-dir /target/rebuild
