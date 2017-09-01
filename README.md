# outdated-aur-package-installer

Sometimes files installed from AUR packages quit working because they were compiled against local libraries which have been updated since then.

This script allows to search for those files, and reinstall the packages they belong to, in the correct order.

Mostly it is used to update ROS packages in an Arch Linux system, since they rely heavily on boost which is constantly updated.
