class PseudoMatchup:
    """A skeleton of the Matchup class"""

    def __init__(self, home_team, away_team):
        self.home_team = home_team
        self.away_team = away_team

    def __repr__(self):
        return f"Matchup({self.home_team}, {self.away_team})"

    def __hash__(self):
        return hash((self.home_team, self.away_team))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return (self.home_team.team_id, self.away_team.team_id) == (
            other.home_team.team_id,
            other.away_team.team_id,
        )
