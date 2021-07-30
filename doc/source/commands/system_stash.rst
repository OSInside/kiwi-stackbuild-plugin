kiwi-ng system stash
====================

SYNOPSIS
--------

.. code:: bash

   kiwi-ng [global options] service <command> [<args>]

   kiwi-ng system stash -h | --help
   kiwi-ng system stash --root=<directory>
       [--tag=<name>]
       [--container-name=<name>]
   kiwi-ng system stash --list
   kiwi-ng system stash help

DESCRIPTION
-----------

Create a container from the given root directory. The command
takes the contents of the given root directory at call time
and creates a container from it.

OPTIONS
-------

--root=<directory>

  The path to the root directory, usually the result of
  a former system prepare or build call

--tag=<name>

  The tag name for the container. By default 'latest'
  is used

--container-name=<name>

  The name of the container. By default
  set to the image name of the stash

--list

  list the available stashes

EXAMPLE
-------

.. code:: bash

   $ kiwi-ng system stash --root /tmp/mytest/build/image-root
