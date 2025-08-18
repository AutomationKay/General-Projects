import sys
import signal
from config import *
from modes.person_follower import PersonFollowingMode
from modes.line_follower import LineFollowingMode, EnhancedLineFollowingMode, test_ir_sensors

class RobotController:
    """
    
    Main robot controller
    
    """
    
    def __init__(self):
        self.current_mode = None
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """
        
        Setup signal handlers for graceful shutdown
        
        """
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """
        
        Handle shutdown signals
        
        
        """

        print("\nReceived shutdown signal. Stopping robot...")
        if self.current_mode:
            self.current_mode.stop_mode()
            self.current_mode.cleanup()
        sys.exit(0)
    
    def run_person_following(self, duration: int = 60, display_video: bool = False):
        """
        
        Run person following mode
        
        """
        print("Starting Person Following Mode...")
        print(f"Duration: {duration} seconds")
        print("Press Ctrl+C to stop early")
        
        try:
            self.current_mode = PersonFollowingMode()
            self.current_mode.run_mode(duration=duration, display_video=display_video)
        
        except Exception as e:
            print(f"Error running person following mode: {e}")
        
        finally:
            if self.current_mode:
                self.current_mode.cleanup()
            self.current_mode = None
    
    def run_line_following(self, duration: int = 60, line_color: str = "black", 
                          display_video: bool = False, enhanced: bool = True):
        """
        
        Run line following mode with optional IR sensor enhancment
        
        """
        mode_type = "Enhanced" if enhanced else "Basic"
        print(f"Starting {mode_type} Line Following Mode...")
        print(f"Line Color: {line_color}")
        print(f"Duration: {duration} seconds")
        if enhanced:
            print("IR Sensors: Enabled")
        print("Press Ctrl+C to stop early")
        
        try:
            if enhanced:
                self.current_mode = EnhancedLineFollowingMode(
                    line_color=line_color, 
                    use_ir_sensors=True
                )
            else:
                # Use original line following without IR sensors
                self.current_mode = LineFollowingMode(line_color=line_color)
                
            self.current_mode.run_mode(duration=duration, display_video=display_video)
            
        except Exception as e:
            print(f"Error running line following mode: {e}")
        finally:
            if self.current_mode:
                self.current_mode.cleanup()
            self.current_mode = None
    
    def test_ir_sensors(self):
        """
        
        Test IR sensor functionality
        
        """
        print("Testing IR Sensor Array...")
        print("This will read sensors for 10 iterations")
        print("Press Ctrl+C to stop early")
        
        try:
            test_ir_sensors()
        except KeyboardInterrupt:
            print("\nIR sensor test stopped by user")
        except Exception as e:
            print(f"Error testing IR sensors: {e}")
    

    def run_interactive_mode(self):
        """
        
        Interactive mode selection
        
        """
        while True:
            print("\n" + "="*50)
            print("🤖 ROBOT CONTROLLER - Multi-Mode System")
            print("="*50)
            print("1. Person Following Mode")
            print("2. Enhanced Line Following Mode (with IR sensors)")
            print("3. Basic Line Following Mode (camera only)")
            print("4. Test IR Sensors")
            print("5. Exit")
            print("="*50)
            
            try:
                choice = input("Select mode (1-5): ").strip()
                
                if choice == "1":
                    duration = int(input("Duration in seconds (default 60): ") or 60)
                    display = input("Display video? (y/n, default n): ").lower().startswith('y')
                    self.run_person_following(duration, display)
                
                elif choice == "2":
                    duration = int(input("Duration in seconds (default 60): ") or 60)
                    color = input("Line color (black/white/red/blue/green, default black): ").strip() or "black"
                    display = input("Display video? (y/n, default n): ").lower().startswith('y')
                    self.run_line_following(duration, color, display, enhanced=True)
                
                elif choice == "3":
                    duration = int(input("Duration in seconds (default 60): ") or 60)
                    color = input("Line color (black/white/red/blue/green, default black): ").strip() or "black"
                    display = input("Display video? (y/n, default n): ").lower().startswith('y')
                    self.run_line_following(duration, color, display, enhanced=False)
                
                elif choice == "4":
                    self.test_ir_sensors()
                
                elif choice == "5":
                    print("Exiting...")
                    break
                
                else:
                    print("Invalid choice. Please select 1-5.")
                    
            except ValueError:
                print("Invalid input. Please enter a number.")
            except KeyboardInterrupt:
                print("\nExiting...")
                break

def main():
    """
    
    Main application function
    
    """

    print("=== Robot Controller - Multi-Mode System ===")
    
    # Create robot controller
    robot = RobotController()
    
   # Check command line arguments
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        
        if mode == "person":
            robot.run_person_following(duration=duration, display_video=not HARDWARE_AVAILABLE)

        elif mode == "line":
            line_color = sys.argv[3] if len(sys.argv) > 3 else "black"
            # Default to enhanced mode, use "basic" as 4th argument to disable IR
            enhanced = sys.argv[4] != "basic" if len(sys.argv) > 4 else True
            robot.run_line_following(
                duration=duration, 
                line_color=line_color, 
                display_video=not HARDWARE_AVAILABLE,
                enhanced=enhanced
            )
            
        elif mode == "test-ir":
            robot.test_ir_sensors()

        else:
            print("Usage: python main.py [person|line|test-ir] [duration] [line_color] [basic]")
            print("Examples:")
            print("  python main.py person 30")
            print("  python main.py line 45 black          # Enhanced mode with IR")
            print("  python main.py line 45 black basic    # Basic mode without IR")
            print("  python main.py test-ir                # Test IR sensors")
    else:
        # Run interactive mode
        robot.run_interactive_mode()

if __name__ == "__main__":
    main()