---
title: Capture the real location
date: 2026-09-22
summary: We tried to source locations from splat libraries and stock drone footage. None of it matched the storyboard. So our pipeline now starts with planning our own capture.
---

Our pipeline rests on one idea: generated shots should start from a real place. The obvious shortcut is to not go there: find a Gaussian splat of a similar location online, or pull stock drone footage, and generate from that. We tried hard to make that work. It doesn't.

## Close enough isn't close enough

We went through the free and commercial splat libraries and the big stock footage sites. There is plenty of beautiful material. The problem is that it's never *your* shot. A found scan gives you a place, but not the angle the storyboard calls for, not the lens, and not the detail inserts that were planned. Adapting it means hand-tailoring every frame, which is exactly the kind of fiddly compositing work the pipeline is supposed to remove.

Licensing makes it worse. For a film you intend to distribute, only a few licences are clean. Many "free" scans don't allow commercial use or derivatives, and generating from a scan is a derivative. Stock footage licences generally don't allow turning the footage into a redistributable 3D scan at all.

## The shot list already knows what's needed

There's one stage of production where everyone knows exactly which angles, lenses and details matter: the day the crew is standing at the location with the shot list. So instead of replacing that step, we organise it.

The shot list becomes the spec for the capture. For each set, our tools work out which scan passes cover the planned framings, which close-up photos carry the textures the model needs, and afterwards, where the scan has gaps.

## Clean up the image, not the scan

A phone or drone scan is never perfect. Rather than trying to fix the 3D scan, we use it for what it's good at, which is getting the space and the camera position right, and then restore the rendered frame into a photographic keyframe using reference photos from the same location. The scan provides structure; the photos provide detail. We'll write up how well that works in the next post.

Longer term, we'd love a community where drone operators can offer their own captures of real locations. But that comes after the core loop works: capture the place, plan the shots, and generate coverage that actually belongs in the film.
