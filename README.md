## KIWI Rebuild Plugin

This is [KIWI](https://osinside.github.io/kiwi/) plugin that allows to store
and reuse KIWI built root-trees as OCI containers. The idea is using OCI images
as portable format to store and distribute a root-tree, so they can be pushed
and pulled from OCI registries.

**Disclaimer: This is a proof of concept and in any case it should not be
considered a production ready software**

This plugin allows the user to:

* Build a regular image and, in addition, store the root-tree (the result
  of prepare step) in to an OCI image. Note that the stored OCI image includes
  full KIWI description.

  ```
  kiwi-ng system rebuild --description <my_project_folder> --keep-root <image_reference> -- --target-dir <my_build_folder>
  ```

* Rebuild a regular image by just pulling a previously stored OCI image,
  without a KIWI XML description. In that case only the create step is
  exectued following the pre stored XML description contained in the
  pulled OCI image.

  ```
  kiwi-ng system rebuild --root <image_reference> -- --target-dir <my_build_folder>
  ```

* Rebuild a regular image by importing a previously stored OCI image and
  provinfing a custom KIWI XML description. In that case preare and create
  steps are executed according to the provided XML and ignoring any description
  artifact from the pulled image.

  ```
  kiwi-ng system rebuild --root <image_reference> -- --description <my_project_folder> --target-dir <my_build_folder>
  ```

* Build a derived image. In that case the user provides an KIWI Rebuild Plugin
  XML description (based on a slighly different XML schema) that is merged into
  the KIWI XML description. In that case prepare and create steps are executed
  based on the pulled root-tree and the merged description.

  ```
  kiwi-ng system rebuild --description <my_project_folder> -- --target-dir <my_build_folder>
  ```


### TODOS

* Make use of the KIWI Rebuild Plugin schema on derived images.
* Improve the XML merge code. I am convinced this can be coded in a nice way.
* Improve the experience with OCI registries. Currently the plugin just
  creates image references that are directly by passed to `skopeo`. It is not
  obvious how to interact with remote OCI registries.
* Code unit tests. It shouldn't be hard since the plugin does not include
  tons of code lines
* Include a Makefile with proper targets for pip eggs, rpm builds, tests
  execution, etc.
* Write some proper documentation
* Improve client UX. Current set of flags is confusing an not nicely integrated
  with current `kiwi-ng system build` command.
* Include type hints in code.
