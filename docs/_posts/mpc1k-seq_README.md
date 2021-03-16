I often use my MPC 1000 as a player for backing tracks or drum loops when practicing music or just quickly want something to jam along. I usually create a drum loop in my DAW of choice and then export several wav files in different speeds. I would then copy those files on to my MPC and save one sequence for each wav file. The next time I want to practice or jam I just have to quickly load a folder of sequence and wav files and can easily switch between several speeds.

Creating all the sequences on the MPC itself is a very tedious task, that's why I wrote this tool. I now just have to create one "template sequence" on the MPC, copy it over to the computer, and create several (renamed) files from it. I then let the tool help me show meta information of the sequence files and do repititive tasks like replacing the filename in the AUDIO tracks or replacing the sequences BPM.

Though I wrote it for sequence files created from the MPC 1000 running JJOS, I assume the tool would work with the MPC 2500's files as well, I think they share the same format. Maybe also the one's from the MPC 500 would work, not sure about that. I'd certainly appreciate any testing and feedback about usage with those MPC models files.

## Setup instructions

### Using the self-contained executables

If you don't want to bother with installing Python on your OS, and are not interested in running the latest development version, just use the self-contained executables available since release v1.2: https://github.com/JOJ0/mpc1k-seq/releases/tag/v1.2

- For Windows 10 download `seq.exe`
- For MacOS X 10.13 download `seq` (not sure if newer MacOS versions will work, please report back any problems)

To be able to execute `seq` from anywhere on your system, copy it to a place that is searched for:

#### Windows

Use Windows Explorer to copy the seq.exe file to c:\windows\system32\

Note that this is a dirty hack. If you don't want to do this or don't have the privileges to do it, on your command prompt you can always just "cd" to the place where seq.exe is saved and execute it from there :-)

#### Mac OS

Make sure you are residing inside the directory where seq is saved. Your user needs to have admin privileges. You will be asked for your password when executing the following command:

`sudo cp seq /usr/local/bin/`

#### Linux

Please just follow the steps in the following chapter!



### Using the latest development version

_skip this chapter if you are using the executables as describe above_

First of all, check if you already have a Python version on your system with ```python --version```

You need Python 2.7.x

Clone the github repo and jump into the directory.

```
git clone https://github.com/JOJ0/mpc1k-seq.git
cd mpc1k-seq
```


#### Windows

Download an msi installer [here](https://www.python.org/downloads/release/python-2717/)

install the tool by adding the cloned repo directory to the system %path% variable,

or just quick and dirty copy it to a path that already is in the systems search path

```copy seq.py c:\windows\system32\```


#### Mac

Mac OS X 10.11 "El Capitan" ships with Python 2.7.6 pre-installed, which is the version the utility was developed on and is tested with. OX X 10.8 had Python 2.6, which probably also would work. 10.9 and newer all have 2.7.x, which should be fine.

If you don't have above, install the latest 2.7 package from [here](https://www.python.org/downloads/release/python-2717/) or use [homebrew](https://brew.sh) to get it.

install the tool

```cp seq.py /usr/local/bin/```


#### Linux

You most probably have a running Python version already! Check as described above!

Some modern Linux Distributions already use Python 3.x by default, you would have to install a python2 package

Debian based systems
```
apt install python2.7
```

Redhat based
```
yum install python27
```

and set the first line of the script to use this python version (eg ```#!/usr/bin/python2.7```)


finally, install the tool

```cp seq.py /usr/local/bin/```





## How to use it

_In case you are using the developement version, you would have to execute seq.py instead of seq. Further note that the Windows seq.exe can be executed without the .exe ending. The MacOS executable is called just seq and doesn't have a file ending_

The utility comes as a UNIX-style command line utility and as such shows all it's capabilities when being run with the typical --help or -h options:

```
seq -h


usage: seq [-h] [--search SEARCHTERM] [--replace REPLACETERM]
              [--correct-wav] [--correct-wav-bpm] [--filter BPM_LIST]
              [--correct-bpm] [--hex] [--verbose]
              path

positional arguments:
  path                  path of *.SEQ files to be processed

optional arguments:
  -h, --help            show this help message and exit
  --search SEARCHTERM, -s SEARCHTERM
                        search for given string in file contents
  --replace REPLACETERM, -r REPLACETERM
                        replace SEARCHTERM with REPLACETERM
  --correct-wav, -w     sets basename of .SEQ file to the place where
                        SEARCHTERM is found. Use this if your seq and wav
                        files are named identically
  --correct-wav-bpm, -p
                        replace BPM in found SEARCHTERM with BPM found in
                        filename
  --filter BPM_LIST, --bpm BPM_LIST, -b BPM_LIST
                        historically was used as a space seperated BPM list
                        but actually it is a simple filter: only filenames
                        containing one of the strings in the list, will be
                        processed
  --correct-bpm, -c     set BPM to the same as in filename
  --correct-length, -l  set the sequences looplength (bars) to the same as in
                        filename. Assumes value in filename is marked with
                        trailing "b" (eg 8b)
  --hex, -x             show hex values next to decimal and strings
  --verbose, -v         also show border markers and not yet studied header
                        information
```

### Simple usage examples

just show meta information of all seq files in current directory
```
seq .
```

show info of all seq files that have 64 or 512 in the filename (usually BPM values)
```
seq -b "64 512" .
```
also display values in hex
```
seq -b "64 512" -x .
```
search for a string
```
seq -b "64 512" -x -s "FunkBG" .
```
replace _first occurence_ of SEARCHTERM with REPLACETERM (run script again to replace next instance of SEARCHTERM)

FIXME - "replacecount" may be configurable in future releases
```
seq -b "64 512" -x -s "FunkBG" -r "Blues01" .
```


### A more detailed usage example

Show all .SEQ files in the current directory (```.```) that have 80 in the filename (```-b "80"``` or ```--filter "80"``` and search for the term ```"FunkBG"``` in the file

Usually this is useful if we would like to search and replace a wav files name in an audio track, but we probably also could use it to replace the name of an MPC "program file" (.PGM) somewhere in the (binary) seq file.

Let's have a look at the command line and it's output:

```
seq -b "80" -s FunkBG .

* PATH used: .
* searching for "FunkBG" (after End of header)
* bpm_list (filter_list): ['80']

############### FunkBG_080_8bar.SEQ ################
4:20  version:    MPC1000 SEQ 4.40
28:30 bars:       8
32:34 bpm:        80
################## End of header ###################
Found first occurence of SEARCHTERM at index 7168, it's 6 chars long
If SEARCHTERM is the START of a wav filename in an AUDIO track,
this would be the first half:       "FunkBG_0"
and this would be the second half:  "80_8bar"
** REPLACE OPTIONS: ********************************
** --replace simply replaces FunkBG with REPLACETERM.
** --correct-wav (-w) puts this files basename at found terms position,
**     it would replace "FunkBG_0" with "FunkBG_0",
**     and              "80_8bar" with "80_8bar".
** --correct-wav-bpm (-p) just replaces the bpm part in the found term,
?? didn't find a possible bpm value in given term (FunkBG),
?? use underscores or dashes as seperating characters!
**     it would replace "FunkBG" with "FunkBG".
** If this all looks like crap, don't do it! Existing files will be OVERWRITTEN!
```


The first section of the output is showing us meta information saved in the files header like version, number of bars and the BPM of the sequence.

After the "End of header" marker we see that our searchterm "FunkBG" was found and it most likely is the start of the name of a wav file in an AUDIO track.

Let's assume we would like to replace part of the wav files name configured into the seq file. The name of a wav file oddly is saved in two 8 Byte chunks in different places. The script is trying to help us with finding out if it just found part of a wav file name or something else (like a pgm file name or some other string).

Next are our possibilities to replace that string:

```--replace (-r)``` is the simplest form of replacement, it just puts the REPLACETERM at the position where it found SEARCHTERM. If REPLACETERM is longer than SEARCHTERM it will overwrite the remaining part.


```--correct-wav (-w)``` is the option to use when our wav files are exactely identically named to our wav files (except the file ending of course). This is the option I use most. In case of the example seq file from the github repo, the wav and seq file names where identically already, so this option currently is not very useful.

```--correct-wav-bpm (-p)``` only makes sense when SEARCHTERM contains numbers that represent BPM values. I'll show it in another example.

Each of the options exactely state what they would replace, so if we are happy with one of them we just rerun the script and additionally add the replace option to the command line.

For example if we chose ```-r``` to be the option to use, because we want to simply replace "FunkBG" with "PunkBG", this would be the command and its resulting output:

```
seq -b "80" -s FunkBG -r "PunkBG" .

* PATH used: .
* searching for "FunkBG" (after End of header)
* replace is enabled! REPLACETERM is "PunkBG"
* bpm_list (filter_list): ['80']

############### FunkBG_080_8bar.SEQ ################
4:20  version:    MPC1000 SEQ 4.40
28:30 bars:       8
32:34 bpm:        80
################## End of header ###################
Found first occurence of SEARCHTERM at index 7168, it's 6 chars long
If SEARCHTERM is the START of a wav filename in an AUDIO track,
this would be the first half:       "FunkBG_0"
and this would be the second half:  "80_8bar"
!!! replacing FIRST occurence of "FunkBG" with "PunkBG",
!!! and overwriting ./FunkBG_080_8bar.SEQ ...
```

If we now search for FunkBG again, we certainly won't find it anymore:

```
seq -b "80" -s "FunkBG" .

* PATH used: .
* searching for "FunkBG" (after End of header)
* bpm_list (filter_list): ['80']

############### FunkBG_080_8bar.SEQ ################
4:20  version:    MPC1000 SEQ 4.40
28:30 bars:       8
32:34 bpm:        80
################## End of header ###################
your SEARCHTERM "FunkBG" was not found!
```

Punk would instead be found and we _would have_ similar options as with our first search above:

```
seq -b "80" -s "Punk" .

* PATH used: .
* searching for "Punk" (after End of header)
* bpm_list (filter_list): ['80']

############### FunkBG_080_8bar.SEQ ################
4:20  version:    MPC1000 SEQ 4.40
28:30 bars:       8
32:34 bpm:        80
################## End of header ###################
Found first occurence of SEARCHTERM at index 7168, it's 4 chars long
If SEARCHTERM is the START of a wav filename in an AUDIO track,
this would be the first half:       "PunkBG_0"
and this would be the second half:  "80_8bar"
** REPLACE OPTIONS: ********************************
** --replace simply replaces Punk with REPLACETERM.
** --correct-wav (-w) puts this files basename at found terms position,
**     it would replace "PunkBG_0" with "FunkBG_0",
**     and              "80_8bar" with "80_8bar".
** --correct-wav-bpm (-p) just replaces the bpm part in the found term,
?? didn't find a possible bpm value in given term (Punk),
?? use underscores or dashes as seperating characters!
**     it would replace "Punk" with "Punk".
** If this all looks like crap, don't do it! Existing files will be OVERWRITTEN!
```


## Another more sophisticated example

This is the use case I actually wrote this script for. Let's take the file from above example where we had replaced Funk with Punk, but let's copy and _rename_ them. You can do the copy/renaming however you like, eg iOS X Finder has a nice mass renaming tool built-in. I do it directly on the commandline now, while we are at it:


```
cp FunkBG_080_8bar.SEQ PunkBG_080_8bar.SEQ
cp FunkBG_080_8bar.SEQ PunkBG_090_8bar.SEQ
cp FunkBG_080_8bar.SEQ PunkBG_100_8bar.SEQ
```

Ok now we'd like to set the wav files name in all of the 3 "Punk sequence files" to the same as the filename. We first search for Punk and see what we have. Probably there are other seq files in this folder so we particularily select our 3 files with the ```--filter (-b)``` option:


```
seq --filter Punk -s "PunkBG" .

* PATH used: .
* searching for "PunkBG" (after End of header)
* bpm_list (filter_list):	['Punk']

############### PunkBG_080_8bar.SEQ ################
4:20  version:    MPC1000 SEQ 4.40
28:30 bars:       8
32:34 bpm:        80
################## End of header ###################
Found first occurence of SEARCHTERM at index 7168, it's 6 chars long
If SEARCHTERM is the START of a wav filename in an AUDIO track,
this would be the first half:       "PunkBG_0"
and this would be the second half:  "80_8bar"
** REPLACE OPTIONS: ********************************
** --replace simply replaces PunkBG with REPLACETERM.
** --correct-wav (-w) puts this files basename at found terms position,
**     it would replace "PunkBG_0" with "PunkBG_0",
**     and              "80_8bar" with "80_8bar".
** --correct-wav-bpm (-p) just replaces the bpm part in the found term,
?? didn't find a possible bpm value in given term (PunkBG),
?? use underscores or dashes as seperating characters!
**     it would replace "PunkBG" with "PunkBG".
** If this all looks like crap, don't do it! Existing files will be OVERWRITTEN!


############### PunkBG_090_8bar.SEQ ################
4:20  version:    MPC1000 SEQ 4.40
28:30 bars:       8
32:34 bpm:        80
bpm in filename is different! correct with -c
################## End of header ###################
Found first occurence of SEARCHTERM at index 7168, it's 6 chars long
If SEARCHTERM is the START of a wav filename in an AUDIO track,
this would be the first half:		"PunkBG_0"
and this would be the second half:	"80_8bar"
** REPLACE OPTIONS: ********************************
** --replace simply replaces PunkBG with REPLACETERM.
** --correct-wav (-w) puts this files basename at found terms position,
**     it would replace "PunkBG_0" with "PunkBG_0",
**     and              "80_8bar" with "90_8bar".
** --correct-wav-bpm (-p) just replaces the bpm part in the found term,
?? didn't find a possible bpm value in given term (PunkBG),
?? use underscores or dashes as seperating characters!
**     it would replace "PunkBG" with "PunkBG".
** If this all looks like crap, don't do it! Existing files will be OVERWRITTEN!


############### PunkBG_100_8bar.SEQ ################
4:20  version:    MPC1000 SEQ 4.40
28:30 bars:       8
32:34 bpm:        80
bpm in filename is different! correct with -c
################## End of header ###################
Found first occurence of SEARCHTERM at index 7168, it's 6 chars long
If SEARCHTERM is the START of a wav filename in an AUDIO track,
this would be the first half:		"PunkBG_0"
and this would be the second half:	"80_8bar"
** REPLACE OPTIONS: ********************************
** --replace simply replaces PunkBG with REPLACETERM.
** --correct-wav (-w) puts this files basename at found terms position,
**     it would replace "PunkBG_0" with "PunkBG_1",
**     and              "80_8bar" with "00_8bar".
** --correct-wav-bpm (-p) just replaces the bpm part in the found term,
?? didn't find a possible bpm value in given term (PunkBG),
?? use underscores or dashes as seperating characters!
**     it would replace "PunkBG" with "PunkBG".
** If this all looks like crap, don't do it! Existing files will be OVERWRITTEN!
```

If we closely examine the output for the 3 files we'd find these useful possibilities

  * ```--correct-bpm (-c)``` could correct the BPM of the sequence in files 2 and 3 (the copies)
  * ```--correct-wav (-w)``` could replace the name of the AUDIO tracks wav file so it's equal to the seq files name. Also in files 2 and 3 (the copies)

If we would now use options ```-w``` and ```-c``` option we are getting the following output:

```
seq --filter Punk -s "PunkBG" -w -c

* PATH used: .
* searching for "PunkBG" (after End of header)
* bpm_list (filter_list): ['Punk']
* correct-bpm is enabled!
* correct-wav is enabled!

############### PunkBG_080_8bar.SEQ ################
4:20  version:    MPC1000 SEQ 4.40
28:30 bars:       8
32:34 bpm:        80
################## End of header ###################
Found first occurence of SEARCHTERM at index 7168, it's 6 chars long
If SEARCHTERM is the START of a wav filename in an AUDIO track,
this would be the first half:       "PunkBG_0"
and this would be the second half:  "80_8bar"
-> found underscore seperated bpm value in given term: 80
!!! putting "PunkBG_0" where "PunkBG_0",
!!! putting "80_8bar" where "80_8bar",
!!! replacing bpm value,
!!! and overwriting ./PunkBG_080_8bar.SEQ ...


############### PunkBG_090_8bar.SEQ ################
4:20  version:    MPC1000 SEQ 4.40
28:30 bars:       8
32:34 bpm:        80
bpm in filename is different! This will be fixed now!
################## End of header ###################
Found first occurence of SEARCHTERM at index 7168, it's 6 chars long
If SEARCHTERM is the START of a wav filename in an AUDIO track,
this would be the first half:       "PunkBG_0"
and this would be the second half:  "80_8bar"
-> found underscore seperated bpm value in given term: 90
!!! putting "PunkBG_0" where "PunkBG_0",
!!! putting "90_8bar" where "80_8bar",
!!! replacing bpm value,
!!! and overwriting ./PunkBG_090_8bar.SEQ ...


############### PunkBG_100_8bar.SEQ ################
4:20  version:    MPC1000 SEQ 4.40
28:30 bars:       8
32:34 bpm:        80
bpm in filename is different! This will be fixed now!
################## End of header ###################
Found first occurence of SEARCHTERM at index 7168, it's 6 chars long
If SEARCHTERM is the START of a wav filename in an AUDIO track,
this would be the first half:       "PunkBG_0"
and this would be the second half:  "80_8bar"
-> found underscore seperated bpm value in given term: 100
!!! putting "PunkBG_1" where "PunkBG_0",
!!! putting "00_8bar" where "80_8bar",
!!! replacing bpm value,
!!! and overwriting ./PunkBG_100_8bar.SEQ ...
```

A last check is showing us that the wav file name and also the BPM have been corrected: 

```
seq --filter Punk -s "PunkBG" .

* PATH used: .
* searching for "PunkBG" (after End of header)
* bpm_list (filter_list): ['Punk']

############### PunkBG_080_8bar.SEQ ################
4:20  version:    MPC1000 SEQ 4.40
28:30 bars:       8
32:34 bpm:        80
################## End of header ###################
Found first occurence of SEARCHTERM at index 7168, it's 6 chars long
If SEARCHTERM is the START of a wav filename in an AUDIO track,
this would be the first half:       "PunkBG_0"
and this would be the second half:  "80_8bar"
** REPLACE OPTIONS: ********************************
** --replace simply replaces PunkBG with REPLACETERM.
** --correct-wav (-w) puts this files basename at found terms position,
**     it would replace "PunkBG_0" with "PunkBG_0",
**     and              "80_8bar" with "80_8bar".
** --correct-wav-bpm (-p) just replaces the bpm part in the found term,
?? didn't find a possible bpm value in given term (PunkBG),
?? use underscores or dashes as seperating characters!
**     it would replace "PunkBG" with "PunkBG".
** If this all looks like crap, don't do it! Existing files will be OVERWRITTEN!


############### PunkBG_090_8bar.SEQ ################
4:20  version:    MPC1000 SEQ 4.40
28:30 bars:       8
32:34 bpm:        90
################## End of header ###################
Found first occurence of SEARCHTERM at index 7168, it's 6 chars long
If SEARCHTERM is the START of a wav filename in an AUDIO track,
this would be the first half:       "PunkBG_0"
and this would be the second half:  "90_8bar"
** REPLACE OPTIONS: ********************************
** --replace simply replaces PunkBG with REPLACETERM.
** --correct-wav (-w) puts this files basename at found terms position,
**     it would replace "PunkBG_0" with "PunkBG_0",
**     and              "90_8bar" with "90_8bar".
** --correct-wav-bpm (-p) just replaces the bpm part in the found term,
?? didn't find a possible bpm value in given term (PunkBG),
?? use underscores or dashes as seperating characters!
**     it would replace "PunkBG" with "PunkBG".
** If this all looks like crap, don't do it! Existing files will be OVERWRITTEN!


############### PunkBG_100_8bar.SEQ ################
4:20  version:    MPC1000 SEQ 4.40
28:30 bars:       8
32:34 bpm:        100
################## End of header ###################
Found first occurence of SEARCHTERM at index 7168, it's 6 chars long
If SEARCHTERM is the START of a wav filename in an AUDIO track,
this would be the first half:       "PunkBG_1"
and this would be the second half:  "00_8bar"
** REPLACE OPTIONS: ********************************
** --replace simply replaces PunkBG with REPLACETERM.
** --correct-wav (-w) puts this files basename at found terms position,
**     it would replace "PunkBG_1" with "PunkBG_1",
**     and              "00_8bar" with "00_8bar".
** --correct-wav-bpm (-p) just replaces the bpm part in the found term,
?? didn't find a possible bpm value in given term (PunkBG),
?? use underscores or dashes as seperating characters!
**     it would replace "PunkBG" with "PunkBG".
** If this all looks like crap, don't do it! Existing files will be OVERWRITTEN!
```

FIXME... example how to use --correct-wav-bpm


