---
fingerprint: ee76b7fce86b5b8a
---
The shop's shared visual pieces: two button styles, and a wine bottle drawn in SVG — so the shop needs no image files at all.

@@ 1-2
**`button`** — the main button: a rounded pill in amber with dark text, a soft amber shadow, slightly brighter on hover (`hover:brightness-110`), and a visible outline for keyboard focus.

@@ 4-5
**`quietButton`** — the secondary button: transparent, with a faint border, lighting up slightly on hover.

@@ 7
The doc comment.

@@ 8
**`Bottle`** — draws a bottle in a wine's colour, with a word on its label.

@@ 9-10
An SVG drawing space 60 wide and 160 tall, shown 10 rem tall (`h-40`), with its width following the proportions (`w-auto`) and a deep shadow. Hidden from screen readers: the wine's name is written next to it anyway.

@@ 11-14
**The bottle's outline**, as one path filled with the wine's colour. Its instructions, in short: the neck (12 wide) from the top down to y = 40, curving out to the shoulders, straight down the body to y = 148, rounded bottom corners (the `a` arc commands), and back up the other side. `z` closes the shape.

@@ 15
**The label**: a slightly see-through cream rectangle with rounded corners.

@@ 16-18
**The label's word**, centred (`textAnchor="middle"`) in a small serif font, in dark brown.

@@ 19-21
The closing tags.
