from dataclasses import dataclass


@dataclass
class ApertureBlock:
    id: str
    body: list[str]  # primitive o statements interni al blocco


def _parse_ab_start(self, value: str):
    # value es: "AB10*" (senza i % perché il tokenizer li ha rimossi)
    block_id = value[2:-1]  # togli "AB" e "*" finale
    if not block_id:
        raise ValueError("Aperture Block senza id")
    if self.current_ap_block is not None:
        raise ValueError(f"Nesting di AB non supportato (già in {self.current_ap_block})")
    self.current_ap_block = block_id
    self.aperture_blocks[block_id] = []


def _parse_ab_end(self, value: str):
    # value es: "ABEND*"
    if self.current_ap_block is None:
        raise ValueError("ABEND trovato senza blocco aperto")
    self.current_ap_block = None


def _collect_ab_body(self, kind: str, value: str):
    """
    Accumula qualunque token (stmt o param) dentro il blocco AB.
    Puoi decidere se normalizzare/filtrare: qui manteniamo raw.
    """
    if self.current_ap_block is None:
        return
    # Accumula la rappresentazione grezza: puoi raffinare in seguito
    self.aperture_blocks[self.current_ap_block].append((kind, value))
