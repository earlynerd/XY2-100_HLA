# High Level Analyzer for the XY2-100 Protocol
# For more information and documentation, please go to https://support.saleae.com/extensions/high-level-analyzer-extensions

from saleae.analyzers import HighLevelAnalyzer, AnalyzerFrame, StringSetting, NumberSetting, ChoicesSetting

class Hla(HighLevelAnalyzer):
    """
    Decodes the XY2-100 laser scanner protocol by implementing a state machine.

    This HLA requires the 'Simple Parallel' low-level analyzer to be
    configured first. See the README.md for setup instructions.
    """

    # Setting to identify which axis is being decoded.
    channel_name = ChoicesSetting(choices=('X', 'Y', 'Z'), label='Channel')

    # Define the output frame types and their display formats.
    result_types = {
        'xy2_100_16bit': {
            'format': '{{data.channel}} | Header: {{data.header}} | Pos: {{data.position}} (16-bit) | Parity: {{data.parity_status}}'
        },
        'xy2_100_18bit': {
            'format': '{{data.channel}} | Header: {{data.header}} | Pos: {{data.position}} (18-bit) | Parity: {{data.parity_status}}'
        },
        'error': {
            'format': 'Error: {{data.error_message}}'
        }
    }

    def __init__(self):
        """
        Initialize the HLA.
        This method is called once when the HLA is created.
        """
        self.state = 'IDLE'
        self.bits = []
        self.frame_start_time = None
        self.prev_sync_bit = None  # Initialize to None for robust start condition handling

    def decode(self, frame: AnalyzerFrame) -> AnalyzerFrame:
        """
        Process a frame from the Simple Parallel analyzer.

        The input frame should contain the state of D0 (Data) and D1 (SYNC)
        on each falling clock edge.
        """
        # Only process 'data' type frames from the underlying analyzer.
        if frame.type != 'data' or 'data' not in frame.data:
            return

        # The Simple Parallel analyzer combines all lines into a single integer.
        # We need to extract the individual bits for SYNC and Data.
        parallel_value = frame.data['data']

        # D0 was configured as the Data line.
        data_bit = (parallel_value >> 0) & 1
        # D1 was configured as the SYNC line.
        sync_bit = (parallel_value >> 1) & 1
        
        # On the first frame, just establish the initial sync state and exit.
        # This prevents a false rising-edge detection if the capture starts with SYNC high.
        if self.prev_sync_bit is None:
            self.prev_sync_bit = sync_bit
            return

        # State: IDLE - waiting for the start of a frame (rising edge on SYNC)
        if self.state == 'IDLE':
            if sync_bit == 1 and self.prev_sync_bit == 0:
                # Rising edge detected, start collecting bits
                self.state = 'COLLECTING'
                self.bits = [data_bit]
                self.frame_start_time = frame.start_time
        
        # State: COLLECTING - gathering the 20 bits of a frame
        elif self.state == 'COLLECTING':
            self.bits.append(data_bit)

            if len(self.bits) == 20:
                # We have a full 20-bit frame, so decode it
                frame_end_time = frame.end_time
                output_frame = None
                
                # Combine the collected bits into a single integer
                data_word = 0
                for bit in self.bits:
                    data_word = (data_word << 1) | bit
                
                # Decode based on the protocol specification
                # Check for enhanced 18-bit mode (bit 19 == 1).
                if (data_word >> 19) & 1:
                    header = (data_word >> 19) & 1
                    position = (data_word >> 1) & 0x3FFFF
                    received_parity = data_word & 1
                    bits_for_parity_check = data_word >> 1
                    num_set_bits = bin(bits_for_parity_check).count('1')
                    expected_parity = 1 if (num_set_bits % 2 == 0) else 0  # Odd parity
                    parity_ok = (received_parity == expected_parity)
                    output_frame = AnalyzerFrame('xy2_100_18bit', self.frame_start_time, frame_end_time, {
                        'channel': self.channel_name,
                        'header': f'0b{header:01b}',
                        'position': f'0x{position:05X}',
                        'parity_status': 'OK' if parity_ok else 'FAIL'
                    })
                
                # Check for standard 16-bit mode (bits 19,18,17 == 001).
                elif (data_word >> 17) & 0b111 == 0b001:
                    header = (data_word >> 17) & 0b111
                    position = (data_word >> 1) & 0xFFFF
                    received_parity = data_word & 1
                    bits_for_parity_check = data_word >> 1
                    num_set_bits = bin(bits_for_parity_check).count('1')
                    expected_parity = 1 if (num_set_bits % 2 != 0) else 0  # Even parity
                    parity_ok = (received_parity == expected_parity)
                    output_frame = AnalyzerFrame('xy2_100_16bit', self.frame_start_time, frame_end_time, {
                        'channel': self.channel_name,
                        'header': f'0b{header:03b}',
                        'position': f'0x{position:04X}',
                        'parity_status': 'OK' if parity_ok else 'FAIL'
                    })
                
                # If header is not recognized, create an error frame.
                else:
                    output_frame = AnalyzerFrame('error', self.frame_start_time, frame_end_time, {
                        'error_message': f'Invalid frame header: 0b{data_word >> 17:03b}'
                    })
                
                # Reset state machine for the next frame
                self.state = 'IDLE'
                self.bits = []
                
                # Store current sync bit for next cycle's edge detection
                self.prev_sync_bit = sync_bit
                return output_frame

        # Store current sync bit for next cycle's edge detection
        self.prev_sync_bit = sync_bit

