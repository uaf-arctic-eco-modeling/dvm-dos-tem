# run_tests.py
import unittest
import doctest
import util
import os
import shutil

class DoctestTestSuite(unittest.TestSuite):
  '''
  This sub class allows for bundling up all the doctests in a script and
  treating them as a ``unittest.TestSuite``. The main utility here is that we
  can define setup and teardown functions for the test suite, essentially
  allowing for the addition of fixtures to the doctests in a file.

  '''
  def __init__(self, tests=(), setUp=None, tearDown=None):
    super().__init__(tests)
    self.setUp = setUp
    self.tearDown = tearDown

  def run(self, result, debug=False):
    if self.setUp is not None:
      self.setUp()
    super().run(result, debug)
    if self.tearDown is not None:
      self.tearDown()


def custom_setUp():
    # Add your common setup code here
    print("Setting up...")
    '''
     - setup working directory
     - twiddle run mask
     - set output variables
     - run model
    '''
    #util.mkdir_p('/tmp/UtilDoctestTestSuite')
    
    print("Done setting up.")

def custom_tearDown():
    # Add your common teardown code here
    print("Tearing down...")

if __name__ == '__main__':

    suite3 = DoctestTestSuite(
        setUp=custom_setUp,
        tearDown=custom_tearDown,
        tests=doctest.DocFileSuite(
          'doctests/doctests_Sensitivity_calib_mode.md',
        )  
    )

    suite2 = DoctestTestSuite(
        setUp=custom_setUp,
        tearDown=custom_tearDown,
        tests=doctest.DocFileSuite(
        # 'doctests/doctests_outspec_utils.md',
        # 'doctests/doctests_runmask_util.md',
        # #'doctests/doctests_output_utils.rst',
        # 'doctests/doctests_Sensitivity.md',
        'doctests/doctests_param_util.md',
        #'doctests/doctests_qcal.md', # For some reason if this one is not last, it makes param_util fail...
        
    ))
    
    runner = unittest.TextTestRunner()
    
    runner.run(suite2)

    runner.run(suite3)