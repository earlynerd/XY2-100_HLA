# XY2-100_HLA
XY2-100 High Level Analyzer for Saleae Logic 2
This repository contains a Saleae High Level Analyzer (HLA) for decoding the XY2-100 serial protocol used for laser galvanometer scanners.

![Logic 2 screenshot](/resources/analyzer.png)
## Protocol Overview
The XY2-100 protocol is a 20-bit serial protocol for transmitting X, Y, or Z position data. It has two main modes:

Standard 16-bit mode: Transmits 16 bits of position data with an even parity check. The frame is identified by the header 001.

Enhanced 18-bit mode: Transmits 18 bits of position data with an odd parity check. The frame is identified by a 1 in the most significant bit.

This HLA decodes both modes and verifies the parity bit.

## Setup in Saleae Logic 2
This High Level Analyzer requires a low-level analyzer to be configured first to handle the clock, data, and framing signals. The Simple Parallel analyzer is the correct choice for this protocol.

1. Capture Signals
Start by capturing the CLK, SYNC, and Data lines from your XY2-100 device.

2. Add and Configure the Simple Parallel Analyzer
Click on the "Analyzers" panel on the right.

Click the "+" button and add a Simple Parallel analyzer.

Configure the parallel analyzer settings as follows:

Input Channels:

CLK: Your XY2-100 CLK channel.

D0: Your XY2-100 Data channel.

D1: Your XY2-100 SYNC channel.

(You can leave the other D channels unassigned).

Settings:

Number of Data Lines: 2

Clock Edge: Falling Edge (Data is valid on clock trailing edge).

3. Add the XY2-100 HLA
Click the "+" button in the "Analyzers" panel again.

Select the XY2-100 analyzer from the list.

For its input, select the output of the Simple Parallel analyzer you just created.

In the XY2-100 analyzer's settings, choose whether you are decoding the X, Y, or Z channel to label the decoded data correctly.

You should now see the decoded XY2-100 position data on the timeline. Repeat for each channel (X, Y, Z) you wish to decode.
