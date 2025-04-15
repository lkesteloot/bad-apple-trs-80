
from itertools import batched

INDIRECT_ASM_CODE = """
        .org 4000h

main
        ld ix,frames

next_frame
        ld hl,15360

        ; Delay a bit, otherwise it runs at 2x speed.
        ld de,1400
wait
        dec de
        ld a,d
        or e
        jr nz,wait

loop
        ; Get the next byte of data.
        ld a,(ix)
        inc ix

        ; See if we're at the end of the frame.
        or a
        jp z,end_of_frame

        ; See if it's a length of 128 (blank).
        ld c,a
        and a,0xc0
        jr z,rle_128

        ; See if it's a length of 191 (full).
        cp 0xc0
        jr z,rle_191

        ; Literal.
        ld (hl),c
        inc hl
        jp loop

        ; c has number of 128 to write.
rle_128
        ld b,0 ; Can move to top?
        dec c ; Build into data?
        ld de,hl
        inc de
        ld (hl),128
        ldir
        inc hl
        jp loop

        ; c has number of 191 to write.
rle_191
        ld b,0 ; Can move to top?
        ld a,c
        and a,0x3F
        ld c,a
        dec c ; Build into data?
        ld de,hl
        inc de
        ld (hl),191
        ldir
        inc hl
        jp loop

end_of_frame
        ; See if it's end of data.
        ld a,(ix)
        or a
        jp nz, next_frame

        jp $

frames"""

def load_pgm(pathname):
    lines = open(pathname).readlines()
    assert lines[0] == "P2\n"
    assert lines[1] == "128 48\n"
    assert lines[2] == "255\n"
    image = [[p >= 186 for p in [int(p) for p in row.split()]] for row in lines[3:]]
    return image

def convert_to_chars(image):
    chars = []

    for y in range(16):
        for x in range(64):
            char = 128 + (image[y*3    ][x*2    ] << 0) + \
                         (image[y*3    ][x*2 + 1] << 1) + \
                         (image[y*3 + 1][x*2    ] << 2) + \
                         (image[y*3 + 1][x*2 + 1] << 3) + \
                         (image[y*3 + 2][x*2    ] << 4) + \
                         (image[y*3 + 2][x*2 + 1] << 5)
            chars.append(char)

    return chars

def run_length_encode(chars):
    # (char, count) pairs.
    rle = []

    for char in chars:
        if len(rle) == 0 or rle[-1][0] != char:
            rle.append( (char, 0) )
        rle[-1] = (rle[-1][0], rle[-1][1] + 1)

    return rle

def rle_to_direct_asm(rle):
    asm = []
    addr = 15360
    asm.append(f"        ld hl,{addr}")
    asm.append(f"        ld de,{addr + 1}")
    for char, count in rle:
        asm.append(f"        ld (hl),{char}")
        if count == 1:
            asm.append("        inc hl")
            asm.append("        inc de")
        else:
            asm.append(f"        ld bc,{count}")
            # LDIR = copy (HL) to (DE), increment both, decrement BC.
            asm.append("        ldir")
    return asm

def rle_to_indirect_asm(rle):
    # Top two bits of byte:
    # 00: Lower 6 bits are number of 128 bytes.
    # 01: Unused, could use next byte as run, or specify number of literal bytes, or audio.
    # 10: Byte is written once.
    # 11: Lower 6 bits are number of 191 bytes.
    # All-zero byte means end of frame. Two all-zero bytes means end of sequence.
    data = []
    for char, count in rle:
        while count > 0:
            this_count = min(count, 63)
            if this_count == 1 or (char != 128 and char != 191):
                data.extend([char] * this_count)
            elif char == 128:
                data.append(this_count)
            elif char == 191:
                data.append(this_count | 0xC0)
            else:
                print(char, this_count)
                assert False
            count -= this_count

    # End of frame.
    data.append(0)

    asm = []
    for line in batched(data, 8):
        asm.append("        .byte " + ",".join("0x%02x" % b for b in line))

    return asm

def main():
    direct_asm = []
    direct_asm.append("        .org 5200h")

    indirect_asm = []
    indirect_asm.extend(INDIRECT_ASM_CODE.split("\n"))

    begin = 230
    begin = 35
    # begin = 600 # Drop apple.
    end = begin + 60
    end = begin + 490
    for i in range(begin, end):
        image = load_pgm("converted_images/bad_apple_%03d.pgm" % i)
        chars = convert_to_chars(image)
        rle = run_length_encode(chars)
        direct_asm.extend(rle_to_direct_asm(rle))
        indirect_asm.append(f"        ; Frame {i}")
        indirect_asm.extend(rle_to_indirect_asm(rle))

    direct_asm.append("        jp $")

    if False:
        print("\n".join(direct_asm) + "\n")
    else:
        indirect_asm.append("        ; End of frames")
        indirect_asm.append("        .byte 0x00")
        indirect_asm.append("")
        indirect_asm.append("        end main")
        print("\n".join(indirect_asm) + "\n")

main()
