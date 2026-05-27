
#from util.setup_working_directory import mkdir_p
# import os
# import errno

# def mkdir_p(path):
#   '''Emulates the shell's `mkdir -p`.'''
#   try:
#     os.makedirs(path)
#   except OSError as exc:  # Python >2.5
#     if exc.errno == errno.EEXIST and os.path.isdir(path):
#       pass
#     else:
#       raise