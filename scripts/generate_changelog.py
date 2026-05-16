import glob
import json
from datetime import datetime
from pathlib import Path


def main() -> None:
    metadata_files = glob.glob("metadata_files/**/*.json", recursive=True)
    if not metadata_files:
        print("No metadata files found.")
        return

    db_file = Path("changelog.json")
    db = json.loads(db_file.read_text()) if db_file.exists() else {}

    # Merge new metadata
    for mf in metadata_files:
        data = json.loads(Path(mf).read_text())
        pkg = data.get("package")
        version = data.get("version")
        if pkg and version:
            db.setdefault(pkg, {}).setdefault(version, {})
            db[pkg][version].update(data)
            db[pkg][version]["release_date"] = datetime.now().strftime("%Y-%m-%d")

    db_file.write_text(json.dumps(db, indent=2))

    # Generate CHANGELOG.md
    cl_content = "# Plugins Release Changelog\n\n"
    for pkg in sorted(db.keys()):
        cl_content += f"## {pkg}\n\n"

        for version in sorted(db[pkg].keys(), reverse=True):
            data = db[pkg][version]
            date = data["release_date"]
            cl_content += f"### Version {version} ({date})\n\n"

            if "notes" in data:
                cl_content += f"{data['notes']}\n\n"

            for k, v in data.items():
                if k not in ["package", "version", "release_date", "notes"]:
                    formatted_key = k.replace("_", " ").title()
                    formatted_key = (
                        formatted_key.replace("Macos", "macOS")
                        .replace("Onnx", "ONNX")
                        .replace("Ncnn", "NCNN")
                        .replace("Cuda", "CUDA")
                    )
                    cl_content += f"- **{formatted_key}**: {v}\n"
        cl_content += "\n"

    Path("CHANGELOG.md").write_text(cl_content)
    print(f"Changelog generated successfully. Updated {len(db)} packages.")


if __name__ == "__main__":
    main()
