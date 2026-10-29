"""
Automated Test Suite for Automotive ECU Diagnostic Server (ISO 14229 / UDS)
Validates positive responses, NRC error handling, security access, and fault clearing.
"""

import pytest
from uds_server_mock import ECUDiagnosticServer

@pytest.fixture
def ecu():
    """Initializes a fresh ECU diagnostic server instance for each test."""
    return ECUDiagnosticServer()

# --- Test Case 1: Diagnostic Session Control (0x10) ---
def test_session_transition_to_extended(ecu):
    # Request transition to Extended Diagnostic Session (0x03)
    request = [0x10, 0x03]
    response = ecu.handle_request(request)
    assert response == [0x50, 0x03], "Failed to switch to Extended Session"
    assert ecu.active_session == 0x03

def test_session_invalid_subfunction(ecu):
    # Request invalid session (0x05) -> Expect SubFunctionNotSupported (0x12)
    request = [0x10, 0x05]
    response = ecu.handle_request(request)
    assert response == [0x7F, 0x10, 0x12], "ECU did not reject unsupported sub-function"

# --- Test Case 2: Read Data By Identifier (0x22) ---
def test_read_vin_did(ecu):
    # Read DID 0xF190 (VIN)
    request = [0x22, 0xF1, 0x90]
    response = ecu.handle_request(request)
    expected_payload = [0x62, 0xF1, 0x90, 0x56, 0x49, 0x4E, 0x31, 0x32, 0x33]
    assert response == expected_payload, "VIN Read DID mismatch"

def test_read_invalid_did(ecu):
    # Read non-existent DID 0x9999 -> Expect RequestOutOfRange (0x31)
    request = [0x22, 0x99, 0x99]
    response = ecu.handle_request(request)
    assert response == [0x7F, 0x22, 0x31], "ECU accepted non-existent DID"

# --- Test Case 3: Security Access (0x27) ---
def test_security_access_seed_and_key(ecu):
    # 1. Request Seed
    seed_request = [0x27, 0x01]
    seed_response = ecu.handle_request(seed_request)
    assert seed_response[:2] == [0x67, 0x01]
    
    seed = (seed_response[2] << 8) | seed_response[3]
    
    # 2. Compute Key (Key = Seed ^ 0xAAAA) and Send Key
    valid_key = seed ^ 0xAAAA
    key_request = [0x27, 0x02, (valid_key >> 8) & 0xFF, valid_key & 0xFF]
    key_response = ecu.handle_request(key_request)
    assert key_response == [0x67, 0x02], "Security unlock failed with valid key"
    assert ecu.security_unlocked is True

def test_security_access_invalid_key(ecu):
    # Send incorrect key -> Expect InvalidKey (0x35)
    invalid_key_request = [0x27, 0x02, 0x12, 0x34]
    response = ecu.handle_request(invalid_key_request)
    assert response == [0x7F, 0x27, 0x35], "ECU accepted incorrect security key"
    assert ecu.security_unlocked is False

# --- Test Case 4: Clear Diagnostic Information (0x14) ---
def test_clear_dtc_conditions_not_correct(ecu):
    # Attempt clearing DTCs in Default Session -> Expect ConditionsNotCorrect (0x22)
    ecu.active_session = 0x01
    request = [0x14]
    response = ecu.handle_request(request)
    assert response == [0x7F, 0x14, 0x22], "DTC cleared without Extended Session"

def test_clear_dtc_success_in_extended_session(ecu):
    # Switch to Extended Session then Clear DTCs
    ecu.active_session = 0x03
    request = [0x14]
    response = ecu.handle_request(request)
    assert response == [0x54], "DTC clear failed in Extended Session"
    assert len(ecu.active_dtcs) == 0