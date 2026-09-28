#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script for improved regex patterns"""

import re

# Test cases for each specification type
test_cases = {
    'peso': [
        ('Peso dell\'articolo   1,2 Chilogrammi', 1.2, 'Chilogrammi'),
        ('Peso dell\'articolo: 1.2 kg', 1.2, 'kg'),
        ('Peso 2 kg', 2.0, 'kg'),
    ],
    'serbatoio': [
        ('Serbatoio da 1.5L', 1500, 'L'),
        ('Serbatoio: 300ml', 300, 'ml'),
        ('300 ml', 300, 'ml'),
        ('1,8L', 1800, 'L'),
    ],
    'vapore': [
        ('Colpo Vapore 240g/min', 240, 'g/min'),
        ('Vapore continuo 120 g/min', 120, 'g/min'),
        ('500 g', 500, 'g'),
        ('120g', 120, 'g'),
    ],
    'potenza': [
        ('2400W', 2400, 'W'),
        ('Potenza 2400 W', 2400, 'W'),
        ('2200 watt', 2200, 'watt'),
        ('Potenza: 1800W', 1800, 'W'),
    ],
    'cavo': [
        ('Cavo 180 cm', 180, 'cm'),
        ('180cm', 180, 'cm'),
        ('1.8 m', 180, 'm->cm'),
    ],
}

print("=" * 70)
print("TESTING IMPROVED REGEX PATTERNS")
print("=" * 70)

# Test Peso
print("\n[PESO - Weight]")
peso_pattern = r'Peso\s+dell.articolo[:\s]+([0-9,\.]+)\s*(Chilogrammi|kg|g)'
for test_val, expected, unit in test_cases['peso']:
    match = re.search(peso_pattern, test_val, re.IGNORECASE)
    if match:
        peso = float(match.group(1).replace(',', '.'))
        if 'g' in match.group(2).lower() and 'kg' not in match.group(2).lower():
            peso = peso / 1000
        status = "✓ PASS" if abs(peso - expected) < 0.01 else f"✗ FAIL (got {peso}, expected {expected})"
        print(f"  {status}: '{test_val}' -> {peso} kg")
    else:
        print(f"  ✗ NO MATCH: '{test_val}'")

# Test Serbatoio
print("\n[SERBATOIO - Tank Capacity]")
serbatoio_pattern = r'[Ss]erbatoio[:\s]+([0-9,\.]+)\s*([mlL]+|litri?)'
for test_val, expected, unit in test_cases['serbatoio']:
    match = re.search(serbatoio_pattern, test_val, re.IGNORECASE)
    if match:
        tank = float(match.group(1).replace(',', '.'))
        if 'l' in match.group(2).lower() and 'ml' not in match.group(2).lower():
            tank = tank * 1000
        status = "✓ PASS" if abs(tank - expected) < 1 else f"✗ FAIL (got {tank}, expected {expected})"
        print(f"  {status}: '{test_val}' -> {tank} ml")
    else:
        print(f"  ✗ NO MATCH: '{test_val}'")

# Test Vapore
print("\n[VAPORE - Steam Output]")
vapor_pattern = r'(\d+)\s*(?:g(?:/min)?)'
for test_val, expected, unit in test_cases['vapore']:
    match = re.search(vapor_pattern, test_val, re.IGNORECASE)
    if match:
        vapor = int(match.group(1))
        status = "✓ PASS" if vapor == expected else f"✗ FAIL (got {vapor}, expected {expected})"
        print(f"  {status}: '{test_val}' -> {vapor} g/min")
    else:
        print(f"  ✗ NO MATCH: '{test_val}'")

# Test Potenza
print("\n[POTENZA - Power]")
power_pattern = r'(\d{3,4})\s*[wW]?'
for test_val, expected, unit in test_cases['potenza']:
    match = re.search(power_pattern, test_val)
    if match:
        power = int(match.group(1))
        status = "✓ PASS" if power == expected else f"✗ FAIL (got {power}, expected {expected})"
        print(f"  {status}: '{test_val}' -> {power} W")
    else:
        print(f"  ✗ NO MATCH: '{test_val}'")

# Test Cavo
print("\n[CAVO - Cable Length]")
cable_pattern = r'(\d+(?:[,\.]\d+)?)\s*(cm|m(?!m))'
for test_val, expected, unit in test_cases['cavo']:
    match = re.search(cable_pattern, test_val, re.IGNORECASE)
    if match:
        cable = float(match.group(1).replace(',', '.'))
        if match.group(2).lower() == 'm':
            cable = cable * 100
        status = "✓ PASS" if abs(cable - expected) < 1 else f"✗ FAIL (got {cable}, expected {expected})"
        print(f"  {status}: '{test_val}' -> {int(cable)} cm")
    else:
        print(f"  ✗ NO MATCH: '{test_val}'")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)