import os
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
from pykml import parser
from lxml import etree

def extract_coordinates(coordinates_text):
    coords = [tuple(map(float, coord.split(','))) for coord in coordinates_text.strip().split()]
    return coords

def extract_placemark_data(placemark):
    data = {}

    name = placemark.find('.//{http://www.opengis.net/kml/2.2}name')
    description = placemark.find('.//{http://www.opengis.net/kml/2.2}description')

    data['name'] = name.text if name is not None else 'No Name'
    data['description'] = description.text if description is not None else 'No Description'

    # Check for different types of geometries
    point = placemark.find('.//{http://www.opengis.net/kml/2.2}Point')
    linestring = placemark.find('.//{http://www.opengis.net/kml/2.2}LineString')
    polygon = placemark.find('.//{http://www.opengis.net/kml/2.2}Polygon')
    gx_track = placemark.find('.//{http://www.google.com/kml/ext/2.2}Track')

    if point is not None:
        coordinates = point.find('.//{http://www.opengis.net/kml/2.2}coordinates')
        if coordinates is not None:
            coords = extract_coordinates(coordinates.text)
            data['geometry'] = Point(coords[0])

    elif linestring is not None:
        coordinates = linestring.find('.//{http://www.opengis.net/kml/2.2}coordinates')
        if coordinates is not None:
            coords = extract_coordinates(coordinates.text)
            data['geometry'] = LineString(coords)

    elif polygon is not None:
        outer_boundary = polygon.find('.//{http://www.opengis.net/kml/2.2}outerBoundaryIs')
        if outer_boundary is not None:
            linear_ring = outer_boundary.find('.//{http://www.opengis.net/kml/2.2}LinearRing')
            if linear_ring is not None:
                coordinates = linear_ring.find('.//{http://www.opengis.net/kml/2.2}coordinates')
                if coordinates is not None:
                    coords = extract_coordinates(coordinates.text)
                    data['geometry'] = Polygon(coords)

    elif gx_track is not None:
        coord_elements = gx_track.findall('.//{http://www.google.com/kml/ext/2.2}coord')
        coords = []
        for coord in coord_elements:
            coords.append(tuple(map(float, coord.text.strip().split())))
        if coords:
            data['geometry'] = LineString(coords)
    
    if 'geometry' not in data:
        data['geometry'] = None

    return data

def kml_to_shp(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.endswith('.kml'):
            kml_file = os.path.join(input_folder, filename)
            shp_file = os.path.join(output_folder, os.path.splitext(filename)[0] + '.shp')

            with open(kml_file, 'r', encoding='utf-8') as f:
                kml_content = f.read()

            root = parser.fromstring(kml_content.encode('utf-8'))

            # Extract Placemarks
            placemarks = root.findall('.//{http://www.opengis.net/kml/2.2}Placemark')
            print(f"Found {len(placemarks)} placemarks in {kml_file}")
            if not placemarks:
                print(f'No Placemarks found in {kml_file}')
                continue

            features = []
            for placemark in placemarks:
                data = extract_placemark_data(placemark)
                print(f"Placemark: {data['name']}, Geometry: {data['geometry']}")
                if data['geometry'] is not None:
                    features.append(data)

            if not features:
                print(f'No valid features found in {kml_file}')
                continue

            gdf = gpd.GeoDataFrame(features)
            gdf.crs = 'EPSG:4326'  # Set CRS to WGS84
            gdf.to_file(shp_file)
            print(f'Converted {kml_file} to {shp_file}')


# Ubah path input dan output folder sesuai kebutuhan
input_folder = r'C:\Users\ASUS\Downloads\input'
output_folder = r'C:\Users\ASUS\Downloads\output'
kml_to_shp(input_folder, output_folder)