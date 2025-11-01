from abc import ABC, abstractmethod

# Abstract Product A
class Button(ABC):
    @abstractmethod
    def paint(self):
        pass

# Abstract Product A1
class WinButton(Button):
    def paint(self):
        print("Rendering a button in a Windows style.")

# Abstract Product A2
class MacButton(Button):
    def paint(self):
        print("Rendering a button in a Mac style.")

# Abstract Product B
class Checkbox(ABC):
    @abstractmethod
    def paint(self):
        pass

# Concrete Product B1
class WinCheckbox(Checkbox):
    def paint(self):
        print("Rendering a checkbox in a Windows style.")

# Concrete Product B2
class MacCheckbox(Checkbox):
    def paint(self):
        print("Rendering a checkbox in a Mac style.")

# Abstract Factory
class GUIFactory(ABC):
    @abstractmethod
    def create_button(self):
        pass

    @abstractmethod
    def create_checkbox(self):
        pass

# Concrete Factory 1
class WinFactory(GUIFactory):
    def create_button(self):
        return WinButton()

    def create_checkbox(self):
        return WinCheckbox()

# Concrete Factory 2
class MacFactory(GUIFactory):
    def create_button(self):
        return MacButton()

    def create_checkbox(self):
        return MacCheckbox()

# Client code
class Application:
    def __init__(self, factory):
        self.factory = factory
        self.button = self.factory.create_button()
        self.checkbox = self.factory.create_checkbox()

    def paint(self):
        self.button.paint()
        self.checkbox.paint()

if __name__ == '__main__':
    os_type = "Windows"  # Change to "Mac" to see Mac UI
    factory = None

    if os_type == "Windows":
        factory = WinFactory()
    elif os_type == "Mac":
        factory = MacFactory()

    if factory:
        app = Application(factory)
        app.paint()
        # Output:
        # Rendering a button in a Windows style.
        # Rendering a checkbox in a Windows style.
    else:
        print("Unknown OS type.")
