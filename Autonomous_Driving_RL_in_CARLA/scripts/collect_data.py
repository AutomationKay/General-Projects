import carla

def list_vehicles():
    client = carla.Client("localhost", 2000)
    client.set_timeout(5.0)
    world = client.get_world()
    blueprints = world.get_blueprint_library().filter('vehicle.*')

    print("Available vehicle blueprints:")
    for bp in blueprints:
        print(bp.id)

if __name__ == '__main__':
    list_vehicles()
