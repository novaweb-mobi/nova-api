class NoRowsAffectedException(IOError):
    def __init__(self, message="No rows affected"):
        super(NoRowsAffectedException, self).__init__(message)
