# Facade design pattern in Python

"""Facade Pattern (Python)
Provide a unified interface to a subsystem.
"""

class Amplifier:
    def __init__(self):
        self.volume = 5
        self.is_on = False
    def on(self):
        self.is_on = True
        print("Amplifier ON")
    def off(self):
        self.is_on = False
        print("Amplifier OFF")
    def set_volume(self, v: int):
        self.volume = v
        print(f"Volume -> {v}")

class DVDPlayer:
    def __init__(self):
        self.is_on = False
    def on(self):
        self.is_on = True
        print("DVD ON")
    def off(self):
        self.is_on = False
        print("DVD OFF")
    def play(self, movie: str):
        print(f"Playing {movie}")
    def stop(self):
        print("Stop DVD")

class HomeTheaterFacade:
    def __init__(self, amp: Amplifier, dvd: DVDPlayer):
        self.amp = amp
        self.dvd = dvd
    def watch_movie(self, title: str):
        print("Prepare to watch a movie...")
        self.amp.on(); self.amp.set_volume(7)
        self.dvd.on(); self.dvd.play(title)
    def end_movie(self):
        print("Shutdown theater...")
        self.dvd.stop(); self.dvd.off()
        self.amp.off()

if __name__ == "__main__":
    facade = HomeTheaterFacade(Amplifier(), DVDPlayer())
    facade.watch_movie("Inception")
    facade.end_movie()
# an outward appearance that is maintained to conceal a less pleasant or creditable reality.
# In the programming world, the "outward appearance" is the class or interface we interact with as programmers. 
# And the "less pleasant reality" is the complexity that is hidden from us.
# So a Facade, is simply a wrapper class that can be used to abstract lower-level details that we don't want 
# to worry about.

# use for the APIs Design

class Array:
    def __init__(self):
        self.capacity=3
        self.length=0
        self.arr=[0]*2
    
    def pushback(self,n):
        if self.length==self.capacity:
            self.resize()

        self.arr[self.length]=n
        self.length+=1

    def resize(self):
        self.capacity=2*self.capacity
        newArr=[0]*self.capacity

        for i in range(self.length):
            newArr[i]=self.arr[i]
        self.arr=newArr

    def popback(self):
        if self.length>0:
            self.length-=1