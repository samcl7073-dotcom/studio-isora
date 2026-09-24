---
title: "Test 00: from a rough scan to a usable keyframe"
date: 2026-09-23
summary: Our first bench test took a phone scan of a bedroom, framed shots in it, and restored those renders into photographic keyframes on a laptop. Reference photos cut the hallucinations, with one important catch.
---

Before shooting anything outdoors, we ran the whole idea on the smallest possible set: a bedroom, scanned with a phone as a Gaussian splat, plus a handful of ordinary photos of the room.

## Framing shots inside the scan

A splat lets you put a virtual camera anywhere in the captured space. We framed several angles for a short three-scene test script, including a wide establishing shot, a medium profile beside the window, and a low angle across the bed. The scan made it obvious which angles were usable: where the capture was thin, like a corner by the door, the render fell apart, and those angles were dropped before any generation happened.

Raw splat renders look like what they are, smeared and soft, with blotchy detail. Not something you could cut into a film.

## Restoring the frame

Each render then went through a local image model (FLUX.2 [klein] 4B, running on a 16 GB MacBook) with an instruction to restore it into a photograph without changing the camera or the layout. We ran every angle twice: once with reference photos of the real room, once without.

The results were clear:

- **The camera held.** The restored images kept the render's viewpoint and layout, and the smeared duvet, blinds and furniture came back looking photographic.
- **Reference photos cut the invention.** With the real photos, the shelf above the bed came back with the actual objects on it, and the window showed the real blinds and the real tree outside. Without them, the model made things up: a potted plant, an alarm clock, blinds that weren't there.
- **Photos can't fix what nobody photographed.** Where no reference covered a region, both versions guessed. A half-captured stool in the corner turned into a folding table.

## The catch: wide photos hijack the camera

On two of the angles, adding the reference photos made things worse. The model stopped following the render and reproduced the *photo's* camera instead: the output was simply the reference shot again. It doesn't distinguish "use this for structure" from "use this for texture"; the image with the strongest composition wins.

The fix is to give the model close-up crops of materials that carry no room geometry: the duvet pattern, the blind slats, the wood grain. So our capture plans now ask for detail photos as their own shot type, not just wide plates of the location.

## What's next

Next up is re-running these angles with material crops, then taking the restored keyframes into video generation, and repeating the whole test outdoors, on a real location, in real light.
