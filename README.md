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

2. Click the "+" button and add a Simple Parallel analyzer.

3. Configure the parallel analyzer settings as follows:

    - Clock: Select your CLK+ signal line.

    - Data Lines: This is the most important step. You must add the Data and SYNC lines in the exact order shown below. You can add up to 4 lines for this analyzer.

    - D0: Select your Data_X+ signal.

    - D1: Select your Data_Y+ signal.

    - D2: Select your Data_Z+ signal (if you are using it).

    - D3: Select your SYNC+ signal.

    - Data is Valid: Set to On falling edge of clock.

    - You can uncheck the boxes for "stream to terminal" and "show in protocol results table" to speed up processing and declutter the result table.

    - Click Save.

4. Add the XY2-100 HLA
    - Click the "+" button in the "Analyzers" panel again.

    - Select the XY2-100 analyzer from the list.

    - For its input, select the output of the Simple Parallel analyzer you just created.

That's it! The single XY2-100 HLA instance will now process the data from the parallel analyzer and output separate, tagged frames for the X, Y, and Z channels.


