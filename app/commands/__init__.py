import glob
import os

__all__ = list(set([os.path.basename(f)[:-3] for f in glob.glob(os.path.join(os.path.dirname(__file__), '*.py'))]))