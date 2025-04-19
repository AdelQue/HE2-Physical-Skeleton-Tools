from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Union, Tuple, List
import struct
import math
from io import BytesIO
from BINA import *

RMS = math.sqrt(2) / 2

@dataclass(eq=False)
class PBAHeader(BINASegment):
    name_segment: Optional[Union[str, StringSegment]]
    has_softbody: int = field(default=1, repr=False)

    rigidbody_count: int = field(default=0, repr=True)
    rigidbody_offset: int = field(default=0, repr=False)
    rigidbody_segment: Optional[Union[None, BINASegment]] = field(default=None, repr=False)

    constraint_count: int = field(default=0, repr=True)
    constraint_offset: int = field(default=0, repr=False)
    constraint_segment: Optional[Union[None, BINASegment]] = field(default=None, repr=False)

    softbody_count: int = field(default=0, repr=True)
    softbody_offset: int = field(default=0, repr=False)
    softbody_segment: Optional[Union[None, BINASegment]] = field(default=None, repr=False)
    
    def __post_init__(self, **kwargs):
        super().init_require_name(**kwargs)
        self.align_to = 16
    
    def from_bytes(self, bina_stream, seek_addr=None, seek_mode=0):
        super().from_bytes(bina_stream, seek_addr, seek_mode)
        
        magic = bina_stream.read(4).decode()
        self.has_softbody = struct.unpack('<i', bina_stream.read(4))[0]
        self.name_segment = StringSegment(name=seek_string(bina_stream, 8))

        self.rigidbody_count, self.constraint_count = struct.unpack('<II', bina_stream.read(8))
        self.rigidbody_offset, self.constraint_offset = struct.unpack('<QQ', bina_stream.read(16))

        self.softbody_count= struct.unpack('<I', bina_stream.read(4))[0]
        bina_stream.read(4)
        self.softbody_offset= struct.unpack('<Q', bina_stream.read(8))[0]
        bina_stream.read(8)

    def to_bytes(self) -> BytesIO:
        buffer = BytesIO()
        self.clear_pointers()

        buffer.write(bytes('PBA ', 'ascii'))
        buffer.write(struct.pack('<i', self.has_softbody))

        self.add_pointer(buffer, self.name_segment)
        buffer.write(struct.pack('<Q', self.name_segment.node_location))

        buffer.write(struct.pack('<II', self.rigidbody_count, self.constraint_count))

        if self.rigidbody_count > 0 and self.rigidbody_segment is not None:
            self.add_pointer(buffer, self.rigidbody_segment)
            self.rigidbody_offset = self.rigidbody_segment.node_location
        buffer.write(struct.pack('<Q', self.rigidbody_offset))

        if self.constraint_count > 0 and self.constraint_segment is not None:
            self.add_pointer(buffer, self.constraint_segment)
            self.constraint_offset = self.constraint_segment.node_location
        buffer.write(struct.pack('<Q', self.constraint_offset))

        buffer.write(struct.pack('<II', self.softbody_count, 0))
        
        if self.softbody_count > 0 and self.softbody_segment is not None:
            self.add_pointer(buffer, self.softbody_segment)
            self.softbody_offset = self.softbody_segment.node_location
        buffer.write(struct.pack('<QQ', self.softbody_offset, 0))   
                         
        return buffer


@dataclass(eq=False)
class PBARigidBody(BINASegment):
    name_segment: Optional[Union[str, StringSegment]]
    bStaticObject: bool = field(default=False, repr=False)
    bIsBox: bool = field(default=False, repr=False)
    unkParam1: int = field(default=0, repr=False)
    unkParam2: int = field(default=0, repr=False)
    shapeRadius: float = field(default=0.1, repr=False)
    shapeHeight: float = field(default=0.0, repr=False)
    unkParam3: float = field(default=0.0, repr=False)
    gravityMultiplier: float = field(default=0.1, repr=False)
    friction: float = field(default=1.0, repr=False)
    resitution: float = field(default=0.5, repr=False)
    linearDamping: float = field(default=0.5, repr=False)
    angularDamping: float = field(default=0.5, repr=False)
    offsetPosition: Tuple[float, float, float] = field(default_factory=tuple, repr=False)
    offsetRotation: Tuple[float, float, float, float] = field(default_factory=tuple, repr=False)

    def __post_init__(self, **kwargs):
        super().init_require_name(**kwargs)
        self.align_to = 8
        if self.offsetPosition == ():
            self.offsetPosition = (0.0, 0.0, 0.0)
        if self.offsetRotation == ():
            self.offsetRotation = (RMS, 0.0, 0.0, -RMS)

    def from_bytes(self, bina_stream, seek_addr = None, seek_mode = 0):
        super().from_bytes(bina_stream, seek_addr, seek_mode)
        self.name_segment = StringSegment(name=seek_string(bina_stream, 8))
        self.bStaticObject, self.bIsBox = [bool(x) for x in struct.unpack('<??', bina_stream.read(2))]
        self.unkParam1, self.unkParam2 = struct.unpack('<bb', bina_stream.read(2))
        self.shapeRadius, self.shapeHeight, self.unkParam3, self.gravityMultiplier = struct.unpack('<ffff', bina_stream.read(16))
        self.friction, self.resitution, self.linearDamping, self.angularDamping = struct.unpack('<ffff', bina_stream.read(16))
        align_bytes(bina_stream, 16, write=False)
        self.offsetPosition = struct.unpack('<fff', bina_stream.read(12))
        align_bytes(bina_stream, 16, write=False)
        self.offsetRotation = struct.unpack('<ffff', bina_stream.read(16))

    def to_bytes(self) -> BytesIO:
        buffer = BytesIO()
        self.clear_pointers()
        self.add_pointer(buffer, self.name_segment)
        buffer.write(struct.pack('<Q', self.name_segment.node_location))
        buffer.write(struct.pack('<??bb', self.bStaticObject, self.bIsBox, self.unkParam1, self.unkParam2))
        buffer.write(struct.pack('<f', self.shapeRadius))
        buffer.write(struct.pack('<f', self.shapeHeight))
        buffer.write(struct.pack('<f', self.unkParam3))
        buffer.write(struct.pack('<f', self.gravityMultiplier))
        buffer.write(struct.pack('<f', self.friction))
        buffer.write(struct.pack('<f', self.resitution))
        buffer.write(struct.pack('<f', self.linearDamping))
        buffer.write(struct.pack('<f', self.angularDamping))
        buffer.write(struct.pack('<f', 0))
        posX, posY, posZ = self.offsetPosition
        buffer.write(struct.pack('<ffff', posX, posY, posZ, 0))
        rotX, rotY, rotZ, rotW = self.offsetRotation
        buffer.write(struct.pack('<ffff', rotX, rotY, rotZ, rotW))
        return buffer


@dataclass(eq=False)
class PBAConstraint(BINASegment):
    @dataclass
    class Limit:
        flags: int = field(default=2, repr=False)   # 1 disabled, 2 enabled
        enabledSpring: bool = field(default=False, repr=False)
        lowLimit: float = field(default=0.0, repr=False)
        highLimit: float = field(default=0.0, repr=False)
        springStiffness: float = field(default=0.0, repr=False)
        springDamping: float = field(default=0.0, repr=False)
    
    name_segment: Optional[Union[str, StringSegment]]
    unknown1: int = field(default=1, repr=False)
    unknown2: int = field(default=1, repr=False)
    numIterations: int = field(default=20, repr=False)
    localParentBoneIndex: int = field(default=-1, repr=False)
    localBoneIndex: int = field(default=-1, repr=False)
    realParentBoneIndex: int = field(default=-1, repr=False)
    limits: List[Limit] = field(default_factory=list, repr=False)
    offsetPosition1: Tuple[float, float, float] = field(default_factory=tuple, repr=False)
    offsetRotation1: Tuple[float, float, float, float] = field(default_factory=tuple, repr=False)
    offsetPosition2: Tuple[float, float, float] = field(default_factory=tuple, repr=False)
    offsetRotation2: Tuple[float, float, float, float] = field(default_factory=tuple, repr=False)

    def __post_init__(self, **kwargs):
        super().init_require_name(**kwargs)

        self.align_to = 16
        if self.offsetPosition1 == ():
            self.offsetPosition1 = (0.0, 0.0, 0.0)
        if self.offsetPosition2 == ():
            self.offsetPosition2 = (0.0, 0.0, 0.0)

        if self.offsetRotation1 == ():
            self.offsetRotation1 = (1.0, 0.0, 0.0, 0.0)
        if self.offsetRotation2 == ():
            self.offsetRotation2 = rotation = (RMS, 0.0, 0.0, RMS)
        
        if len(self.limits) != 6:
            self.limits = [self.Limit() for _ in range(6)]

    def from_bytes(self, bina_stream, seek_addr=None, seek_mode=0):
        super().from_bytes(bina_stream, seek_addr, seek_mode)

        self.name_segment = StringSegment(name=seek_string(bina_stream, 8))
        self.unknown1, self.unknown2 = struct.unpack('<bb', bina_stream.read(2))
        self.numIterations, self.localParentBoneIndex = struct.unpack('<hh', bina_stream.read(4))
        self.localBoneIndex, self.realParentBoneIndex = struct.unpack('<hh', bina_stream.read(4))
        align_bytes(bina_stream, 4, write=False)
        self.limits = []
        for _ in range(6):
            limit = self.Limit()
            limit.flags = struct.unpack('<b', bina_stream.read(1))[0]
            limit.enabledSpring = bool(struct.unpack('<?', bina_stream.read(1))[0])
            align_bytes(bina_stream, 4, write=False)
            limit.lowLimit, limit.highLimit = struct.unpack('<ff', bina_stream.read(8))
            limit.springStiffness, limit.springDamping = struct.unpack('<ff', bina_stream.read(8))
            self.limits.append(limit)
        align_bytes(bina_stream, 16, write=False)
        self.offsetPosition1 = struct.unpack('<fff', bina_stream.read(12))
        align_bytes(bina_stream, 16, write=False)
        self.offsetRotation1 = struct.unpack('<ffff', bina_stream.read(16))
        align_bytes(bina_stream, 16, write=False)
        self.offsetPosition2 = struct.unpack('<fff', bina_stream.read(12))
        align_bytes(bina_stream, 16, write=False)
        self.offsetRotation2 = struct.unpack('<ffff', bina_stream.read(16))

    def to_bytes(self) -> BytesIO:
        buffer = BytesIO()
        self.clear_pointers()
        self.add_pointer(buffer, self.name_segment)
        buffer.write(struct.pack('<Q', self.name_segment.node_location))
        buffer.write(struct.pack('<bbh', self.unknown1, self.unknown2, self.numIterations))
        buffer.write(struct.pack('<hhh', self.localParentBoneIndex, self.localBoneIndex, self.realParentBoneIndex))
        align_bytes(buffer, 4)

        for limit in self.limits:
            buffer.write(struct.pack('<b?', limit.flags, limit.enabledSpring))
            align_bytes(buffer, 4)
            buffer.write(struct.pack('<ff', limit.lowLimit, limit.highLimit))
            buffer.write(struct.pack('<ff', limit.springStiffness, limit.springDamping))
        
        align_bytes(buffer, 16)
        posX, posY, posZ = self.offsetPosition1
        buffer.write(struct.pack('<fff', posX, posY, posZ))

        align_bytes(buffer, 16)
        rotX, rotY, rotZ, rotW = self.offsetRotation1
        buffer.write(struct.pack('<ffff', rotX, rotY, rotZ, rotW))

        align_bytes(buffer, 16)
        posX, posY, posZ = self.offsetPosition2
        buffer.write(struct.pack('<fff', posX, posY, posZ))

        align_bytes(buffer, 16)
        rotX, rotY, rotZ, rotW = self.offsetRotation2
        buffer.write(struct.pack('<ffff', rotX, rotY, rotZ, rotW))
        align_bytes(buffer, 16)
        return buffer


@dataclass(eq=False)
class PBAClothNode(BINASegment):
    name_segment: Optional[Union[str, StringSegment]]
    mass: float = field(default=0.01, repr=False)
    unknown1: int = field(default=-1, repr=False)
    pinned: bool = field(default=False, repr=False)
    child_idx: int = field(default=-1, repr=False)
    parent_idx: int = field(default=-1, repr=False)
    unknown2: int = field(default=-1, repr=False)
    left_idx: int = field(default=-1, repr=False)
    right_idx: int = field(default=-1, repr=False)

    def __post_init__(self, **kwargs):
        super().init_require_name(**kwargs)

        if self.parent_idx == -1:
            self.pinned = True
        
        self.align_to = 8
    
    def from_bytes(self, bina_stream, seek_addr = None, seek_mode = 0):
        super().from_bytes(bina_stream, seek_addr, seek_mode)

        self.name_segment = StringSegment(name=seek_string(bina_stream, 8))
        self.mass, self.unknown1 = struct.unpack('<fh', bina_stream.read(6))
        self.pinned = bool(struct.unpack('<h', bina_stream.read(2))[0])
        self.child_idx, self.parent_idx = struct.unpack('<hh', bina_stream.read(4))
        self.unknown2 = struct.unpack('<i', bina_stream.read(4))[0]
        self.left_idx, self.right_idx = struct.unpack('<hh', bina_stream.read(4))

    def to_bytes(self) -> BytesIO:
        buffer = BytesIO()
        self.clear_pointers()
        self.add_pointer(buffer, self.name_segment)
        buffer.write(struct.pack('<Q', self.name_segment.node_location))
        buffer.write(struct.pack('<f', self.mass))
        buffer.write(struct.pack('<hh', self.unknown1, self.pinned))
        buffer.write(struct.pack('<hh', self.child_idx, self.parent_idx))
        buffer.write(struct.pack('<i', self.unknown2))
        buffer.write(struct.pack('<hh', self.left_idx, self.right_idx))
        return buffer


@dataclass(eq=False)
class PBAClothLink(BINASegment):
    verts: Tuple[int, int]
    length: float = field(repr=False)
    stiffness: float = field(default=1.0, repr=False)

    def __post_init__(self):
        self.align_to = 4

    def from_bytes(self, bina_stream, seek_addr = None, seek_mode = 0):
        super().from_bytes(bina_stream, seek_addr, seek_mode)
        self.verts = struct.unpack('<hh', bina_stream.read(4))
        self.length, self.stiffness = struct.unpack('<ff', bina_stream.read(8))
    
    def to_bytes(self) -> BytesIO:
        buffer = BytesIO()
        buffer.write(struct.pack('<HH', self.verts[0], self.verts[1]))
        buffer.write(struct.pack('<ff', self.length, self.stiffness))
        return buffer


@dataclass(eq=False)
class PBASoftBody(BINASegment):
    name_segment: Optional[Union[str, StringSegment]]
    scale: float = field(default=0.035, repr=False)
    dampingCoeff: float = field(default=0.035, repr=False)
    dragCoeff: float = field(default=1.0, repr=False)
    liftCoeff: float = field(default=0.0, repr=False)
    dynamicFrictionCoeff: float = field(default=0.1, repr=False)
    poseMatchingCoeff: float = field(default=0, repr=False)
    rigidContactsCoeff: float = field(default=1.0, repr=False)
    kineticContactsHardness: float = field(default=1.0, repr=False)
    softContactsHardness: float = field(default=1.0, repr=False)
    anchorsHardness: float = field(default=0.7, repr=False)
    positionIterations: int = field(default=10, repr=False)
    unknown1: int = field(default=3, repr=False)
    unknown2: int = field(default=31, repr=False)

    cloth_nodes: List[PBAClothNode] = field(default_factory=list, repr=False)
    cloth_nodes_count: int = field(default=0, repr=False)
    cloth_nodes_segment: Optional[Union[None, PBAClothNode]] = field(default=None, repr=False)
    cloth_nodes_offset: int = field(default=0, repr=False)

    cloth_links: List[PBAClothLink] = field(default_factory=list, repr=False)
    cloth_links_count: int = field(default=0, repr=False)
    cloth_links_segment: Optional[Union[None, PBAClothLink]] = field(default=None, repr=False)
    cloth_links_offset: int = field(default=0, repr=False)
    
    def __post_init__(self, **kwargs):
        super().init_require_name(**kwargs)
        self.align_to = 8

    def from_bytes(self, bina_stream, seek_addr = None, seek_mode = 0):
        super().from_bytes(bina_stream, seek_addr, seek_mode)

        self.name_segment = StringSegment(name=seek_string(bina_stream, 8))
        self.scale, self.dampingCoeff = struct.unpack('<ff', bina_stream.read(8))
        self.dragCoeff, self.liftCoeff = struct.unpack('<ff', bina_stream.read(8))
        self.dynamicFrictionCoeff, self.poseMatchingCoeff = struct.unpack('<ff', bina_stream.read(8))
        self.rigidContactsCoeff, self.kineticContactsHardness = struct.unpack('<ff', bina_stream.read(8))
        self.softContactsHardness, self.anchorsHardness = struct.unpack('<ff', bina_stream.read(8))
        self.positionIterations, self.unknown1, self.unknown2 = struct.unpack('<bbh', bina_stream.read(4))
        self.cloth_nodes_count, self.cloth_links_count = struct.unpack('<ii', bina_stream.read(8))
        align_bytes(bina_stream, 8, write=False)
        self.cloth_nodes_offset, self.cloth_links_offset = struct.unpack('<QQ', bina_stream.read(16))

    def to_bytes(self) -> BytesIO:
        buffer = BytesIO()
        self.clear_pointers()
        self.add_pointer(buffer, self.name_segment)
        buffer.write(struct.pack('<Q', self.name_segment.node_location))
        buffer.write(struct.pack('<ff', self.scale, self.dampingCoeff))
        buffer.write(struct.pack('<ff', self.dragCoeff, self.liftCoeff))
        buffer.write(struct.pack('<ff', self.dynamicFrictionCoeff, self.poseMatchingCoeff))
        buffer.write(struct.pack('<ff', self.rigidContactsCoeff, self.kineticContactsHardness))
        buffer.write(struct.pack('<ff', self.softContactsHardness, self.anchorsHardness))
        buffer.write(struct.pack('<bbh', self.positionIterations, self.unknown1, self.unknown2))
        
        self.cloth_nodes_count = len(self.cloth_nodes)
        self.cloth_links_count = len(self.cloth_links)
        buffer.write(struct.pack('<ii', self.cloth_nodes_count, self.cloth_links_count))
        
        align_bytes(buffer, 8)
        
        self.add_pointer(buffer, self.cloth_nodes_segment)
        buffer.write(struct.pack('<Q', self.cloth_nodes_offset))

        self.add_pointer(buffer, self.cloth_links_segment)
        buffer.write(struct.pack('<Q', self.cloth_links_offset))
        
        return buffer

    def add_nodes(self, *nodes: PBAClothNode):
        for node in nodes:
            self.cloth_nodes.append(node)
        self.cloth_nodes_count = len(self.cloth_nodes)
        self.cloth_nodes_segment = self.cloth_nodes[0]
        self.cloth_nodes_offset = self.cloth_nodes_segment.node_location

    def add_links(self, *links: PBAClothLink):
        for link in links:
            self.cloth_links.append(link)
        self.cloth_links_count = len(self.cloth_links)
        self.cloth_links_segment = self.cloth_links[0]
        self.cloth_links_offset = self.cloth_links_segment.node_location
    
    def clear_nodes(self):
        self.cloth_nodes = []
        self.cloth_nodes_count = 0
        self.cloth_nodes_segment = None
    
    def clear_links(self):
        self.cloth_links = []
        self.cloth_links_count = 0
        self.cloth_links_segment = None

@dataclass(eq=False)
class PBA(BINA):
    header: Optional[Union[str, StringSegment, PBAHeader]]
    rigidbodies: List[PBARigidBody] = field(default_factory=list, repr=False)
    constraints: List[PBAConstraint] = field(default_factory=list, repr=False)
    softbodies: List[PBASoftBody] = field(default_factory=list, repr=False)

    def __post_init__(self):
        if isinstance(self.header, str):
            self.header = PBAHeader(StringSegment(self.header))
        elif isinstance(self.header, StringSegment):
            self.header = PBAHeader(self.header)
        elif isinstance(self.header, PBAHeader):
            self.header = self.header
        else:
            raise_input_error(self, self.header, *[str, StringSegment, PBAHeader])

    def add_rigidbody(self, *rigidbodies_in: PBARigidBody):
        for rigidbody in rigidbodies_in:
            if rigidbody not in self.rigidbodies:
                self.rigidbodies.append(rigidbody)
        
        self.header.rigidbody_count = len(self.rigidbodies)
        if self.header.rigidbody_count > 0:
            self.header.rigidbody_segment = self.rigidbodies[0]
            self.header.rigidbody_offset = self.header.rigidbody_segment.node_location
        else:
            self.header.rigidbody_offset = 0
            self.header.rigidbody_segment = None

    def clear_rigidbodies(self):
        self.rigidbodies = []
        self.header.rigidbody_count = 0
        self.header.rigidbody_offset = 0
        self.header.rigidbody_segment = None

    def add_constraint(self, *constraints_in: PBAConstraint):
        for constraint in constraints_in:
            if constraint not in self.constraints:
                self.constraints.append(constraint)

        self.header.constraint_count = len(self.constraints)
        if self.header.constraint_count > 0:
            self.header.constraint_segment = self.constraints[0]
            self.header.constraint_offset = self.header.constraint_segment.node_location
        else:
            self.header.constraint_offset = 0
            self.header.constraint_segment = None

    def clear_constraints(self):
        self.constraints = []
        self.header.constraint_count = 0
        self.header.constraint_offset = 0
        self.header.constraint_segment = None

    def add_softbody(self, *softbodies_in: PBASoftBody):
        for softbody in softbodies_in:
            if softbody not in self.softbodies:
                self.softbodies.append(softbody)

        self.header.softbody_count = len(self.softbodies)
        if self.header.softbody_count > 0:
            self.header.softbody_segment = self.softbodies[0]
            self.header.softbody_offset = self.header.softbody_segment.node_location
        else:
            self.header.softbody_offset = 0
            self.header.softbody_segment = None

    def clear_softbodies(self):
        self.softbodies = []
        self.header.softbody_count = 0
        self.header.softbody_offset = 0
        self.header.softbody_segment = None

    def structure_elements(self):
        self.clear_bina_segments()
        self.clear_string_segments()

        if self.header.rigidbody_count > 0:
            self.header.rigidbody_segment = self.rigidbodies[0]
        if self.header.constraint_count > 0:
            self.header.constraint_segment = self.constraints[0]
        if self.header.softbody_count > 0:
            self.header.softbody_segment = self.softbodies[0]

        self.add_bina_segment(self.header)
        for rigidbody in self.rigidbodies:
            self.add_bina_segment(rigidbody)
        for constraint in self.constraints:
            self.add_bina_segment(constraint)

        for i, softbody in enumerate(self.softbodies):
            self.add_bina_segment(softbody)

            if softbody.cloth_nodes_count > 0:
                softbody.cloth_nodes_segment = softbody.cloth_nodes[0]
                for cloth_node in softbody.cloth_nodes:
                    self.add_bina_segment(cloth_node)

            if softbody.cloth_links_count > 0:
                softbody.cloth_links_segment = softbody.cloth_links[0]
                for cloth_link in softbody.cloth_links:
                    self.add_bina_segment(cloth_link) 
            

        self.add_strings_from_bina_segments()

    def import_file(self, filepath):
        bina_stream = BytesIO()

        with open(filepath, 'rb') as file:
            file.seek(0x40)
            bina_stream.write(file.read())
            bina_stream.seek(0)
            
        self.header.from_bytes(bina_stream)
        
        for i in range(self.header.rigidbody_count):
            offset = self.header.rigidbody_offset + (i * 0x50)
            rigidbody = PBARigidBody("temp")
            rigidbody.from_bytes(bina_stream, offset)
            self.rigidbodies.append(rigidbody)
        
        for i in range(self.header.constraint_count):
            offset = self.header.constraint_offset + (i * 0xD0)
            constraint = PBAConstraint("temp")
            constraint.from_bytes(bina_stream, offset)
            self.constraints.append(constraint)

        # TODO: Add tracking for segment sizes when reading
        offset = self.header.softbody_offset 
        for i in range(self.header.softbody_count):
            softbody = PBASoftBody("temp")
            softbody.from_bytes(bina_stream, offset)
            
            bina_stream.seek(softbody.cloth_nodes_offset)
            for j in range(softbody.cloth_nodes_count):
                cloth_node = PBAClothNode("temp")
                cloth_node.from_bytes(bina_stream)
                softbody.cloth_nodes.append(cloth_node)
            
            bina_stream.seek(softbody.cloth_links_offset)
            for j in range(softbody.cloth_links_count):
                cloth_link = PBAClothLink((0,1), 1.0)   # Temp
                cloth_link.from_bytes(bina_stream)
                softbody.cloth_links.append(cloth_link)
            
            self.softbodies.append(softbody)
            align_bytes(bina_stream, 8)
            offset = bina_stream.tell()

        self.structure_elements()




        
