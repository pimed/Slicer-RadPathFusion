cmake_minimum_required(VERSION 2.8.9)

project(RadPathFusion)

#-----------------------------------------------------------------------------
set(EXTENSION_HOMEPAGE "http://http://pimed.stanford.edu")
set(EXTENSION_CATEGORY "Radiology-Pathology Fusion")
set(EXTENSION_CONTRIBUTORS "Mirabela Rusu (Stanford)")
set(EXTENSION_DESCRIPTION "Tools for the radiology pathology fusion")
#set(EXTENSION_ICONURL "https://www.slicer.org/w/images/a/a9/Deepinfer-256.png")
#set(EXTENSION_SCREENSHOTURLS "://www.slicer.org/w/images/d/d3/Deepinfer-screenshot1.png")
#-----------------------------------------------------------------------------
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
add_subdirectory(RadPathFusion)

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_CPACK})
