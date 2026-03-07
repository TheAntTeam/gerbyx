"""Pytest configuration and shared fixtures"""

import pytest
from pathlib import Path


@pytest.fixture
def fixtures_dir():
    """Return path to test fixtures directory"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def simple_gerber():
    """Simple valid Gerber X3 file"""
    return """
%FSLAX24Y24*%
%MOMM*%
%ADD10C,1.0*%
D10*
X10000Y10000D03*
M02*
"""


@pytest.fixture
def gerber_with_macro():
    """Gerber with macro aperture (using polygon primitive instead of circle)"""
    return """
%FSLAX24Y24*%
%MOMM*%
%AMHEXAGON*
5,1,6,2.0,0,0,0*
%AM*%
%ADD10HEXAGON*%
D10*
X10000Y10000D03*
M02*
"""


@pytest.fixture
def gerber_with_attributes():
    """Gerber with X3 attributes"""
    return """
%FSLAX24Y24*%
%MOMM*%
%TF.FileFunction,Copper,L1,Top*%
%ADD10C,1.0*%
%TO.C,R1*%
%TO.CVal,10K*%
D10*
X10000Y10000D03*
M02*
"""


@pytest.fixture
def gerber_with_region():
    """Gerber with region"""
    return """
%FSLAX24Y24*%
%MOMM*%
G36*
X0Y0D02*
X10000Y0D01*
X10000Y10000D01*
X0Y10000D01*
X0Y0D01*
G37*
M02*
"""


@pytest.fixture
def gerber_with_aperture_block():
    """Gerber with aperture block"""
    return """
%FSLAX24Y24*%
%MOMM*%
%ADD10C,1.0*%
%ABD20*%
D10*
X0Y0D03*
X5000Y0D03*
%ABEND*%
D20*
X10000Y10000D03*
M02*
"""


@pytest.fixture
def invalid_gerber_no_m02():
    """Invalid Gerber - missing M02"""
    return """
%FSLAX24Y24*%
%MOMM*%
%ADD10C,1.0*%
D10*
X10000Y10000D03*
"""


@pytest.fixture
def invalid_gerber_no_fs():
    """Invalid Gerber - missing FS"""
    return """
%MOMM*%
%ADD10C,1.0*%
D10*
X10000Y10000D03*
M02*
"""
