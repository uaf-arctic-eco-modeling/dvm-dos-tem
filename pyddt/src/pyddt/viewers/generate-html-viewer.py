#!/usr/bin/env python

# Script to generate an html page that can view
# several sets of dvmdostem calibration plots side by side

# T. Carman Spring 2016

import fnmatch
import os
import collections
import webbrowser
import argparse
import textwrap
import glob


from jinja2 import Template

def generate_head_tag():
  '''Generates the <head> tag to be used in an html page.'''
  h = textwrap.dedent('''\
    <head>
      <meta charset="utf-8">

      <!-- Latest compiled and minified CSS -->
      <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css">

      <!-- jQuery library -->
      <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.1.1/jquery.min.js"></script>

      <!-- Latest compiled JavaScript -->
      <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js"></script>

      <!-- something about mobile first design with bootstrap... -->
      <meta name="viewport" content="width=device-width, initial-scale=1">

      <title>dvmdostem output viewer</title>
      <link rel="stylesheet" href="">

      <style type="text/css">
      body div#fixed-header-container {
        background: rgba(0,0,0,0.75);
        padding: 5px 0 0 5px;
        height: 35px;
        width: 100%;
        position: fixed;
        top: 0px;
        left: 0px;    
      }

      body div#fixed-header-container div {
        float: left;
        width: 392px;
        margin: 0 0 0 4px;
        padding: 5px;

      }
      body div#content-container div {
        float: left;
        width: 400px;
        margin: 35px 0 0 0;
        padding: 5px;
      }

      div.fixed-title-item {
        width: 390px;
        background: yellow;
        /*padding: 5px;*/
        border: 1px solid gray;
        margin: 5px 0 0 0;

      }
      body div img {
        width: 390px;
        border: 1px solid gray;
        margin: 5px 0 0 0;

      }

      .plot-column object {
        height: 200px;
      }
      </style>


    </head>''')

  return h


def NEW_template():
  '''
  Returns a jinja2 template instance. To use the template instance, 
  call template.render(...)

  Parameters that must be passed to template.render(...)
  -------------------------------------------------------
  dm : dict
    A dict mapping 'categories' to lists of image
    paths (one list for each column).
  titles : dict
    A dict mapping columns (L, C, R) to title text.

  Returns
  -------
  A jinja2 Template instance.
  '''
  return Template(textwrap.dedent('''\

  <!DOCTYPE html>
  <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta http-equiv="X-UA-Compatible" content="IE=edge">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <!-- The above 3 meta tags *must* come first in the head; any other head content must come *after* these tags -->

      <title>dvmdostem output viewer</title>

      <!-- Bootstrap -->
      <!--<link href="css/bootstrap.min.css" rel="stylesheet">-->

      <!-- Latest compiled and minified CSS -->
      <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">

      <!-- Optional theme -->
      <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap-theme.min.css" integrity="sha384-rHyoN1iRsVXV4nD0JutlnGaslCJuC7uwjduW9SVrLvRYooPp2bWYgmgJQIXwl/Sp" crossorigin="anonymous">

      <!-- jQuery (necessary for Bootstrap's JavaScript plugins) -->
      <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.12.4/jquery.min.js"></script>
      <!-- Include all compiled plugins (below), or include individual files as needed -->
      <!--<script src="js/bootstrap.min.js"></script>-->

      <!-- Latest compiled and minified JavaScript -->
      <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js" integrity="sha384-Tc5IQib027qvyjSMfHjOMaLkfuWVxZxUPnCJA7l2mCWNIpG9mGCD8wGNIcPD7Txa" crossorigin="anonymous"></script>

      <!-- HTML5 shim and Respond.js for IE8 support of HTML5 elements and media queries -->
      <!-- WARNING: Respond.js doesn't work if you view the page via file:// -->
      <!--[if lt IE 9]>
        <script src="https://oss.maxcdn.com/html5shiv/3.7.3/html5shiv.min.js"></script>
        <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
      <![endif]-->

      <script>
        !window.jQuery && alert("This page won't work properly without " + 
          "jQuery and Boostrap, which are loaded from a Content Delivery " +
          "Network, and cached locally. Try again when you are conncected to " +
          "the internet.");
      </script>

      <style type="text/css">

        .fixed-column-headerbox {
          padding: 5px;
          margin: 4px;
          border: 1px solid gray;
          background-color: yellow;

        }

        .main-data-area {
          margin-top: 50px;
        }

      </style>
    </head>
    <body>
      <div class="container-fluid">
      <div class="navbar-fixed-top">
        <div class="row">
          <div class="col-sm-4"><div class="fixed-column-headerbox">{{ titles.L }}</div></div>
          <div class="col-sm-4"><div class="fixed-column-headerbox">{{ titles.C }}</div></div>
          <div class="col-sm-4"><div class="fixed-column-headerbox">{{ titles.R }}</div></div>
        </div>
      </div>
      </div>
      <div class="container-fluid main-data-area">
        {% for category, col2imglistmap in dm.iteritems() %}
        <div class="row">
          <div class="panel-group">
            <div class="panel panel-default">

              <div class="panel-heading clearfix">
                  {% for column, paths in col2imglistmap.iteritems() %}
                    <div class="col-sm-4">
                      <h4 class="panel-title">
                      <a data-toggle="collapse" href="#collapse-{{ category }}">{{ category }}</a>
                      </h4>
                    </div>
                  {% endfor %}
              </div>

              <div id="collapse-{{ category }}" class="panel-collapse collapse">
                {% for column, paths in col2imglistmap.iteritems() %}
                <div class="col-sm-4">
                  <ul class="list-group">
                    {% for image in paths %}
                    <li class="list-group-item">
                      {% if '.txt' in image %}
                        {{ image | safe }}
                      {% else %}
                        <img class="img-responsive" src="{{ image }}" />
                      {% endif %}
                    </li>
                    {% endfor %}
                  </ul>
                </div>
                {% endfor %}
              </div>

            </div>
          </div>
        </div>
        {% endfor %}
      </div>
    </body>
  '''))


def build_new_page(left_path, center_path, right_path, autoshow=False):
  # Unused...
  # def build_list_imgs_in_category(category, image_list):
  #   list_of_imgs_in_category = []
  #   for image in image_list:
  #     print classify(image)
  #     if classify(image) == category:
  #       list_of_imgs_in_category.append(image)
  #   return list_of_imgs_in_category


  def walkdepth(some_dir, depth=1):
    '''Like os.path.walk, but with depth control. 
    From: http://stackoverflow.com/questions/229186/
    '''
    some_dir = some_dir.rstrip(os.path.sep)
    assert os.path.isdir(some_dir)
    num_sep = some_dir.count(os.path.sep)
    for root, dirs, files in os.walk(some_dir):
      yield root, dirs, files
      num_sep_this = root.count(os.path.sep)
      if num_sep + depth <= num_sep_this:
        del dirs[:]

  def classify(filepath):
    '''
    Attempts to classify a file based on the underscore seperated fields.
    Expects a file name something like the following:

        "sometag_Vegetation_pft0.png"    # calibration "suites"
        "_histo_pestplot.png"            # pest plots
        "*-diagnostics.png"              # diagnostics plots


    For the calibration suites, the category is the last filed before the 
    extension, unless 'pft' is in the last field, in which case the category
    is the second to last field.

    For pest plots, the category is the last field before the extension.

    For diagnostic plots, the category is the second to last field before the
    extension.

    Parameters
    ----------
    filepath : str (required)
      Splits the last element (basename) of a path on underscores, and
      then looks for either the last element, or second to last element.

    Returns
    -------
    c : str
      The classification string.
    '''
    bn = os.path.basename(filepath)
    sbn = os.path.splitext(bn)[0]
    tokens = sbn.split('_')
    #print tokens
    classification = None
    if 'pft' in tokens[-1]:
      classification =  tokens[-2]
    elif 'diagnostic' in tokens[-1]:
      classification = "diagnostic-" + tokens[-2]
    else:
      classification = tokens[-1]

    #print "returning %s" % (classification) 
    return classification

  def build_full_image_list(path, depth=None):
    images, pdfs, pngs, txts = [], [], [], []
    if path == "" or path == None:
      pass # Nothing to do with an empty path...
    else:
      path = os.path.normpath(path)
      for root, dirs, files in walkdepth(path, depth=depth):
        pdfs += [os.path.join(root, filename) for filename in fnmatch.filter(files, "*.pdf")]
        pngs += [os.path.join(root, filename) for filename in fnmatch.filter(files, "*.png")]
        txts += [os.path.join(root, filename) for filename in fnmatch.filter(files, "*.txt")]

    print("%s" % path)
    print("  pdfs: %8i" % len(pdfs))
    print("  pngs: %8i" % len(pngs))
    print("  txts: %8i" % len(txts))
    images = pdfs + pngs + txts

    return images

  # Find all the images in the left, center and right paths/trees - recursive!!
  left_img_list = build_full_image_list(args.left, depth=1)
  center_img_list = build_full_image_list(args.center, depth=1)
  right_img_list = build_full_image_list(args.right, depth=1)

  # Figure out what rows we need - one row for every category, that shows up in 
  # any of the three lists.
  categories = sorted(set(map(classify, left_img_list+center_img_list+right_img_list)))
  print("Found %i categories: %s" % (len(categories), ' '.join(categories)))
  print("")

  # Build up this dict mapping 'categories' of plots to lists of file paths
  # for each column that can be passed to the template...
  dm = {}
  for cat in categories:
    dm[cat] = collections.OrderedDict()
    for col, imglist in zip(['L','C','R'], (left_img_list, center_img_list, right_img_list)):
      dm[cat][col] = [i for i in imglist if classify(i)==cat]

  titles = {
    'L':left_path,
    'C':center_path,
    'R':right_path,
  }


  ns = NEW_template().render(dm=dm, titles=titles)

  newFileName = "output-view.html"
  with open(newFileName, 'w') as f:
    f.write( ns )

  print("Created file: %s" % (newFileName))
  print("Open this file in a web-browser: file://%s" % (os.path.join(os.getcwd(), newFileName))) 
  if autoshow:
    print("Trying to auto-show in browser (doesn't work on all platforms)...")
    webbrowser.open("file://{}".format(os.path.join(os.getcwd(), newFileName)), new=0, autoraise=True)
  print("")



def generate_col_div(imglist, tag_type):
  '''Generates a <div> with <img> tags inside, one for each item in the list.'''
  HTML = ""

  if tag_type == "img":
    HTML = '''<div class="plot-column">\n'''
    for i in imglist:
      HTML += '''<img src="%s" />\n''' % (i)

    HTML += '''</div>\n'''

  elif tag_type == "object/embed":
    # Some web browsers have a hard time viewing pdfs inline
    # in which case this might work better:
    HTML = '''<div class="plot-column">\n'''
    for i in imglist:
      HTML += textwrap.dedent('''\
        <object height="400px" data="{0:}" type="application/pdf">
          <embed src="{0:}" type="application/pdf" />
        </object>\n'''.format(i)
      )
    HTML += '''</div>\n'''

  else:
    print("Error: unrecognized tag type!")

  # pass the string back
  return HTML

def generate_page(left_img_list=[], center_img_list=[], right_img_list=[], titlelist=[], tag_type='img'):
  print(tag_type)
  '''Generates a page of html, returns it as a string'''

  page = textwrap.dedent('''
    <!DOCTYPE html>
    <html lang="en">

    {headtag:}

    <body id="" class="" style="">

      <div id="fixed-header-container">
        <div class="fixed-title-item">{lefttitle:}</div>
        <div class="fixed-title-item">{centertitle:}</div>
        <div class="fixed-title-item">{righttitle:}</div>
      </div>

      <div id="content-container">
        {leftcol:}
        {centercol:}
        {rightcol:}
      </div>

    </body>
    </html>'''.format(
        headtag=generate_head_tag(),
        leftcol=generate_col_div(left_img_list, tag_type),
        centercol=generate_col_div(center_img_list, tag_type),
        rightcol=generate_col_div(right_img_list, tag_type),
        lefttitle=titlelist[0],
        centertitle=titlelist[1],
        righttitle=titlelist[2]
        # center_img_list(),
        # right_img_list(),
      ))
  return page

def generate_version_1_html(args):
  LEFT = sorted(glob.glob("%s/*.pdf" % (args.left)))
  CENTER = sorted(glob.glob("%s/*.pdf" % (args.center)))
  RIGHT = sorted(glob.glob("%s/*.pdf" % (args.right)))
  titlelist = (args.left, args.center, args.right)


  # unused??
  def build_list_imgs_in_category(category, image_list):
    list_of_imgs_in_category = []
    for image in image_list:
      print(classify(image))
      if classify(image) == category:
        list_of_imgs_in_category.append(image)

    return list_of_imgs_in_category


  with open("three-view.html", 'w') as f:
    f.write( generate_page(LEFT, CENTER, RIGHT, titlelist, tag_type=args.display_method[0]) )



if __name__ == '__main__':

  parser = argparse.ArgumentParser(
    #formatter_class=argparse.RawDescriptionHelpFormatter,
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    description=textwrap.dedent('''
      Generate an HTML page with a 3-column layout for looking at sets of 
      dvmdostem output plots side by side. 

      The resulting three column page has a collapsible row for each "category"
      of images found in the directories provided with the --left, --center, 
      and --right arguments.

      Open the resulting .html file in a web-browser to see the plots.
    ''')
  )

  parser.add_argument('-l', '--left', metavar='',
    help=textwrap.dedent('''Path to a directory of files for the left column'''))

  parser.add_argument('-c', '--center', metavar='',
    help=textwrap.dedent('''A path to a directory of files for the center column'''))

  parser.add_argument('-r', '--right', metavar='',
    help=textwrap.dedent('''A path to a directory of files for the right column'''))

  parser.add_argument('--show', action='store_true',
    help=textwrap.dedent('''Attempt to open the resulting page in a web-browser
      tab. Might not work on all platforms. If the browser does not pop up with
      the new page loaded, then copy/paste the provided URL into a browser.'''))

  parser.add_argument('--display-method', nargs=1, default=["img"], choices=['img', 'object/embed'],
    help=textwrap.dedent('''Deprecated. Which method to use to display the pdfs.'''))

  parser.add_argument('--create-bundle', default=None,
    help=textwrap.dedent('''Create a self-contained bundle with the generated
    HTML file all the data and found in the --left, --center, and --right 
    locations. The HTML file will use relative paths, so assuming the bundle
    is not modified, the viewer should work.'''))

  parser.add_argument('--version-1-output', action='store_true', 
    help=textwrap.dedent('''Generate the first version of html page. Writes
    a file static HTML page, 'three-view.html', that attempts to display all
    .pdf images in the --left, --right and --center directories.'''))

  args = parser.parse_args()
  #print args

  if args.version_1_output:
    generate_version_1_html(args)

  build_new_page(args.left, args.center, args.right, autoshow=args.show)

  if args.create_bundle:
    print("NOT IMPLEMENTED YET...")



