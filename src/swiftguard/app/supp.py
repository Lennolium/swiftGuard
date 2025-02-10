#!/usr/bin/env python3

"""
supp.py: TODO: Headline...

TODO: Description...
"""

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.0.1"
__date__ = "2024-05-21"
__status__ = "Prototype/Development/Production"

# Imports.

# Additional qss styles for individual components/widgets.
state_on = """
#XXX_button{
    background: qlineargradient(spread:pad, x1:0, 
    y1:0, x2:1, y2:0, 
    stop:0 rgb(237, 127, 137), stop:1 rgb(255, 167, 
    167));
    border-radius: 11px;
}

#XXX_button:hover{
    background: qlineargradient(spread:pad, x1:0, y1:0, 
    x2:1, y2:0, stop:0 
    rgb(255, 147, 157), stop:1 rgb(255, 187, 187));
}"""

count_on = """
#XXX_count{
    background-color: rgb(229, 137, 147);
    color: rgb(252, 252, 252);
    font-weight: 600;
    font-size: 11px;
    text-align:center;
    border-radius: 10.4px;
}
"""

state_off = """
#XXX_button{
    background: qlineargradient(spread:pad, x1:0, 
    y1:0, x2:1, y2:0, 
    stop:0 rgb(164, 165, 172), stop:1 rgb(204, 
    205, 
    212));
    border-radius: 11px;
}

#XXX_button:hover{
    background: qlineargradient(spread:pad, x1:0, 
    y1:0, 
    x2:1, y2:0, stop:0 
    rgb(134, 135, 142), stop:1 rgb(204, 205, 212));
}"""

state_off_dark = """
#XXX_button{
    background: qlineargradient(spread:pad, x1:0, 
    y1:0, x2:1, y2:0, 
    stop:0 rgb(74, 75, 82), stop:1 rgb(94, 95, 
    102));
    border-radius: 11px;
}

#XXX_button:hover{
    background: qlineargradient(spread:pad, x1:0, 
    y1:0, 
    x2:1, y2:0, stop:0 
    rgb(94, 95, 102), stop:1 rgb(114, 115, 122));
}"""

state_manip = """
#XXX_button{
    background: qlineargradient(spread:pad, x1:0,
    y1:0, x2:1, y2:0,
    stop:0 rgb(245, 50, 50), stop:1 rgb(245, 80, 
    80));
    border-radius: 11px;
}

#XXX_button:hover{
    background: qlineargradient(spread:pad, x1:0, y1:0,
    x2:1, y2:0, stop:0
    rgb(245, 80, 80), stop:1 rgb(245, 120, 120));
}"""

count_manip = """
#XXX_count{
    background-color: rgb(255, 0, 0);
    color: rgb(252, 252, 252);
    font-weight: 700;
    font-size: 14px;
    text-align:center;
    border-radius: 10.4px;
}
"""

count_off = """
#XXX_count{
    background-color: rgb(164, 165, 172);
    color: rgb(252, 252, 252);
    font-weight: 600;
    font-size: 11px;
    text-align:center;
    border-radius: 10.4px;
}
"""

count_off_dark = """
#XXX_count{
    background-color: rgb(114, 115, 122);
    color: rgb(242, 242, 242);
    font-weight: 600;
    font-size: 11px;
    text-align:center;
    border-radius: 10.4px;
}
"""
