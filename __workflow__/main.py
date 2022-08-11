from pathlib import Path
from util import read_metadata, pack_module, combine_metadata
from model import Module


print("Reading metadata...")
modules: list[Module] = [
    module
    for m in Path().resolve().iterdir()
    if (module := read_metadata(m)) is not None
]
modules.sort(key=lambda m: m.pack)

print("Packing modules...")
for module in modules:
    print(repr(module))
    pack_module(module)
    print(f"Packed: {module.pack.split('.')[-1]}-{module.version}.zip\n\n")

print("Combining metadata...")
combine_metadata(*modules)
