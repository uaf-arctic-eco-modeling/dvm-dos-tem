"""General utilities that do not clearly fit in the more specific
modules, such as path or directory-related operations.
"""

import os


def breakdown_outfile_name(outfilepath):
  """Split a model output filename into its directory, variable, and timing.

  Parameters
  ----------
  outfilepath : str or os.PathLike
    Path to an output file named ``VARIABLE_timeres_stage.nc``, such as
    ``ALD_yearly_sc.nc``. Relative paths are resolved from the current
    working directory; the file does not need to exist.

  Returns
  -------
  path_prefix : str
    Absolute directory path with symbolic links resolved.
  varname : str
    Output variable name, such as ``ALD``.
  timeres : str
    Time resolution text from the filename, such as ``yearly``.
  stage : str
    Model stage text from the filename, such as ``sc`` for scenario.

  Raises
  ------
  ValueError
    If the filename portion before the first period does not contain
    exactly three underscore-separated fields.

  Notes
  -----
  The fields are extracted as written; their values and the file extension
  are not validated.

  Examples
  --------
  >>> directory, variable, resolution, stage = breakdown_outfile_name('ALD_yearly_sc.nc')
  >>> variable, resolution, stage
  ('ALD', 'yearly', 'sc')
  """

  #Resolve any symbolic links
  outputfile = os.path.realpath(outfilepath)

  #Collapse any extra separators (and remove any trailing slashes)
  outputfile = os.path.normpath(outputfile)

  path_prefix, filename = os.path.split(outputfile)

  #Split filename: varname_timeres_stage.nc
  filename_base = filename.partition('.')[0]
  varname, timeres, stage = filename_base.split('_')

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

  Returns
  -------
  None

  Notes
  -----
  Filenames containing ``.png`` are selected as images; filenames containing
  ``.pdf`` are selected for merging. Matching is case-sensitive.
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
