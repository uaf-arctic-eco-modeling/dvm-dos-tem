# How to create a release of dvmdostem

1. Decide on a commit upon which to base your release. The commit you choose
   must be on the master branch. Following the rest of the release process will
   create a new commit that updates version numbers.

2. Choose a version number, see below.

3. Create a lightweight tag:

    ```
    $ git checkout master
    $ git pull upstream master
    $ git tag vN.N.N
    ```

4. Build images, compile model, run all tests:

   * Run the `docker-build-wrapper.sh`
   * Launch new containers from the new images:

         ```
         # alternatively, set V_TAG in your .env file
         $ V_TAG=$(git describe --tags) docker compose up -d
         ```

   * Run the tests in the container:

         ```
         $ docker compose exec dvmdostem-dev bash
         develop@987b5bc3c824:/work/ $ cd scripts
         develop@987b5bc3c824:/work/ $ for i in $(ls doctests_*); do python -m doctest $i; done
         ```

   If the tests fail, then you very likely will need to make more modifications
   and commits before the release. Depending on the magnitude of the changes
   this could be a single commit directly to the master branch or might trigger
   a new topic branch/pull request process. Once the commit(s) have been made,
   go back to step 1. You will need to delete the tag created in step 3 so that
   you can re-create it.

5. Bump version numbers:
  -  in `docs_src/sphinx/sources/conf.py `, and
  -  in the `CITATION.cff` file, specifically under the
     `identifiers.description` for the Github release URL.

  Then commit the changes and build the docs:

         ```
         $ docker compose exec --workdir /work/docs_src/sphinx \
         dvmdostem-dev make version=vN.N.N release=vN.N.N html
         ```

6. Compose a release note. This should be something like an itemized list of
   changes since the last release. The note should be formatted with Markdown.
   See past notes and the notes below for more formatting guidelines.

7. Tag the new commit you just made with the version number bump. Make sure to
   use an annotated tag and use the release note you just composed as the tag
   message body. This is best done via the command line: 

    ```
    $ git tag -d vN.N.N # Delete temporary lightweight tag before creating new annotated tag
    $ git tag -a vN.N.N <commit SHA> --cleanup verbatim --file /tmp/release_msg.txt
    ```

   The Github web interface lists and sorts releases based on commit date (for
   lightweight tags) and by creation date (for annotated tags and presumably
   releases created on the web interface). The message you provide will show up
   in gitk as well as on Github. To use a detailed message, you can write your
   notes in a file, (e.g. `/tmp/release_msg.txt`) and then pass that file to
   `git-tag`. By default, the message is cleaned up so git strips it of comments
   and whitespace. This means that if you wrote your message with markdown
   formatting it might not end up as you expect! So you can ask git not to touch
   the message contents with the `--cleanup=verbatim` flag.

8. **Important** Push tag to github: `$ git push upstream vN.N.N`, push version bump, then tag

9. **Important!** Create the release on Github so that the Zenodo integration
works. Basically Zendo is tied to the release event notification coming from
Github and while pushed annotated tags show up in the "Releases" list on Github,
the event does not trigger unless an actual release is drafted and published.
There is probably an automated way to do this, but I haven't figured it out yet.
So:
   * Go to https://github.com/ua-snap/dvm-dos-tem/releases.
   * Click the button for "Draft new release" (upper right).
   * Choose the Tag version in the tag box.
   * Put the version number and date in the title box (first line of your
     release note).
   * Paste your markdown release message into the description box.
   * Check the preview.
   * Click the Publish button.

10. Optionally edit the info on the github website release page. Editing 
does not trigger a new release notification and does not break the Zenodo
integration.

11. Update published documentation, use `publish_github_pages.sh`.

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


