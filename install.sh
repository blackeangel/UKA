SKIPMOUNT=false
PROPFILE=false
POSTFSDATA=false
LATESTARTSERVICE=false

print_modname() {
  ui_print " "
  ui_print "*********************"
  ui_print "- Установка UKA"
  ui_print "*********************"
  ui_print " "
}

on_install() {
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
    jo_b="$1"
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
  if [ "$ABI" = "x86" ]; then
    ui_print "Wrong arch!"
    ui_print " "
    abort
  fi
  if [ "$ABI2" = "x86" ]; then
    ui_print "Wrong arch!"
    ui_print " "
    abort
  fi
  moun_t /data
  touch /data/a_a
  [ ! -f /data/a_a ] && {
    ui_print "Aborting!"
    ui_print "Failed to read\write '/data' partition!"
    abort
  }
  rm -rf /data/a_a
  ui_print "- Moving files to /system, /data"
  [ ! -d /data/local ] && mkdir -m 755 -p /data/local
  [ ! -d /data/local ] && {
    ui_print "Aborting!"
    ui_print "Failed to create kitchen directory!"
    abort
  }
  rm -rf $MODPATH/*
  mkdir -p $MODPATH/system
  [ ! -d $MODPATH/system ] && {
    ui_print "Aborting!"
    ui_print "Failed to create module directory!"
    abort
  }
  unzip -p "$ZIPFILE" "bin.tar.xz" | tar xJ -C $MODPATH/system >/dev/null
  unzip -o "$ZIPFILE" "uninstall.sh" -d $MODPATH >/dev/null
  unzip -p "$ZIPFILE" "binary.tar.xz" | tar xJ -C /data >/dev/null
  unzip -p "$ZIPFILE" "python39.tar.xz" | tar xJ -C /data/local >/dev/null
  unzip -p "$ZIPFILE" "aik.tar.xz" | tar xJ -C /data/local >/dev/null
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

set_permissions() {
  set_perm_recursive $MODPATH 0 0 0755 0644
  set_perm_recursive $MODPATH/system/bin 0 0 0755 0755
}
