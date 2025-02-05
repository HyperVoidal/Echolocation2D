import arcade

print(arcade.version)

try:
    spatial_hash = arcade.SpatialHash()
    print("SpatialHash created!")
except AttributeError as e:
    print(f"Error: {e}")