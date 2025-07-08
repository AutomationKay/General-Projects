# scripts/my_drive_script.py

import carla
import time
import random

def main():
    actor_list = []

    try:
        # Connect to CARLA server
        client = carla.Client("localhost", 2000)
        client.set_timeout(5.0)
        world = client.get_world()

        blueprint_library = world.get_blueprint_library()
        vehicle_bp = blueprint_library.filter('vehicle.dodge.charger')[0]

        spawn_point = random.choice(world.get_map().get_spawn_points())
        vehicle = world.spawn_actor(vehicle_bp, spawn_point)
        actor_list.append(vehicle)

        # Enable autopilot
        vehicle.set_autopilot(True)

        print("Vehicle spawned and set to autopilot.")
        
        # Move the spectator (camera) to follow the vehicle
        spectator = world.get_spectator()
        transform = vehicle.get_transform()
        spectator.set_transform(carla.Transform(
            transform.location + carla.Location(z=50),  # Camera above the car
            carla.Rotation(pitch=-90)                   # Look straight down
        ))


        # Run for 20 seconds
        start_time = time.time()
        while time.time() - start_time < 20:
            transform = vehicle.get_transform()
            spectator.set_transform(carla.Transform(
                transform.location + carla.Location(z=50),
                carla.Rotation(pitch=-90)
            ))

            velocity = vehicle.get_velocity()
            location = vehicle.get_location()
            print(f"Speed: {velocity}, Position: {location}")
            time.sleep(0.2)

    finally:
        print("Cleaning up actors...")
        for actor in actor_list:
            actor.destroy()

if __name__ == '__main__':
    main()
