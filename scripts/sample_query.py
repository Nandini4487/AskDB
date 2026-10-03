"""
Sample script to verify Chinook SQLite database connectivity.
Executes a sample JOIN and GROUP BY query in strict read-only mode.
"""

import os
from pathlib import Path
import sqlite3


def get_db_path() -> Path:
    """Locate the Chinook SQLite database in data/ directory."""
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"

    # Check for chinook.sqlite or Chinook.sqlite
    candidates = [
        data_dir / "chinook.sqlite",
        data_dir / "Chinook.sqlite",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(f"Chinook database not found in {data_dir}")


def run_sample_query() -> None:
    """Execute a sample JOIN/GROUP BY query on Chinook and display results."""
    db_file = get_db_path()
    print(f"Connecting to database: {db_file}")

    # Rule: Open target database strictly in read-only mode
    # Converting path to URI format for sqlite3
    db_uri = f"{db_file.as_uri()}?mode=ro"
    
    conn = sqlite3.connect(db_uri, uri=True)
    cursor = conn.cursor()

    try:
        # Enforce read-only at the SQLite engine level as defense-in-depth
        cursor.execute("PRAGMA query_only = ON;")

        # Sample analytical query: Top 5 artists by number of tracks
        query = """
        SELECT 
            Artist.Name AS artist_name,
            COUNT(Track.TrackId) AS total_tracks
        FROM Artist
        JOIN Album ON Artist.ArtistId = Album.ArtistId
        JOIN Track ON Album.AlbumId = Track.AlbumId
        GROUP BY Artist.ArtistId, Artist.Name
        ORDER BY total_tracks DESC
        LIMIT 5;
        """

        print("\nExecuting Query:")
        print("----------------")
        print(query.strip())
        print("----------------\n")

        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]

        # Pretty print results
        print(f"{columns[0]:<35} | {columns[1]:<12}")
        print("-" * 50)
        for artist, count in rows:
            print(f"{artist:<35} | {count:<12}")
        print("-" * 50)
        print(f"Successfully retrieved {len(rows)} rows.")

    finally:
        conn.close()


if __name__ == "__main__":
    run_sample_query()
