---
layout: post
title: Volca Beats JTCTRL
comments: true
published: 2019-05-23
image: /images/2018-5-10-volca-beats-m4l-jtctrl/Volca_Beats_JTCTRL_v0.8.3_snippet.png
draft: false
---

This is a quick one: I extended my [Volca Beats Velocititzer]({% post_url 2018-3-11-volca-beats-m4l-velocity %}) with a couple of features.<br>
Download the "Max for Live" device [here](http://www.maxforlive.com/library/device/5479/volca-beats-jtctrl)<br>

![JTCTRL screenshot](/images/2018-5-10-volca-beats-m4l-jtctrl/Volca_Beats_JTCTRL_v0.8.3.png)

<a name="features"></a>
### Features

* Everything that's MIDI-CC-controllable on the Beats can be controlled via the dial controls.

* The "4x4 MODE" switch moves Agogo and Claves to MIDI notes inide the 4x4 grid of the "first bank" of your MPC-style controller. No more switching to the next 16 pads!

* The "SEND STATE" button sends, as you probably have already guessed, the current state (duh!), of all dials to your Beats - Thus you can save the settings of your machine together with your Ableton Live project!

* The "BLOCKED" button is a weird one: It changes the "default loading behaviour" of Ableton Live projects containing M4L devices.
    * Normally whenever you are loading a Live project, all contained M4L devices "bang" out the settings of all their dials via MIDI - which means: immediately your Volca Beats sounds different - I don't like this behaviour, especially in live performance situations, so this M4L device initially prevents all data sending to the Volca Beats - it does not let MIDI through until you manually switch off the _blocked-mode_!
    * So basicaly the user has to first _unblock_ the device with this button before it can be used! (The text "BLOCKED" has to be _unlit_) - This has to be done each time you load a Live project containing the JTCTRL device!

* And yes, certainly it makes your Volca Beats velocity sensitive, as long as it's controlled via MIDI notes, exactely like the Velocitizer does.

The device was developed around Mar to May 2018, since then I've used it on each and every gig with my band [ADHS](https://www.facebook.com/ADHSband/) - It's tried and tested well, consider it stable! :-)

I am up for feature requests and suggestions!
