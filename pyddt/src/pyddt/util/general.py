#This module provides very general utility methods

import os


def breakdown_outfile_name(outfilepath):
  '''
  Takes a TEM output file name, with or without full path,
  and returns the path, variable name, time step, and stage.

  Example inputs:
    /data/workflows/testing1/output/ALD_yearly_sc.nc
    ALD_yearly_sc.nc

  Example outputs:
    /data/workflows/testing1/output, ALD, yearly, sc
    [current dir], ALD, yearly, sc
  '''

  #Resolve any symbolic links
  outputfile = os.path.realpath(outfilepath)

  #Collapse any extra separators (and remove any trailing slashes)
  outputfile = os.path.normpath(outputfile)

  path_prefix, filename = os.path.split(outputfile)

  #Split filename: varname_timeres_stage.nc
  filename_base = filename.partition('.')[0]
  varname, timeres, stage = filename_base.split('_')

#  print(path_prefix)
#  print(varname)
#  print(timeres)
#  print(stage)

  return path_prefix, varname, timeres, stage


def merge_pngs_to_pdf(outdir, png_dir=None, pdf_name='result.pdf'):
  """Combine PNG images into a PDF report, retaining the original images.

  Parameters
  ----------
  outdir : str or os.PathLike
    Existing directory in which to write the final PDF report.
  png_dir : str or os.PathLike, optional
    Existing directory containing the PNG images. Defaults to ``results/``
    inside ``outdir``. An explicitly supplied relative path is interpreted
    relative to the current working directory.
  pdf_name : str, optional
    Filename for the final report inside ``outdir``. Defaults to
    ``result.pdf``. An existing report with this name is replaced.

  Notes
  -----
  Each PNG is converted to a temporary PDF in ``png_dir``. All PDF files in
  that directory, including any that already exist, are merged in filename
  order and deleted after being appended. Use a directory dedicated to the
  report images to avoid removing unrelated PDFs. PNG images are preserved.
  """
  from pypdf import PdfWriter
  from PIL import Image

  if png_dir is None:
    png_dir = os.path.join(outdir, 'results')
  report_path = os.path.join(outdir, pdf_name)

  # Convert images to PDF pages before assembling the combined report.
  listpng = os.listdir(png_dir)
  listpng2 = [ x for x in listpng if '.png' in x ]

  for png in listpng2:
    image_1 = Image.open(os.path.join(png_dir, png))
    im_1 = image_1.convert('RGB')
    im_1.save(os.path.join(png_dir, png.replace(".png", "") + '.pdf'))

  if os.path.isfile(report_path):
    os.remove(report_path)

  listpdf = os.listdir(png_dir)
  listpdf2 = [ x for x in listpdf if '.pdf' in x ]

  # Sorting filenames makes the page order repeatable across runs.
  writer = PdfWriter()
  for pdf in sorted(listpdf2):
    writer.append(os.path.join(png_dir, pdf))
    os.remove(os.path.join(png_dir, pdf))

  writer.write(report_path)

  print("PNGs merged to PDF.")


'''
pyTEM
pytem
dvmdostem
pydvmdostem
dvmdostempy
tempy
TEMpy


pyddt
  README
  pyproject.toml
  
  docs/

  tests/
    pull_request_test.py
    doctests/
      doctests_outspec_utils.md
        
  util.general.py
  util.metrics.py
  util.param.py
  util.runmask.py
  util.outspec.py
    
  util.drivers
    BaseDriver.py
    MadsTEMDriver.py
    Sensitivity.py
  
  calibration
    ca-config-demo.yaml
    AC-MADS-TEM.jl
    AC-SCIPY-TEM.py

  sensitivity
    SA_setup_and_run.py
    SA_post_hoc_analysis.py
    sa-demo-config.yaml
  
  

'''