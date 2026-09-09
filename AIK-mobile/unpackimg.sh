#!/system/bin/sh

#
# AIK Next - Universal Android Image Unpacker
# Single file version
#
# Supports:
# Android boot header v0-v4
# vendor_boot v4 fragments
# zstd/lz4/gzip/xz/lzo
#

set -u


#######################################
# Paths
#######################################

aik="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
bin="$aik/bin"
bb="$bin/busybox"

cd "$aik" || exit 1


#######################################
# Global vars
#######################################

img=""
imgtype=""
header_version=""
compression=""
frag_real=false

#######################################
# Work directory
#######################################

img_name="$(basename "$img")"
img_name="${img_name%.*}"

work_dir="$aik/$img_name"

split_dir="$work_dir/split_img"
ramdisk_dir="$work_dir/ramdisk"
config_dir="$split_dir/config"

metadata_dir="$work_dir/metadata"
log_dir="$work_dir/logs"

#######################################
# Utils
#######################################

log()
{
    echo "$*"
}


abort()
{
    echo "...Error!"
    exit 1
}


need_file()
{
    [ -f "$1" ] || {
        echo "Missing: $1"
        abort
    }
}


#######################################
# Cleanup
#######################################

cleanup()
{
    rm -rf "$work_dir"

    mkdir -p "$split_dir"
    mkdir -p "$ramdisk_dir"
    mkdir -p "$config_dir"
    mkdir -p "$metadata_dir"
    mkdir -p "$log_dir"
}

#######################################
# Compression detection
#######################################

detect_compression()
{
    f="$1"

    "$bin/file" -m "$bin/magic" "$f" 2>/dev/null |
    "$bb" cut -d: -f2 |
    "$bb" awk '{print $1}'
}


decompress()
{
    src="$1"
    dst="$2"
    comp="$3"


    case "$comp" in

        zstd|zst)
            log "...Decompressing ZSTD: $src"
            "$bin/zstd" -dc "$src" > "$dst" || return 1
            ;;


        lz4|lz4-l)
            log "...Decompressing LZ4: $src"
            "$bin/lz4" -dc "$src" > "$dst" || return 1
            ;;


        gzip|gz)
            log "...Decompressing GZIP: $src"
            "$bin/gzip" -dc "$src" > "$dst" || return 1
            ;;


        xz|lzma)
            log "...Decompressing XZ: $src"
            "$bin/xz" -dc "$src" > "$dst" || return 1
            ;;


        lzo)
            log "...Decompressing LZO: $src"
            "$bin/lzop" -dc "$src" > "$dst" || return 1
            ;;


        cpio|data|empty)
            cp "$src" "$dst" || return 1
            ;;


        *)
            echo "Unsupported compression: $comp"
            return 1
            ;;

    esac

    return 0
}



#######################################
# Image detection
#######################################

detect_image()
{

    need_file "$img"


    test=$(
        "$bin/file" \
        -m "$bin/androidbootimg.magic" \
        "$img" 2>/dev/null |
        "$bb" cut -d: -f2
    )


    imgtype=$(
        echo "$test" |
        "$bb" awk '{print $1}'
    )


    echo "$imgtype" > "$split_dir/image_type"


    case "$imgtype" in

        AOSP|AOSP_VNDR)
            ;;

        *)
            echo "Unknown image type: $imgtype"
            ;;
    esac

}



#######################################
# Header parser
#######################################

parse_header()
{

    header=$(
        "$bin/unpackbootimg" \
        -i "$img" 2>&1
    )


    echo "$header" > "$config_dir/unpackbootimg.log"


    header_version=$(
        echo "$header" |
        "$bb" awk '/BOARD_HEADER_VERSION/ {print $2}'
    )


    if [ -z "$header_version" ]; then

        header_version=$(
            echo "$header" |
            "$bb" awk '/HEADER_VERSION/ {print $2}'
        )

    fi


    if [ -z "$header_version" ]; then
        header_version=0
    fi


    echo "$header_version" \
        > "$config_dir/header_version"


    log "header_version=$header_version"

}

#######################################
# Start
#######################################

main_init()
{

    if [ $# -lt 1 ]; then
        echo "Usage:"
        echo "$0 image.img"
        exit 1
    fi


    img="$(readlink -f "$1")"
    img_name="$(basename "$img")"
    img_name="${img_name%.*}"

    work_dir="$aik/$img_name"

    split_dir="$work_dir/split_img"
    ramdisk_dir="$work_dir/ramdisk"
    config_dir="$split_dir/config"

    metadata_dir="$work_dir/metadata"
    log_dir="$work_dir/logs"

    cleanup


    log
    log "Android Image Kitchen Next"
    log "Workdir: $work_dir"
    log


    detect_image
    parse_header

}
#######################################
# CPIO handling
#######################################

extract_cpio()
{
    cpio_file="$1"
    out_dir="$2"


    mkdir -p "$out_dir" || return 1


    (
        cd "$out_dir" || exit 1

        "$bin/bootpatch" cpio "$cpio_file" extract
    )

    return $?
}

save_metadata()
{
    dir="$1"
    out="$2"

    (
        cd "$dir" || exit 1

        "$bb" find . \( -type f -o -type d \) |
        while read f
        do
            "$bb" stat \
                -c "%n %u %g %a" "$f" \
                >> "$out"
        done
    )
}


#######################################
# Legacy ramdisk unpack
#######################################

unpack_ramdisk()
{
    ramdisk="$1"


    [ -f "$ramdisk" ] || return 1


    comp=$(detect_compression "$ramdisk")


    log "...Ramdisk compression: $comp"


    cpio="$config_dir/ramdisk.cpio"


    decompress \
        "$ramdisk" \
        "$cpio" \
        "$comp" || abort



    extract_cpio \
        "$cpio" \
        "$ramdisk_dir" || abort



    save_metadata \
        "$ramdisk_dir" \
        "$config_dir/perm.txt"

}



#######################################
# Find boot ramdisk
#######################################

find_ramdisk()
{

    cd "$split_dir" || return 1


    for f in *
    do

        case "$f" in

            *ramdisk*)
                echo "$split_dir/$f"
                return 0
                ;;

        esac

    done


    return 1
}



#######################################
# Boot image v0-v2
#######################################

unpack_boot_v0_v2()
{

    log "...Unpacking legacy boot image"


    rd=$(find_ramdisk)


    [ -n "$rd" ] || {
        echo "Ramdisk not found"
        abort
    }


    unpack_ramdisk "$rd"

}



#######################################
# Boot image v3
#######################################

unpack_boot_v3()
{

    log "...Unpacking boot header v3"


    rd=$(find_ramdisk)


    [ -n "$rd" ] || abort


    unpack_ramdisk "$rd"

}



#######################################
# Boot image v4
#######################################

unpack_boot_v4()
{

    log "...Unpacking boot header v4"


    rd=$(find_ramdisk)


    [ -n "$rd" ] || abort


    unpack_ramdisk "$rd"

}



#######################################
# Boot dispatcher
#######################################

unpack_boot()
{

    case "$header_version" in

        0|1|2)
            unpack_boot_v0_v2
            ;;


        3)
            unpack_boot_v3
            ;;


        4)
            unpack_boot_v4
            ;;


        *)
            echo "Unsupported header version"
            abort
            ;;

    esac

}
#######################################
# vendor_boot v4
#######################################

parse_vendor_fragments()
{
    log "...Parsing vendor ramdisk fragments"


    # unpackbootimg должен создать vendor_ramdisk*
    # в split_img

    cd "$work_dir" || abort

    index=0
    for rd in vendor_ramdisk/*.cpio
    do

        [ -f "$rd" ] || continue


        case "$rd" in
            *.cpio|*.txt|*comp)
                continue
                ;;
        esac


        comp=$(detect_compression "$rd")


        case "$comp" in

            zstd)
                ext="zstd"
                ;;

            lz4|lz4-l)
                ext="lz4"
                ;;

            *)
                ext="$comp"
                ;;

        esac


        conf="$config_dir/fragment$(printf "%02d" "$index").conf"


        {
            echo "index=$index"
            echo "file=$rd"
            echo "compression=$ext"
        } > "$conf"



        log "...Decompressing $ext: $rd"


        cpio="$rd"



        out="$aik/vendor_ramdisk$(printf "%02d" "$index")"


        mkdir -p "$out"


        log "...Extracting CPIO: $rd"


        extract_cpio \
            "$cpio" \
            "$out" || abort



        save_metadata \
            "$out" \
            "$config_dir/perm$(printf "%02d" "$index").txt"


        index=$((index+1))

    done


    echo "$index" > "$config_dir/vendor_fragment_count"

}



#######################################
# Detect vendor_boot
#######################################

is_vendor_boot()
{

    "$bin/unpackbootimg" -i "$img" 2>&1 |
    "$bb" grep -q "VNDRBOOT"

}

#######################################
# vendor boot dispatcher
#######################################

unpack_vendor_boot()
{

    log "...Unpacking vendor_boot"


    log "...Splitting vendor ls"


    (
    cd "$work_dir" || exit 1

    "$bin/bootpatch" unpack "$img" || true
)


    parse_vendor_fragments


    frag_real=true


    echo "vendor_boot_v4" \
        > "$config_dir/image_mode"

}

#######################################
# Final
#######################################

finish()
{

    log
    log "...Done!"
    log


    echo "Image type: $imgtype"
    echo "Header version: $header_version"

}



#######################################
# Main
#######################################

main()
{

    main_init "$@"


    if is_vendor_boot
    then

        unpack_vendor_boot

    else

        unpack_boot

    fi


    finish

}



main "$@"