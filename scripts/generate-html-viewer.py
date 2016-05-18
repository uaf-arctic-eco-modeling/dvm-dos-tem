#!/usr/bin/env python

# Script to generate an html page that can view
# several sets of dvmdostem calibration plots side by side

# T. Carman Spring 2016

import argparse
import textwrap
import glob

def generate_head_tag():
  '''Generates the <head> tag to be used in an html page.'''
  h = textwrap.dedent('''\
    <head>
      <meta charset="utf-8">
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
    print "Error: unrecognized tag type!"

  # pass the string back
  return HTML

def generate_page(left_img_list=[], center_img_list=[], right_img_list=[], titlelist=[], tag_type='img'):
  print tag_type
  '''Generates a page of html, returns it as a string'''

  page = textwrap.dedent('''
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

if __name__ == '__main__':

  parser = argparse.ArgumentParser(
    #formatter_class=argparse.RawDescriptionHelpFormatter,
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    description=textwrap.dedent('''
      Generate an HTML page for looking at sets of dvmdostem \
      calibraiton plots side by side. Open the resulting .html file
      in a webbrowser to see the plots.
    ''')
  )

  parser.add_argument('-l', '--left', metavar='',
    help=textwrap.dedent('''Path to a directory of files for the left column'''))

  parser.add_argument('-c', '--center', metavar='',
    help=textwrap.dedent('''A path to a directory of files for the center column'''))

  parser.add_argument('-r', '--right', metavar='',
    help=textwrap.dedent('''A path to a directory of files for the right column'''))

  parser.add_argument('--display-method', nargs=1, default=["img"], choices=['img', 'object/embed'],
    help=textwrap.dedent('''Which method to use to display the pdfs.'''))

  args = parser.parse_args()
  print args


  LEFT = sorted(glob.glob("%s/*.pdf" % (args.left)))
  CENTER = sorted(glob.glob("%s/*.pdf" % (args.center)))
  RIGHT = sorted(glob.glob("%s/*.pdf" % (args.right)))
  titlelist = (args.left, args.center, args.right)

  with open("three-view.html", 'w') as f:
    f.write( generate_page(LEFT, CENTER, RIGHT, titlelist, tag_type=args.display_method[0]) )


