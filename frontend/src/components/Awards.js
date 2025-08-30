export class Award {
    constructor(description, value, owner) {
        this.description = description;
        this.value = value;
        this.owner = owner;
    }
}

export const awards = {
    bestMatchAwards: [
        new Award('Highest points in a game', '170.4 pts', 'Nikki Pilla'),
        new Award('Highest QB pts in a game', '40.1 pts', 'Nikki Pilla'),
        new Award('Highest RB pts in a game', '48.1 pts', 'Jojo & Matt'),
        new Award('Highest WR pts in a game', '32.3 pts', 'Ben Caro'),
        new Award('Highest TE pts in a game', '28.2 pts', 'Julia Selleck'),
        new Award('Highest RB/WR/TE pts in a game', '31.9 pts', 'Carmine Pilla'),
    ],
    worstMatchAwards: [
        new Award('Lowest points in a game', '62.0 pts', 'Julia Selleck'),
        new Award('Lowest QB pts in a game', '1.1 pts', 'Carmine Pilla'),
        new Award('Lowest RB pts in a game', '4.2 pts', 'Gianna Selleck'),
        new Award('Lowest WR pts in a game', '2.1 pts', 'Julia Selleck'),
        new Award('Lowest TE pts in a game', '0 pts', 'Marc Chirico'),
        new Award('Lowest RB/WR/TE pts in a game', '1.3 pts', 'Julia Selleck'),
    ],
    bestSeasonAwards: [
        new Award('Most wins this season', '10 wins', 'Nikki  Pilla'),
        new Award('Most PPG this season', '125.0 pts', 'Nikki  Pilla'),
        new Award('Most QB pts this season', '25.4 pts', 'Marc Chirico'),
        new Award('Most RB pts this season', '16.7 pts', 'Nikki  Pilla'),
        new Award('Most WR pts this season', '15.9 pts', 'Julia Selleck'),
        new Award('Most TE pts this season', '16.1 pts', 'Desi Pilla'),
        new Award('Most RB/WR/TE pts this season', '12.3 pts', 'James Selleck'),
    ],
    worstSeasonAwards: [
        new Award('Fewest wins this season', '1 win', 'Julia Selleck'),
        new Award('Fewest PPG this season', '99.0 pts', 'Julia Selleck'),
        new Award('Fewest QB pts this season', '17.1 pts', 'Desi Pilla'),
        new Award('Fewest RB pts this season', '11.8 pts', 'Gianna Selleck'),
        new Award('Fewest WR pts this season', '10.1 pts', 'Julia Selleck'),
        new Award('Fewest TE pts this season', '8.8 pts', 'Marc Chirico'),
        new Award('Fewest RB/WR/TE pts this season', '10.0 pts', 'Julia Selleck'),
    ]
};

export const allAwardsData = {
    "bestMatchAwards": awards.bestMatchAwards,
    "worstMatchAwards": awards.worstMatchAwards,
    "bestSeasonAwards": awards.bestSeasonAwards,
    "worstSeasonAwards": awards.worstSeasonAwards
};
