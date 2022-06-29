import glob
import os
import sys
import tifffile as tiff
from PIL import Image
import exifread
import numpy as np

from read_data import read_image
from write_data import write_image

#Check if .tiff file is a 2D or 3D image
def evaluate_dimensions(directory: str, starting_file: str):
    #Exifread code from https://stackoverflow.com/questions/46477712/reading-tiff-image-metadata-in-python
    path = directory+starting_file
    f = open(path, 'rb')

    # Return Exif tags
    tags = exifread.process_file(f)
    tags_list = list(tags.keys())

    #Iterate through each image tag
    i = 0
    slices = 1
    while(slices == 1 and i < len(tags_list)):
        tag = tags_list[i]
        
        #Find image description tag
        if "ImageDescription" in tag:
            value = str(tags[tag])
            description_parts = value.split("\n")

            #Iterate through each part of the description
            for part in description_parts:

                #Find number of slices
                if "slices" in part:
                    find_slices = part.split("=")
                    slices = int(find_slices[-1])
        i += 1

    return slices


def _sort_files(directory: str, extension: str, starting_file: str, slices: int) -> list:
    """
    A function to sort the files in a directory by number slice.
    This is useful when dealing with directories of tiff slices rather than volumetric tiff
    """
    unsorted_files = {}
    sorted_files = []
    count = slices

    # Find all files with extension in directory
    path = directory+"/*"+extension
    found = glob.glob(path)

    # Split up file names for sorting
    for obj in found:
        split1 = obj.split(".")
        split2 = split1[0].split(" ")
        split3 = split2[-1].split("_")
        split4 = split3[-1].split("\\")
        unsorted_files[split4[-1]] = obj

    # Sort files
    sorting_list = sorted(unsorted_files)

    # Append full path names to sorted list using sorted file names
    for i in sorting_list:

        # Start appending names to list using user-provided range
        if i in starting_file:
            sorted_files.append(unsorted_files[i])
            count = 1
        elif count < slices:
            sorted_files.append(unsorted_files[i])
            count = count + 1

    return sorted_files

# TODO Add option to combine based on indices of desired slices
def _combine_slices(filepath: str, filenames: list) -> np.ndarray:
    """
    Combines individual slices in a stack.
    To control which slices to include, supply a list of filenames
    """

    # Read first slices and determine datatype
    first_slice = read_image(os.path.join(filepath, filenames[0]))
    datatype = first_slice.dtype

    # Create new array for combined file
    combined_stack = np.zeros(
        [len(filenames), first_slice.shape[0], first_slice.shape[1]], dtype=datatype
    )

    # Add first slice to array
    combined_stack[0] = np.array(first_slice)

    # Read each image and add to array
    for count, file in enumerate(filenames[1:], 1):
        next_file = read_image(os.path.join(filepath, file))
        combined_stack[count] = np.array(next_file)

    # Convert array to .tiff file and save it
    print("Final shape of combined stack = ", combined_stack.shape)
    print("-" * 53)
    # Check if bigtiff is needed
    # is_bigtiff = False if combined_stack.nbytes < 4294967296 else True

    write_image(save_path=filepath, save_name=f'combined_stack_0-{len(filenames)}.tif',
                image=combined_stack, filetype='tiff')

    return combined_stack


def convert_filetype(filepath: str, convert_to: str) -> None:

    conversion_list = ['raw', 'tiff', 'tif', 'nc']
    filepath = filepath.replace('\\', '/')
    original_image = read_image(filepath)

    filepath, filename = filepath.rsplit('/', 1)
    basename, extension = filename.rsplit('.', 1)

    assert extension in conversion_list, "Unsupported filetype, cannot convert"

    filename = basename + convert_to.lower()
    write_image(save_path=filepath, save_name=filename, image=original_image, filetype=convert_to)



