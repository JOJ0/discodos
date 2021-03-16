---
layout: post
title: Volca Beats Velocity - Max for Live edition
comments: true
published: 2018-03-23
image: /images/2018-3-11_volca-beats-m4l-velocity/VolcaBeatsVelocitizer-v1.0-screenshot.png
---

I got some feedback on my last [post]({% post_url 2017-8-29-volca-beats-velocity %}), learned some Max 4 Live and managed to create a device that hacks MIDI velocity sensitivity into the Korg Volca Beats.

{::comment}
[post]({% post_url 2017-8-29-volca-beats-velocity %})
image: /images/2018-3-11_volca-beats-m4l-velocity/VolcaBeatsVelocitizer-v1.0-screenshot-thumb.png
{:/comment}

{% include figure.html filename='/images/2018-3-11_volca-beats-m4l-velocity/VolcaBeatsVelocitizer-v1.0-screenshot.png' alt_text='Velocitizer screenshot' caption='' width="49%" float="left" margin="0 10px 0 0" %}

<p style="margin-top: -5px;">As already described in detail in the mentioned post, the Volca does not interpret a MIDI note's velocity, each drum's volume can only be changed by sending a Control Change command. My M4L device simply translates the MIDI note's velocitiy values to the corresponding CC values and prepends each note hit with such a MIDI message. It also visualizes each drum hit and its velocity.
</p>

Download it from [maxforlive.com](http://www.maxforlive.com/library/device/4624/volca-beats-velocitizer)

Alright, and now for those who are interested about the internals or want to learn something about Max for Live: A friend from Berlin left a comment on my last post and pointed me to a device named "Volca FM Velocitizer" which does exactly the same but for only one note at a time (and not 10 notes/drums simultaneously). If solving this exercise in an ordinary programming language you would probably think about just adding something like an array, a matrix, a list, a dictionary, or whatever it's called in the particular language. In other words a kind of mapping table that translates a note number to a CC number. 

I did not know how such an object is called in Max, so I asked in the Max for Live department of the Ableton Live forum. The answer I got was a whole Max patch, actually the essence of my device. I built from there, learned a lot and here we go, this is what I came up with:

<div class="clearfix">
{% include figure.html filename='/images/2018-3-11_volca-beats-m4l-velocity/VolcaBeatsVelocitizer-v1.0-internals.png' alt_text='' caption='' width="100%" float="left" %}
</div>

The bottom left portion is the core of the device, it's part of the patch I got sent on the forum. The top left portion are just debug note triggers to test the functionality. The bottom right part is the visualisation.

I won't go into detail about how the whole thing works but I'd like to point out a couple of things I find valuable to know: As mentioned you would need some kind of mapping table. In Max one object that can do this is called "coll", short for collection.

This is the contents of "coll ---NotesToCC":
~~~ python
36, 40;
38, 41;
43, 42;
50, 43;
42, 44;
46, 45;
39, 46;
75, 47;
67, 48;
49, 49;
~~~
If e.g. you send number 36 (Note C2 - Kick drum) into the colls input (top left of object), it sends out number 40 on its output (bottom left of object), which is the CC number that controls the Kicks volume.

As you can see in the picture I used more colls to map stuff. "coll ---NamesToNotes" maps the debug drum buttons names to the right MIDI note numbers e.g.:
~~~ python
Kick, 36;
Snare, 38;
...
~~~

I built these manual drum triggers out of annoyance. Switching between Max and Live for running test-MIDI-clips gets boring after a while. Also I was curious about how I actually could generate simple MIDI note-on and note-off messages myself.

and the third one, "coll ---NotesToSliders", maps the note numbers to the  "slider" of the visualisation object (it's called a "multislider"). The sliders are indexed starting from 0, left to right:
~~~ python
36, 0;
38, 1;
...
~~~
One detail that cost me quite some troubleshooting time is that a coll does not save its data by default, you have to enable a checkbox in the inspector window "Save Data With Patcher", otherwise the coll is empty, the next time you open the device! Another feature of a coll, that I actually did not use in this procject but worth knowing: It cannot only send out existing data, it can also save new data. If you send it two values at the same time (in Max speak this is called a "list"), so e.g. if you send "12 34" into its input, the coll would be appended with another line that looks like this: 

~~~ python
12, 34;
~~~

Before creating this device, I had poor M4L knowledge, I once added a feature to a [Jomox Airbase99 control device](http://www.maxforlive.com/library/device/244/fm-jomox-air-base-99-control) but that was about 2 years ago and my memories where dark already. So thanks again to Hannes, to wzrdzl, the creator of "Volca FM Velocitizer", and to Ableton-forum user doubleUG for motivating and teaching me.

There will be more M4L on this blog in the future! I am currently working on another Volca Beats control device, it will feature a MIDI note remapping option for MPC style (4x4) drumpad controllers (Volca Beats has General-MIDI-mapping, Agogo and Claves are far off the default 4x4 grid, no more scrolling your drumpad to reach them!)


