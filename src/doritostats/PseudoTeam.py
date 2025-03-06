class PseudoTeam:
    """A skeleton of the Team class"""

    def __init__(self, team_id):
        self.team_id = team_id

    def __repr__(self):
        return "Team(Bye)"

    def __hash__(self):
        return hash((self.team_id))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.team_id == other.team_id
