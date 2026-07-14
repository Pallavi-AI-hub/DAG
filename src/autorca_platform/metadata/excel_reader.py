"""Dependency-free reader for the AI AutoRCA architecture workbook."""

from __future__ import annotations

import re
import zipfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

from autorca_platform.core.exceptions import MetadataValidationError

_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_NS = {"a": _MAIN_NS, "r": _REL_NS}
_CELL_REF_PATTERN = re.compile(r"([A-Z]+)([0-9]+)")


@dataclass(frozen=True)
class SheetTable:
    """A sheet table discovered by locating a required header row."""

    name: str
    header_row_number: int
    headers: tuple[str, ...]
    rows: tuple[dict[str, str | int], ...]


@dataclass(frozen=True)
class WorkbookTables:
    """Structured tables extracted from the architecture workbook."""

    dag_inventory: SheetTable
    dag_structure: SheetTable
    incident_catalogue: SheetTable
    expected_ai_rca: SheetTable
    metadata_model: SheetTable

    def schema(self) -> dict[str, tuple[str, ...]]:
        """Return sheet names and discovered headers."""

        return {
            table.name: table.headers
            for table in (
                self.dag_inventory,
                self.dag_structure,
                self.incident_catalogue,
                self.expected_ai_rca,
                self.metadata_model,
            )
        }


class ArchitectureWorkbookReader:
    """Read the architecture workbook into row dictionaries."""

    def read(self, path: Path) -> WorkbookTables:
        """Read all Phase 2-relevant sheets from a workbook.

        Args:
            path: Path to ``.xlsx`` workbook.

        Returns:
            Extracted workbook tables.

        Raises:
            MetadataValidationError: If the workbook cannot be read or lacks required sheets.
        """

        if not path.exists():
            raise MetadataValidationError(f"Workbook does not exist: {path}")
        if path.suffix.lower() != ".xlsx":
            raise MetadataValidationError(f"Workbook must be an .xlsx file: {path}")

        sheets = _read_workbook_cells(path)
        return WorkbookTables(
            dag_inventory=_extract_table(
                sheets,
                "DAG Inventory",
                "DAG ID",
                (
                    "DAG ID",
                    "DAG Name",
                    "Business Domain",
                    "LRJ Category",
                    "Schedule",
                    "SLA",
                    "Priority",
                    "Criticality",
                    "Source",
                    "Destination",
                ),
            ),
            dag_structure=_extract_table(
                sheets,
                "DAG Structure",
                "DAG ID",
                (
                    "DAG ID",
                    "Task Name",
                    "Task Type",
                    "Upstream Tasks",
                    "Downstream Tasks",
                    "Parallel Group",
                    "Trigger Rule",
                    "Dependencies",
                ),
            ),
            incident_catalogue=_extract_table(
                sheets,
                "Incident Catalogue",
                "Incident ID",
                (
                    "Incident ID",
                    "DAG ID",
                    "Incident Name",
                    "Category",
                    "Severity",
                    "Description",
                    "Symptoms",
                    "Root Cause",
                    "Business Impact",
                    "Resolution",
                ),
            ),
            expected_ai_rca=_extract_table(
                sheets,
                "Expected AI RCA",
                "Incident ID",
                (
                    "Incident ID",
                    "Expected RCA Summary",
                    "Evidence Required",
                    "Airflow Logs",
                    "Datadog Metrics",
                    "Confidence Score",
                    "Resolution",
                    "Preventive Action",
                ),
            ),
            metadata_model=_extract_table(
                sheets,
                "Metadata Model",
                "Section",
                (
                    "Section",
                    "Field Name",
                    "Data Type",
                    "Required",
                    "Description",
                    "Example Value",
                ),
            ),
        )


def _column_to_index(column: str) -> int:
    """Convert Excel column letters to a zero-based index."""

    index = 0
    for character in column:
        index = index * 26 + ord(character) - 64
    return index - 1


def _read_workbook_cells(path: Path) -> dict[str, tuple[tuple[int, tuple[str, ...]], ...]]:
    """Read workbook cells directly from OOXML package parts."""

    try:
        with zipfile.ZipFile(path) as workbook_zip:
            shared_strings = _read_shared_strings(workbook_zip)
            workbook_root = ElementTree.fromstring(workbook_zip.read("xl/workbook.xml"))
            rels_root = ElementTree.fromstring(workbook_zip.read("xl/_rels/workbook.xml.rels"))
            relation_targets = {
                relation.attrib["Id"]: relation.attrib["Target"] for relation in rels_root
            }
            sheets: dict[str, tuple[tuple[int, tuple[str, ...]], ...]] = {}
            for sheet in workbook_root.findall("a:sheets/a:sheet", _NS):
                name = sheet.attrib["name"]
                relation_id = sheet.attrib[f"{{{_REL_NS}}}id"]
                target = relation_targets[relation_id].lstrip("/")
                worksheet_path = target if target.startswith("xl/") else f"xl/{target}"
                sheets[name] = _read_sheet_rows(workbook_zip, worksheet_path, shared_strings)
            return sheets
    except KeyError as exc:
        raise MetadataValidationError(f"Workbook is missing required part: {exc}") from exc
    except zipfile.BadZipFile as exc:
        raise MetadataValidationError(f"Workbook is not a readable .xlsx file: {path}") from exc


def _read_shared_strings(workbook_zip: zipfile.ZipFile) -> tuple[str, ...]:
    """Read Excel shared strings from the workbook package."""

    if "xl/sharedStrings.xml" not in workbook_zip.namelist():
        return ()

    root = ElementTree.fromstring(workbook_zip.read("xl/sharedStrings.xml"))
    values: list[str] = []
    for item in root.findall("a:si", _NS):
        values.append("".join(text.text or "" for text in item.findall(".//a:t", _NS)))
    return tuple(values)


def _read_sheet_rows(
    workbook_zip: zipfile.ZipFile,
    worksheet_path: str,
    shared_strings: tuple[str, ...],
) -> tuple[tuple[int, tuple[str, ...]], ...]:
    """Read populated rows from a worksheet package part."""

    worksheet_root = ElementTree.fromstring(workbook_zip.read(worksheet_path))
    rows: list[tuple[int, tuple[str, ...]]] = []
    for row in worksheet_root.findall("a:sheetData/a:row", _NS):
        values: list[str] = []
        for cell in row.findall("a:c", _NS):
            reference = cell.attrib.get("r", "A1")
            match = _CELL_REF_PATTERN.match(reference)
            column_index = _column_to_index(match.group(1)) if match else len(values)
            while len(values) <= column_index:
                values.append("")
            values[column_index] = _read_cell_value(cell, shared_strings)
        rows.append((int(row.attrib.get("r", "0")), tuple(values)))
    return tuple(rows)


def _read_cell_value(cell: ElementTree.Element, shared_strings: tuple[str, ...]) -> str:
    """Read a cell's string value or cached formula value."""

    value = cell.find("a:v", _NS)
    if value is None:
        return ""

    raw_value = value.text or ""
    if cell.attrib.get("t") == "s":
        return shared_strings[int(raw_value)]
    return raw_value


def _extract_table(
    sheets: dict[str, tuple[tuple[int, tuple[str, ...]], ...]],
    sheet_name: str,
    first_header: str,
    required_headers: Iterable[str],
) -> SheetTable:
    """Extract a table by locating its header row."""

    if sheet_name not in sheets:
        raise MetadataValidationError(f"Workbook is missing required sheet '{sheet_name}'.")

    rows = sheets[sheet_name]
    header_index = next(
        (index for index, (_, values) in enumerate(rows) if values and values[0] == first_header),
        None,
    )
    if header_index is None:
        raise MetadataValidationError(
            f"Sheet '{sheet_name}' does not contain expected header '{first_header}'."
        )

    header_row_number, headers = rows[header_index]
    missing_headers = tuple(header for header in required_headers if header not in headers)
    if missing_headers:
        raise MetadataValidationError(
            f"Sheet '{sheet_name}' is missing required headers: {missing_headers}."
        )

    output_rows: list[dict[str, str | int]] = []
    for row_number, values in rows[header_index + 1 :]:
        if not any(value.strip() for value in values):
            continue
        padded_values = values + ("",) * (len(headers) - len(values))
        row = {header: padded_values[index].strip() for index, header in enumerate(headers)}
        row["_row_number"] = row_number
        output_rows.append(row)

    return SheetTable(
        name=sheet_name,
        header_row_number=header_row_number,
        headers=headers,
        rows=tuple(output_rows),
    )
