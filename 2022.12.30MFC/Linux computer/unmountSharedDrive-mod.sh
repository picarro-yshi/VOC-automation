#!/bin/bash

# This script will accept an argument from the network.sh menu
# and unmount the applicable drive.


# Define the argument
arg="all"


# Define command components
unmountCommand="sudo umount"
unmountLocation="/mnt/$arg"
removeMountLocation="sudo umount $unmountLocation"


function unmountDrive()
	{
	if [ $arg = "all" ]; then
		$unmountCommand /mnt/r
		$unmountCommand /mnt/s
		$unmountCommand /mnt/x
		$unmountCommand /mnt/m
		echo ""
		echo "Unmounting All Drives"
		echo ""
		sleep 1s
	elif [ $arg = "r" ]; then
		$unmountCommand $unmountLocation
		echo ""
		echo "Unmounting R Drive"
		echo ""
		sleep 1s
	elif [ $arg = "s" ]; then
		$unmountCommand $unmountLocation
		echo ""
		echo "Unmounting S Drive"
		echo ""
		sleep 1s
	elif [ $arg = "x" ]; then
		$unmountCommand $unmountLocation
		echo ""
		echo "Unmounting X Drive"
		echo ""
		sleep 1s
	elif [ $arg = "m" ]; then
		$unmountCommand $unmountLocation
		echo ""
		echo "Unmounting M Drive"
		echo ""
		sleep 1s
	else
		echo ""
		echo "Error! Incorrect Argument!"
		echo ""
		sleep 1s
	fi
	}

unmountDrive
