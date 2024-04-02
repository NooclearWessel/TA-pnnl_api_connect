# encoding = utf-8
import os
###################################################################################################################
#
#                                               Splunk Functions
#
###################################################################################################################

def readCheckpoint(checkpoint_file_path):
    try:
        with open(checkpoint_file_path, 'r') as file:
            return file.read()
    except:
        with open(checkpoint_file_path, "a") as file:
            file.write("")
            return

def writeCheckpoint(checkpoint_file_path, value):
    with open(checkpoint_file_path, "w") as file:
        file.write(value)
    file.close
    return

def getCheckpointFile(inputs, checkpoint_file_name):
    return os.path.join(_getCheckpointPath(inputs), checkpoint_file_name + ".txt")

def _getCheckpointPath(inputs):
    	return inputs.metadata["checkpoint_dir"]


