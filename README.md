Launcher
============

Text-based launcher for your Linux box. Launches text-based and graphical programs correctly. Includes fuzzy-searching.

![Image of Laucher (what a great name!)]
(scrot.png)

##Fuzzy Searching
Gives whole words priority, then phrases containing all the letters in the search query in order. So `ema` matches `Emacs` first of all, but then finds other things like `GearyMail`.

The search matches programs' full names, as well as the names of the commands required to execute them. So `gnome-control-center` will match the program called "GCCenter", since in a terminal you'd have to type `gnome-control-center` to run it.

##Available Programs
Currently this program detects all programs listed in the debian menu system. However, this is obsolete, so in future the program will read `.desktop` files from `/usr/share/applications`.
