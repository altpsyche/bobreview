#!/usr/bin/env python3
"""
Data parsing utilities for BobReview.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class DataPoint:
    """Represents a single performance data point."""
    testcase: str
    tris: int
    draws: int
    ts: int
    img: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert datapoint to dictionary."""
        return {
            'testcase': self.testcase,
            'tris': self.tris,
            'draws': self.draws,
            'ts': self.ts,
            'img': self.img
        }


def parse_filename(filename: str) -> Dict[str, Any]:
    """
    Parse a PNG filename encoding a test case, triangle count, draw calls, and timestamp.
    
    The filename must follow the pattern: TestCase_tricount_drawcalls_timestamp.png
    Example: Level1_85000_520_1234567890.png
    
    Parameters:
        filename (str): The PNG filename to parse.
    
    Returns:
        dict: A dictionary with keys:
            - 'testcase' (str): Test case name.
            - 'tris' (int): Triangle count.
            - 'draws' (int): Draw call count.
            - 'ts' (int): Timestamp.
            - 'img' (str): Original filename.
    
    Raises:
        ValueError: If the file is not a PNG, the format is incorrect, numeric fields cannot be parsed,
                    or any numeric field is negative.
    """
    if not filename.lower().endswith('.png'):
        raise ValueError(f"File must be a PNG: {filename}")
    
    parts = filename.replace('.png', '').replace('.PNG', '').split('_')
    if len(parts) < 4:
        raise ValueError(
            f"Invalid filename format: {filename}\n"
            f"Expected format: TestCase_tricount_drawcalls_timestamp.png\n"
            f"Example: Level1_85000_520_1234567890.png"
        )
    
    try:
        testcase = parts[0]
        tricount = int(parts[1])
        drawcalls = int(parts[2])
        timestamp = int(parts[3])
    except ValueError as e:
        raise ValueError(
            f"Invalid numeric values in filename: {filename}\n"
            f"Triangle count, draw calls, and timestamp must be integers.\n"
            f"Error: {e}"
        ) from e
    
    if tricount < 0 or drawcalls < 0 or timestamp < 0:
        raise ValueError(
            f"Triangle count, draw calls, and timestamp must be non-negative: {filename}"
        )
    
    return {
        'testcase': testcase,
        'tris': tricount,
        'draws': drawcalls,
        'ts': timestamp,
        'img': filename
    }

