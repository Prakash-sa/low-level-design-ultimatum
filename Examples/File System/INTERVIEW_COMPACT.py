"""Compact In-Memory File System with Patterns
Run: python3 INTERVIEW_COMPACT.py
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Tuple
import zlib

# ---------------- Storage Strategies -----------------
class StorageStrategy:
    def name(self) -> str:
        return self.__class__.__name__
    def encode(self, text: str) -> bytes:
        raise NotImplementedError
    def decode(self, data: bytes) -> str:
        raise NotImplementedError

class PlainStorageStrategy(StorageStrategy):
    def encode(self, text: str) -> bytes:
        return text.encode("utf-8")
    def decode(self, data: bytes) -> str:
        return data.decode("utf-8")

class CompressedStorageStrategy(StorageStrategy):
    def encode(self, text: str) -> bytes:
        return zlib.compress(text.encode("utf-8"))
    def decode(self, data: bytes) -> str:
        if not data:
            return ""
        return zlib.decompress(data).decode("utf-8")

# ---------------- Composite Nodes -----------------
@dataclass
class FsNode:
    name: str
    parent: Optional['Directory'] = None
    def path(self) -> str:
        if self.parent is None:
            return '/' if self.name == '' else f'/{self.name}'
        base = self.parent.path()
        return (base.rstrip('/') + '/' + self.name) if self.name else base

@dataclass
class File(FsNode):
    _data: bytes = b''
    version: int = 0
    def write(self, text: str, storage: StorageStrategy) -> None:
        self._data = storage.encode(text)
        self.version += 1
    def read(self, storage: StorageStrategy) -> str:
        return storage.decode(self._data)
    def logical_size(self, storage: StorageStrategy) -> int:
        return len(self.read(storage))
    def physical_size(self) -> int:
        return len(self._data)

@dataclass
class Directory(FsNode):
    children: Dict[str, FsNode] = field(default_factory=dict)
    def add(self, node: FsNode) -> None:
        self.children[node.name] = node
        node.parent = self
    def remove(self, name: str) -> FsNode:
        node = self.children.pop(name)
        node.parent = None
        return node
    def get(self, name: str) -> Optional[FsNode]:
        return self.children.get(name)

# ---------------- Commands -----------------
class Command:
    def execute(self, fs: 'FileSystem') -> None:
        raise NotImplementedError
    def undo(self, fs: 'FileSystem') -> None:
        raise NotImplementedError
    def describe(self) -> str:
        return self.__class__.__name__

class CreateFileCommand(Command):
    def __init__(self, path: str) -> None:
        self.path = path
        self.created = False
    def execute(self, fs: 'FileSystem') -> None:
        if fs.exists(self.path):
            raise ValueError("File already exists")
        fs._create_file(self.path)
        self.created = True
    def undo(self, fs: 'FileSystem') -> None:
        if self.created:
            fs._delete_node(self.path)
    def describe(self) -> str:
        return f"CreateFile {self.path}"

class WriteFileCommand(Command):
    def __init__(self, path: str, new_text: str) -> None:
        self.path = path
        self.new_text = new_text
        self.old_text: Optional[str] = None
    def execute(self, fs: 'FileSystem') -> None:
        file = fs._get_file(self.path)
        self.old_text = file.read(fs.storage)
        file.write(self.new_text, fs.storage)
    def undo(self, fs: 'FileSystem') -> None:
        if self.old_text is None:
            return
        file = fs._get_file(self.path)
        file.write(self.old_text, fs.storage)
    def describe(self) -> str:
        return f"WriteFile {self.path}"

class MoveNodeCommand(Command):
    def __init__(self, src_path: str, dest_dir_path: str) -> None:
        self.src_path = src_path
        self.dest_dir_path = dest_dir_path
        self.original_parent: Optional[Directory] = None
        self.node_name: Optional[str] = None
    def execute(self, fs: 'FileSystem') -> None:
        node = fs._resolve(self.src_path)
        if node is None:
            raise ValueError("Source not found")
        dest_dir = fs._resolve(self.dest_dir_path)
        if not isinstance(dest_dir, Directory):
            raise ValueError("Destination is not a directory")
        if node.parent is None:
            raise ValueError("Cannot move root")
        self.original_parent = node.parent
        self.node_name = node.name
        node.parent.remove(node.name)
        dest_dir.add(node)
    def undo(self, fs: 'FileSystem') -> None:
        if self.original_parent and self.node_name:
            node = fs._resolve(self.dest_dir_path + '/' + self.node_name)
            if node:
                node.parent.remove(node.name)
                self.original_parent.add(node)
    def describe(self) -> str:
        return f"MoveNode {self.src_path} -> {self.dest_dir_path}"

class DeleteNodeCommand(Command):
    def __init__(self, path: str) -> None:
        self.path = path
        self.snapshot: Optional[FsNode] = None
        self.parent_path: Optional[str] = None
    def execute(self, fs: 'FileSystem') -> None:
        node = fs._resolve(self.path)
        if node is None or node.parent is None:
            raise ValueError("Cannot delete root or non-existent")
        self.snapshot = fs._clone_node(node)
        self.parent_path = node.parent.path()
        node.parent.remove(node.name)
    def undo(self, fs: 'FileSystem') -> None:
        if self.snapshot and self.parent_path:
            parent = fs._resolve(self.parent_path)
            if isinstance(parent, Directory):
                parent.add(fs._clone_node(self.snapshot))
    def describe(self) -> str:
        return f"DeleteNode {self.path}"

class RestoreSnapshotCommand(Command):
    def __init__(self, old_root: Directory, new_root: Directory) -> None:
        self.old_root = old_root
        self.new_root = new_root
    def execute(self, fs: 'FileSystem') -> None:
        fs.root = self.new_root
    def undo(self, fs: 'FileSystem') -> None:
        fs.root = self.old_root
    def describe(self) -> str:
        return "RestoreSnapshot"

class CreateDirectoryCommand(Command):
    def __init__(self, path: str) -> None:
        self.path = path.rstrip('/')
        self.created = False
    def execute(self, fs: 'FileSystem') -> None:
        if fs.exists(self.path):
            raise ValueError("Directory already exists")
        fs._create_directory(self.path)
        self.created = True
    def undo(self, fs: 'FileSystem') -> None:
        if self.created:
            node = fs._resolve(self.path)
            if isinstance(node, Directory) and not node.children and node.parent is not None:
                node.parent.remove(node.name)
                fs._emit("node_deleted", {"path": self.path})
                fs._refresh_metrics()
    def describe(self) -> str:
        return f"CreateDirectory {self.path}"

# ---------------- Snapshot -----------------
@dataclass
class Snapshot:
    root_clone: Directory

# ---------------- FileSystem Singleton -----------------
class FileSystem:
    _instance: Optional['FileSystem'] = None
    def __init__(self) -> None:
        self.root = Directory(name='')
        self.storage: StorageStrategy = PlainStorageStrategy()
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []
        self.listeners: List[Callable[[str, Dict[str, Any]], None]] = []
        self.metrics: Dict[str, int] = {"file_count": 0, "dir_count": 1, "total_bytes": 0, "compressed_bytes": 0, "command_executed": 0, "command_undone": 0}
    @classmethod
    def instance(cls) -> 'FileSystem':
        if cls._instance is None:
            cls._instance = FileSystem()
        return cls._instance
    def register(self, fn: Callable[[str, Dict[str, Any]], None]) -> None:
        self.listeners.append(fn)
    def _emit(self, event: str, payload: Dict[str, Any]) -> None:
        for listener_fn in self.listeners:
            listener_fn(event, payload)
    # ---- Path Resolution ----
    def _resolve(self, path: str) -> Optional[FsNode]:
        if path == '/' or path == '':
            return self.root
        parts = [p for p in path.strip('/').split('/') if p]
        node: FsNode = self.root
        for part in parts:
            if not isinstance(node, Directory):
                return None
            node = node.get(part)  # type: ignore[assignment]
            if node is None:
                return None
        return node
    def exists(self, path: str) -> bool:
        return self._resolve(path) is not None
    def _get_file(self, path: str) -> File:
        node = self._resolve(path)
        if not isinstance(node, File):
            raise ValueError("Not a file")
        return node
    # ---- Primitive Ops (used by commands) ----
    def _create_file(self, path: str) -> None:
        if path.endswith('/'):
            raise ValueError("File path cannot end with /")
        parent_path, name = path.rsplit('/', 1)
        parent = self._resolve(parent_path or '/')
        if not isinstance(parent, Directory):
            raise ValueError("Parent directory missing")
        parent.add(File(name=name))
        self._emit("node_created", {"path": path})
        self._refresh_metrics()
    def _create_directory(self, path: str) -> None:
        parent_path, name = path.rsplit('/', 1) if '/' in path.strip('/') else ('/', path.strip('/'))
        parent = self._resolve(parent_path or '/')
        if not isinstance(parent, Directory):
            raise ValueError("Parent directory missing for directory creation")
        if parent.get(name):
            raise ValueError("Name already exists in parent")
        parent.add(Directory(name=name))
        self._emit("node_created", {"path": path})
        self._refresh_metrics()
    def _delete_node(self, path: str) -> None:
        node = self._resolve(path)
        if node is None or node.parent is None:
            raise ValueError("Cannot delete root or non-existent")
        node.parent.remove(node.name)
        self._emit("node_deleted", {"path": path})
        self._refresh_metrics()
    def _clone_node(self, node: FsNode) -> FsNode:
        if isinstance(node, File):
            clone = File(name=node.name, _data=node._data, version=node.version)
            return clone
        if isinstance(node, Directory):
            new_dir = Directory(name=node.name)
            for child in node.children.values():
                child_clone = self._clone_node(child)
                new_dir.add(child_clone)
            return new_dir
        raise ValueError("Unknown node type")
    # ---- Commands API ----
    def execute(self, cmd: Command) -> None:
        cmd.execute(self)
        self.undo_stack.append(cmd)
        self.redo_stack.clear()
        self.metrics["command_executed"] += 1
        self._emit("command_executed", {"cmd": cmd.describe()})
    def undo(self) -> None:
        if not self.undo_stack:
            return
        cmd = self.undo_stack.pop()
        cmd.undo(self)
        self.redo_stack.append(cmd)
        self.metrics["command_undone"] += 1
        self._emit("command_undone", {"cmd": cmd.describe()})
    def redo(self) -> None:
        if not self.redo_stack:
            return
        cmd = self.redo_stack.pop()
        cmd.execute(self)
        self.undo_stack.append(cmd)
        self.metrics["command_executed"] += 1
        self._emit("command_executed", {"cmd": cmd.describe(), "redo": True})
    def set_storage_strategy(self, strategy: StorageStrategy) -> None:
        old = self.storage.name()
        # Re-encode all file contents into new strategy for transparency
        all_files = self._all_files()
        logical_contents: List[Tuple[File, str]] = [(f, f.read(self.storage)) for f in all_files]
        self.storage = strategy
        for f, text in logical_contents:
            f.write(text, self.storage)
        self._emit("strategy_swapped", {"old": old, "new": strategy.name()})
        self._refresh_metrics()
    def take_snapshot(self) -> Snapshot:
        snap = Snapshot(root_clone=self._clone_node(self.root))  # type: ignore[arg-type]
        self._emit("snapshot_taken", {"file_count": self.metrics["file_count"]})
        return snap
    def restore_snapshot(self, snap: Snapshot) -> None:
        old_root = self.root
        new_root = self._clone_node(snap.root_clone)  # type: ignore[arg-type]
        self.execute(RestoreSnapshotCommand(old_root, new_root))
        self._refresh_metrics()
        self._emit("snapshot_restored", {})
    def _all_files(self) -> List[File]:
        result: List[File] = []
        def walk(node: FsNode) -> None:
            if isinstance(node, File):
                result.append(node)
            elif isinstance(node, Directory):
                for c in node.children.values():
                    walk(c)
        walk(self.root)
        return result
    def _refresh_metrics(self) -> None:
        files = self._all_files()
        dirs = []
        def walk_dirs(d: Directory) -> None:
            dirs.append(d)
            for c in d.children.values():
                if isinstance(c, Directory):
                    walk_dirs(c)
        walk_dirs(self.root)
        logical_total = sum(f.logical_size(self.storage) for f in files)
        physical_total = sum(f.physical_size() for f in files)
        self.metrics.update({"file_count": len(files), "dir_count": len(dirs), "total_bytes": logical_total, "compressed_bytes": physical_total})
        self._emit("metrics_updated", {"file_count": len(files), "dir_count": len(dirs)})

# ---------------- Demo Helpers -----------------

def print_header(title: str) -> None:
    print("\n=== " + title + " ===")

def listener(event: str, payload: Dict[str, Any]) -> None:
    print(f"[EVENT] {event} -> {payload}")

# ---------------- Demo Scenarios -----------------

def demo_1_setup() -> None:
    print_header("Demo 1: Setup & Create Files")
    fs = FileSystem.instance()
    fs.register(listener)
    fs.execute(CreateFileCommand("/readme.txt"))
    fs.execute(WriteFileCommand("/readme.txt", "Hello FS"))
    fs.execute(CreateDirectoryCommand("/docs"))
    fs.execute(CreateFileCommand("/docs/spec.md"))
    fs.execute(WriteFileCommand("/docs/spec.md", "Initial spec"))
    print("readme:", fs._get_file("/readme.txt").read(fs.storage))


def demo_2_strategy_swap() -> None:
    print_header("Demo 2: Storage Strategy Swap")
    fs = FileSystem.instance()
    fs.execute(WriteFileCommand("/docs/spec.md", "Expanded specifications"))
    before_physical = fs.metrics["compressed_bytes"]
    fs.set_storage_strategy(CompressedStorageStrategy())
    after_physical = fs.metrics["compressed_bytes"]
    print("Compression effect bytes:", before_physical, "->", after_physical)


def demo_3_move_node() -> None:
    print_header("Demo 3: Move Node")
    fs = FileSystem.instance()
    fs.execute(CreateFileCommand("/docs/plan.txt"))
    fs.execute(WriteFileCommand("/docs/plan.txt", "Roadmap"))
    fs.execute(MoveNodeCommand("/docs/plan.txt", "/"))
    print("Moved plan exists at /plan.txt:", fs.exists("/plan.txt"))


def demo_4_delete_undo_redo() -> None:
    print_header("Demo 4: Delete + Undo/Redo")
    fs = FileSystem.instance()
    fs.execute(DeleteNodeCommand("/plan.txt"))
    print("Exists after delete:", fs.exists("/plan.txt"))
    fs.undo()
    print("Exists after undo:", fs.exists("/plan.txt"))
    fs.redo()
    print("Exists after redo:", fs.exists("/plan.txt"))


def demo_5_snapshot_restore() -> None:
    print_header("Demo 5: Snapshot & Restore")
    fs = FileSystem.instance()
    snap = fs.take_snapshot()
    fs.execute(CreateFileCommand("/temp.log"))
    fs.execute(WriteFileCommand("/temp.log", "Transient data"))
    print("Temp exists pre-restore:", fs.exists("/temp.log"))
    fs.restore_snapshot(snap)
    print("Temp exists post-restore:", fs.exists("/temp.log"))
    print("Metrics summary:", fs.metrics)

# ---------------- Main -----------------
if __name__ == "__main__":
    demo_1_setup()
    demo_2_strategy_swap()
    demo_3_move_node()
    demo_4_delete_undo_redo()
    demo_5_snapshot_restore()
