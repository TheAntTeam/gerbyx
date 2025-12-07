import re
from dataclasses import dataclass, field


@dataclass
class AttributeScope:
    file_attrs: dict = field(default_factory=dict)
    object_attrs: dict = field(default_factory=dict)
    active: bool = False


def parse_attribute_block(block: str, scope: AttributeScope, layer_meta: dict):
    if block.startswith('TF.'):
        key, _, rest = block[3:].partition(',')
        values = tuple(v for v in rest.strip('*').split(',') if v)
        layer_meta[key] = values
        scope.file_attrs[key] = values
    elif block.startswith('TA.'):
        scope.active = True
        m = re.match(r'TA\.(\w+)(?:=|,)(.+)\*?', block)
        if m:
            k = m.group(1)
            raw = m.group(2).strip('*')
            vals = [x for x in re.split(r'[,\s]+', raw) if x]
            scope.object_attrs[k] = vals[0] if len(vals) == 1 else tuple(vals)
    elif block.startswith('TD'):
        scope.active = False
        scope.object_attrs.clear()


def attach_attrs_to_geom(geom, scope: AttributeScope):
    return geom, dict(scope.object_attrs)
