# How to create a release of dvmdostem

1. Ensure that all desired features, bugfixes, and contributions for this
   release have been merged into the `develop` branch and that all CI checks
   on `develop` are green.

2. Choose a version number, see below.

3. Create a release branch off `develop`:

    ```bash
    $ git checkout develop
    $ git pull upstream develop
    $ git checkout -b release/vN.N.N
    ```

4. Bump version numbers and update release notes:
   - In `docs_src/sphinx/source/conf.py` (`version = 'vN.N.N'`, `release = 'vN.N.N'`)
   - In `CITATION.cff`, specifically under the `identifiers.description` for
     the Github release URL: `https://github.com/uaf-arctic-eco-modeling/dvm-dos-tem/releases/tag/vN.N.N`
   - Update `changelog.txt` with the itemized list of changes for this release.

   Test docs build locally if desired:

    ```bash
    $ docker compose exec --workdir /work/docs_src/sphinx \
        dvmdostem-dev make version=vN.N.N release=vN.N.N html
    ```

   Commit the version bump and changelog:

    ```bash
    $ git commit -am "Prepare release vN.N.N"
    ```

5. Push the release branch and open a Pull Request into `master`:

    ```bash
    $ git push upstream release/vN.N.N
    ```

   - Go to GitHub and open a Pull Request with base `master` and compare
     `release/vN.N.N`.
   - GitHub Actions CI (doctests and smoke tests) will run automatically on the
     Pull Request targeting `master`.
   - Once the checks pass and reviews are complete, merge the Pull Request
     into `master`.

6. Tag the release commit on `master`:

    ```bash
    $ git checkout master
    $ git pull upstream master
    $ git tag -a vN.N.N -m "Release vN.N.N" --cleanup verbatim --file /tmp/release_msg.txt
    $ git push upstream master
    $ git push upstream vN.N.N
    ```

   Make sure to use an annotated tag (`-a`). You can compose your release note
   in a file (`/tmp/release_msg.txt`) and pass `--file` with `--cleanup verbatim`
   so markdown formatting is preserved.

7. Back-merge `master` into `develop` so `develop` receives the version bump
   commit and release history:

    ```bash
    $ git checkout develop
    $ git pull upstream develop
    $ git merge master
    $ git push upstream develop
    $ git branch -d release/vN.N.N
    $ git push upstream --delete release/vN.N.N
    ```

8. **Important!** Create the release on GitHub so that the Zenodo integration
   and release workflow trigger:

   Zenodo is tied to the release event notification coming from GitHub.
   While pushed annotated tags show up in the "Releases" list on GitHub,
   the event does not trigger unless an actual release is published.
   Furthermore, the automated release workflow (`.github/workflows/release.yml`)
   triggers on release publication to build/upload binaries and publish Docker images.

   Via the GitHub Web UI:
   * Go to https://github.com/uaf-arctic-eco-modeling/dvm-dos-tem/releases.
   * Click the button for "Draft new release" (upper right).
   * Choose the tag `vN.N.N` in the tag box (target: `master`).
   * Put the version number and date in the title box (`vN.N.N - YYYY-MM-DD`).
   * Paste your markdown release notes into the description box.
   * Check the preview.
   * Click the "Publish release" button.

   Or via the GitHub CLI:

    ```bash
    $ gh release create vN.N.N --target master --title "vN.N.N - $(date +%Y-%m-%d)" --notes-file /tmp/release_msg.txt
    ```

   Publishing the release triggers:
   - The automated `.github/workflows/release.yml` workflow: runs test suites,
     compiles the `dvmdostem` binary, packages it into a tarball with sha256
     checksum, attaches it as a GitHub Release asset, and builds/pushes
     release-tagged Docker images (`dvmdostem-dev:vN.N.N`, `cpp-dev:vN.N.N`,
     and `:latest`) to GHCR.
   - Zenodo DOI minting / archive creation.

9. Update published documentation:
   Run `publish_github_pages.sh` from the `master` branch.

## Release note format

Here is a possible release note format:

    ```
    # v0.1.0 - YYYY-MM-DD
    
    General description

    ## Added
     * some feature...

    ## Fixed
     * broken part...

    ## Changed
     * Some critical part...

    ## Removed
     * old cruft...
    
    ```
The above format renders ok on github (as raw markdown, not formatted),
and it looks ok when printed using `git-tag`, (also unformatted) i.e.:

    ```
    $ git tag -l -n99 v0.2*
    ```


## Choosing a version number

The project uses a three part version number: vMAJOR.MINOR.PATCH.

We use the following rules for incrementing the version number:
 * The PATCH number (farthest right) will be incremented for changes 
   that do not affect the general scientific concepts in the 
   software.
 * The MINOR number (middle) will be updated when changes have been made 
   to science concepts, major implementation changes for scienctifc aspects 
   of the code calibration numbers are updated, or large new features are added.
 * The MAJOR (left) number will be updated for major milestones. This will likely 
   be points where the model is run for "production" or major testing and
   validation steps are completed and documented.

This project is not using traditional [Semantic Versioning](https://semver.org/spec/v2.0.0.html),
however we have borrowed some concepts.

Until the project reaches v1.0.0, we will not make any guarantees about backwards
compatibility. Once the project reaches v1.0.0, we may decide to handle the rules
for incrementing version numbers differently.


