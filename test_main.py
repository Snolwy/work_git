import json
import os
import tempfile
from unittest.mock import patch

import pytest

from main import process_logs, generate_report, validate_date

def test_validate_date():
    assert validate_date("2023-01-01") == True
    assert validate_date("2023-13-01") == False
    assert validate_date("invalid-date") == False

def test_process_logs_single_file():
    log_content = [
        '{"endpoint": "/api/users", "response_time": 100}',
        '{"endpoint": "/api/users", "response_time": 150}',
        '{"endpoint": "/api/products", "response_time": 200}',
        '{"endpoint": "/api/orders", "response_time": 300}'
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        for line in log_content:
            f.write(line + '\n')
        temp_file = f.name
    
    try:
        stats = process_logs([temp_file])
        
        assert len(stats) == 3
        assert stats['/api/users']['count'] == 2
        assert stats['/api/users']['total_time'] == 250
        assert stats['/api/products']['count'] == 1
        assert stats['/api/products']['total_time'] == 200
        assert stats['/api/orders']['count'] == 1
        assert stats['/api/orders']['total_time'] == 300
        
    finally:
        os.unlink(temp_file)

def test_generate_report():
    stats = {
        '/api/users': {'count': 2, 'total_time': 250},
        '/api/products': {'count': 2, 'total_time': 450}
    }
    
    report = generate_report(stats)
    
    assert len(report) == 2
    assert report[0][0] == '/api/products'  
    assert report[0][1] == 2
    assert report[0][2] == 225.0
    assert report[1][0] == '/api/users'
    assert report[1][1] == 2
    assert report[1][2] == 125.0

def test_process_logs_with_date_filter():
    log_content = [
        '{"timestamp": "2023-01-01T10:00:00Z", "endpoint": "/api/users", "response_time": 100}',
        '{"timestamp": "2023-01-02T10:00:00Z", "endpoint": "/api/users", "response_time": 150}',
        '{"timestamp": "2023-01-01T11:00:00Z", "endpoint": "/api/products", "response_time": 200}'
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        for line in log_content:
            f.write(line + '\n')
        temp_file = f.name
    
    try:
        stats = process_logs([temp_file], "2023-01-01")
        
        assert len(stats) == 2
        assert stats['/api/users']['count'] == 1
        assert stats['/api/products']['count'] == 1
        
    finally:
        os.unlink(temp_file)

def test_empty_log():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        temp_file = f.name
    
    try:
        stats = process_logs([temp_file])
        assert len(stats) == 0
    finally:
        os.unlink(temp_file)

def test_invalid_json_lines():
    log_content = [
        '{"endpoint": "/api/users", "response_time": 100}',
        'invalid json line',
        '{"endpoint": "/api/products", "response_time": 200}'
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        for line in log_content:
            f.write(line + '\n')
        temp_file = f.name
    
    try:
        stats = process_logs([temp_file])
        assert len(stats) == 2
        assert stats['/api/users']['count'] == 1
        assert stats['/api/products']['count'] == 1
        
    finally:
        os.unlink(temp_file)