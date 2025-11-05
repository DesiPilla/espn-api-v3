class PseudoPlayer:
    """A skeleton of the Player class"""

    def __init__(self):
        self.name = "Fake Player"
        self.stats = {}
        self.points = 0

    def __repr__(self):
        return "Player(Bye)"

    def __hash__(self):
        return hash((self.name))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.name == other.name
