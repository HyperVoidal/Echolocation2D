import arcade
import random
import math
from arcade.tilemap import load_tilemap
import traceback

# Constants
SCREEN_WIDTH = arcade.window_commands.get_display_size()[0]
SCREEN_HEIGHT = arcade.window_commands.get_display_size()[1]
SCREEN_TITLE = "Echolocator"
SPRITE_SCALING_PLAYER = 0.5
SPRITE_SCALING_ENEMY = 0.1  # Make enemies smaller

# Constants for the player
RUNNING_SPEED = 3
WALK_SPEED = 1.5
SHOUT_PAUSE_TIME = 3
SHOUT_COOL = 15 #num of seconds before shout can be used again
RUNDETECTRAD = 400

# Constants for the enemy
ENEMY_SPEED = 3.25
CHASE_RADIUS = 100  # Radius within which the enemy switches to simple pathing

# Constants for the mouse
mouse_x = None
mouse_y = None

class Enemy(arcade.Sprite):
    def __init__(self, window, player):
        super().__init__("images/enemy.png", SPRITE_SCALING_ENEMY)
        self.player = player  # Correctly assign the player instance
        self.window = window
        # Position
        self.center_x = None
        self.center_y = None
        # Movement variables
        self.change_x = 0
        self.change_y = 0
        self.speed = ENEMY_SPEED
        # Path variables
        self.path = []
        self.barrierlist = None
        self.cur_position = 0

    def definebarrierlist(self, player, walls, mapwidth, mapheight, tile_size):
        # Define the barrier list for the enemy
        self.barrierlist = arcade.AStarBarrierList(
            self,  # Use self (the enemy instance) as the moving sprite
            walls,
            tile_size,
            0,
            mapwidth,
            0,
            mapheight
        )

    def spawnenemies(self, enemycount, map_width, map_height, walls, tile_size):
        if enemycount == 1:
            self.center_x = random.randint(0, map_width)
            self.center_y = random.randint(0, map_height)
            self.definebarrierlist(self.player, walls, map_width, map_height, tile_size)  # Use self to call the method
        else:
            print("More than one enemy spawn is not yet supported. :(")
        
    
    def findpath(self, player, walls, mapwidth, mapheight):
        #Find enemy path
            try:
                enemyloc = (self.center_x, self.center_y)
                playerloc = (self.player.center_x, self.player.center_y)
                new_path = arcade.astar_calculate_path(enemyloc, playerloc, self.barrierlist, diagonal_movement=True)
                if new_path:  # Only update the path if a valid one is found
                    self.path = new_path
                print(self.path)
            except Exception:
                traceback.print_exc()
    
    def drawpath(self):
        #draw enemy paths
        try:
            if self.path:
                arcade.draw_line_strip(self.path, arcade.color.BLUE, 2)
            else:
                print("No path to pull from")
        except Exception:
            traceback.print_exc()
            
    def followpath(self):
        try:
            start_x = self.center_x
            start_y = self.center_y
            
            dest_x = self.path[self.cur_position][0]
            dest_y = self.path[self.cur_position][1]
            
            x_diff = dest_x - start_x
            y_diff = dest_y - start_y
            
            # Calculate angle to get there
            angle = math.atan2(y_diff, x_diff)
            
            # How far are we?
            distance = math.sqrt((self.center_x - dest_x) ** 2 + (self.center_y - dest_y) ** 2)

            # How fast should we go? If we are close to our destination,
            # lower our speed so we don't overshoot.
            speed = min(self.speed, distance)
            
            # Calculate vector to travel
            change_x = math.cos(angle) * speed
            change_y = math.sin(angle) * speed
            
            # If we are there, head to the next point.
            if distance <= self.speed:
                self.cur_position += 1
                # Reached the end of the list, start over.
                if self.cur_position >= len(self.position_list):
                    self.cur_position = 0
        except Exception as e:
            print("something happened in followpath idk what")
        
        

    
    
class Player(arcade.Sprite):
    def __init__(self, window):
        super().__init__("images/player.png", SPRITE_SCALING_PLAYER)
        self.window = window
        # Position variables
        self.center_x = 50
        self.center_y = 50
        # Movement variables
        self.change_x = 0
        self.change_y = 0
        self.speed = WALK_SPEED
        # Shout Variables
        self.shout = False
        self.shout_time = SHOUT_PAUSE_TIME
        self.shout_cooldown = SHOUT_COOL
        # Direction variables
        self.forward_x = 0
        self.forward_y = 0
        # Movement state
        self.moving_forwards = False
        self.moving_backwards = False
        self.running = False
        # Mouse position
        self.mouse_x = None
        self.mouse_y = None
        self.echowave_timer = 0.5  # Timer for echowave
        self.is_running_forwards = False  # Flag for running forwards
        self.detection_circle = None  # Store detection circle
        

    def update(self, camera):
        # Update shout time
        if self.shout_time > 0:
            self.shout_time -= 1
        else:
            self.shout = False
        # Update cooldown
        if self.shout_cooldown > 0:
            self.shout_cooldown -= 1
        # Update direction based on mouse position
        self.update_direction(camera)
        # Update position
        if self.moving_forwards:
            self.change_x = self.forward_x * self.speed
            self.change_y = self.forward_y * self.speed
        elif self.moving_backwards:
            self.change_x = -self.forward_x * self.speed
            self.change_y = -self.forward_y * self.speed
        else:
            self.change_x = 0
            self.change_y = 0
        self.center_x += self.change_x
        self.center_y += self.change_y

        if self.is_running_forwards and self.speed == RUNNING_SPEED:
            self.echowave_timer -= 1 / 60  # Assuming 60 FPS
            if self.echowave_timer <= 0:
                self.window.game_view.echowave(step = 0.5, speed = 10, max_range = 100, repetitions=1)
                self.echowave_timer = 0.5  # Reset timer
        else:
            self.echowave_timer = 0.5  # Reset timer if not running
        
        # Update detection circle position
        if self.detection_circle:
            self.detection_circle.center_x = self.center_x
            self.detection_circle.center_y = self.center_y

    def shout_wave(self):
        if self.shout_time == 0 and self.shout_cooldown == 0:
            self.shout = True
            self.shout_time = SHOUT_PAUSE_TIME
            self.shout_cooldown = SHOUT_COOL

    def update_direction(self, camera):
        # Get the position of the mouse using Arcade's built-in methods
        self.mouse_x = self.window._mouse_x + camera.position[0]
        self.mouse_y = self.window._mouse_y + camera.position[1]
        # Get the position of the player
        playerpos = [self.center_x, self.center_y]
        # Get the difference between the two
        diff = [self.mouse_x - playerpos[0], self.mouse_y - playerpos[1]]
        # Normalize the difference
        norm = math.sqrt(diff[0] ** 2 + diff[1] ** 2)
        if norm != 0:
            self.forward_x = diff[0] / norm
            self.forward_y = diff[1] / norm
        # Rotate image to face mouse
        self.angle = math.degrees(math.atan2(diff[1], diff[0])) - 90

        # Stop moving if the player reaches the mouse position
        if norm < 5:
            self.stop()

    def move_forwards(self):
        self.moving_forwards = True
        self.moving_backwards = False
        self.is_running_forwards = True

    def move_backwards(self):
        self.moving_forwards = False
        self.moving_backwards = True
        self.is_running_forwards = False
    
    def runningkey(self):
        self.running = True

    def stop(self):
        self.moving_forwards = False
        self.moving_backwards = False
        self.is_running_forwards = False
        self.running = False
        self.speed = WALK_SPEED
    
    def rundetection(self):
        self.detection_circle = arcade.SpriteSolidColor(RUNDETECTRAD * 2, RUNDETECTRAD * 2, (255, 0, 0, 0))
        self.detection_circle.center_x = self.center_x
        self.detection_circle.center_y = self.center_y
        return self.detection_circle


class Game(arcade.View):
    def __init__(self, window):
        super().__init__(window)
        self.player = None
        self.enemy = None
        self.tile_map = None
        self.scene = None
        self.physics_engine = None
        self.camera = None
        self.mapscale = 1.9
        self.wave_radius = 0
        self.wave_position = None
        self.walls = None  # Store the walls SpriteList
        self.fps = 0  # Add FPS attribute
        self.dot_sprite = None  # For optimized dot drawing
        self.window = window  # Store window reference
        self.walking = False
        self.stopped = True
        self.backcolour = arcade.color.BLACK
        self.enemies = arcade.SpriteList()
        self.enemy_physics_engines = []  # Store physics engines for enemies
        self.chase_time = 0
        # Values for movement keys detecting walking
        self.w_key_held = False
        self.s_key_held = False

    def setup(self):
        self.player = Player(self.window)
        self.player.center_x = 2 * self.mapscale
        self.player.center_y = 2 * self.mapscale

        # Load the tile map
        self.tile_map = load_tilemap("map_files/testingenemyaimap.tmx", self.mapscale)
        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        # Get the walls SpriteList. This is CRUCIAL for your collision detection.
        self.walls = self.scene["Walls"]

        # Add the player to the scene
        self.scene.add_sprite("Player", self.player)

        # Set up the physics engine for collision detection
        self.physics_engine = arcade.PhysicsEngineSimple(self.player, self.walls)

        # Initialise the camera
        self.camera = arcade.Camera(viewport_width=SCREEN_WIDTH, viewport_height=SCREEN_HEIGHT)

        # Initialize the dot sprite
        self.dot_sprite = arcade.Sprite("images/player.png", scale=0.001)
        self.dot_sprite.visible = False

        # Initialize the rectangle sprite
        self.rect_sprite = arcade.SpriteSolidColor(8, 2, arcade.color.RED)
        self.rect_sprite.visible = False

        self.window.game_view = self  # Set game_view reference in window

        map_width = self.tile_map.width * self.tile_map.tile_width * self.mapscale
        map_height = self.tile_map.height * self.tile_map.tile_height * self.mapscale

        self.enemy = Enemy(self.window, player=self.player)  # Pass the player instance
        self.enemy.spawnenemies(1, map_width, map_height, self.walls, self.tile_map.tile_width)  # Call on the Enemy instance

    def echowave(self, step, speed, max_range, repetitions):
        for i in range(repetitions):
            try:
                if self.wave_position is None:
                    self.wave_position = (self.player.center_x, self.player.center_y)
                    self.wave_radius = 0

                self.wave_radius += speed * step

                if self.wave_radius > max_range:
                    self.wave_position = None
                    self.stopped = True  # Ensure stopped is set to True when wave completes
                    return

                if self.wave_position is not None:
                    num_dots = 20
                    thickness = 1

                    angles = [-2 * math.pi * i / num_dots for i in range(num_dots)]  # Rotate angles in the opposite direction

                    for t in range(thickness):
                        numcount = 0
                        for i in range(num_dots):
                            angle = angles[i]
                            radius = self.wave_radius + t * 5  # Precompute the radius addition
                            x = self.wave_position[0] + radius * math.cos(angle)
                            y = self.wave_position[1] + radius * math.sin(angle)

                            a = 255
                            b = 0
                            c = 0
                            alpha = 255

                            self.rect_sprite.center_x = x
                            self.rect_sprite.center_y = y
                            self.rect_sprite.angle = math.degrees(angles[numcount])  # Rotate to face outwards
                            numcount += 1
                            self.rect_sprite.visible = True

                            hit_list = arcade.check_for_collision_with_list(self.rect_sprite, self.walls)
                            if hit_list:
                                a = 0
                                b = 255
                                c = 0
                            
                            if self.rect_sprite.visible: #only draw if it wasn't a collision
                                if self.wave_radius / max_range > 0.2:
                                    alpha = int(255 * (1 - self.wave_radius / max_range))

                                camera_left = self.camera.position[0]
                                camera_bottom = self.camera.position[1]
                                camera_right = camera_left + self.camera.viewport_width
                                camera_top = camera_bottom + self.camera.viewport_height

                                if camera_left <= x <= camera_right and camera_bottom <= y <= camera_top:
                                    arcade.draw_rectangle_filled(x, y, 64, 16, (a, b, c, alpha), self.rect_sprite.angle)

                                self.rect_sprite.visible = False #hide it again

            except Exception:
                traceback.print_exc()

    def on_show(self):
        pass

    def on_draw(self):
        arcade.start_render()
        self.camera.use()
        self.scene.draw()
        arcade.set_background_color(self.backcolour)
        if not self.stopped or self.wave_position is not None:
            if not self.walking:
                self.echowave(step = 0.5, speed = 10, max_range = 100, repetitions=1)
        
        # Draw the detection circle
        if self.player.detection_circle:
            self.player.detection_circle.draw()
        
        # Check if mouse_x and mouse_y are not None before drawing the line
        if self.player.mouse_x is not None and self.player.mouse_y is not None:
            mouse_x = self.player.mouse_x
            mouse_y = self.player.mouse_y
            playerpos = [self.player.center_x, self.player.center_y]
            arcade.draw_line(playerpos[0], playerpos[1], mouse_x, mouse_y, arcade.color.RED, 2)

        # Draw FPS counter
        self.draw_fps()

        self.enemy.draw()

        self.enemy.drawpath()
        
        try:
            arcade.draw_lrtb_rectangle_filled(0, self.mapwidth, self.mapheight, 0, (0, 0, 255, 100))
        except Exception:
            traceback.print_exc()


    def on_update(self, delta_time):
        self.player.update(self.camera)
        self.physics_engine.update()
        self.update_camera()
        self.fps = 1 / delta_time  # Update FPS

        self.enemy.findpath(self.player, self.walls, self.mapwidth, self.mapheight)
        #Allow enemy to follow Path
        self.enemy.followpath()
        


    def draw_fps(self):
        fps_text = f"FPS: {int(self.fps)}"
        camera_left = self.camera.position[0]
        camera_bottom = self.camera.position[1]
        arcade.draw_text(fps_text, camera_left + SCREEN_WIDTH - 10, camera_bottom + SCREEN_HEIGHT - 20, arcade.color.GREEN, 14, anchor_x="right")

    def update_camera(self):
        # Center the camera on the player
        screen_center_x = self.player.center_x - (self.camera.viewport_width / 2)
        screen_center_y = self.player.center_y - (self.camera.viewport_height / 2)

        # Don't let the camera go beyond the boundaries of the map
        map_width = self.tile_map.width * self.tile_map.tile_width * self.mapscale
        map_height = self.tile_map.height * self.tile_map.tile_height * self.mapscale
        self.mapwidth = map_width
        self.mapheight = map_height

        screen_center_x = max(screen_center_x, 0)
        screen_center_y = max(screen_center_y, 0)
        screen_center_x = min(screen_center_x, map_width - self.camera.viewport_width)
        screen_center_y = min(screen_center_y, map_height - self.camera.viewport_height)

        self.camera.move_to((screen_center_x, screen_center_y))

        # Update the player's direction with the adjusted mouse coordinates
        self.player.update_direction(self.camera)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE:
            self.player.shout_wave()
            self.wave_position = None  # Reset wave position when shout is triggered
        if key == arcade.key.W:
            self.stopped = False
            self.player.move_forwards()
            self.player.running = False
            self.w_key_held = True
        if key == arcade.key.S:
            self.stopped = False
            self.player.move_backwards()
            self.player.running = False
            self.s_key_held = True
        if key == arcade.key.R:
            if self.w_key_held or self.s_key_held:
                self.walking = False
                self.player.running = True

                self.player.speed *= 2
        if key == arcade.key.SPACE:
            self.backcolour = arcade.color.WHITE
        if key == arcade.key.ESCAPE:
            self.window.close()
            quit()


    def on_key_release(self, key, modifiers):
        if key == arcade.key.W:
            self.player.stop()
            self.stopped = True
            self.w_key_held = False
        if key == arcade.key.S:
            self.player.stop()
            self.stopped = True
            self.s_key_held = False
        if key == arcade.key.R:
            self.walking = True
            self.player.speed = WALK_SPEED
            self.running = False
            
        if key == arcade.key.SPACE:
            self.backcolour = arcade.color.BLACK

        # Ensure echowave completes its path
        if self.wave_position is not None:
            self.stopped = False

                
        

def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, fullscreen=True)
    game_view = Game(window)  # Initialize game_view HERE
    game_view.__init__(window)
    game_view.setup()
    window.show_view(game_view)
    arcade.run()

if __name__ == "__main__":
    main()