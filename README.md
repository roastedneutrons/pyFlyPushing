An open source library to manage fly crosses and stocks. Still under construction

###Some features/annoyances
- google app engine friendly. It does not use any C backend libraries, or other libraries that google app engine's python interpreter hates. So you dont need to worry about such stuff if you want to include this in a web app
- Doesnt use itertools or numpy even in places where it is convenient to do so. This to to facilitate easy porting to coffeescript for web apps
