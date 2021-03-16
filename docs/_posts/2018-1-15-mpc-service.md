---
layout: post
title: MPC 1000 service - a Photo-Love-Story
comments: true
published: 2018-04-25
image: /images/2018-1-15-mpc-service/IMG_6210-th.jpg
draft: false
---
Alright, probably every MPC owner experiences it after a while: Buttons getting sluggish, you have to really bang them hard to still get a function.

Especially with heavy used buttons like "cursor right", which is also used as kind of a "return" key it can get pretty annoying. But let's face it: These units are dated! According to the timestamps on the circuit boards, mine was built around 2009, that's 9 years ago now. Some parts are even stamped with 2006. I suppose the MPC 500 and 2500, which AKAI produced around the same time (2005~2010) suffer from similar problems.

You guessed it, this post is about repairing or rather replacing these buttons.

Don't be overwhelmed because of the amount of pictures, it's not as much work as it looks. I replaced 10 of those so called "small tact switches" that do the work underneath the plastic buttons. It took me 3 hours, including taking photos. I also had to reopen it a second time because I forgot to connect a cable, so I'd say: 2 hours should be doable. If you are only replacing a couple of switches certainly even shorter.

For recommendations where to buy the switches and what types you need, jump to [bottom of post](#get_switches)

Ok, so this is the Photo-Love-Story. If you click on the thumbnails you'll find some short descriptions, for example how many screws you'd have to take out or what to pay special attention to. If you've never soldered out a component before, watch a youtube video and practice on some junk first. Also: soldering-out with four hands is easier than with two!

<div class="photo-gallery-frame clearfix">
  <ul class="photo-gallery-list">
    {% for photo in site.mpc-service %}
    <li>
      <a href="{{ photo.url | prepend: site.baseurl }}" name="{{ photo.title }}">
        <img src="{{ photo.image-path|remove: ".jpg"| append: '-th'|append: ".jpg" }}" alt="{{ photo.caption }}" />
      </a>
    </li>
    {% endfor %}
  </ul>
</div>
<a name="get_switches"></a>
## Where to get the switches? ##

For general electronics tools and components you could order at reichelt.at, it's a well sorted german electronics online shop with reasonable prices and cheap shippping costs! So if you are somewhere in Europe this is a nice option. You want [this one](https://secure.reichelt.at/TASTER-9302/3/index.html?ACTION=3&LA=55&ARTICLE=44579)

I bought my switches at conrad.at as far as I remember. Even though I wouldn't recommend buying any stuff there because they overprice literally everything, you still wouldn't pay much for those there. You could get [this one](https://www.conrad.at/de/drucktaster-24-vdc-005-a-1-x-ausein-te-connectivity-1825910-2-tastend-1-st-701749.html) or [that one](https://www.conrad.at/de/drucktaster-12-vdc-005-a-1-x-ausein-namae-electronics-jtp-1130-tastend-1-st-705247.html)

Unfortunately I don't have any recommendations for other countries/continents but I'd like to warn about one thing: Don't, don't, don't ever buy one of those switches at mpcstuff.com. At the time of writing they charge 8$ for one of those little nothings. Eight Dollars! This is ridiculous! Their switches are not better or something they just overprice because they can!!! Don't support this! Thanks! 

If you are buying somewhere else: There are several sizes available. You need those that have a _height_ of 5mm. Heigth is measured from the bottom of the switches case to the top surface of the round black button. Have a look at the [datasheet](http://cdn-reichelt.de/documents/datenblatt/C200/TASTER93XX.pdf), the bottom left drawing shows height with the letter "L". The table on the right side shows the available values for "L". 
