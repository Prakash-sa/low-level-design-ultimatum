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

# production code

class Amplifier:
    def __init__(self):
        self.volume = 5
        self.is_on = False

    def on(self):
        if not self.is_on:
            self.is_on = True
            print("Amplifier On")
    
    def off(self):
        if self.is_on:
            self.is_on = False
            print("Amplifier Off")
    
    def set_volume(self, v):
        if self.is_on:
            self.volume = v
            print(f"Volume set to {v}")
        else:
            print("Cannot set volume: Amplifier is off")


class DVDPlayer:
    def __init__(self):
        self.is_on = False
        self.current_movie = None
    
    def on(self):
        if not self.is_on:
            self.is_on = True
            print("DVD Player On")
    
    def off(self):
        if self.is_on:
            self.is_on = False
            print("DVD Player Off")

    def play(self, movie):
        if self.is_on:
            self.current_movie = movie
            print(f"Playing: {movie}")
        else:
            print("Cannot play: DVD Player is off")
    
    def stop(self):
        if self.is_on and self.current_movie:
            print(f"Stopping: {self.current_movie}")
            self.current_movie = None


class Projector:
    def __init__(self):
        self.is_on = False
    
    def on(self):
        if not self.is_on:
            self.is_on = True
            print("Projector On")
    
    def off(self):
        if self.is_on:
            self.is_on = False
            print("Projector Off")
    
    def wide_screen_mode(self):
        if self.is_on:
            print("Projector: Wide screen mode (16:9)")


class HomeTheaterFacade:
    """Simplified interface for home theater system"""
    
    def __init__(self, amp, dvd, projector):
        self.amp = amp
        self.dvd = dvd
        self.projector = projector

    def watch_movie(self, title):
        print("\n=== Get ready to watch a movie ===")
        self.projector.on()
        self.projector.wide_screen_mode()
        self.amp.on()
        self.amp.set_volume(7)
        self.dvd.on()
        self.dvd.play(title)
        print(f"=== Enjoy '{title}'! ===\n")

    def end_movie(self):
        print("\n=== Shutting down theater ===")
        self.dvd.stop()
        self.dvd.off()
        self.amp.off()
        self.projector.off()
        print("=== Theater off ===\n")

    def set_volume(self, level):
        """Quick volume adjustment"""
        self.amp.set_volume(level)


if __name__ == "__main__":
    # Create subsystems
    amp = Amplifier()
    dvd = DVDPlayer()
    projector = Projector()
    
    # Facade simplifies everything
    theater = HomeTheaterFacade(amp, dvd, projector)
    
    # Client code is simple!
    theater.watch_movie("Inception")
    theater.set_volume(10)  # Adjust during movie
    theater.end_movie()
    
    print("\n" + "="*40)
    print("Without facade, you'd need to call:")
    print("projector.on(), projector.wide_screen_mode(),")
    print("amp.on(), amp.set_volume(7),")
    print("dvd.on(), dvd.play('Inception')")
    print("Facade makes it ONE call: theater.watch_movie('Inception')")
    print("="*40)

# an outward appearance that is maintained to conceal a less pleasant or creditable reality.
# In the programming world, the "outward appearance" is the class or interface we interact with as programmers. 
# And the "less pleasant reality" is the complexity that is hidden from us.
# So a Facade, is simply a wrapper class that can be used to abstract lower-level details that we don't want 
# to worry about.

# use for the APIs Design
