import json
import logging
from itertools import groupby
from pathlib import Path
import shutil

from pydantic import ValidationError

from model import Module

PACKAGE_PATH = Path("__packed__")
PACKAGE_PATH.mkdir(exist_ok=True)


def read_metadata(path: Path) -> Module | None:
    if path.stem.startswith("__") or path.stem.startswith(".") or not path.exists():
        logging.info(f"{path.name}: skipping...")
        return
    if path.is_file():
        if path.suffix != ".py":
            return
        new_path = path.parent / path.stem
        new_path.mkdir(exist_ok=True)
        path.rename(new_path / "__init__.py")
        logging.info(f"{path.name}: moved to {new_path.name}/__init__.py")
        path = new_path
    metadata_path = path / "metadata.json"
    if metadata_path.is_file():
        with metadata_path.open() as f:
            try:
                return Module.parse_obj(json.load(f))
            except ValidationError:
                logging.warning(f"{path.name}: invalid metadata.json")
    module = Module(
        pack=f"module.{path.stem}", pypi=(path / "requirements.txt").is_file()
    )
    write_metadata(metadata_path, module)
    return module


def write_metadata(path: Path, module: Module):
    with path.open("w") as f:
        json.dump(module.dict(), f, indent=4, ensure_ascii=False)
        logging.info(f"{path.name}: written")


def pack_module(module: Module):
    pack_name = f"{module.pack.split('.')[-1]}-{module.version}"
    name = module.pack.split(".")[-1]
    shutil.make_archive(pack_name, "zip", root_dir=Path().resolve(), base_dir=name)
    if (PACKAGE_PATH / f"{pack_name}.zip").exists():
        logging.warning("File exists, removing...")
        (PACKAGE_PATH / f"{pack_name}.zip").unlink(missing_ok=True)
    shutil.move(f"{pack_name}.zip", PACKAGE_PATH)
    Path(f"{pack_name}.zip").unlink(missing_ok=True)


def combine_metadata(*modules: Module):
    with Path("metadata.json").open("w") as f:
        f.write(json.dumps([m.dict() for m in modules], indent=4, ensure_ascii=False))
        logging.info("metadata.json: combined")


def generate_packed_list():
    files = [p.name for p in PACKAGE_PATH.iterdir() if p.is_file()]
    data = {
        k: sorted(
            (lambda x: [_x.rstrip(".zip").split("-")[-1] for _x in x])(list(v)),
            reverse=True,
        )
        for k, v in groupby(sorted(files), key=lambda _: _.split("-")[0])
        if k != "packed_list.json"
    }
    with (PACKAGE_PATH / "packed_list.json").open("w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        logging.info("packed_list.json: generated")
