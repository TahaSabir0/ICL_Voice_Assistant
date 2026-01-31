"""
ICL Voice Assistant - Main Entry Point

Run the voice assistant in interactive mode.
"""

import sys
import signal
from src.pipeline import VoicePipeline, PipelineConfig


def main():
    """Main entry point for the ICL Voice Assistant."""
    print("=" * 60)
    print("  ICL Voice Assistant")
    print("  Innovation & Creativity Lab - Gettysburg College")
    print("=" * 60)
    print()
    
    # Create pipeline with default config
    config = PipelineConfig()
    pipeline = VoicePipeline(config)
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\n\nShutting down...")
        pipeline.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Initialize
    print("Initializing voice pipeline...\n")
    if not pipeline.initialize():
        print("Failed to initialize pipeline. Exiting.")
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("  Ready! Press Enter to start listening, or type 'quit' to exit.")
    print("  You can also type a question directly to test the LLM.")
    print("=" * 60)
    print()
    
    # Main loop
    while True:
        try:
            user_input = input("> ").strip()
            
            if user_input.lower() in ('quit', 'exit', 'q'):
                break
            elif user_input == "":
                # Empty input = start voice recording
                result = pipeline.process_turn()
                if result:
                    print(f"\n✅ Turn complete!")
            else:
                # Text input = skip recording
                result = pipeline.process_text(user_input)
                if result:
                    print(f"\n✅ Response complete!")
            
            print()
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            continue
    
    # Cleanup
    pipeline.shutdown()
    print("Goodbye!")


if __name__ == "__main__":
    main()
