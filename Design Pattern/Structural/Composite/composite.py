"""Composite Pattern (Python)
- Treat individual objects and compositions uniformly
"""
from __future__ import annotations
from typing import List

class Component:
    def render(self) -> str:
        raise NotImplementedError

class Leaf(Component):
    def __init__(self, name: str):
        self.name = name
    def render(self) -> str:
        return self.name

class Composite(Component):
    def __init__(self, name: str):
        self.name = name
        self.children: List[Component] = []
    def add(self, c: Component):
        self.children.append(c)
    def render(self) -> str:
        inner = ", ".join(child.render() for child in self.children)
        return f"{self.name}:[{inner}]"

if __name__ == "__main__":
    root = Composite("root")
    root.add(Leaf("fileA"))
    folder = Composite("folder")
    folder.add(Leaf("fileB"))
    folder.add(Leaf("fileC"))
    root.add(folder)
    print(root.render())
