---
layout: post
title: Template Blog Post
comments: true
published: 2019-01-01
image: /images/2017-9-24-das-adhs/IMG_5209.jpg
draft: true
---

Intro blabla

<a name="chapter_1"></a>
### Chapter 1



two thumbs included here:

<div class="clearfix">
  {% include thumb.html filename='/images/2017-9-24-das-adhs/xx.jpg' alt_text='' caption='' width="49%" float="left" %}
  {% include thumb.html filename='/images/2017-9-24-das-adhs/xx.jpg' alt_text='' caption='apostroph example wasn&#34;t' width="49%" float="right" %}
</div>
<br>




3 pics in a row template here:

<div class="pic_row_3">
  <div class="pic_left">
    {% include thumb.html filename='/images/2018-11-17-midictrl1/matrixmidi-xx.jpg' caption='' %}
  </div>
  <div class="pic_middle">
    {% include thumb.html filename='/images/2018-11-17-midictrl1/matrixmidi-xx.jpg' caption='' %}
  </div>
  <div class="pic_right">
    {% include thumb.html filename='/images/2018-11-17-midictrl1/matrixmidi-xx.jpg' caption='' %}
  </div>
</div>




youtube video here:

{% include youtube.html id="xxxxxx" width="100%" %}
text under youtube video
<br><br>




photogallery here (collection has to be createdi first):

<div class="photo-gallery-frame clearfix">
  <ul class="photo-gallery-list">
    {% for photo in site.the_collections_name %}
    <li>
      <a href="{{ photo.url | prepend: site.baseurl }}" name="{{ photo.title }}">
        <img src="{{ photo.image-path|remove: ".jpg"| append: '-th'|append: ".jpg" }}" alt="{{ photo.caption }}" />
      </a>
    </li>
    {% endfor %}
  </ul>
</div>



### Supplies

blabla getting stuff

[link 1](https://www.musikding.de/20-Pin-inline-socket)<br>
[link 2](https://www.musikding.de/10-Pin-strip)<br>
