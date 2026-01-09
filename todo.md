# Features to add:

## Security

- [ ] Add google authentication for login

## League setup

- [ ] Allow for picking IDP players
- [ ] Allow for custom scoring
- [x] Add flex as an option
- [x] Specify how many of each position to include
  - Somehow handle flex
- [ ] Make the "create league" button at the bottom prettier
  - As well as the spinner icon that appears after pressing it

## Draft
- [ ] Make the "start draft" button prettier
- [ ] Bug where drafted players still appear in the available players table
- [ ] Bug when searching for a player and then clearing the search, where the top result stays on top.
  - Reproduce by searching "josh" and then CMD + BACKSPACE
- [ ] Add Flex as a possible filter position
- [ ] Show how many of each position a team has drafted
- [ ] Prevent a team from selecting more than the allowable number of players for a given position
  - Must work with Flex

## League page

- [ ] Build a page to view weekly standings
  - Must work when there are not yet any scores (all zeros)



4. In the draft we will restrict the draftable players for a team based on if they have already picked their allotment of players for that position.
   - Recall that no players have the position "Flex", it is just a placeholder that means they can have N extra RB/WR/TE (any combination based on how big N is)