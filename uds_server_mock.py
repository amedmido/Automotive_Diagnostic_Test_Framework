"""
Automotive ECU Diagnostic Server Mock (ISO 14229 / UDS over CAN)
Simulates standard diagnostic responses, security access, and fault codes.
"""

class ECUDiagnosticServer:
    def __init__(self):
        # Service IDs (SIDs)
        self.SID_DIAG_SESSION_CONTROL = 0x10
        self.SID_CLEAR_DTC            = 0x14
        self.SID_READ_DTC_INFO         = 0x19
        self.SID_READ_DATA_BY_ID       = 0x22
        self.SID_SECURITY_ACCESS       = 0x27
        self.SID_WRITE_DATA_BY_ID      = 0x2E

        # State Variables
        self.active_session = 0x01 # 0x01: Default, 0x02: Programming, 0x03: Extended
        self.security_unlocked = False
        self.seed = 0xBEEF
        
        # Telemetry Data Identifiers (DIDs)
        self.did_database = {
            0xF190: [0x56, 0x49, 0x4E, 0x31, 0x32, 0x33], # VIN: "VIN123"
            0x2001: [0x0E, 0xD8],                          # Battery Voltage (380.0V)
            0x2002: [0x37]                                 # Battery Temp (55 deg C)
        }
        self.active_dtcs = [0x04] # Active Fault: Over-Temperature

    def handle_request(self, payload):
        if not payload or len(payload) == 0:
            return [0x7F, 0x00, 0x13] # Incorrect message length

        sid = payload[0]

        # 1. Diagnostic Session Control (0x10)
        if sid == self.SID_DIAG_SESSION_CONTROL:
            if len(payload) < 2:
                return [0x7F, sid, 0x13]
            sub_function = payload[1]
            if sub_function in [0x01, 0x02, 0x03]:
                self.active_session = sub_function
                return [sid + 0x40, sub_function]
            return [0x7F, sid, 0x12] # SubFunctionNotSupported

        # 2. Read Data By Identifier (0x22)
        elif sid == self.SID_READ_DATA_BY_ID:
            if len(payload) < 3:
                return [0x7F, sid, 0x13]
            did = (payload[1] << 8) | payload[2]
            if did in self.did_database:
                return [sid + 0x40, payload[1], payload[2]] + self.did_database[did]
            return [0x7F, sid, 0x31] # RequestOutOfRange

        # 3. Security Access (0x27)
        elif sid == self.SID_SECURITY_ACCESS:
            sub_function = payload[1]
            if sub_function == 0x01: # Request Seed
                return [sid + 0x40, 0x01, (self.seed >> 8) & 0xFF, self.seed & 0xFF]
            elif sub_function == 0x02: # Send Key
                if len(payload) < 4:
                    return [0x7F, sid, 0x13]
                sent_key = (payload[2] << 8) | payload[3]
                expected_key = self.seed ^ 0xAAAA
                if sent_key == expected_key:
                    self.security_unlocked = True
                    return [sid + 0x40, 0x02]
                return [0x7F, sid, 0x35] # InvalidKey
            return [0x7F, sid, 0x12]

        # 4. Clear Diagnostic Information (0x14)
        elif sid == self.SID_CLEAR_DTC:
            if self.active_session != 0x03:
                return [0x7F, sid, 0x22] # ConditionsNotCorrect
            self.active_dtcs.clear()
            return [sid + 0x40]

        # Default: Service Not Supported
        return [0x7F, sid, 0x11]