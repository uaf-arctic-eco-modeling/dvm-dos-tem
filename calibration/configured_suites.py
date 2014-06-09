##########################################################################
#
# Configure different suites here
#
##########################################################################

# A suite is an assemblage of variables to plot in one or more sub-plots
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
  'Environment': {
    'desc': "Environmental variables plot (precip, temps, light, water)",
    'rows': 5,
    'cols': 1,
    'traces': [
      # Commented Variables are not yet available in yearly json files
      #{ 'jsontag': 'TempOrganicLayer', 'axesnum': 0, },
      #{ 'jsontag': 'TempMineralLayer', 'axesnum': 0, },
      #{ 'jsontag': 'TempAir', 'axesnum': 0, },

      { 'jsontag': 'Snowfall', 'axesnum': 1, },
      { 'jsontag': 'Rainfall', 'axesnum': 1, },
      #{ 'jsontag': 'Evapotranspiration', 'axesnum': 1, },

      { 'jsontag': 'WaterTable', 'axesnum': 2, },
      #{ 'jsontag': 'ActiveLayerDepth', 'axesnum': 2, },

      #{ 'jsontag': 'VWCOrganicLayer', 'axesnum': 3, },
      #{ 'jsontag': 'VWCMineralLayer', 'axesnum': 3, },

      #{ 'jsontag': 'PARAbsorb', 'axesnum': 4, },
      #{ 'jsontag': 'PARDown', 'axesnum': 4, },
    ]
  },
  'Soil': {
    'desc': "A set of carbon soil variables.",
    'rows': 3,
    'cols': 1,
    'traces': [
      { 'jsontag': 'CarbonShallow', 'axesnum': 0, },
      { 'jsontag': 'CarbonDeep', 'axesnum': 0, },
      { 'jsontag': 'CarbonMineralSum', 'axesnum': 0, },
      { 'jsontag': 'MossdeathCarbon', 'axesnum': 0, },

      { 'jsontag': 'OrganicNitrogenSum', 'axesnum':1, },

      { 'jsontag': 'AvailableNitrogenSum', 'axesnum':2, },
      { 'jsontag': 'NitrogenUptakeAll', 'axesnum':2, },
    ]
  },
  'Vegetation':{
    'desc': "The standard targetted vegetation outputs",
    'rows': 5,
    'cols': 1,
    'traces': [
      { 'jsontag': 'GPPAllIgnoringNitrogen', 'units': 'gC/m^2', 'axesnum': 0, 'pft': '', },
      { 'jsontag': 'NPPAllIgnoringNitrogen', 'units': 'gC/m^2', 'axesnum': 0, 'pft': '', },

      { 'jsontag': 'GPPAll', 'axesnum': 1, 'units': 'gC/m^2', 'pft': '', },
      { 'jsontag': 'NPPAll', 'axesnum': 1, 'units': 'gC/m^2', 'pft': '', },

      { 'jsontag': 'VegCarbon', 'axesnum': 2, 'pft': '', 'pftpart': 'Leaf'},
      { 'jsontag': 'VegCarbon', 'axesnum': 2, 'pft': '', 'pftpart': 'Stem'},
      { 'jsontag': 'VegCarbon', 'axesnum': 2, 'pft': '', 'pftpart': 'Root'},
      { 'jsontag': 'LitterfallCarbonAll', 'axesnum': 2, 'units': 'gC/m^2', 'pft': '', },

      { 'jsontag': 'VegStructuralNitrogen', 'axesnum': 3, 'pft': '', 'pftpart': 'Leaf'},
      { 'jsontag': 'VegStructuralNitrogen', 'axesnum': 3, 'pft': '', 'pftpart': 'Stem'},
      { 'jsontag': 'VegStructuralNitrogen', 'axesnum': 3, 'pft': '', 'pftpart': 'Root'},

      { 'jsontag': 'LitterfallNitrogenAll', 'axesnum': 4, 'units': 'gC/m^2', 'pft': '', },
      { 'jsontag': 'NitrogenUptake', 'axesnum': 4, 'units': 'gC/m^2', 'pft': '', }
    ] 
  },
  'VegSoil':{
    'desc': "The standard targetted vegetation outputs",
    'rows': 8,
    'cols': 1,
    'traces': [
      { 'jsontag': 'GPPAllIgnoringNitrogen', 'units': 'gC/m^2', 'axesnum': 0, 'pft': '', },
      { 'jsontag': 'NPPAllIgnoringNitrogen', 'units': 'gC/m^2', 'axesnum': 0, 'pft': '', },

      { 'jsontag': 'GPPAll', 'axesnum': 1, 'units': 'gC/m^2', 'pft': '', },
      { 'jsontag': 'NPPAll', 'axesnum': 1, 'units': 'gC/m^2', 'pft': '', },

      { 'jsontag': 'VegCarbon', 'axesnum': 2, 'units': 'gC/m^2', 'pft': '', 'pftpart': 'Leaf'},
      { 'jsontag': 'VegCarbon', 'axesnum': 2, 'units': 'gC/m^2', 'pft': '', 'pftpart': 'Stem'},
      { 'jsontag': 'VegCarbon', 'axesnum': 2, 'units': 'gC/m^2', 'pft': '', 'pftpart': 'Root'},
      { 'jsontag': 'LitterfallCarbonAll', 'axesnum': 2, 'units': 'gC/m^2', 'pft': '', },

      { 'jsontag': 'VegStructuralNitrogen', 'axesnum': 3, 'units': 'gN/m^2', 'pft': '', 'pftpart': 'Leaf'},
      { 'jsontag': 'VegStructuralNitrogen', 'axesnum': 3, 'units': 'gN/m^2', 'pft': '', 'pftpart': 'Stem'},
      { 'jsontag': 'VegStructuralNitrogen', 'axesnum': 3, 'units': 'gN/m^2', 'pft': '', 'pftpart': 'Root'},

      { 'jsontag': 'LitterfallNitrogenAll', 'axesnum': 4, 'units': 'gN/m^2', 'pft': '', },
      { 'jsontag': 'NitrogenUptake', 'axesnum': 4, 'units': 'gN/m^2', 'pft': '', },

      { 'jsontag': 'CarbonShallow', 'axesnum': 5, 'units': 'gC/m^2', },
      { 'jsontag': 'CarbonDeep', 'axesnum': 5, 'units': 'gC/m^2', },
      { 'jsontag': 'CarbonMineralSum', 'axesnum': 5, 'units': 'gC/m^2', },
      { 'jsontag': 'MossdeathCarbon', 'axesnum': 5, 'units': 'gC/m^2', },

      { 'jsontag': 'OrganicNitrogenSum', 'axesnum':6, 'units': 'gN/m^2', },

      { 'jsontag': 'AvailableNitrogenSum', 'axesnum':7, 'units': 'gN/m^2', },
      { 'jsontag': 'NitrogenUptakeAll', 'axesnum':7, 'units': 'gN/m^2', },
    ] 
  },
}
