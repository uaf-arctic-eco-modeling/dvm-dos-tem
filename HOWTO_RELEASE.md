# How to create a release of dvmdostem

1. Decide on a commit to release. Should be on the master branch!
   * Choose a version number, see below. 

2. Compose a release note. May use markdown, see below.

3. Tag the commit. Make sure to use an annotated tag and the release 
   note you just composed. This is best done via the command line: 

    ```
    $ git tag -a v0.2.3 <commit SHA> --cleanup verbatim --file /tmp/release_msg.txt
    ```

   The github web interface lists and sorts releases based on commit date 
   (for lightweight tags) and by creation date (for annotated tags
   and presumably releases created on the web interface).
   The message you provide will show up in gitk as well as
   on Github. To use a detailed message, you can write your
   notes in a file, (e.g. `/tmp/release_msg.txt`) and then pass
   that file to `git-tag`. By default, the message is cleaned up
   so git strips it of comments and whitespace. This means that
   if you wrote your message with markdown formatting it might not 
   end up as you expect! So you can ask git not to touch the message 
   contents with the `--cleanup=verbatim` flag.

5. Push tag to github: `$ git push upstream v0.2.3`

6. Optionally edit the info on the github website release page.

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
   of the code or new calibration numbers.
 * The MAJOR (left) number will be updated for major milestones. This will likely 
   be points where the model is run for "production" or major testing and
   validation steps are completed and documented.

This project is not using traditional [Semantic Versioning](https://semver.org/spec/v2.0.0.html),
however we have borrowed some concepts.

Until the project reaches v1.0.0, we will not make any guarantees about backwards
compatibility. Once the project reaches v1.0.0, we may decide to handle the rules
for incrementing version numbers differently.


