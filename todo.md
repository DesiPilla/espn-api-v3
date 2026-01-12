# Features to add:

## Security
- [ ] Add google authentication for login
- [ ] Add a "forgot my password" button
- [ ] Add a profile button to edit password or delete account

## League setup
- [x] Allow for custom scoring
  - [x] Save all scoring (even with a zero multiplier) in case it is changed later
  - [x] Ability to edit scoring after created (currently says no stats found)
- [x] Add flex as an option
- [x] Specify how many of each position to include
  - Somehow handle flex
- [x] Make the "create league" button at the bottom prettier
  - [ ] As well as the spinner icon that appears after pressing it
- [ ] Allow for picking IDP players
- [x] Add year to each league
- [ ] Fix the scoring inputs so that integer values increment by integers, and floats increment by 0.01

## Draft
- [x] If a team has 0 WR but 1 Flex, WR need to be available to draft (currently not)
- [x] Make the "start draft" button prettier
- [x] Bug where drafted players still appear in the available players table
- [x] Bug when searching for a player and then clearing the search, where the top result stays on top.
  - Reproduce by searching "josh" and then CMD + BACKSPACE
- [x] Add Flex as a possible filter position
- [x] Show how many of each position a team has drafted
- [x] Prevent a team from selecting more than the allowable number of players for a given position
  - [x] Must work with Flex
- [x] Display players from the correct year
- [ ] In the team rosters widget, display the first team by default when opened
- [ ] Sort by Draft value, then regular season point total (both desc)
   - [x] Also the draft value should not have a floor. Right now all players below a certain value are made to zero. This leaves TE's with 50 pts at 0 value.

## League page

- [x] Build a page to view weekly standings
  - [x] Must work when there are not yet any scores (all zeros)
  - [x] If a league's draft is complete, it automatically displays on the league home page
- [x] Display the roster size instead of the number of positions
- [x] Lock the scoring settings after the draft has started
- [x] Be able to reset the draft (will unlock scoring settings)

## Team rosters page
- [x] Display actual scores, not the draft fantasy points



- [x] Edit settings toggle
- [x] Points allowed settings must show up in the scoring settings
- [x] Points allowed must appear in calculations
- [x] When rendering points allowed, include a "-" between the points, and replace "Plus" with "+"
- [ ] When rendering points allowed, put them in the correct order (not alphabetic, but based on ordinal)
- [x] Add Flex to the dropdown
- [x] Reset draft option
- [x] Team names editable
