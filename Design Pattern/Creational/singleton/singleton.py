class Logger:
    __instance = None

    @staticmethod
    def getInstance():
        if Logger.__instance == None:
            Logger.__instance = Logger()
        return Logger.__instance

    def log(self, message):
        print(message)

if __name__ == "__main__":
    logger = Logger.getInstance()
    logger.log("Singleton pattern example with Logger.") # Output: Singleton pattern example with Logger.
    another_logger = Logger.getInstance()
    print(logger is another_logger)  # This will print True, as only one instance should exist


## production code

class Logger:
    __instance = None

    def __new__(cls):c
        """Enforce singleton - only one instance can exist"""
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance
    
    def log(self, message):
        print(message)


if __name__ == "__main__":
    # Both ways work and return the same instance
    logger = Logger()
    logger.log("Singleton pattern example with Logger.")
    
    another_logger = Logger()
    print(f"Same instance? {logger is another_logger}")  # True
    
    # Even direct instantiation returns the singleton
    direct_logger = Logger()
    print(f"All three are same? {logger is another_logger is direct_logger}")  # True



## Thread safe code


from threading import Lock


class Logger:
    __instance = None
    __lock = Lock()

    def __new__(cls):
        """Thread-safe singleton using double-checked locking"""
        if cls.__instance is None:  # First check (without lock)
            with cls.__lock:  # Acquire lock
                if cls.__instance is None:  # Second check (with lock)
                    cls.__instance = super().__new__(cls)
        return cls.__instance
    
    def log(self, message):
        print(message)


if __name__ == "__main__":
    # Test basic functionality
    logger = Logger()
    logger.log("Singleton pattern example with Logger.")
    
    another_logger = Logger()
    print(f"Same instance? {logger is another_logger}")  # True
    
    # Test thread safety
    import threading
    instances = []
    
    def create_logger():
        instances.append(Logger())
    
    threads = [threading.Thread(target=create_logger) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    print(f"All 10 threads got same instance? {all(inst is logger for inst in instances)}")  # True




