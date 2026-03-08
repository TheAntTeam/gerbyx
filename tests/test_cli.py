import pytest
import sys
import json
from pathlib import Path
import subprocess

# Define the root of the project
PROJECT_ROOT = Path(__file__).parent.parent



@pytest.fixture
def gerber_file():
    """Fixture to provide the path to the test Gerber file."""
    return PROJECT_ROOT / "data" / "copper_top.gbr"


def test_cli_geojson_export(gerber_file, tmp_path):
    """Test that the CLI can export a GeoJSON file."""
    output_file = tmp_path / "output.geojson"

    # Run the CLI command
    command = [
        sys.executable,
        "-m",
        "gerbyx.cli",
        str(gerber_file),
        "--output",
        str(output_file),
    ]

    result = subprocess.run(command, capture_output=True, text=True, cwd=PROJECT_ROOT)

    # Check that the command ran successfully
    assert result.returncode == 0, f"CLI command failed with error: {result.stderr}"

    # Check that the output file was created
    assert output_file.exists(), "Output GeoJSON file was not created."

    # Check that the output file is a valid JSON
    with open(output_file, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            pytest.fail("Output file is not a valid JSON.")

    # Check for basic GeoJSON structure
    assert isinstance(data, dict), "GeoJSON data should be a dictionary."
    assert data.get("type") == "FeatureCollection", "GeoJSON 'type' should be 'FeatureCollection'."
    assert "features" in data, "GeoJSON should have a 'features' key."
    assert isinstance(data["features"], list), "'features' should be a list."

    # Check that there is at least one feature
    assert len(data["features"]) > 0, "GeoJSON should contain at least one feature."

    # Check the first feature's structure
    first_feature = data["features"][0]
    assert first_feature.get("type") == "Feature", "Feature 'type' should be 'Feature'."
    assert "geometry" in first_feature, "Feature should have a 'geometry' key."
    assert "properties" in first_feature, "Feature should have a 'properties' key."

    # Check the geometry structure
    geometry = first_feature["geometry"]
    assert "type" in geometry, "Geometry should have a 'type' key."
    assert "coordinates" in geometry, "Geometry should have a 'coordinates' key."
    assert isinstance(geometry["coordinates"], list), "Coordinates should be a list."
