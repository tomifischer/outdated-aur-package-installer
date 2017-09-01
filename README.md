# Motivation

Sometimes files installed from AUR packages quit working because they were compiled against local libraries which have been updated since then.

This script allows to search for those files, and reinstall the packages they belong to, in the correct order.

Mostly it is used to update ROS packages in an Arch Linux system, since they rely heavily on boost which is constantly updated.

# Example

As an example, suppose we have a ROS installation under /opt/ros/kinetic and the system boost libraries have since the last (re-)installation been updated from 1.63 to 1.64.
Many ROS libraries will be linked to boost 1.63 and need to be recompiled. Knowing this, we can execute the script

  `./search-and-install.py -i /opt/ros/kinetic boost 1.63`

which will reinstall every ROS package with outdated files.

Ignoring the installation flag (-i) will only print the outdated packages to the screen.
