---
layout: post
title: The story of ADHS-Tron
comments: true
published: 2018-01-31
last_modified_at: 2018-02-07
image: images/2017-09-10_adhs-tron/17-th.jpg
---

The mission: My friend Lena&#39;s Korg Monotron should become controllable via MIDI from a DAW. <br>

<br>

<div class="clearfix">
{% include figure.html filename='/images/2017-09-10_adhs-tron/1.jpg' alt_text='pic 1' caption='Starting Point: Monotron, a Perfboard and an Arduino Uno' width="49%" float="left" %}
{% include figure.html filename='/images/2017-09-10_adhs-tron/2.jpg' alt_text='pic 2' caption='Naked-Tron' width="49%" float="right" %}
</div>
<br>

![pic 3](/images/2017-09-10_adhs-tron/3.jpg)
First goal reached: Arduino receives MIDI notes through a MIDI input circuit
<br><br>

{% include youtube.html id="5jWiUlhN29o" width="100%" %}
Arduino receives MIDI through input circuit and triggers Gate and Pitch CV inputs on Monotron. As you can hear it&#39;s not quite a major or chromatic scale. Arduino Uno&#39;s 8bit DAC can&#39;t output precise enough voltages for Pitch CV.
<br><br>

The code necessary for above functionality:
<!--<script src="http://gist-it.appspot.com/https://github.com/JOJ0/ADHS-Tron/blob/0d57429476b3d251b1390e9532fc67db75ba6be8/hyperactron.ino"></script>-->
<!--<script src="https://gist.github.com/JOJ0/518416dc60bfcbd5bf2322b101b25076.js"></script>-->
{% gist 518416dc60bfcbd5bf2322b101b25076 %}

At this point it's about time to tell you that the snippets you see on this page are reconstructed with the help of my git history and I can't guarantee that the program was completely working/bugfree at that particular commit. If you find something odd please leave a comment and I'm happy to help, correct it, whatever. On the bottom of this page you find a link to the final code that worked for me.
<br><br>

{% include figure.html filename='/images/2017-09-10_adhs-tron/4.jpg' alt_text='pic 4' caption='' width="49%" float="left" %}
{% include figure.html filename='/images/2017-09-10_adhs-tron/4.5.jpg' alt_text='pic 4.5' caption='' width="49%" float="right" %}
The solution to the Pitch Control Voltage problem with Arduino Uno: Microcontroller &#34;Teensy 3.2&#34;, equipped with a 12 bit DAC, precise enough to generate the needed voltages.
<br><br>

Arduino compatible code needs to be changed slightly to run on a Teensy (different serial ports and obviously pin numbers):
<!--<script src="http://gist-it.appspot.com/https://github.com/JOJ0/ADHS-Tron/blob/1ae1e123f3df8902e356ed3d87fe8f05327972fd/hyperactron.ino?slice=1:23"></script>-->
{% gist 84f34b373e50df24faadbd5e51d7d514 %}

At that time I was not quite sure how I could possibly get the pitches right, I just did not know what the volts/octave definition is for the Monotron. After hours of trial and error I came up with this formula that sounded correctly over almost a 3 octave range (the lowest 3 notes always are a bit too low if you tune your Monotron to about 10:00 o'clock):
{% gist e623e3313837de6596103585f59856fd %}

Weeks later I found a little mark on the freely available Monotron schematic that probably would have helped a little! ;-)

whole ribbon Vbe offset<br>
24.49mV@0deg<br>
26.29mV@20deg<br>
28.08mV@40deg<br>
<br>


![pic 5](/images/2017-09-10_adhs-tron/5.jpg)
Added two new features: Filter cutoff controllable via MIDI CC or MIDI velocity, MIDI control can be switched off to keep original onboard filter control intact (see bottom of post for code)
<br><br>

![pic 6](/images/2017-09-10_adhs-tron/6.jpg)
The first cardboard prototype of Tron&#34;s new housing.
<br><br>

{% include youtube.html id="5XTypg-dH6w" width="100%" %}
Filter controlled via MIDI CC (pink line), playing around with the resonance is always fun
<br><br>

![pic 7](/images/2017-09-10_adhs-tron/7.jpg)
To fit everything in the case, all components on the breadboard (white) are to be soldered on a perfboard (brown). The original Monotron printed circuit board should sit right next to it.
<br><br>

![pic 8](/images/2017-09-10_adhs-tron/8.jpg)
Designing and soldering the perfboard
<br><br>

![pic 9](/images/2017-09-10_adhs-tron/9.jpg)
The almost finished perfboard
<br><br>

![pic 10](/images/2017-09-10_adhs-tron/10.jpg)
Perfboard flipside
<br><br>

{% include youtube.html id="JBsHow5AMUg" width="100%" %}
Features presented in order of appearance (If unpatient skip to 2:30 for some acidish sounds)
* Filter cutoff and resonance controlled locally
* Filter cutoff controlled via MIDI CC (pink line), resonance locally
* LFO modulating filter cutoff, amount and rate controlled locally

additional features not shown here
* Filter cutoff controlled via MIDI velocity
* LFO controlled via MIDI CC
<br><br>

![pic 11](/images/2017-09-10_adhs-tron/11.jpg)
Happy outdoor hacking
<br><br>

![pic 12](/images/2017-09-10_adhs-tron/12.jpg)
Designing the final layout of the control elements
<br><br>

![pic 13](/images/2017-09-10_adhs-tron/13.jpg)
The final cardboard prototype
<br><br>

![pic 14](/images/2017-09-10_adhs-tron/14.jpg)
Inside the prototype, trying to fit the cables in the case...
<br><br>

![pic 15](/images/2017-09-10_adhs-tron/15.jpg)
Drilling the case
<br><br>

![pic 16](/images/2017-09-10_adhs-tron/16.jpg)
Mounting the control elements
<br><br>

![pic 17](/images/2017-09-10_adhs-tron/17.jpg)
ADHS-Tron ready to roll!
<br><br>

Get the final code to this project here: [github.com/joj0/adhs-tron](https://github.com/joj0/adhs-tron). Feel free to fork, send issues and so on!
<br><br>
