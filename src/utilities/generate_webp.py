from pathlib import Path

from PIL import Image

SOURCE_IMAGE_DIRECTORY = (
    "/Applications/LackeyCCG/plugins/Redemption/sets/setimages/general"
)
TARGET_IMAGE_DIRECTORY = "assets/cardimages"
CARDDATA_FILE = "assets/carddata/carddata.txt"


def load_carddata_filenames() -> set:
    """
    Load all image filenames from carddata.txt to preserve original naming.

    Returns:
        set: Set of original image filenames from carddata.txt
    """
    carddata_filenames = set()

    try:
        with open(CARDDATA_FILE, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):  # Skip empty lines and comments
                    continue

                # Split by tab and get the image filename (3rd column, index 2)
                parts = line.split("\t")
                if len(parts) > 2:
                    image_filename = parts[2].strip()
                    if image_filename:  # Only add non-empty filenames
                        carddata_filenames.add(image_filename)

    except FileNotFoundError:
        print(f"Warning: {CARDDATA_FILE} not found. Using fallback logic.")
    except Exception as e:
        print(f"Error reading {CARDDATA_FILE}: {e}")

    return carddata_filenames


def create_webp_file_dict(target_dir: str, carddata_filenames: set) -> dict:
    """
    Create a dictionary of existing .webp files in the target directory.

    Args:
        target_dir (str): Path to the target directory
        carddata_filenames (set): Set of filenames from carddata.txt

    Returns:
        dict: Dictionary with normalized filenames as keys and full paths as values
    """
    webp_files = {}
    target_path = Path(target_dir)

    if target_path.exists():
        for webp_file in target_path.glob("*.webp"):
            # Store the full webp filename as key for comparison
            webp_files[webp_file.name] = str(webp_file)

    return webp_files


def convert_jpg_to_webp(
    source_dir: str,
    target_dir: str,
    quality: int = 50,
) -> None:
    """
    Convert all .jpg files in source directory to .webp files in target directory,
    preserving filenames and skipping files that already exist.

    Args:
        source_dir (str): Path to source directory containing .jpg files
        target_dir (str): Path to target directory for .webp files
        quality (int): WebP quality (0-100, default: 85)
    """
    source_path = Path(source_dir)
    target_path = Path(target_dir)

    # Create target directory if it doesn't exist
    target_path.mkdir(parents=True, exist_ok=True)

    # Load carddata filenames for proper naming
    carddata_filenames = load_carddata_filenames()
    print(f"Loaded {len(carddata_filenames)} filenames from carddata.txt")

    # Get dictionary of existing .webp files
    existing_webp_files = create_webp_file_dict(target_dir, carddata_filenames)
    print(f"Found {len(existing_webp_files)} existing .webp files in target directory")

    # Process all .jpg files in source directory
    jpg_files = list(source_path.glob("*.jpg")) + list(source_path.glob("*.JPG"))

    if not jpg_files:
        print(f"No .jpg files found in {source_dir}")
        return

    converted_count = 0
    skipped_count = 0

    for jpg_file in jpg_files:
        # Get the expected WebP filename using carddata naming
        expected_webp_filename = normalize_filename_for_webp(
            jpg_file.name, carddata_filenames
        )

        # Check if .webp version already exists
        if expected_webp_filename in existing_webp_files:
            print(f"Skipping {jpg_file.name} - .webp version already exists")
            print(f"  Expected: {expected_webp_filename}")
            skipped_count += 1
            continue

        # Create full path for the new webp file
        webp_path = target_path / expected_webp_filename

        try:
            # Open and convert image
            with Image.open(jpg_file) as img:
                # Convert to RGB if necessary (WebP doesn't support CMYK)
                if img.mode in ("CMYK", "RGBA"):
                    img = img.convert("RGB")

                # Save as WebP
                img.save(webp_path, "WebP", quality=quality, optimize=True)
                print(f"Converted: {jpg_file.name} -> {expected_webp_filename}")
                converted_count += 1

        except Exception as e:
            print(f"Error converting {jpg_file.name}: {str(e)}")

    print("\nConversion complete!")
    print(f"Converted: {converted_count} files")
    print(f"Skipped: {skipped_count} files")


def normalize_filename_for_webp(original_filename: str, carddata_filenames: set) -> str:
    """
    Convert filename to WebP format, preserving original naming from carddata.txt.

    Args:
        original_filename (str): The original .jpg filename
            (e.g., "The-Judean-Mediums-Regional.jpg")
        carddata_filenames (set): Set of filenames from carddata.txt

    Returns:
        str: The WebP filename (e.g., "The-Judean-Mediums-Regional.jpg.webp")
    """
    # Remove .jpg extension from the original filename to get the base name
    if original_filename.lower().endswith(".jpg"):
        base_name = original_filename[:-4]  # Remove .jpg
    else:
        base_name = original_filename

    # Look for this base name in carddata filenames
    for carddata_name in carddata_filenames:
        # Check if the carddata name matches our base name
        if carddata_name == base_name:
            # This is the normal case: carddata has "The_Jeering_Youths_(RA)"
            return f"{carddata_name}.webp"
        elif carddata_name == f"{base_name}.jpg":
            # This is the edge case: carddata has "The-Judean-Mediums-Regional.jpg"
            return f"{carddata_name}.webp"

    # Fallback: if not found in carddata, just add .webp
    return f"{base_name}.webp"


def main():
    """Main function to run the conversion process."""
    print("Starting JPG to WebP conversion...")
    print(f"Source directory: {SOURCE_IMAGE_DIRECTORY}")
    print(f"Target directory: {TARGET_IMAGE_DIRECTORY}")

    # Check if source directory exists
    if not Path(SOURCE_IMAGE_DIRECTORY).exists():
        print(f"Error: Source directory '{SOURCE_IMAGE_DIRECTORY}' does not exist!")
        return

    if not Path(TARGET_IMAGE_DIRECTORY).exists():
        print(f"Error: Target directory '{TARGET_IMAGE_DIRECTORY}' does not exist!")
        return

    # Run the conversion
    convert_jpg_to_webp(SOURCE_IMAGE_DIRECTORY, TARGET_IMAGE_DIRECTORY)


if __name__ == "__main__":
    main()
