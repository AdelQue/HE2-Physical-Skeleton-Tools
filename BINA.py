from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Union, Tuple, List, Dict
import struct
from io import BytesIO

def raise_input_error(object, received, *needed):
    msg = f"\nObject \'{object}\' of type {type(object).__name__} needs one of the following input types: {[need.__name__ for need in needed]}\nReceived type \'{type(received).__name__}\' instead."
    raise TypeError(msg)

def hex_string(num: int):
    return str(hex(num)[:2] + hex(num)[2:].upper())

def align_bytes(bina_stream, align_to: int, write=True):
    buffer_loc = bina_stream.tell()
    if (align_to > 0) and (buffer_loc % align_to):
        pad = align_to - buffer_loc % align_to
        if write == True:
            bina_stream.write((0).to_bytes(pad))
        else:
            bina_stream.read(pad)

def seek_string(bina_stream, read_by, big_endian=False) -> str:
    if big_endian:
        endianness = 'big'
    else:
        endianness = 'little'
    cur_offset = bina_stream.tell()
    str_offset = int.from_bytes(bina_stream.read(read_by), endianness)
    bina_stream.seek(str_offset)
    name = read_zero_term_string(bina_stream)
    bina_stream.seek(cur_offset + read_by)
    return name

def read_zero_term_string(stream) -> str:
    name = ""
    while True:
        extract = stream.read(1)
        if extract == b'\x00':
            if name == "":
                return None
            else:
                return name
        else:
            name += extract.decode()


@dataclass(kw_only=True, eq=False)
class BINASegment:
    align_to: int = field(default=4, repr=False)
    name_segment: Optional[Union[None, StringSegment]] = field(default=None, repr=False)
    node_location: int = field(default=0, repr=False)
    pointers: List[Tuple[int, BINASegment]] = field(default_factory=list, repr=False)
    """Use __post_init__ in BINASegment type classes to reset default arguments"""

    def init_require_name(self):
        if isinstance(self.name_segment, str):
            self.name_segment = StringSegment(self.name_segment)
        elif isinstance(self.name_segment, StringSegment):
            self.name_segment = self.name_segment
        else:
            raise_input_error(self, self.name_segment, *[str, StringSegment])

    def add_pointer(self, stream, segment: BINASegment):
        self.pointers.append((stream.tell(), segment))
    
    def clear_pointers(self):
        self.pointers = []
        
    def from_bytes(self, bina_stream, seek_addr:Union[None, int]=None, seek_mode:int=0):
        """User implementation per segment"""
        if seek_addr is not None:
            bina_stream.seek(seek_addr, seek_mode)
        else:
            align_bytes(bina_stream, self.align_to, write=False)
        
    def to_bytes(self) -> BytesIO:
        """User implementation per segment"""
        buffer = BytesIO()
        self.clear_pointers()
        
        # self.add_pointer(buffer, BINASegment())
        # return buffer

    def add_to_bina_segments(self, bina_instance: BINA):
        bina_instance.add_bina_segment(self)

    def update_pointers(self):
        for i, pointer in enumerate(self.pointers):
            self.pointers[i] = (pointer[0] + self.node_location, pointer[1])

    def write_to_bina(self, bina_stream):
        self.node_location = bina_stream.tell()
        buffer = self.to_bytes()
        self.update_pointers()
        bina_stream.write(buffer.getvalue())


@dataclass(eq=True)
class StringSegment(BINASegment):
    name: str
    
    def __post_init__(self):
        self.align_to = 1

    def to_bytes(self) -> BytesIO:
        buffer = BytesIO()
        buffer.write(bytes(self.name, 'ascii'))
        buffer.write((0).to_bytes(1))
        return buffer
    
    
        super().from_bytes(bina_stream, seek_addr, seek_mode)
        self.name = read_zero_term_string(bina_stream)
         

@dataclass(kw_only=True, eq=False)
class BINA:
    version: str = field(default="210", repr=False)
    string_table_offset: int = field(default=0, repr=False)
    string_table_length: int = field(default=0, repr=False)
    offset_table_length: int = field(default=0, repr=False)
    bina_segments: List[BINASegment] = field(default_factory=list, repr=False)
    string_segments: Dict[str, StringSegment] = field(default_factory=dict, repr=False)
    pointers: List[int] = field(default_factory=list, repr=False)

    def add_bina_segment(self, *segments: BINASegment):
        for segment in segments:
            if isinstance(segment, StringSegment):
                self.add_string_segment(segment)
            else:
                if segment not in self.bina_segments:
                    self.bina_segments.append(segment)

    def clear_bina_segments(self):
        self.bina_segments = []

    def add_strings_from_bina_segments(self):
        for segment in self.bina_segments:
            if isinstance(segment.name_segment, StringSegment):
                # self.add_string_segment(segment.name_segment)
                """Retains ID this way instead"""
                name = segment.name_segment.name
                if name not in self.string_segments:
                    self.string_segments[name] = segment.name_segment
                else:
                    segment.name_segment = self.string_segments[name]

    """Doesn't work as intended"""
    def add_string_segment(self, *string_segments: StringSegment):
        for string_segment in string_segments:
            name = string_segment.name
            if name not in self.string_segments:
                self.string_segments[name] = string_segment
            else:
                """Does not retain ID"""
                string_segment = self.string_segments[name]

    def clear_string_segments(self):
        self.string_segments = {}

    def write_all_segments(self, bina_stream):
        for segment in self.bina_segments:
            align_bytes(bina_stream, segment.align_to)
            segment.write_to_bina(bina_stream)
        
        align_bytes(bina_stream, 4)

        self.string_table_offset = bina_stream.tell()

        for name in self.string_segments:
            string_segment = self.string_segments[name]
            string_segment.write_to_bina(bina_stream)

        align_bytes(bina_stream, 4)

        self.string_table_length = bina_stream.tell() - self.string_table_offset

    def update_segment_pointers(self, bina_stream):
        for segment in self.bina_segments:
            for pointers in segment.pointers:
                location, target = pointers
                bina_stream.seek(location)
                bina_stream.write(struct.pack('<Q', target.node_location))

    def write_offset_table(self, bina_stream):
        start = bina_stream.tell()
        offsets = []
        for segment in self.bina_segments:
            for pointer in segment.pointers:
                offsets.append(pointer[0])
        
        last_offset = 0
        offset_difs = []
        for cur_offset in offsets:
            dif = cur_offset - last_offset
            last_offset = cur_offset
            offset_difs.append(dif)

        for dif in offset_difs:
            if dif % 4:
                raise ValueError("Offset dif must be aligned to 4 bytes")
            
            if dif == 0:
                byte_len = 0
                bits_start = '00'
            elif dif <= 0xFC:
                byte_len = 1
                bits_start = '01'
            elif dif <= 0xFFFC:
                byte_len = 2
                bits_start = '10'
            elif dif <= 0xFFFFFFFC:
                byte_len = 4
                bits_start = '11'
            else:
                raise ValueError("Offset length too big")
            
            bits_end = "{0:b}".format(dif >> 2)
            fill_len =  ((byte_len * 8) - 2) - len(bits_end)
            bits_fill = "".join("0" for _ in range(fill_len))
            entry_value = int(bits_start + bits_fill + bits_end, 2)
            bina_stream.write(entry_value.to_bytes(byte_len, 'little'))

        align_bytes(bina_stream, 4)
        self.offset_table_length = bina_stream.tell() - start

    def export_file(self, filepath, big_endian=False):
        tmp_buffer = BytesIO()
        self.write_all_segments(tmp_buffer)
        self.write_offset_table(tmp_buffer)
        self.update_segment_pointers(tmp_buffer)

        filesize = tmp_buffer.getbuffer().nbytes + 0x40

        if big_endian:
            endian_id = 'B'
            esign = '>'
        else:
            endian_id = 'L'
            esign = '<'
        id_string = f'BINA{self.version}{endian_id}'

        with open(filepath, 'wb+') as file:            
            # BINA Header
            file.write(bytes(bytes(id_string, 'ascii')))
            file.write(struct.pack(f'{esign}IHH', filesize, 1, 0))
            align_bytes(file, 0x10)

            # Data Header
            file.write(bytes(bytes('DATA', 'ascii')))
            file.write(struct.pack(f'{esign}I', filesize - 0x10))   # Data size
            file.write(struct.pack(f'{esign}I', self.string_table_offset))   # String Table Offset
            file.write(struct.pack(f'{esign}I', self.string_table_length))   # String Table Size
            file.write(struct.pack(f'{esign}I', self.offset_table_length))   # Offset Table Size
            file.write(struct.pack(f'{esign}H', 0x18))   # Relative Data Offset
            align_bytes(file, 0x20)

            # Data
            file.write(tmp_buffer.getvalue())
