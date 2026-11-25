"""Read a WebDataScope snapshot from a zip file or extracted directory."""

from __future__ import annotations

import json
import re
import zipfile
import zlib
from pathlib import Path

try:
    import msgpack
except ImportError as exc:  # pragma: no cover - exercised by the CLI process
    raise RuntimeError(
        "缺少依赖 msgpack。请运行: python -m pip install msgpack openpyxl"
    ) from exc


INFO_PATH = "data/oth/info_data.bin"
OSIS_PATH = "data/oth/osis_data.bin"
DATASET_LIST_PATH = "data/dataSetList.json"
REQUIRED_PATHS = (INFO_PATH, OSIS_PATH)


class SnapshotSource:
    """Expose zip and directory snapshots through the same logical paths."""

    def __init__(self, source_path: Path, zip_file=None, data_root=None):
        self.path = source_path
        self._zip = zip_file
        self._data_root = data_root
        if zip_file:
            self._names = set(zip_file.namelist())
        else:
            self._names = {
                "data/" + item.relative_to(data_root).as_posix()
                for item in data_root.rglob("*")
                if item.is_file()
            }

    def close(self):
        if self._zip:
            self._zip.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    @property
    def names(self):
        return self._names

    @property
    def display_name(self):
        return str(self.path)

    def read_bytes(self, logical_path):
        if logical_path not in self._names:
            raise KeyError(logical_path)
        if self._zip:
            return self._zip.read(logical_path)
        relative = logical_path.removeprefix("data/")
        return (self._data_root / Path(relative)).read_bytes()

    def load_bin(self, logical_path):
        return msgpack.unpackb(
            zlib.decompress(self.read_bytes(logical_path)), strict_map_key=False
        )

    def load_json(self, logical_path):
        return json.loads(self.read_bytes(logical_path).decode("utf-8"))

    def archive_names(self):
        return sorted(
            name
            for name in self._names
            if name.startswith("data/")
            and name.endswith(".bin")
            and name not in REQUIRED_PATHS
        )


def discover_sources(script_dir):
    script_dir = Path(script_dir)
    return sorted(script_dir.glob("WebData_*.zip"))


def resolve_source(raw_path, script_dir):
    """Resolve an explicit path, or the single WebData zip beside the CLI."""
    if raw_path and str(raw_path).strip():
        path = Path(str(raw_path).strip().strip('"')).expanduser().resolve()
    else:
        candidates = discover_sources(script_dir)
        if not candidates:
            raise ValueError("未指定 --source，脚本目录旁也没有 WebData_*.zip")
        path = candidates[-1].resolve()

    if not path.exists():
        raise ValueError(f"输入位置不存在: {path}")

    if path.is_file():
        if path.suffix.lower() != ".zip":
            raise ValueError(f"输入文件不是 ZIP: {path}")
        try:
            source = SnapshotSource(path, zip_file=zipfile.ZipFile(path))
        except (OSError, zipfile.BadZipFile) as exc:
            raise ValueError(f"ZIP 无法读取: {path} ({exc})") from exc
    else:
        if (path / "data" / "oth" / "info_data.bin").is_file():
            data_root = path / "data"
        elif (path / "oth" / "info_data.bin").is_file():
            data_root = path
        else:
            raise ValueError(
                f"目录结构不正确: {path}；需要插件根目录或其 data 目录"
            )
        source = SnapshotSource(path, data_root=data_root)

    missing = [name for name in REQUIRED_PATHS if name not in source.names]
    if missing:
        source.close()
        raise ValueError(f"快照缺少必需文件: {', '.join(missing)}")
    return source


def parse_region_delay(key):
    match = re.fullmatch(r"(.+)_([0-9]+)", str(key))
    return (match.group(1), int(match.group(2))) if match else (None, None)


def parse_archive_name(name, regions):
    """Parse from the right so dataset IDs may contain underscores."""
    if not name.startswith("data/") or not name.endswith(".bin"):
        return None
    stem = name[5:-4]
    delay_match = re.search(r"_Delay([0-9]+)$", stem)
    if not delay_match:
        return None
    delay = int(delay_match.group(1))
    body = stem[: delay_match.start()]
    for region in sorted(set(regions), key=len, reverse=True):
        marker = f"_{region}_"
        dataset, found, universe = body.rpartition(marker)
        if found and dataset and universe:
            return {
                "path": name,
                "dataset": dataset,
                "region": region,
                "universe": universe,
                "delay": delay,
            }
    return None


def inventory(source, info):
    regions = {
        parse_region_delay(key)[0]
        for key in info
        if parse_region_delay(key)[0]
    }
    return [
        parsed
        for name in source.archive_names()
        if (parsed := parse_archive_name(name, regions))
    ]
