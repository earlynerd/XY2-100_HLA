# High Level Analyzer for the XY2-100 Protocol
# For more information and documentation, please go to https://support.saleae.com/extensions/high-level-analyzer-extensions

from saleae.analyzers import HighLevelAnalyzer, AnalyzerFrame

class Hla(HighLevelAnalyzer):
    """
    Decodes the X, Y, and Z channels of the XY2-100 laser scanner protocol.

    This HLA requires a single 'Simple Parallel' low-level analyzer to be
    configured first with X, Y, Z data lines and the common SYNC line.
    See the README.md for detailed setup instructions.
    """

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
        self.frame_start_time = None
        self.prev_sync_bit = None

        # Initialize bit buffers for each channel
        self.bits_x = []
        self.bits_y = []
        self.bits_z = []

    def _decode_channel(self, channel_name, bits, start_time, end_time):
        """
        Helper function to decode a single channel's data from a 20-bit word.
        Returns an AnalyzerFrame.
        """
        if not bits:
            return None

        data_word = 0
        for bit in bits:
            data_word = (data_word << 1) | bit

        # Check for enhanced 18-bit mode (bit 19 == 1).
        if (data_word >> 19) & 1:
            header = (data_word >> 19) & 1
            position = (data_word >> 1) & 0x3FFFF
            received_parity = data_word & 1
            bits_for_parity_check = data_word >> 1
            num_set_bits = bin(bits_for_parity_check).count('1')
            expected_parity = 1 if (num_set_bits % 2 == 0) else 0  # Odd parity
            parity_ok = (received_parity == expected_parity)
            return AnalyzerFrame('xy2_100_18bit', start_time, end_time, {
                'channel': channel_name,
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
            return AnalyzerFrame('xy2_100_16bit', start_time, end_time, {
                'channel': channel_name,
                'header': f'0b{header:03b}',
                'position': f'0x{position:04X}',
                'parity_status': 'OK' if parity_ok else 'FAIL'
            })
        
        # If header is not recognized, create an error frame.
        else:
            # Only create an error bubble if there was actual data activity.
            # This prevents creating errors for unused (e.g. Z) channels that are all zero.
            if data_word != 0:
                return AnalyzerFrame('error', start_time, end_time, {
                    'error_message': f'Invalid frame header for {channel_name}: 0b{data_word >> 17:03b}'
                })
            return None


    def decode(self, frame: AnalyzerFrame):
        """
        Process a frame from the Simple Parallel analyzer. The HLA can return a
        list of frames, allowing us to output decoded data for X, Y, and Z
        simultaneously.
        """
        if frame.type != 'data' or 'data' not in frame.data:
            return

        parallel_value = frame.data['data']

        # Extract individual bits based on the required channel mapping.
        # D0: X, D1: Y, D2: Z, D3: SYNC
        x_bit = (parallel_value >> 0) & 1
        y_bit = (parallel_value >> 1) & 1
        z_bit = (parallel_value >> 2) & 1
        sync_bit = (parallel_value >> 3) & 1
        
        if self.prev_sync_bit is None:
            self.prev_sync_bit = sync_bit
            return

        if self.state == 'IDLE':
            if sync_bit == 1 and self.prev_sync_bit == 0:
                self.state = 'COLLECTING'
                self.bits_x = [x_bit]
                self.bits_y = [y_bit]
                self.bits_z = [z_bit]
                self.frame_start_time = frame.start_time
        
        elif self.state == 'COLLECTING':
            self.bits_x.append(x_bit)
            self.bits_y.append(y_bit)
            self.bits_z.append(z_bit)

            if len(self.bits_x) == 20:
                frame_end_time = frame.end_time
                output_frames = []

                # Divide the total frame duration into separate slots for each channel
                # to prevent timestamp collisions.
                duration = frame_end_time - self.frame_start_time
                num_channels = 3.0
                duration_per_channel = duration / num_channels

                x_start = self.frame_start_time
                x_end = x_start + duration_per_channel
                y_start = x_end
                y_end = y_start + duration_per_channel
                z_start = y_end
                z_end = frame_end_time
                
                # Decode each channel and add the result to a list of frames.
                x_frame = self._decode_channel('X', self.bits_x, x_start, x_end)
                y_frame = self._decode_channel('Y', self.bits_y, y_start, y_end)
                z_frame = self._decode_channel('Z', self.bits_z, z_start, z_end)
                
                if x_frame: output_frames.append(x_frame)
                if y_frame: output_frames.append(y_frame)
                if z_frame: output_frames.append(z_frame)
                
                # Reset state for the next frame
                self.state = 'IDLE'
                self.bits_x, self.bits_y, self.bits_z = [], [], []
                
                self.prev_sync_bit = sync_bit
                return output_frames

        self.prev_sync_bit = sync_bit

