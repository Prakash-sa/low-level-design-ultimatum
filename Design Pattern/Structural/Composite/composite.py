

from abc import ABC, abstractmethod


class Component(ABC):
    @abstractmethod
    def render(self):
        """Render the component structure"""
        pass
    
    def add(self, component):
        """Override in Composite"""
        raise NotImplementedError("Cannot add to a leaf component")
    
    def remove(self, component):
        """Override in Composite"""
        raise NotImplementedError("Cannot remove from a leaf component")


class Leaf(Component):
    def __init__(self, name):
        self.name = name
    
    def render(self):
        return self.name


class Composite(Component):
    def __init__(self, name):
        self.name = name
        self.children = []
    
    def add(self, component):
        self.children.append(component)
        return self  # Enable chaining
    
    def remove(self, component):
        self.children.remove(component)
        return self
    
    def render(self):
        if not self.children:
            return f"{self.name}:[]"
        inner = ", ".join(child.render() for child in self.children)
        return f"{self.name}:[{inner}]"


if __name__ == "__main__":
    # Build file system structure
    root = Composite("root")
    root.add(Leaf("fileA"))
    
    folder = Composite("folder")
    folder.add(Leaf("fileB")).add(Leaf("fileC"))  # Chaining
    
    root.add(folder)
    root.add(Leaf("fileD"))
    
    print(root.render())
    # Output: root:[fileA, folder:[fileB, fileC], fileD]
    
    # Test removal
    root.remove(folder)
    print(root.render())
    # Output: root:[fileA, fileD]