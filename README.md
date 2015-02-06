# GitCheck

## Overview

This is a simple `gtk` based script to provide a visual status check of
multiple git repo's. It was spawned from
[batchgit](https://github.com/maxhebditch/batchgit), a bash script to perform
batch operations on multiple repo's. This indicator is designed to work with
`batchgit`, but could with a small amount of setup work independently. 

## Current status
This work is currently in a testing stage trying to get the features stable
enough to use across linux platforms and with different UIs. 

## Similar work

Of course this idea is not original, or even as well implemented the
alternative, so you may prefer to look at:

* [UbikZ git-indicator](https://github.com/UbikZ/git-indicator): An indicator
  for the Unity panel which finds all repo's in home directory. This is very
much a more developed version.

However, `GitCheck` does not rely on the Unity panel, so it has that going for
it..

There is also 
 
* [sickill git-dude](https://github.com/sickill/git-dude): Not actively
  developed, but provides pop-up notifications for changes.

## TODO

* Understand why some status lines contain no remote information

* Catch cases where passwords are requested and somehow inform the user

* Write section on how to setup the indicator to start automatically

* Add automatic remote checking to manual update

* Document the use  
