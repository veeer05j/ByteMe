
import json
import re
import math

# Healthcare categories accepted in the dataset
VALID_CATEGORIES = ["pharmacy", "clinic", "hospital"]

FILENAME = "dayweave/src/map_data.json"


# Remove locations with missing names
def clean_missing_locations(filename):

    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)

    except FileNotFoundError:
        print("Error: File not found.")
        return False

    except json.JSONDecodeError:
        print("Error: Invalid JSON format.")
        return False

    # Check dataset structure
    if not isinstance(data, dict) or data.get("type") != "FeatureCollection":
        print("Error: Invalid GeoJSON FeatureCollection.")
        return False

    if not isinstance(data.get("features"), list):
        print("Error: Features must be a list.")
        return False

    original_count = len(data["features"])
    cleaned_features = []

    for feature in data["features"]:

        # Keep malformed records so validation can report them
        if not isinstance(feature, dict):
            cleaned_features.append(feature)
            continue

        properties = feature.get("properties")

        if not isinstance(properties, dict):
            cleaned_features.append(feature)
            continue

        # Check name, English name and French name
        has_name = any(
            isinstance(properties.get(field), str)
            and properties[field].strip()
            for field in ["name", "name:en", "name:fr"]
        )

        if has_name:
            cleaned_features.append(feature)

    # Update original dataset
    data["features"] = cleaned_features

    removed_count = original_count - len(cleaned_features)

    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    except OSError as error:
        print(f"Error saving dataset: {error}")
        return False

    print("\n========== DATA CLEANING REPORT ==========")
    print(f"Original locations: {original_count}")
    print(f"Locations removed: {removed_count}")
    print(f"Remaining locations: {len(cleaned_features)}")
    print("Original dataset updated successfully.")
    print("==========================================")

    return True


# Validate the cleaned dataset
def validate_data(filename):

    errors = []
    warnings = []

    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)

    except FileNotFoundError:
        print("Error: File not found.")
        return

    except json.JSONDecodeError:
        print("Error: Invalid JSON format.")
        return

    # Check GeoJSON structure
    if not isinstance(data, dict):
        print("Error: Dataset must be a dictionary.")
        return

    if data.get("type") != "FeatureCollection":
        print("Error: Invalid GeoJSON FeatureCollection.")
        return

    features = data.get("features")

    if not isinstance(features, list):
        print("Error: Features must be a list.")
        return

    existing_ids = set()

    # Validate each healthcare location
    for index, feature in enumerate(features):

        location = f"Location {index + 1}"

        # Check feature structure
        if not isinstance(feature, dict):
            errors.append(f"{location}: Invalid feature format.")
            continue

        if feature.get("type") != "Feature":
            errors.append(f"{location}: Invalid feature type.")

        # Check ID
        feature_id = feature.get("id")

        if not isinstance(feature_id, str) or not feature_id.strip():
            errors.append(f"{location}: Missing or invalid ID.")

        elif feature_id in existing_ids:
            errors.append(f"{location}: Duplicate ID ({feature_id}).")

        else:
            existing_ids.add(feature_id)

        # Check properties
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            errors.append(f"{location}: Missing or invalid properties.")
            continue

        # Check healthcare category
        category = properties.get("amenity")

        if category not in VALID_CATEGORIES:
            errors.append(f"{location}: Invalid healthcare category.")

        # Check facility name
        name = next(
            (
                properties.get(field)
                for field in ["name", "name:en", "name:fr"]
                if isinstance(properties.get(field), str)
                and properties[field].strip()
            ),
            None
        )

        if name is None:
            warnings.append(f"{location}: Missing facility name.")

        # Check geometry
        geometry = feature.get("geometry")

        if not isinstance(geometry, dict):
            errors.append(f"{location}: Missing geometry.")
            continue

        if geometry.get("type") != "Point":
            errors.append(f"{location}: Invalid geometry type.")
            continue

        # Check coordinates
        coordinates = geometry.get("coordinates")

        if not isinstance(coordinates, list) or len(coordinates) != 2:
            errors.append(f"{location}: Invalid coordinates.")
            continue

        longitude, latitude = coordinates

        if not all(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
            for value in coordinates
        ):
            errors.append(f"{location}: Coordinates must be valid numbers.")

        elif not (-180 <= longitude <= 180):
            errors.append(f"{location}: Invalid longitude.")

        elif not (-90 <= latitude <= 90):
            errors.append(f"{location}: Invalid latitude.")

        # Check phone number if provided
        phone = properties.get("phone") or properties.get("contact:phone")

        if phone:
            cleaned_phone = re.sub(r"[\s()\-]", "", str(phone))

            if not re.fullmatch(r"\+?\d{7,15}", cleaned_phone):
                warnings.append(f"{location}: Invalid phone number.")

    # Display validation results
    print("\n========== DATA VALIDATION REPORT ==========")

    print(f"Total locations checked: {len(features)}")
    print(f"Valid unique IDs: {len(existing_ids)}")

    print(f"\nErrors found: {len(errors)}")

    for error in errors:
        print("[ERROR]", error)

    print(f"\nWarnings found: {len(warnings)}")

    for warning in warnings:
        print("[WARNING]", warning)

    if not errors:
        print("\nDATA VALIDATION SUCCESSFUL!")
    else:
        print("\nDATA VALIDATION FAILED!")

    print("============================================")


# Run cleaning first, then validation
if clean_missing_locations(FILENAME):
    validate_data(FILENAME)
