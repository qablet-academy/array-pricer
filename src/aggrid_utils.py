"""Utilities for AG Grid"""


def select_cell(field, values, width=100):
    return {
        "headerName": field,
        "field": field,
        "editable": True,
        "cellEditor": "agSelectCellEditor",
        "cellEditorParams": {"values": values},
        "width": width,
    }


def numeric_cell(field, width=100):
    return {
        "headerName": field,
        "field": field,
        "editable": True,
        "type": "numericColumn",
        "cellEditor": "agNumberCellEditor",
        "width": width,
    }


def datestring_cell(field, width=150):
    return {
        "headerName": field,
        "field": field,
        "editable": True,
        "cellEditor": "agDateStringCellEditor",
        "width": width,
    }
