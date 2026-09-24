---
title: Why our pipeline runs locally
date: 2026-09-16
summary: The first design for our production tools was a cloud platform. We threw it out on day one. Here's why a local-first pipeline is the right shape for hybrid filmmaking.
---

The first architecture for Isora, the software behind the studio, was a cloud platform: upload footage and location scans, let a server enrich them with AI-generated context about the place, then query that context whenever a shot is generated. It looked good on a whiteboard. It lasted about fifteen minutes once we did the math.

## Footage is heavy

Professional footage runs close to a gigabyte a minute. A cloud pipeline has to upload it, store it and stream it back, on every project. That cost lands on the production, and it buys nothing the film needs.

The only part of this workflow that genuinely needs the cloud is the video model itself. Everything else, from breaking down the script to organising takes to building keyframes, runs well on a laptop. So our pipeline runs locally. A project is an ordinary folder on our machines, and nothing leaves them except the few reference frames a given shot needs to send to a model.

## Pay for what's generated, nothing else

Video models change fast, and so do their prices. Our tools treat each model provider as an interchangeable part, so we can pick the right one for each shot, and they estimate what a generation will cost before it runs. Clients see generation costs up front instead of discovering them later.

## Facts beat guesses

The cloud design also had an AI "context layer" that would guess things about a location: plant species, how the trees look in another season, likely weather. We cut it. A few well-chosen photos of the real place anchor a generation better than any description, and the facts that do matter are cheap and exact: coordinates, where the sun is at call time, which camera and lens were used, and what the weather was on the day. None of that needs a language model.

## What that means on a production

- Your footage stays with the production, not on someone else's platform.
- Every generated clip records its model, prompt, references, seed and cost, so the edit always knows what was shot and what was made.
- The finished work goes into a normal edit. Our tools hand off to Final Cut Pro; they don't try to replace it.

It's a smaller system than the cloud version. It's also one an independent production can afford.
