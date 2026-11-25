import sys
import os

# Add the current directory to sys.path so we can import the deu_miner package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from deu_miner.runner import MinerRunner

if __name__ == "__main__":
    print("Starting DEU DateFields Alpha Miner...")
    runner = MinerRunner()
    try:
        runner.run_loop()
    except KeyboardInterrupt:
        print("\nMiner stopped by user.")
    except Exception as e:
        print(f"\nMiner encountered an error: {e}")
