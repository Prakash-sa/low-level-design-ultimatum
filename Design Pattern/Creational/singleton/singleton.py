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
