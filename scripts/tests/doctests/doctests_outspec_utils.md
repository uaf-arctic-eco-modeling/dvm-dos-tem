Load library

    >>> import outspec_utils as ou

Read the sample file that ships with the code:

    >>> data = ou.csv_file_to_data_dict_list("../config/output_spec.csv")

Turn everything off:

    >>> data2 = ou.all_vars_off(data)

Write it to a file:

    >>> ou.write_data_to_csv(data2, "/tmp/test-outspec_utils.csv")

Now read in the file we just created and verify that there are no variables
enabled.

    >>> ou.cmdline_entry(['--summary','/tmp/test-outspec_utils.csv'])
                    Name                Units       Yearly      Monthly        Daily          PFT Compartments       Layers    Data Type     Description
    0

Enable a single variable (AVLN, yearly, by layer) and write out again

    >>> data2 = ou.toggle_on_variable(data2, "AVLN", 'yearly layer')
    >>> ou.write_data_to_csv(data2, "/tmp/test-outspec_utils.csv")

Check summary for that single variable

    >>> ou.cmdline_entry(['--summary','/tmp/test-outspec_utils.csv'])
                    Name                Units       Yearly      Monthly        Daily          PFT Compartments       Layers    Data Type     Description
                    AVLN                 g/m2            y                   invalid      invalid      invalid            l       double     Total soil available N
    0

Looking at the original file however, there should be only the default variable(s) enabled:

    >>> ou.cmdline_entry(['-s', '../config/output_spec.csv'])
                    Name                Units       Yearly      Monthly        Daily          PFT Compartments       Layers    Data Type     Description
                     GPP            g/m2/time            y                   invalid                                invalid       double     GPP
    0

Enable all yearly variables at the highest detail possible in the test file

    >>> ou.cmdline_entry(['--max-yearly','/tmp/test-outspec_utils.csv'])
    0

Enable all monthly variables at the highest detail possible in the test file

    >>> ou.cmdline_entry(['--max-monthly','/tmp/test-outspec_utils.csv'])
    0

Enable all variables at the highest resolution possible in the test file

    >>> ou.cmdline_entry(['--max-output','/tmp/test-outspec_utils.csv'])
    WARNING! Invalid TIME setting detected! You won't get output for NDRAIN
    0

Clear the test file and check that it is actually empty

    >>> ou.cmdline_entry(['--empty','/tmp/test-outspec_utils.csv'])
    0
    >>> ou.cmdline_entry(['--summary','/tmp/test-outspec_utils.csv'])
                    Name                Units       Yearly      Monthly        Daily          PFT Compartments       Layers    Data Type     Description
    0

Check available options for a single variable

    >>> ou.cmdline_entry(['--show-options','NPP','../config/output_spec.csv'])
    ['Yearly', 'Monthly', 'PFT', 'Compartments']
    0
