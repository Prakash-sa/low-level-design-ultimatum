# Composite Pattern

> Compose objects into tree structures to represent part-whole hierarchies. Composite lets clients treat individual objects and compositions of objects uniformly.

---

## Problem

You need to work with hierarchical tree structures (files/folders, UI components, organizational charts) where clients need to treat individual objects and collections of objects the same way.

## Solution

The Composite pattern represents part-whole hierarchies as tree structures composed of objects, all inheriting from a common component interface.

---

## Implementation

```python
from abc import ABC, abstractmethod
from typing import List, Optional

# ============ FILE SYSTEM EXAMPLE ============

class FileSystemComponent(ABC):
    @abstractmethod
    def get_size(self) -> int:
        pass
    
    @abstractmethod
    def display(self, indent: int = 0):
        pass

class File(FileSystemComponent):
    """Leaf node - represents individual file"""
    
    def __init__(self, name: str, size: int):
        self.name = name
        self.size = size
    
    def get_size(self) -> int:
        return self.size
    
    def display(self, indent: int = 0):
        print(" " * indent + f"📄 {self.name} ({self.size} KB)")

class Folder(FileSystemComponent):
    """Composite node - represents folder containing files/folders"""
    
    def __init__(self, name: str):
        self.name = name
        self.children: List[FileSystemComponent] = []
    
    def add_component(self, component: FileSystemComponent):
        self.children.append(component)
    
    def remove_component(self, component: FileSystemComponent):
        self.children.remove(component)
    
    def get_size(self) -> int:
        """Recursive size calculation"""
        total = 0
        for child in self.children:
            total += child.get_size()
        return total
    
    def display(self, indent: int = 0):
        print(" " * indent + f"📁 {self.name}/")
        for child in self.children:
            child.display(indent + 2)

# ============ GRAPHIC COMPONENTS EXAMPLE ============

class GraphicComponent(ABC):
    @abstractmethod
    def draw(self):
        pass
    
    @abstractmethod
    def rotate(self, angle: int):
        pass

class SimpleGraphic(GraphicComponent):
    """Leaf - simple graphic (circle, rectangle, etc.)"""
    
    def __init__(self, name: str):
        self.name = name
    
    def draw(self):
        print(f"Drawing {self.name}")
    
    def rotate(self, angle: int):
        print(f"Rotating {self.name} by {angle} degrees")

class CompositeGraphic(GraphicComponent):
    """Composite - group of graphics"""
    
    def __init__(self, name: str):
        self.name = name
        self.components: List[GraphicComponent] = []
    
    def add_component(self, component: GraphicComponent):
        self.components.append(component)
    
    def remove_component(self, component: GraphicComponent):
        self.components.remove(component)
    
    def draw(self):
        print(f"Drawing composite group: {self.name}")
        for component in self.components:
            component.draw()
    
    def rotate(self, angle: int):
        print(f"Rotating composite group {self.name} by {angle} degrees")
        for component in self.components:
            component.rotate(angle)

# ============ ORGANIZATIONAL CHART EXAMPLE ============

class Employee(ABC):
    def __init__(self, name: str, position: str):
        self.name = name
        self.position = position
    
    @abstractmethod
    def get_salary(self) -> float:
        pass
    
    @abstractmethod
    def display(self, indent: int = 0):
        pass

class Manager(Employee):
    """Composite - can manage other employees"""
    
    def __init__(self, name: str, position: str, base_salary: float):
        super().__init__(name, position)
        self.base_salary = base_salary
        self.subordinates: List[Employee] = []
    
    def add_subordinate(self, employee: Employee):
        self.subordinates.append(employee)
    
    def remove_subordinate(self, employee: Employee):
        self.subordinates.remove(employee)
    
    def get_salary(self) -> float:
        """Manager salary + subordinates' salaries"""
        total = self.base_salary
        for subordinate in self.subordinates:
            total += subordinate.get_salary()
        return total
    
    def display(self, indent: int = 0):
        print(" " * indent + f"👔 Manager: {self.name} ({self.position}) - ${self.base_salary}")
        for subordinate in self.subordinates:
            subordinate.display(indent + 2)

class Developer(Employee):
    """Leaf - individual contributor"""
    
    def __init__(self, name: str, position: str, salary: float):
        super().__init__(name, position)
        self.salary = salary
    
    def get_salary(self) -> float:
        return self.salary
    
    def display(self, indent: int = 0):
        print(" " * indent + f"💻 Developer: {self.name} ({self.position}) - ${self.salary}")

class Designer(Employee):
    """Leaf - individual contributor"""
    
    def __init__(self, name: str, position: str, salary: float):
        super().__init__(name, position)
        self.salary = salary
    
    def get_salary(self) -> float:
        return self.salary
    
    def display(self, indent: int = 0):
        print(" " * indent + f"🎨 Designer: {self.name} ({self.position}) - ${self.salary}")

# ============ MENU SYSTEM EXAMPLE ============

class MenuItem(ABC):
    @abstractmethod
    def display(self, indent: int = 0):
        pass

class Item(MenuItem):
    """Leaf - actual menu item with action"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def display(self, indent: int = 0):
        print(" " * indent + f"• {self.name}: {self.description}")

class Menu(MenuItem):
    """Composite - menu containing items/submenus"""
    
    def __init__(self, name: str):
        self.name = name
        self.items: List[MenuItem] = []
    
    def add_item(self, item: MenuItem):
        self.items.append(item)
    
    def remove_item(self, item: MenuItem):
        self.items.remove(item)
    
    def display(self, indent: int = 0):
        print(" " * indent + f"📋 {self.name}")
        for item in self.items:
            item.display(indent + 2)

# Demo
if __name__ == "__main__":
    print("=== File System ===")
    root = Folder("root")
    
    documents = Folder("Documents")
    pictures = Folder("Pictures")
    
    doc1 = File("resume.pdf", 50)
    doc2 = File("letter.docx", 30)
    pictures_file = File("vacation.jpg", 2000)
    
    documents.add_component(doc1)
    documents.add_component(doc2)
    pictures.add_component(pictures_file)
    
    root.add_component(documents)
    root.add_component(pictures)
    
    root.display()
    print(f"Total size: {root.get_size()} KB\n")
    
    print("=== Graphics ===")
    group = CompositeGraphic("Main Scene")
    circle = SimpleGraphic("Circle")
    rectangle = SimpleGraphic("Rectangle")
    group.add_component(circle)
    group.add_component(rectangle)
    
    group.draw()
    group.rotate(45)
    print()
    
    print("=== Organizational Chart ===")
    ceo = Manager("John CEO", "CEO", 200000)
    
    dev_manager = Manager("Alice", "Dev Manager", 120000)
    design_manager = Manager("Bob", "Design Manager", 110000)
    
    dev1 = Developer("Charlie", "Senior Dev", 100000)
    dev2 = Developer("Diana", "Junior Dev", 70000)
    designer1 = Designer("Eve", "UI Designer", 80000)
    
    dev_manager.add_subordinate(dev1)
    dev_manager.add_subordinate(dev2)
    design_manager.add_subordinate(designer1)
    
    ceo.add_subordinate(dev_manager)
    ceo.add_subordinate(design_manager)
    
    ceo.display()
    print(f"Total payroll: ${ceo.get_salary()}\n")
    
    print("=== Menu System ===")
    main_menu = Menu("Main Menu")
    
    file_menu = Menu("File")
    file_menu.add_item(Item("New", "Create new file"))
    file_menu.add_item(Item("Open", "Open file"))
    file_menu.add_item(Item("Save", "Save file"))
    
    edit_menu = Menu("Edit")
    edit_menu.add_item(Item("Undo", "Undo action"))
    edit_menu.add_item(Item("Redo", "Redo action"))
    
    main_menu.add_item(file_menu)
    main_menu.add_item(edit_menu)
    
    main_menu.display()
```

---

## Key Concepts

- **Component**: Common interface for leaf and composite objects
- **Leaf**: Terminal objects with no children
- **Composite**: Objects that can contain children
- **Uniformity**: Treat individual and composite objects the same way
- **Recursive Composition**: Composites can contain other composites

---

## When to Use

✅ Hierarchical tree structures (file systems, UI components)  
✅ Need to treat parts and wholes uniformly  
✅ Want to represent part-whole hierarchies  
✅ Client code shouldn't care about object complexity  

---

## Interview Q&A

**Q1: What's the difference between Composite and Decorator?**

A:
- **Composite**: Tree structure, represents part-whole hierarchies
- **Decorator**: Linear wrapping, adds functionality to individual objects

```python
# Composite: Tree
root = Folder("root")
root.add_component(Folder("subfolder"))
root.add_component(File("file.txt", 100))

# Decorator: Linear
base_payment = PaymentProcessor()
logged = LoggingDecorator(base_payment)
validated = ValidationDecorator(logged)
```

---

**Q2: How would you implement search in a composite structure?**

A:
```python
class FileSystemComponent(ABC):
    @abstractmethod
    def search(self, name: str) -> List['FileSystemComponent']:
        pass

class File(FileSystemComponent):
    def search(self, name: str):
        if name in self.name:
            return [self]
        return []

class Folder(FileSystemComponent):
    def search(self, name: str):
        results = []
        for child in self.children:
            results.extend(child.search(name))
        return results
```

---

**Q3: How would you handle composite structure with operations on all nodes?**

A:
```python
class Node(ABC):
    @abstractmethod
    def operation(self):
        pass

class Composite(Node):
    def __init__(self):
        self.children = []
    
    def operation(self):
        # Operation on all children recursively
        for child in self.children:
            child.operation()
```

---

**Q4: Can you have a composite that only accepts certain types of children?**

A:
```python
class TypeRestrictedComposite(FileSystemComponent):
    def add_component(self, component: FileSystemComponent):
        if not isinstance(component, File):
            raise TypeError("Only Files allowed")
        self.children.append(component)
```

---

**Q5: How would you serialize/deserialize a composite structure?**

A:
```python
import json

class SerializableFolder:
    def to_dict(self):
        return {
            "type": "folder",
            "name": self.name,
            "children": [child.to_dict() for child in self.children]
        }
    
    @staticmethod
    def from_dict(data):
        folder = SerializableFolder(data["name"])
        for child_data in data["children"]:
            if child_data["type"] == "file":
                folder.add_component(SerializableFile.from_dict(child_data))
            else:
                folder.add_component(SerializableFolder.from_dict(child_data))
        return folder
```

---

## Trade-offs

✅ **Pros**: Simplifies tree handling, uniform treatment of parts/wholes, clean recursive code  
❌ **Cons**: Can make interface too general, may not fit all use cases

---

## Real-World Examples

- **File systems** (folders, files, symlinks)
- **DOM trees** (HTML elements)
- **Graphics rendering** (shapes, groups)
- **Organization charts** (managers, employees)
- **Menu systems** (menus, menu items)
