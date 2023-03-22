#!/bin/bash

# This script will accept an argument from the network.sh menu
# and mount the applicable drive.

# Make mount-point parent directories if necessary
sudo mkdir -p /mnt/r
sudo mkdir -p /mnt/s
sudo mkdir -p /mnt/x
sudo mkdir -p /mnt/m

# Define the argument
arg="all"

echo Enter your username
read varname

echo Enter your password
read -s varpass

# Define command components
mountCommand="sudo mount -t cifs"
mountLocation="/mnt/$arg"
mountArgs="-o username=$varname,password=$varpass,domain=CORP,nosetuids,noperm,file_mode=0777,dir_mode=0777"
cajaCommand="caja $mountLocation"

function mountDrive()
	{
	if [ $arg = "all" ]; then
		$mountCommand //10.100.1.172/data /mnt/r $mountArgs
		$mountCommand //10.100.1.172/shared /mnt/s $mountArgs
		$mountCommand //10.100.1.172/temp_space /mnt/x $mountArgs
		$mountCommand //10.100.1.172/MFG /mnt/m $mountArgs
		#caja /mnt/r /mnt/s /mnt/x /mnt/m
		echo ""
		echo "Mounting All Drives"
		echo ""
		sleep 1s
	elif [ $arg = "r" ]; then
		$mountCommand //10.100.1.172/data $mountLocation $mountArgs
		#$cajaCommand
		echo ""
		echo "Mounting R Drive"
		echo ""
		sleep 1s
	elif [ $arg = "s" ]; then
		$mountCommand //10.100.1.172/shared $mountLocation $mountArgs
		#$cajaCommand
		echo ""
		echo "Mounting S Drive"
		echo ""
		sleep 1s
	elif [ $arg = "x" ]; then
		$mountCommand //10.100.1.172/temp_space $mountLocation $mountArgs
		#$cajaCommand
		echo ""
		echo "Mounting X Drive"
		echo ""
		sleep 1s
	elif [ $arg = "m" ]; then
		$mountCommand //10.100.1.172/MFG $mountLocation $mountArgs
		#$cajaCommand
		echo ""
		echo "Mounting M Drive"
		echo ""
		sleep 1s
	else
		echo ""
		echo "Error! Incorrect Argument!"
		echo ""
		sleep 1s
	fi
	}

mountDrive
