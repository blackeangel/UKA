##########################################################################################
#
# Magisk Module Installer Script
#
##########################################################################################
##########################################################################################
#
# Instructions:
#
# 1. Place your files into system folder (delete the placeholder file)
# 2. Fill in your module's info into module.prop
# 3. Configure and implement callbacks in this file
# 4. If you need boot scripts, add them into common/post-fs-data.sh or common/service.sh
# 5. Add your additional or modified system properties into common/system.prop
#
##########################################################################################

##########################################################################################
# Config Flags
##########################################################################################

# Set to true if you do *NOT* want Magisk to mount
# any files for you. Most modules would NOT want
# to set this flag to true
SKIPMOUNT=false

# Set to true if you need to load system.prop
PROPFILE=false

# Set to true if you need post-fs-data script
POSTFSDATA=false

# Set to true if you need late_start service script
LATESTARTSERVICE=false

##########################################################################################
# Replace list
##########################################################################################

# List all directories you want to directly replace in the system
# Check the documentations for more info why you would need this

# Construct your list in the following format
# This is an example
REPLACE_EXAMPLE="
/system/app/Youtube
/system/priv-app/SystemUI
/system/priv-app/Settings
/system/framework
"

# Construct your own list here
REPLACE="
"

##########################################################################################
#
# Function Callbacks
#
# The following functions will be called by the installation framework.
# You do not have the ability to modify update-binary, the only way you can customize
# installation is through implementing these functions.
#
# When running your callbacks, the installation framework will make sure the Magisk
# internal busybox path is *PREPENDED* to PATH, so all common commands shall exist.
# Also, it will make sure /data, /system, and /vendor is properly mounted.
#
##########################################################################################
##########################################################################################
#
# The installation framework will export some variables and functions.
# You should use these variables and functions for installation.
#
# ! DO NOT use any Magisk internal paths as those are NOT public API.
# ! DO NOT use other functions in util_functions.sh as they are NOT public API.
# ! Non public APIs are not guranteed to maintain compatibility between releases.
#
# Available variables:
#
# MAGISK_VER (string): the version string of current installed Magisk
# MAGISK_VER_CODE (int): the version code of current installed Magisk
# BOOTMODE (bool): true if the module is currently installing in Magisk Manager
# MODPATH (path): the path where your module files should be installed
# TMPDIR (path): a place where you can temporarily store files
# ZIPFILE (path): your module's installation zip
# ARCH (string): the architecture of the device. Value is either arm, arm64, x86, or x64
# IS64BIT (bool): true if $ARCH is either arm64 or x64
# API (int): the API level (Android version) of the device
#
# Availible functions:
#
# ui_print <msg>
#     print <msg> to console
#     Avoid using 'echo' as it will not display in custom recovery's console
#
# abort <msg>
#     print error message <msg> to console and terminate installation
#     Avoid using 'exit' as it will skip the termination cleanup steps
#
# set_perm <target> <owner> <group> <permission> [context]
#     if [context] is empty, it will default to "u:object_r:system_file:s0"
#     this function is a shorthand for the following commands
#       chown owner.group target
#       chmod permission target
#       chcon context target
#
# set_perm_recursive <directory> <owner> <group> <dirpermission> <filepermission> [context]
#     if [context] is empty, it will default to "u:object_r:system_file:s0"
#     for all files in <directory>, it will call:
#       set_perm file owner group filepermission context
#     for all directories in <directory> (including itself), it will call:
#       set_perm dir owner group dirpermission context
#
##########################################################################################
##########################################################################################
# If you need boot scripts, DO NOT use general boot scripts (post-fs-data.d/service.d)
# ONLY use module scripts as it respects the module status (remove/disable) and is
# guaranteed to maintain the same behavior in future Magisk releases.
# Enable boot scripts by setting the flags in the config section above.
##########################################################################################

# Set what you want to display when installing your module

print_modname() {
ui_print " "
ui_print "*********************"
ui_print "- Установка UKA"
ui_print "*********************"
ui_print " "
}

# Copy/extract your module files into $MODPATH in on_install.

on_install() {
  # The following is the default implementation: extract $ZIPFILE/system to $MODPATH
  # Extend/change the logic to whatever you want
ui_print "- Mounting /system, /data, and rootfs"

sys_mount=/system

is_mounted() {
if [ ! -z "$2" ]; then
cat /proc/mounts | grep -e $1 | grep -e $2 >/dev/null
else
cat /proc/mounts | grep -e $1 >/dev/null
fi
return $?
}
moun_t() {
jo_b="$1";
if (is_mounted ${jo_b}); then
mount -o rw,remount ${jo_b}
else
mount ${jo_b}
mount -o rw,remount ${jo_b}
fi
}
moun_t "/"
if [ -e $sys_mount ]; then
moun_t $sys_mount
else
ui_print " "
ui_print "Aborting! Failed to find system mountpoint!"
ui_print " "
abort
fi
if [ -f $sys_mount/build.prop ]; then
sys_tem="$sys_mount"
else
	if [ -f $sys_mount/system/build.prop ]; then
	sys_tem="$sys_mount/system"
	else
	ui_print " "
	ui_print "Aborting! Failed to find system root!"
	ui_print " "
	abort
	fi
fi
ABI=$(cat $sys_tem/build.prop | grep ro.product.cpu.abi= | dd bs=1 skip=19 count=3)
ABI2=$(cat $sys_tem/build.prop | grep ro.product.cpu.abi2= | dd bs=1 skip=20 count=3)

ARCH=arm
if [ "$ABI" = "x86" ]; then ui_print "Wrong arch!"; ui_print " "; abort; fi;
if [ "$ABI2" = "x86" ]; then ui_print "Wrong arch!"; ui_print " "; abort; fi;
moun_t /data
touch /data/a_a;
[ ! -f /data/a_a ] && { ui_print "Aborting!"; ui_print "Failed to read\write '/data' partition!"; abort; }
rm -rf /data/a_a
ui_print "- Moving files to /system, /data"
[ ! -d /data/local ] && mkdir -m 755 -p /data/local
[ ! -d /data/local ] && { ui_print "Aborting!"; ui_print "Failed to create kitchen directory!"; abort; }
rm -rf  $MODPATH/*;
mkdir -p $MODPATH/system;
[ ! -d $MODPATH/system ] && { ui_print "Aborting!"; ui_print "Failed to create module directory!"; abort; }
unzip -p "$ZIPFILE" "bin.tar.xz" |tar xJ -C $MODPATH/system >/dev/null
#unzip -p "$ZIPFILE" "lib.tar.xz" |tar xJ -C $MODPATH/system >/dev/null
unzip -o "$ZIPFILE" "uninstall.sh" -d $MODPATH >/dev/null
unzip -p "$ZIPFILE" "binary.tar.xz" |tar xJ -C /data >/dev/null
#unzip -p "$ZIPFILE" "python39.tar.xz" |tar xJ -C /data/local >/dev/null
unzip -p "$ZIPFILE" "python31.tar.xz" |tar xJ -C /data/local >/dev/null
unzip -p "$ZIPFILE" "aik.tar.xz" |tar xJ -C /data/local >/dev/null
  #Create work folders
  ui_print "- Creating working folders"
  folder_list="UnpackerContexts UnpackerPayload UnpackerPreloader UnpackerQfil UnpackerSuper UnpackerSystem UnpackerUpdateApp"
  for folder in $folder_list; do
    [ ! -d /data/local/$folder ] && mkdir -m 755 -p /data/local/$folder
  done
  ui_print "- Creating working files"
  /data/local/binary/make_ext4fs -l 268435456 /data/local/AIK-mobile/bin/ramdisk.img  >/dev/null
ui_print "- Unmounting /system, /data, and rootfs"
mount -o ro,remount "/" 2>/dev/null
mount -o ro,remount "$sys_mount" 2>/dev/null
ui_print "- Done !"
}

# Only some special files require specific permissions
# This function will be called after on_install is done
# The default permissions should be good enough for most cases

set_permissions() {
  # The following is the default rule, DO NOT remove
  set_perm_recursive $MODPATH 0 0 0755 0644

  # Here are some examples:
  # set_perm_recursive  $MODPATH/system/lib       0     0       0755      0644
  # set_perm  $MODPATH/system/bin/app_process32   0     2000    0755      u:object_r:zygote_exec:s0
  # set_perm  $MODPATH/system/bin/dex2oat         0     2000    0755      u:object_r:dex2oat_exec:s0
  # set_perm  $MODPATH/system/lib/libart.so       0     0       0644  set_perm $MODPATH/system/$bin/systemize 0 0 0777
  set_perm_recursive $MODPATH/system/bin 0 0 0755 0755
  #set_perm $MODPATH/system/lib/libcap.so.2 0 0 0644
}

# You can add more functions to assist your custom script code
