import logging
from pathlib import Path
from util import read_metadata, pack_module, combine_metadata, generate_packed_list
from model import Module

logging.info("Reading metadata...")
modules: list[Module] = [
    module
    for m in Path().resolve().iterdir()
    if (module := read_metadata(m)) is not None
]
modules.sort(key=lambda m: m.pack)

logging.info("Packing modules...")
for module in modules:
    print(repr(module))
    pack_module(module)
    print(f"Packed: {module.pack.split('.')[-1]}-{module.version}.zip\n\n")

logging.info("Combining metadata...")
combine_metadata(*modules)


logging.info("Generating packed list...")
generate_packed_list()


logging.info("Done!")
