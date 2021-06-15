kiwi-ng system stackbuild
=========================

SYNOPSIS
--------

.. code:: bash

   kiwi-ng [global options] service <command> [<args>]

   kiwi-ng system stackbuild -h | --help
   kiwi-ng system stackbuild help

DESCRIPTION
-----------

This is [KIWI](https://osinside.github.io/kiwi/) plugin that allows to store
and reuse KIWI built root-trees as OCI containers. The idea is using OCI images
as portable format to store and distribute a root-tree, so they can be pushed
and pulled from OCI registries.

This plugin allows the user to:

* Build a regular image and, in addition, store the root-tree (the result
  of prepare step) in to an OCI image. Note that the stored OCI image includes
  full KIWI description.

  .. code:: bash

     kiwi-ng system rebuild --description <my_project_folder> --keep-root <image_reference> -- --target-dir <my_build_folder>

* Rebuild a regular image by just pulling a previously stored OCI image,
  without a KIWI XML description. In that case only the create step is
  exectued following the pre stored XML description contained in the
  pulled OCI image.

  .. code:: bash

     kiwi-ng system rebuild --root <image_reference> -- --target-dir <my_build_folder>
  
* Rebuild a regular image by importing a previously stored OCI image and
  provinfing a custom KIWI XML description. In that case preare and create
  steps are executed according to the provided XML and ignoring any description
  artifact from the pulled image.

  .. code:: bash

     kiwi-ng system rebuild --root <image_reference> -- --description <my_project_folder> --target-dir <my_build_folder>
  
* Build a derived image. In that case the user provides an KIWI Rebuild Plugin
  XML description (based on a slighly different XML schema) that is merged into
  the KIWI XML description. In that case prepare and create steps are executed
  based on the pulled root-tree and the merged description.

  .. code:: bash

     kiwi-ng system rebuild --description <my_project_folder> -- --target-dir <my_build_folder>
  

OPTIONS
-------

EXAMPLE
-------

.. code:: bash

   TODO
