from abc import ABC, abstractmethod

class House:
    def __init__(self):
        self.foundation = None
        self.structure = None
        self.roof = None

    def set_foundation(self, foundation):
        self.foundation = foundation

    def set_structure(self, structure):
        self.structure = structure

    def set_roof(self, roof):
        self.roof = roof

    def show_house(self):
        print(f"House with {self.foundation}, {self.structure}, and {self.roof}.")

class HouseBuilder(ABC):
    @abstractmethod
    def build_foundation(self):
        pass

    @abstractmethod
    def build_structure(self):
        pass

    @abstractmethod
    def build_roof(self):
        pass

    @abstractmethod
    def get_house(self):
        pass

class ConcreteHouseBuilder(HouseBuilder):
    def __init__(self):
        self.house = House()

    def build_foundation(self):
        self.house.set_foundation("Concrete Foundation")

    def build_structure(self):
        self.house.set_structure("Concrete Structure")

    def build_roof(self):
        self.house.set_roof("Concrete Roof")

    def get_house(self):
        return self.house

class WoodenHouseBuilder(HouseBuilder):
    def __init__(self):
        self.house = House()

    def build_foundation(self):
        self.house.set_foundation("Wooden Foundation")

    def build_structure(self):
        self.house.set_structure("Wooden Structure")

    def build_roof(self):
        self.house.set_roof("Wooden Roof")

    def get_house(self):
        return self.house

class BrickHouseBuilder(HouseBuilder):
    def __init__(self):
        self.house = House()

    def build_foundation(self):
        self.house.set_foundation("Brick Foundation")

    def build_structure(self):
        self.house.set_structure("Brick Structure")

    def build_roof(self):
        self.house.set_roof("Brick Roof")

    def get_house(self):
        return self.house

class Director:
    def __init__(self):
        self.builder = None

    def set_builder(self, builder):
        self.builder = builder

    def construct_house(self):
        self.builder.build_foundation()
        self.builder.build_structure()
        self.builder.build_roof()
        return self.builder.get_house()

if __name__ == "__main__":
    director = Director()
    builder = ConcreteHouseBuilder()
    director.set_builder(builder)

    house = director.construct_house()
    house.show_house()
    # Output: House with Concrete Foundation, Concrete Structure, and Concrete Roof.
