"""Console script for gerbyx."""

import typer
import json
from rich.console import Console
from pathlib import Path
from shapely.geometry import mapping

from gerbyx.tokenizer import tokenize_gerber
from gerbyx.parser import GerberParser
from gerbyx.processor import GerberProcessor
from gerbyx.visualizer import plot_shapes

app = typer.Typer()
console = Console()


@app.command()
def main(
    file_path: Path = typer.Argument(..., help="Path to the Gerber file to process"),
    output: Path = typer.Option(None, "--output", "-o", help="Output GeoJSON file path"),
    show: bool = typer.Option(False, "--show", "-s", help="Show the plot of the generated geometries"),
):
    """
    Convert a Gerber file to Shapely geometries and export to GeoJSON.
    """
    if not file_path.exists():
        console.print(f"[bold red]Error:[/bold red] File not found: {file_path}")
        raise typer.Exit(code=1)

    console.print(f"[bold green]Processing file:[/bold green] {file_path}")

    try:
        with open(file_path, 'r') as f:
            gerber_source = f.read()
    except Exception as e:
        console.print(f"[bold red]Error reading file:[/bold red] {e}")
        raise typer.Exit(code=1)

    # Initialize Processor and Parser
    processor = GerberProcessor()
    parser = GerberParser(processor)

    # Tokenize
    console.print("Tokenizing...")
    try:
        tokens = tokenize_gerber(gerber_source)
    except Exception as e:
        console.print(f"[bold red]Tokenization Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    # Parse
    console.print("Parsing...")
    try:
        parser.parse(tokens)
    except Exception as e:
        console.print(f"[bold red]Parsing Error:[/bold red] {e}")
        # We might want to continue or exit depending on severity, but here we exit for major errors
        # Note: The parser itself handles some errors gracefully (like bad apertures)
        # raise typer.Exit(code=1)

    # Results
    geometries = processor.geometries
    count = len(geometries)
    console.print(f"[bold blue]Success![/bold blue] Generated {count} geometries.")

    if count > 0:
        # Export to GeoJSON
        if output:
            console.print(f"Exporting to GeoJSON: {output}")
            try:
                geojson_data = {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": mapping(geom),
                            "properties": {"index": i}
                        }
                        for i, geom in enumerate(geometries)
                    ]
                }
                
                with open(output, 'w') as f:
                    json.dump(geojson_data, f, indent=2)
                
                console.print(f"[bold green]GeoJSON exported successfully![/bold green]")
            except Exception as e:
                console.print(f"[bold red]Error exporting GeoJSON:[/bold red] {e}")
                raise typer.Exit(code=1)
        
        # Show plot if requested
        if show:
            console.print("Visualizing...")
            plot_shapes(geometries)
    else:
        console.print("[yellow]Warning:[/yellow] No geometries generated.")


if __name__ == "__main__":
    app()
