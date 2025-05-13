#!/usr/bin/env python3

try:
    print("Attempting to import moviepy...")
    from moviepy.editor import (
        ImageClip,
        AudioFileClip,
        TextClip,
        CompositeVideoClip,
        concatenate_videoclips,
        CompositeAudioClip,
        VideoFileClip
    )
    print("✅ Successfully imported moviepy!")
except ImportError as e:
    print(f"❌ Error importing moviepy: {e}")
    
    # Try to diagnose the issue
    import sys
    print(f"\nPython version: {sys.version}")
    print(f"Python path: {sys.path}")
    
    try:
        import moviepy
        print(f"\nMoviePy version: {moviepy.__version__}")
        print(f"MoviePy path: {moviepy.__file__}")
    except ImportError:
        print("\nCould not import moviepy at all") 