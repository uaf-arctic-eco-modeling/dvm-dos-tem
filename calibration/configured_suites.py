##########################################################################
#
# Configure different suites here
#
##########################################################################

# A suite is an assembelage of variables to plot in one or more sub-plots
# along with some configuration and meta-data about the variables (i.e.
# which variables to group in which sub-plots and what units/labels to use.

# Sample suite with comments:
#  'standard' : {
#    'desc': "some help text about this suite",  # Notes
#    'rows': 1,        # rows of subplots to create
#    'cols': 1,        # columns of subplots to create NOTE: must be 1 for now!!
#    'traces': [
#      {
#        'jsontag': 'GPPAll',  # The variable name in json file
#        'axesnum': 0,         # Which subplot axes to draw on
#        'units': 'gC/m^2',    # Label for y axis?
#        'pft': '',            # Empty tag indicating this is a pft variable
#                              # Omit for non-pft variables!
#
#        'pftpart': 'Leaf'     # Leaf, Stem, or Root. Only if 'pft' key is present!
#      },
#    ]
#  }

configured_suites = {
  'standard': {
    'desc': "The basic carbon plot blah blah, some pft vars",
    'rows': 5,
    'cols': 1,
    'traces': [
      { 'jsontag': 'GPPAll', 'axesnum': 0, 'units': 'gC/m^2', 'pft': '', },
      { 'jsontag': 'NPPAll', 'axesnum': 0, 'units': 'gC/m^2', 'pft': '', },

      { 'jsontag': 'GPPAllIgnoringNitrogen', 'units': 'gC/m^2', 'axesnum': 1, 'pft': '', },
      { 'jsontag': 'NPPAllIgnoringNitrogen', 'units': 'gC/m^2', 'axesnum': 1, 'pft': '', },

      { 'jsontag': 'PARAbsorb', 'axesnum': 2, 'units': 'percent', 'pft': '', },
      { 'jsontag': 'PARDown', 'axesnum': 2, 'units': 'percent', 'pft': '', },

      { 'jsontag': 'LitterfallCarbonAll', 'axesnum': 3, 'units': 'gC/m^2', 'pft': '', },
      { 'jsontag': 'LitterfallNitrogenAll', 'axesnum': 3, 'units': 'gC/m^2', 'pft': '', },

      { 'jsontag': 'WaterTable', 'axesnum': 4, 'units': 'percent', },
    ]
  },
  's2': {
    'desc': "A set of carbon soil variables.",
    'rows': 2,
    'cols': 1,
    'traces': [
      # BROKEN: in envmodule only warm up period!
      # gotta figure out how to handle C++ > json > numpy nan issue.
      # maybe set to null on encoder side?
      { 'jsontag': 'CarbonShallow', 'axesnum': 0, },
      { 'jsontag': 'CarbonDeep', 'axesnum': 0, },
      { 'jsontag': 'CarbonMineralSum', 'axesnum': 0, },
      { 'jsontag': 'MossdeathCarbon', 'axesnum': 1, },
      { 'jsontag': 'MossdeathNitrogen', 'axesnum': 1, },
    ]
  },
  's3': {
    'desc': "Trying some pft compartment plots",
    'rows': 2,
    'cols': 1,
    'traces': [
      { 'jsontag': 'VegCarbon', 'axesnum': 0, 'pft': '', 'pftpart': 'Leaf'},
      { 'jsontag': 'VegCarbon', 'axesnum': 0, 'pft': '', 'pftpart': 'Stem'},
      { 'jsontag': 'VegCarbon', 'axesnum': 0, 'pft': '', 'pftpart': 'Root'},

      { 'jsontag': 'VegStructuralNitrogen', 'axesnum': 1, 'pft': '', 'pftpart': 'Leaf'},
      { 'jsontag': 'VegStructuralNitrogen', 'axesnum': 1, 'pft': '', 'pftpart': 'Stem'},
      { 'jsontag': 'VegStructuralNitrogen', 'axesnum': 1, 'pft': '', 'pftpart': 'Root'},
    ]
  },
}
