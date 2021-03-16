---
layout: post
title: The Charger Tape
comments: true
published: 2019-03-26
image: /images/2018-11-3-charger-tape/ChrgTpCase-22-th.jpg
#permalink: /charger-tape
draft: false
---

Alright, let's do something boring: Building a battery charger. So why would you do that? I don't have any idea, just go buy one! ;-) But apparently I had a reason to build one myself.

Some time ago I built a couple of rechargeable button-cell-battery-packs which are featured in [this post]({% post_url 2017-9-24-das-adhs %}#building-7-segment)<br>After trying to recharge one of them with an old NiCd fast-charger I learned the hard way how my batteries actually look from the inside:

<div class="pic_row_3">
  <div class="pic_left">
    {% include thumb.html filename='/images/2018-11-3-charger-tape/ChrgTpExpl-01.jpg' caption='' %}
  </div>
  <div class="pic_middle">
    {% include thumb.html filename='/images/2018-11-3-charger-tape/ChrgTpExpl-02.jpg' caption='' %}
  </div>
  <div class="pic_right">
    {% include thumb.html filename='/images/2018-11-3-charger-tape/ChrgTpExpl-03.jpg' caption='' %}
  </div>
</div>

Don't try this at home kids! 

So far so good, I didn't burn my flat yet, so I decided to either buy or build a charger that is designed to charge Nickel-Metal Hybride (NiMH) batteries with very little capacity.


## What you always wanted to know about rechargeable batteries

First off, my tiny button cell accumulators have the following specs:

  * 1,2 V (exactely the same as normal AA, AAA, etc. rechargable batteries;
    this value is nominal, in reality most of them have a little more, something like 1,3 to 1,45 when fully charged) 
  * 80 mAh ([milliampere hours](https://whatis.techtarget.com/definition/milliampere-hour-mAh)) capacity

In short: They are ordinary rechargeable batteries and it actually should be save to load them with an ordinary charger.

So why did my test-candidate explode then?

It was simply overcharged. NiMH cells are designed to be only fast-charged until they reach their full capacity. After that, keeping them connected to high current results in a lot of heat and...you saw the pics.

So either the charger has thermal sensors to shut off before overheating, or it just uses a low current the cell can withstand for a longer (infinite) time duration.

Sensoring seemed tedious so I decided to build a low current charger.

A safe current for NiMH cells is 1/10 of their capacity (1/10 C) or even less. In my batteries case this would be 1/10 * 80 = 8mA. There you have it: No affordable charger on the market seems to handle such a low current. Typically chargers go as low as 150 mA, which is fine for typical batteries which have a capacity of 1500 mAh to 2500 mAh (or even more), but not for my tiny 80 mAh cells.


## Finding and customizing a circuit design
<a name="finding"></a>

Some googling and studying charger designs brought up [this forum thread](https://forum.allaboutcircuits.com/threads/constant-nimh-trickle-charger.14624/). The schematic suggested by member SgtWookie seemed to be a perfect fit:

<div class="clearfix">
{% include thumb.html filename='/images/2018-11-3-charger-tape/ChrgTpSchem-01.jpg' alt_text='' caption='' width="100%" float="left"%}
</div>


It features two regulator ICs (TLV1117C): One limiting the current (U1) and the other one the voltage (U2). The battery(pack) is represented by capacitor C2 (he uses the similar-to-battery-behaviour of the capacitor for the software simulation). I substituted the two regulators with the more common and easy to get LM317 type.


* **Charging voltage** should be set slightly higher than the voltage of the fully charged battery pack. My two-cell packs have about 2 * 1,35 = 2,7 V so around **2,8-2,9 V** should be fine.
  * Fortunately the design already handles charging voltage for two-cell packs. It can be fine tuned using the **trim-pot R5**.
  * measure between point A and ground

* **Charging current** as discussed above, not more than **8 mA**.
  * It is set by **resistors R1,R2** (On first sight it is slightly confusing that he uses 2 identical resistors in parallel. I suppose he did this to split the current  (and thus the power consumption) in half and spare the use of an R with higher power specs (more Watts - more expensive - not as common in ones components stash), I will use just one R as my current is very little compared to the 260 mA in the original design. Let’s just call my resistor R1 and forget about R2.).
  *  open circuit between points A and B and connect multimeter in between for measuring

If you have a look on pages 12 and 13 in the [LM317 datasheet](http://www.ti.com/lit/ds/symlink/lm317.pdf) you will find examples for current and voltage limiting circuits that look almost identical to SgtWookies design. His circuit is basically a combination of two examples. Well done!

This is my final customized version. The 120k resistor R1 configures LM317_1 to limit charging current to 6mA, being even more healthy for my batteries than the discussed 8mA:

<div class="clearfix">
{% include thumb.html filename='/images/2018-11-3-charger-tape/ChrgTpSchem-02.png' alt_text='' caption='' width="100%" float="left" %}
</div>

### Some theory for the geeks

Skip this if it’s boring ;-) I’ll try to explain why in my case R2 surely is not necessary.


#### R1 power consumption - Original design 

Assuming R2 is missing:

The formula for calculating the power consumption of a device (eg. a resistor) is

P = V * I

The V on R1 is unknown so just calculate it using Ohm’s law:

V = R * I = 10 Ohm * 260 mA = 10 * 0,26 = 2,6 V

Now find out how much power R1 has to withstand:

P = V * I = 2,6 * 0,26 = 0,676 W (Watts)

The most common resistors support max power levels of 0,3 to 0,5 Watts. With splitting the current in half by using a second resistor R2 in parallel with R1, also the power consumption is halfed to 0,338 W for each R.


#### R1 power consumption - Customized design

V = R * I = 120 Ohm * 6 mA = 120 * 0,006 = 0,72 V

P = V * I = 0,72 * 0,006 = 0,00432 W = 4,3 mW

4,3 milliwatts is almost nothing and every resistor form factor I know of would withstand it. No need for splitting the current in half with a second R.


#### How long does it take to load then?

theoretically:

t = C / I = 80mAh / 6mA = 0,080 / 0,006 = 13,33 h

I -> current in A<br>
C -> capacity in Ah<br>
t -> time in h

typically a loss of 30-40% has to be counted in, lets calc with 40%:

C = 0,080 + 40% = 0,080 * 1,4 = 0,112
t = C / A = 0,112 / 0,006 = 18,66 h

So let’s say a night and something. It should be safe to leave the charger connected for a couple of days.


<br>

## Giving it a home

...and why it's got its name. Click the thumbnails to zoom in and read short description.

<div class="photo-gallery-frame clearfix">
  <ul class="photo-gallery-list">
    {% for photo in site.charger-tape %}
    <li>
      <a href="{{ photo.url | prepend: site.baseurl }}" name="{{ photo.title }}">
        <img src="{{ photo.image-path|remove: ".jpg"| append: '-th'|append: ".jpg" }}" alt="{{ photo.caption }}" />
      </a>
    </li>
    {% endfor %}
  </ul>
</div>


### Materials

[LM317 regulator](https://www.musikding.de/LM317T_1)<br>

Those are for building power and battery connector plugs:<br>
[10 pin strip (for 4-pin battery connector and 5-pin power supply connector ](https://www.musikding.de/10-Pin-strip)<br>

Unfortunately musikding.de doesn't have the female ones in stock.

Take [these 20 pin inline sockets](https://www.musikding.de/20-Pin-inline-socket) for the resistor connector and the additional regular-battery-holder connector. They are also called transistor-sockets. Keep in mind that they have small holes. Above pin strips won't fit together with them!<br> 

These are some combination packs with headers and sockets that fit together. It's Amazon affiliate links. Click them if you like what you read, I get a tiny percentage of what you bought then. Thanks!<br>
[30 pieces pin headers and sockets pack](https://www.amazon.de/gp/product/B07DBY753C/ref=as_li_tl?ie=UTF8&tag=j0j0sblog-21&camp=1638&creative=6742&linkCode=as2&creativeASIN=B07DBY753C&linkId=26f59e1905e3966e977df01c751fb19b)<br>
[60 pieces pin headers and sockets pack](https://www.amazon.de/gp/product/B01MDRPUFU/ref=as_li_tl?ie=UTF8&tag=j0j0sblog-21&camp=1638&creative=6742&linkCode=as2&creativeASIN=B01MDRPUFU&linkId=663f34d1fe525181873e33ab18d75570)<br>
[40 pieces pin headers and sockets pack](https://www.amazon.de/gp/product/B078SQ1CZF/ref=as_li_tl?ie=UTF8&tag=j0j0sblog-21&camp=1638&creative=6742&linkCode=as2&creativeASIN=B078SQ1CZF&linkId=d296266c2f48d9a38d224eaa07455123)<br>

For resistors buy anything, anywhere. I like [Metal Film types](https://www.musikding.de/Metal-Film-06W), they are quite cheap but can stand about 0,6 Watts, which is a little more than the most common ones with 0,25 Watts (I think they are called carbon-layer). You won't need higher power resistors for this project but it's good to have some in the stash.

The power supply can be almost anything you have lying around. It should deliver a minimum of 6V, I think the LM317 needs this, maybe it works with a 5V one. The absolute maximum input voltage for this IC is up to 30V, so you have a wide range of choices between these values.
